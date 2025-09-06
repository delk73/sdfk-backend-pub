import json
import os
import logging
import traceback
from typing import Dict, List, Tuple, Set, Type, Any

from fastapi.testclient import TestClient
from app.main import app
from app.schema_version import SCHEMA_VERSION
from app.schemas import (
    ShaderLibCreate,
    ShaderCreate,
    ToneCreate,
    ControlCreate,
    HapticCreate,
    ModulationCreate,
)
from synesthetic_schemas.synesthetic_asset import (
    SynestheticAsset as SynAssetCreate,
)
from .logging import get_logger
from app.utils.example_validation import load_example_file, validate_data

# Configure logging
logging.basicConfig(level=logging.INFO)

logger = get_logger(__name__)

# Import component examples and nested SynestheticAsset examples (main behavior).
LOAD_PATTERNS: List[Tuple[str, str, Type[Any]]] = [
    ("ShaderLib_Example*.json", "/shader_libs/", ShaderLibCreate),
    ("Shader_Example*.json", "/shaders/", ShaderCreate),
    ("Tone_Example*.json", "/tones/", ToneCreate),
    ("Control_Example*.json", "/controls/", ControlCreate),
    ("Haptic_Example*.json", "/haptics/", HapticCreate),
    (
        "SynestheticAsset_Example*.json",
        "/synesthetic-assets/nested",
        SynAssetCreate,
    ),
]


class ImportError:
    def __init__(self, filename: str, error_type: str, message: str):
        self.filename = filename
        self.error_type = error_type
        self.message = message

    def __str__(self):
        return f"{self.filename}: {self.error_type} - {self.message}"


def count_existing_records(client) -> Dict[str, int]:
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


def extract_controls_from_synesthetic_asset(asset_data: dict) -> dict:
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


def extract_modulations_from_synesthetic_asset(asset_data: dict) -> dict:
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


def discover_and_validate_examples(
    examples_dir: str,
    load_patterns: List[Tuple[str, str, Type[Any]]],
) -> Tuple[Dict[str, List[Tuple[str, dict]]], Set[str], List[ImportError]]:
    """Discover example files and validate their contents."""
    import glob

    file_examples: Dict[str, List[Tuple[str, dict]]] = {}
    attempted_files: Set[str] = set()
    errors: List[ImportError] = []

    for pattern, endpoint, schema_type in load_patterns:
        pattern_path = os.path.join(examples_dir, pattern)
        matching_files = sorted(glob.glob(pattern_path))

        for filepath in matching_files:
            filename = os.path.basename(filepath)
            attempted_files.add(filename)
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
                is_valid, err = validate_data(example, schema_type)
                if is_valid:
                    file_examples.setdefault(filename, []).append((endpoint, example))
                else:
                    logger.error(err, exc_info=True)
                    errors.append(ImportError(filename, "ValidationError", err))

    return file_examples, attempted_files, errors


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
    """Deprecated: no longer mutating examples; retain for legacy callers (no-op)."""
    return payload

def post_examples_to_api(
    client: TestClient,
    file_examples: Dict[str, List[Tuple[str, dict]]],
) -> Tuple[Set[str], Set[str], List[ImportError]]:
    """Post validated examples to the API."""
    loaded: Set[str] = set()
    failed: Set[str] = set()
    errors: List[ImportError] = []

    for filename, entries in file_examples.items():
        file_success = False
        for endpoint, payload in entries:
            # Post examples as-is; any mismatch will be surfaced by validation
            truncated = (
                json.dumps(payload)[:100] + "..."
                if len(json.dumps(payload)) > 100
                else json.dumps(payload)
            )
            logger.info(f"Sending request to {endpoint} with data: {truncated}")
            try:
                # Strip SSOT envelope metadata key if present
                post_payload = payload.copy() if isinstance(payload, dict) else payload
                if isinstance(post_payload, dict):
                    post_payload.pop("$schemaRef", None)
                response = client.post(endpoint, json=post_payload)
                if response.status_code == 200:
                    file_success = True
                    logger.info(f"Successfully loaded example from {filename}")
                else:
                    err = f"HTTP {response.status_code}"
                    try:
                        error_json = response.json()
                        if isinstance(error_json, dict) and "detail" in error_json:
                            err += f": {error_json['detail']}"
                        else:
                            err += f": {json.dumps(error_json)}"
                    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
                        logger.error("Failed to parse error response", exc_info=True)
                        err += f": {response.content.decode()[:200]}"
                    logger.error(
                        f"Failed to load example from {filename}: {err}",
                        exc_info=True,
                    )
                    errors.append(ImportError(filename, "APIError", err))
            except Exception as e:  # pragma: no cover - unexpected errors
                err = f"Unexpected error: {e}"
                logger.error(f"{err}\n{traceback.format_exc()}", exc_info=True)
                errors.append(ImportError(filename, "UnexpectedError", err))
        if file_success:
            loaded.add(filename)
        else:
            failed.add(filename)

    return loaded, failed, errors


def summarize_import_results(
    loaded_files: Set[str], failed_files: Set[str], attempted_files: Set[str]
) -> bool:
    """Log a summary of the import process and return overall success."""
    logger.info("\n========== IMPORT SUMMARY ==========")
    if loaded_files:
        logger.info(
            f"Successfully loaded ({len(loaded_files)}): {', '.join(sorted(loaded_files))}"
        )
    if failed_files:
        logger.error(
            f"Failed to load ({len(failed_files)}): {', '.join(sorted(failed_files))}",
            exc_info=True,
        )

    success_rate = (
        (len(loaded_files) / len(attempted_files) * 100) if attempted_files else 0
    )
    logger.info(
        (
            f"Import stats: {len(loaded_files)} successful, {len(failed_files)} failed out of"
            f" {len(attempted_files)} files ({success_rate:.1f}% success rate)"
        )
    )
    return len(loaded_files) > 0


def load_examples(client=None) -> Tuple[bool, List[ImportError]]:
    """Load example data from JSON files through the API."""
    if client is None:
        client = TestClient(app)

    import_errors: List[ImportError] = []

    record_counts = count_existing_records(client)
    if sum(record_counts.values()) > 0:
        logger.info(
            f"Database already contains {sum(record_counts.values())} records (continuing with import)"
        )

    # Prefer SSOT examples under libs/synesthetic-schemas; allow override via EXAMPLES_DIR
    examples_dir = os.getenv("EXAMPLES_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "libs",
        "synesthetic-schemas",
        "examples",
    )
    # Warn if user points to legacy app/examples path for comparison only
    legacy_dir = os.path.join(os.path.dirname(__file__), "examples")
    if os.getenv("EXAMPLES_DIR"):
        cfg = os.path.abspath(os.getenv("EXAMPLES_DIR"))
        if os.path.abspath(cfg) == os.path.abspath(legacy_dir):
            logger.warning(
                "Using local examples path '%s' (comparison only). Prefer SSOT path 'libs/synesthetic-schemas/examples' or set EXAMPLES_DIR accordingly.",
                cfg,
            )
    if not os.path.exists(examples_dir):
        logger.error(f"Examples directory not found: {examples_dir}", exc_info=True)
        import_errors.append(
            ImportError(
                "setup",
                "DirectoryError",
                f"Examples directory not found: {examples_dir}",
            )
        )
        return False, import_errors

    file_examples, attempted_files, errors = discover_and_validate_examples(
        examples_dir, LOAD_PATTERNS
    )
    import_errors.extend(errors)

    loaded_files, failed_files, post_errors = post_examples_to_api(
        client, file_examples
    )
    import_errors.extend(post_errors)

    # After loading all assets, mirror synesthetic assets to protobuf assets
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
                        f"Error converting asset {asset_id}: {str(e)}", exc_info=True
                    )
                    import_errors.append(
                        ImportError(
                            f"synesthetic_asset_{asset_id}", "UnexpectedError", str(e)
                        )
                    )
    except Exception as e:
        logger.error(
            f"Failed to fetch synesthetic assets for proto conversion: {str(e)}",
            exc_info=True,
        )

    success = summarize_import_results(loaded_files, failed_files, attempted_files)
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
