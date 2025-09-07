import json
import os
import logging
import traceback
from copy import deepcopy
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
)

import requests
from fastapi.testclient import TestClient
from app.main import app
from app.schema_version import SCHEMA_VERSION
from app.schemas import ShaderLibCreate
from synesthetic_schemas.synesthetic_asset import (
    SynestheticAsset as SynAssetCreate,
)
from synesthetic_schemas.shader import Shader as ShaderCreate
from synesthetic_schemas.tone import Tone as ToneCreate
from synesthetic_schemas.haptic import Haptic as HapticCreate
from synesthetic_schemas.control_bundle import ControlBundle as ControlCreate
from synesthetic_schemas.modulation import Modulation as ModulationCreate
from synesthetic_schemas.rule_bundle import RuleBundle as RuleBundleSchema
from .logging import get_logger
from app.utils.example_validation import load_example_file, validate_data
from typing import Protocol, runtime_checkable
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)

logger = get_logger(__name__)

# Patterns driven by env at runtime; left here for reference
# Default behavior: assets only; components gated via INCLUDE_COMPONENTS


def _env_flag(name: str, default: str = "0") -> str:
    v = os.getenv(name, default).strip()
    return "1" if v == "1" else "0"


def _bool_env(name: str, default: bool = False) -> bool:
    return _env_flag(name, "1" if default else "0") == "1"


def _examples_root() -> str:
    # Resolve strictly to SSOT unless EXAMPLES_DIR overrides
    return os.getenv("EXAMPLES_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "libs",
        "synesthetic-schemas",
        "examples",
    )


def _is_legacy_examples(path: str) -> bool:
    # Keep existing tests stable when pointing at app/examples
    legacy_dir = os.path.join(os.path.dirname(__file__), "examples")
    try:
        return os.path.abspath(path) == os.path.abspath(legacy_dir)
    except Exception:
        return False


def _startup_banner(root: str) -> None:
    flags = {
        "ONLY_ASSETS": _env_flag("ONLY_ASSETS", "0"),
        "INCLUDE_COMPONENTS": _env_flag("INCLUDE_COMPONENTS", "0"),
        "INCLUDE_SKIP": _env_flag("INCLUDE_SKIP", "0"),
        "DRY_RUN": _env_flag("DRY_RUN", "0"),
        "API_MODE": os.getenv("API_MODE", "inproc"),
        "DISABLE_SCHEMA_HEADER": _env_flag("DISABLE_SCHEMA_HEADER", "0"),
    }
    logger.info(
        f"Loader start | root={root} | model_source=SSOT | flags={flags}"
    )


def _build_patterns() -> List[Tuple[str, str, Type[BaseModel], str]]:
    """Return [(glob, route, model, kind)] respecting env flags.

    kind is one of: asset, shader_lib, shader, tone, haptic, modulation, control
    """
    # INCLUDE_COMPONENTS gates standalone components
    # Default behavior: assets-only for SSOT root; include for non-SSOT roots (legacy/test dirs)
    root = _examples_root()
    ssot_root = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "libs",
        "synesthetic-schemas",
        "examples",
    )
    include_components_default = False
    try:
        if os.getenv("EXAMPLES_DIR") and os.path.abspath(root) != os.path.abspath(ssot_root):
            include_components_default = True
        if _is_legacy_examples(root):
            include_components_default = True
    except Exception:
        pass
    include_components = _bool_env("INCLUDE_COMPONENTS", include_components_default)

    patterns: List[Tuple[str, str, Type[BaseModel], str]] = []

    # Assets first — exact patterns only
    asset_globs = [
        "SynestheticAsset_*.json",
        "SynestheticAsset_Example*.json",
    ]
    for g in asset_globs:
        patterns.append((g, "/synesthetic-assets/nested", SynAssetCreate, "asset"))

    if include_components:
        # Shader library remains local model
        for g in ("ShaderLib_*.json", "ShaderLib_Example*.json"):
            patterns.append((g, "/shader_libs/", ShaderLibCreate, "shader_lib"))
        # SSOT models for components
        for g in ("Shader_*.json", "Shader_Example*.json"):
            patterns.append((g, "/shaders/", ShaderCreate, "shader"))
        for g in ("Tone_*.json", "Tone_Example*.json"):
            patterns.append((g, "/tones/", ToneCreate, "tone"))
        for g in ("Haptic_*.json", "Haptic_Example*.json"):
            patterns.append((g, "/haptics/", HapticCreate, "haptic"))
        for g in ("Modulation_*.json", "Modulation_Example*.json"):
            patterns.append((g, "/modulations/", ModulationCreate, "modulation"))
        for g in ("RuleBundle_*.json", "RuleBundle_Example*.json"):
            # RuleBundle import is optional; keep route if present
            patterns.append((g, "/rule-bundles/", RuleBundleSchema, "rule_bundle"))
        for g in ("ControlBundle_*.json", "Control_Example*.json"):
            patterns.append((g, "/controls/", ControlCreate, "control"))

    return patterns


class ImportError:
    filename: str
    error_type: str
    message: str

    def __init__(self, filename: str, error_type: str, message: str):
        self.filename = filename
        self.error_type = error_type
        self.message = message

    def __str__(self):
        return f"{self.filename}: {self.error_type} - {self.message}"


@runtime_checkable
class ResponseLike(Protocol):
    status_code: int

    def json(self) -> Any: ...

    @property
    def content(self) -> bytes: ...


@runtime_checkable
class ClientLike(Protocol):
    def get(self, url: str, *args: Any, **kwargs: Any) -> ResponseLike: ...

    def post(self, url: str, *args: Any, **kwargs: Any) -> ResponseLike: ...


def count_existing_records(client: ClientLike) -> Dict[str, int]:
    """Get record counts from database endpoints - for informational purposes only"""
    result = {}

    endpoints = [
        "/shader_libs/",
        "/shaders/",
        "/tones/",
        "/controls/",
        "/synesthetic-assets/",
    ]

    for endpoint in endpoints:
        try:
            response = client.get(endpoint)
            if response.status_code == 200:
                records = response.json()
                if isinstance(records, list):
                    result[endpoint] = len(records)
                    if len(records) > 0:
                        logger.info(
                            f"Found {len(records)} existing records in {endpoint}"
                        )
            elif response.status_code != 404:
                logger.warning(
                    f"Unexpected status code {response.status_code} from {endpoint}"
                )
        except Exception as e:
            logger.warning(f"Error checking {endpoint}: {str(e)}")

    return result


def extract_controls_from_synesthetic_asset(asset_data: dict) -> Optional[dict]:
    """
    Extract controls from a synesthetic asset and format them as a Control object
    """
    if "controls" not in asset_data:
        return None

    controls = asset_data.get("controls", [])
    if not controls:
        return None

    # Group controls by control_type
    control_groups = {}
    for control in controls:
        control_type = control.get("control_type")
        if not control_type:
            continue

        if control_type not in control_groups:
            control_groups[control_type] = []

        # Create a control entry without the control_type field
        control_entry = {k: v for k, v in control.items() if k != "control_type"}
        control_groups[control_type].append(control_entry)

    if not control_groups:
        return None

    # Create a Control object
    control_data = {
        "name": f"{asset_data.get('name')} Controls",
        "description": f"Controls for {asset_data.get('name')}",
        "meta_info": {
            "category": "control",
            "tags": asset_data.get("meta_info", {}).get("tags", []),
            "source_asset": asset_data.get("name"),
        },
        "control_parameters": control_groups,
    }

    return control_data


def extract_modulations_from_synesthetic_asset(asset_data: dict) -> Optional[dict]:
    """
    Extract modulations from a synesthetic asset and format them as a Modulation object
    """
    if "modulations" not in asset_data:
        return None

    modulations = asset_data.get("modulations", [])
    if not modulations:
        return None

    # Create a Modulation object
    modulation_data = {
        "name": f"{asset_data.get('name')} Modulations",
        "description": f"Modulations for {asset_data.get('name')}",
        "meta_info": {
            "category": "modulation",
            "tags": asset_data.get("meta_info", {}).get("tags", []),
            "source_asset": asset_data.get("name"),
        },
        "modulations": modulations,
    }

    return modulation_data


def _strip_top_level_schema_ref(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return payload
    result = dict(payload)
    result.pop("$schemaRef", None)
    return result


def _validate_with_model(
    data: Any, schema_type: Type[BaseModel]
) -> List[BaseModel] | str:
    """Return list of validated model instances, or error string."""
    try:
        items = data if isinstance(data, list) else [data]
        models: List[Any] = []
        for item in items:
            payload = _strip_top_level_schema_ref(item) if isinstance(item, dict) else item
            instance = schema_type.model_validate(payload)
            models.append(instance)
        return models
    except Exception as e:
        # Build a concise message
        return str(e)


Entry = Tuple[str, str, BaseModel, str]


def _rglob_many(root: str, patterns: List[str], include_skip: bool) -> List[str]:
    """Recursively find files matching multiple patterns, dedup by absolute path.

    Returns sorted POSIX-style paths.
    """
    p = Path(root)
    paths: Set[str] = set()
    for pat in patterns:
        for fp in p.rglob(pat):
            if not fp.is_file():
                continue
            # filter _skip unless included
            if not include_skip:
                parts = fp.resolve().parts
                if any(seg.endswith("_skip") for seg in parts[:-1]):
                    continue
            try:
                paths.add(fp.resolve().as_posix())
            except Exception:
                paths.add(fp.as_posix())
    return sorted(paths)


def discover_and_validate_examples(
    examples_dir: str,
    load_patterns: List[Tuple[str, str, Type[BaseModel], str]],
    include_skip: bool,
) -> Tuple[Dict[str, List[Entry]], Set[str], List[ImportError]]:
    """Discover example files and validate their contents.

    Returns mapping: filename -> list of (endpoint, route_kind, model_instance, kind)
    """
    import glob

    file_entries: Dict[str, List[Entry]] = {}
    attempted_files: Set[str] = set()
    errors: List[ImportError] = []

    # Dedupe file discovery per (endpoint, kind) and log per-variant counts
    files_by_route: Dict[Tuple[str, str], Set[str]] = {}
    variant_counts: List[Tuple[str, str, int]] = []  # (kind, pattern, count)
    for pattern, endpoint, _schema_type, kind in load_patterns:
        files = _rglob_many(examples_dir, [pattern], include_skip)
        variant_counts.append((kind, pattern, len(files)))
        files_by_route.setdefault((endpoint, kind), set()).update(files)

    # Log per-variant and final deduped counts
    for kind, pattern, cnt in sorted(variant_counts, key=lambda x: (x[0], x[1])):
        logger.info(f"[discover] {kind}:{pattern} -> {cnt}")
    kind_counts: Dict[str, int] = {}
    for (_endpoint, kind), files in files_by_route.items():
        kind_counts[kind] = kind_counts.get(kind, 0) + len(files)
    for k in sorted(kind_counts):
        logger.info(f"[discover] {k}: {kind_counts[k]} unique files")

    # Validate discovered files
    for (endpoint, kind), files in files_by_route.items():
        for filepath in sorted(files):
            if not include_skip:
                parts = os.path.normpath(filepath).split(os.sep)
                if any(p.endswith("_skip") for p in parts[:-1]):
                    continue
            filename = os.path.basename(filepath)
            attempted_files.add(filename)
            try:
                raw = load_example_file(filepath)
            except json.JSONDecodeError as e:
                msg = f"JSON Error at line {e.lineno}, column {e.colno}: {e}"
                logger.error(msg)
                errors.append(ImportError(filename, "JSONDecodeError", msg))
                continue
            except Exception as e:  # pragma: no cover - unexpected errors
                msg = f"File read error: {e}"
                logger.error(msg)
                errors.append(ImportError(filename, "FileError", msg))
                continue

            # Find the schema_type for this (endpoint, kind)
            schema_type: Optional[Type[BaseModel]] = None
            for pat, ep, st, kd in load_patterns:
                if ep == endpoint and kd == kind:
                    schema_type = st
                    break
            if schema_type is None:
                errors.append(ImportError(filename, "ConfigError", "Unknown schema type"))
                continue

            validated = _validate_with_model(raw, schema_type)
            if isinstance(validated, str):
                errors.append(ImportError(filename, "ValidationError", validated))
                continue
            for instance in validated:
                file_entries.setdefault(filename, []).append(
                    (endpoint, filename, instance, kind)
                )

    return file_entries, attempted_files, errors


def extract_controls_and_modulations(
    examples_dir: str,
) -> Tuple[List[dict], List[dict], List[ImportError]]:
    """Extract controls and modulations from synesthetic asset examples."""
    import glob

    controls: List[dict] = []
    modulations: List[dict] = []
    errors: List[ImportError] = []

    pattern_path = os.path.join(examples_dir, "SynestheticAsset_Example*.json")
    for filepath in glob.glob(pattern_path):
        filename = os.path.basename(filepath)
        try:
            data = load_example_file(filepath)
        except json.JSONDecodeError as e:
            msg = f"JSON Error at line {e.lineno}, column {e.colno}: {e}"
            logger.error(msg, exc_info=True)
            errors.append(ImportError(filename, "JSONDecodeError", msg))
            continue
        except Exception as e:  # pragma: no cover - unexpected errors
            msg = f"File read error: {e}"
            logger.error(msg, exc_info=True)
            errors.append(ImportError(filename, "FileError", msg))
            continue

        examples = data if isinstance(data, list) else [data]
        for example in examples:
            control_data = extract_controls_from_synesthetic_asset(example)
            if control_data:
                valid, err = validate_data(control_data, ControlCreate)
                if valid:
                    controls.append(control_data)
                else:
                    logger.error(
                        f"Invalid control data extracted from {filename}: {err}",
                        exc_info=True,
                    )
                    errors.append(ImportError(filename, "ValidationError", err))

            modulation_data = extract_modulations_from_synesthetic_asset(example)
            if modulation_data:
                valid, err = validate_data(modulation_data, ModulationCreate)
                if valid:
                    modulations.append(modulation_data)
                else:
                    logger.error(
                        f"Invalid modulation data extracted from {filename}: {err}",
                        exc_info=True,
                    )
                    errors.append(ImportError(filename, "ValidationError", err))

    return controls, modulations, errors


def _strip_shader_lib_id(payload: dict) -> dict:
    """Deprecated: no-op retained for legacy callers."""
    return payload


def _extract_name(kind: str, model_instance: BaseModel) -> Optional[str]:
    try:
        if kind == "asset":
            return getattr(model_instance, "name", None)
        # All components expose name at top-level
        return getattr(model_instance, "name", None)
    except Exception:
        return None


def _list_items(client_get: Callable[[str], ResponseLike], route: str) -> List[Dict[str, Any]]:
    try:
        resp = client_get(route)
        if getattr(resp, "status_code", 200) == 200:
            data = resp.json()
            return data if isinstance(data, list) else []
    except Exception:
        return []
    return []


def _exists_by_name(
    client_get: Callable[[str], ResponseLike], route: str, name: str
) -> bool:
    # Prefer dedicated GET-by-name if available; fallback to listing
    # No by-name routes in this codebase; filter client-side deterministically
    items = _list_items(client_get, route)
    for item in items:
        if isinstance(item, dict) and item.get("name") == name:
            return True
    return False

CounterStats = Dict[str, int]
CountersByKind = Dict[str, CounterStats]


def post_examples_to_api(
    client: ClientLike,
    file_entries: Dict[str, List[Entry]],
) -> Tuple[Set[str], Set[str], List[ImportError], CountersByKind]:
    """Idempotently POST validated examples to the API.

    Returns (loaded_files, failed_files, errors, counters_by_kind)
    """
    loaded: Set[str] = set()
    failed: Set[str] = set()
    errors: List[ImportError] = []
    counters: CountersByKind = {}

    api_mode = os.getenv("API_MODE", "inproc").strip()
    dry_run = _bool_env("DRY_RUN", False)
    disable_header = _bool_env("DISABLE_SCHEMA_HEADER", False)

    def client_get(path: str) -> ResponseLike:
        if api_mode == "http":
            base = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
            return requests.get(base + path)
        return client.get(path)

    def client_post(path: str, json_payload: Dict[str, Any]) -> ResponseLike:
        headers = {}
        if not disable_header:
            headers["X-Schema-Version"] = SCHEMA_VERSION
        if api_mode == "http":
            base = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
            return requests.post(base + path, json=json_payload, headers=headers)
        return client.post(path, json=json_payload, headers=headers)

    def bump(kind: str, key: str) -> None:
        d = counters.setdefault(
            kind, {"imported": 0, "skipped_existing": 0, "failed": 0}
        )
        d[key] += 1

    for filename, entries in file_entries.items():
        file_success = False
        for endpoint, _fname, instance, kind in entries:
            try:
                name = _extract_name(kind, instance)
                if not name or not isinstance(name, str) or not name.strip():
                    msg = f"Missing or invalid name for {kind}"
                    errors.append(ImportError(filename, "ValidationError", msg))
                    bump(kind, "failed")
                    continue

                # Prevent duplicates deterministically
                if _exists_by_name(client_get, endpoint, name):
                    logger.info(f"Skip existing {kind} '{name}' from {filename}")
                    bump(kind, "skipped_existing")
                    file_success = True
                    continue

                payload_dict: Dict[str, Any] = instance.model_dump(mode="json")
                if dry_run:
                    logger.info(f"DRY_RUN: would import {kind} '{name}' via {endpoint}")
                    bump(kind, "skipped_existing")
                    file_success = True
                    continue

                response = client_post(endpoint, payload_dict)
                status = getattr(response, "status_code", 500)
                if status in (200, 201, 202):
                    file_success = True
                    bump(kind, "imported")
                    logger.info(f"Imported {kind} '{name}' from {filename}")
                elif status == 409:
                    bump(kind, "skipped_existing")
                    file_success = True
                    logger.info(f"Skip existing (409) {kind} '{name}' from {filename}")
                else:
                    err = f"HTTP {status}"
                    try:
                        j = response.json()
                        if isinstance(j, dict) and "detail" in j:
                            err += f": {j['detail']}"
                        else:
                            err += f": {json.dumps(j)[:200]}"
                    except Exception:
                        try:
                            err += f": {response.content.decode()[:200]}"
                        except Exception:
                            pass
                    errors.append(ImportError(filename, "APIError", err))
                    bump(kind, "failed")
            except Exception as e:  # pragma: no cover
                err = f"Unexpected error: {e}"
                logger.error(f"{err}\n{traceback.format_exc()}")
                errors.append(ImportError(filename, "UnexpectedError", err))
                bump(kind, "failed")
        if file_success:
            loaded.add(filename)
        else:
            failed.add(filename)

    return loaded, failed, errors, counters


LAST_SUMMARY: CountersByKind = {}


def summarize_import_results(
    loaded_files: Set[str],
    failed_files: Set[str],
    attempted_files: Set[str],
    counters: CountersByKind,
) -> bool:
    """Log a deterministic summary and return overall success (imported or skipped)."""
    global LAST_SUMMARY
    LAST_SUMMARY = {k: dict(v) for k, v in counters.items()}

    logger.info("\n========== IMPORT SUMMARY ==========")
    order = ["asset", "shader_lib", "shader", "tone", "haptic", "modulation", "control"]
    for kind in order:
        c = counters.get(kind, {"imported": 0, "skipped_existing": 0, "failed": 0})
        logger.info(
            f"{kind}: imported={c['imported']} skipped_existing={c['skipped_existing']} failed={c['failed']}"
        )

    success_count = sum(counters.get(k, {}).get("imported", 0) for k in counters)
    skipped_count = sum(
        counters.get(k, {}).get("skipped_existing", 0) for k in counters
    )
    logger.info(
        (
            f"Files: ok={len(loaded_files)} fail={len(failed_files)} attempted={len(attempted_files)}"
        )
    )
    return (success_count + skipped_count) > 0


def load_examples(client: Optional[ClientLike] = None) -> Tuple[bool, List[ImportError]]:
    """Load Synesthetic examples from SSOT with idempotence and stable summary.

    - EXAMPLES_DIR overrides SSOT root
    - Defaults to assets-only; components behind INCLUDE_COMPONENTS=1
    - Strips only top-level $schemaRef
    - Uses model_dump(mode="json") for POST bodies
    - Sends X-Schema-Version unless disabled
    """
    if client is None:
        client = TestClient(app)

    _startup_banner(_examples_root())
    import_errors: List[ImportError] = []

    # Informational counts (non-fatal)
    try:
        record_counts = count_existing_records(client)
        if sum(record_counts.values()) > 0:
            logger.info(
                f"DB already has {sum(record_counts.values())} records (continuing)"
            )
    except Exception:
        pass

    examples_dir = _examples_root()
    if not os.path.exists(examples_dir):
        # Maintain previous behavior for unit tests expecting DirectoryError
        msg = f"Examples directory not found: {examples_dir}"
        logger.error(msg)
        import_errors.append(ImportError("setup", "DirectoryError", msg))
        return False, import_errors

    include_skip = _bool_env("INCLUDE_SKIP", False)
    patterns = _build_patterns()
    file_entries, attempted_files, errors = discover_and_validate_examples(
        examples_dir, patterns, include_skip
    )
    import_errors.extend(errors)

    loaded_files, failed_files, post_errors, counters = post_examples_to_api(
        client, file_entries
    )
    import_errors.extend(post_errors)

    # Optional protobuf mirroring (skip when DRY_RUN)
    if not _bool_env("DRY_RUN", False):
        try:
            response = client.get("/synesthetic-assets/")
            if response.status_code == 200:
                assets = response.json()
                logger.info(f"\nConverting {len(assets)} synesthetic assets to protobuf")
                for asset in assets:
                    asset_id = asset.get("synesthetic_asset_id")
                    if asset_id is None:
                        continue
                    try:
                        resp = client.post(f"/protobuf-assets/from-synesthetic/{asset_id}")
                        if resp.status_code != 200:
                            import_errors.append(
                                ImportError(
                                    f"synesthetic_asset_{asset_id}",
                                    "APIError",
                                    f"HTTP {resp.status_code}",
                                )
                            )
                    except Exception as e:
                        logger.error(
                            f"Error converting asset {asset_id}: {str(e)}"
                        )
                        import_errors.append(
                            ImportError(
                                f"synesthetic_asset_{asset_id}",
                                "UnexpectedError",
                                str(e),
                            )
                        )
        except Exception:
            pass

    success = summarize_import_results(
        loaded_files, failed_files, attempted_files, counters
    )
    return success, import_errors


if __name__ == "__main__":
    success, errors = load_examples()

    # Log human-readable error summary
    if errors:
        logger.error("\n========== IMPORT ERRORS ==========", exc_info=True)
        for i, error in enumerate(errors, 1):
            logger.error(f"\n[{i}] {error}", exc_info=True)

    # Only exit with error if nothing at all was imported
    if not success:
        logger.error("Failed to load any example files", exc_info=True)
        exit(1)
    elif errors:
        logger.warning(f"Imported some examples but encountered {len(errors)} errors")
        exit(0)  # Partial success - exit with success code
    else:
        logger.info("All examples imported successfully")
        exit(0)
