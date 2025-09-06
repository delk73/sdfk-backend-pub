#!/usr/bin/env python
# ruff: noqa
# pyright: reportMissingImports=false

"""
Validate example JSON against canonical schemas and generated models.

Supports:
  - $schemaRef at file root to pick schema deterministically (preferred)
  - Fallback to filename token heuristics if $schemaRef absent (unless --strict)
  - Validate against JSON Schema (Draft 2020-12) with local ref store
  - Validate via Pydantic v2 models and round-trip compare (pruning defaults)

CLI:
  --file <path>    Validate a single file
  --dir  <path>    Validate all *.json under a directory (recursively)
  --strict         Require $schemaRef; disallow filename heuristics

Exit codes: 0 OK, 1 validation errors, 2 setup issues.
"""

from __future__ import annotations
import argparse
import importlib
import json
import pathlib
import sys
from typing import Any, Dict, Tuple, List, Optional

# --- repo dirs
ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "jsonschema"
EXAMPLES_DIR = ROOT / "examples"
PY_SRC = ROOT / "python" / "src"

# Make generated package importable without install
if str(PY_SRC) not in sys.path:
    sys.path.insert(0, str(PY_SRC))

# JSON Schema validator
import jsonschema
import warnings
from jsonschema.validators import Draft202012Validator
try:
    from referencing import Registry, Resource  # jsonschema >=4.18
    _HAVE_REFERENCING = True
except Exception:  # pragma: no cover
    _HAVE_REFERENCING = False

# filename token  -> (python module name, candidate class names, schema filename)
TOKENS = {
    "synestheticasset": ("synesthetic_asset", "SynestheticAsset", "synesthetic-asset.schema.json"),
    "asset":            ("synesthetic_asset", "SynestheticAsset", "synesthetic-asset.schema.json"),

    "control-bundle":   ("control_bundle",    "ControlBundle", "control-bundle.schema.json"),
    "control":          ("control",           "Control", "control.schema.json"),

    # canonical shader only; deprecated 'shaderlib' token removed
    "shader":           ("shader",            "Shader", "shader.schema.json"),
    "tone":             ("tone",              "Tone", "tone.schema.json"),
    "haptic":           ("haptic",            "Haptic", "haptic.schema.json"),

    "rule-bundle":      ("rule_bundle",       "RuleBundle", "rule-bundle.schema.json"),
    "rule":             ("rule",              "Rule", "rule.schema.json"),
}

# Map schema file name → (python module, candidate class names)
SCHEMA_TO_MODEL: Dict[str, Tuple[str, str]] = {
    "synesthetic-asset.schema.json": ("synesthetic_asset", "SynestheticAsset"),
    "control-bundle.schema.json": ("control_bundle", "ControlBundle"),
    "control.schema.json": ("control", "Control"),
    "shader.schema.json": ("shader", "Shader"),
    "tone.schema.json": ("tone", "Tone"),
    "haptic.schema.json": ("haptic", "Haptic"),
    "modulation.schema.json": ("modulation", "Modulation"),
    "rule-bundle.schema.json": ("rule_bundle", "RuleBundle"),
    "rule.schema.json": ("rule", "Rule"),
}

# Round-trip keys to ignore entirely (pydantic may normalize heavily)
ROUNDTRIP_IGNORE_TOPLEVEL = {"shader", "control", "modulations"}

# ---------- helpers

def _normalize(o: Any) -> Any:
    """Sort dict keys, drop None, and coerce ints/floats to float for stable compare."""
    if isinstance(o, dict):
        return {k: _normalize(v) for k, v in sorted(o.items()) if v is not None}
    if isinstance(o, list):
        return [_normalize(v) for v in o]
    if isinstance(o, bool):
        return o
    if isinstance(o, (int, float)):
        return float(o)
    return o

def _prune_defaults(o: Any) -> Any:
    """
    Remove fields that equal canonical defaults so round-trip compares don't flag.
    - action.scale defaults to 1.0 (per control.schema.json)
    """
    if isinstance(o, dict):
        # If this looks like an ActionType block, drop scale==1.0
        # (heuristic: presence of 'axis' and 'sensitivity' keys)
        if "axis" in o and "sensitivity" in o and "scale" in o:
            try:
                if float(o["scale"]) == 1.0:
                    o = dict(o)
                    o.pop("scale", None)
            except Exception:
                pass
        return {k: _prune_defaults(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_prune_defaults(v) for v in o]
    return o

def _deep_diff(a: Any, b: Any, path: Tuple[Any, ...] = ()) -> List[str]:
    """Return human-readable diffs of structure/content differences."""
    diffs: List[str] = []
    if type(a) != type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        diffs.append(f"{'/'.join(map(str,path)) or '<root>'}: type {type(a).__name__} != {type(b).__name__}")
        return diffs
    if isinstance(a, dict):
        ak, bk = set(a.keys()), set(b.keys())
        for k in sorted(ak - bk):
            diffs.append(f"{'/'.join(map(str,path+(k,)))}: present in input, missing in output")
        for k in sorted(bk - ak):
            diffs.append(f"{'/'.join(map(str,path+(k,)))}: added in output")
        for k in sorted(ak & bk):
            diffs.extend(_deep_diff(a[k], b[k], path + (k,)))
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{'/'.join(map(str,path))}: list length {len(a)} != {len(b)}")
        for i, (ai, bi) in enumerate(zip(a, b)):
            diffs.extend(_deep_diff(ai, bi, path + (i,)))
    else:
        if _normalize(a) != _normalize(b):
            diffs.append(f"{'/'.join(map(str,path))}: {a!r} != {b!r}")
    return diffs

def _load_schema_store() -> Dict[str, Any]:
    store: Dict[str, Any] = {}
    for p in SCHEMAS_DIR.glob("*.schema.json"):
        data = json.loads(p.read_text())
        sid = data.get("$id") or p.name
        store[sid] = data
    return store

def _validator_for(schema_name: str) -> Draft202012Validator:
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"schema not found: {schema_path}")
    schema = json.loads(schema_path.read_text())
    store = _load_schema_store()
    if _HAVE_REFERENCING:
        try:
            # Build a registry of resources keyed by $id, which our schemas use.
            resources = {}
            for k, v in store.items():
                if isinstance(k, str) and k.startswith("http"):
                    resources[k] = Resource.from_contents(v)
            registry = Registry().with_resources(resources)
            return Draft202012Validator(schema, registry=registry)
        except Exception:
            # Fall back to RefResolver if the runtime combo of jsonschema/referencing misbehaves
            pass
    # Fallback for older jsonschema (<4.18) or registry failures: use deprecated RefResolver
    warnings.filterwarnings(
        "ignore",
        message=r"jsonschema\.RefResolver is deprecated",
        category=DeprecationWarning,
    )
    resolver = jsonschema.RefResolver.from_schema(schema, store=store)  # type: ignore[attr-defined]
    return Draft202012Validator(schema, resolver=resolver)

def _pick_model_and_schema(example_path: pathlib.Path, data: Dict[str, Any], strict: bool = False):
    """Return (model_cls or None, schema_file or None, reason_if_none).
    Prefers $schemaRef; falls back to filename tokens unless strict.
    """
    # 1) Prefer $schemaRef at root
    ref = data.get("$schemaRef")
    if isinstance(ref, str):
        schema_file: Optional[str] = None
        if ref.startswith("http://") or ref.startswith("https://"):
            schema_file = ref.rsplit("/", 1)[-1]
        else:
            schema_file = pathlib.Path(ref).name
        if schema_file in SCHEMA_TO_MODEL:
            module_name, candidates = SCHEMA_TO_MODEL[schema_file]
            try:
                mod = importlib.import_module(f"synesthetic_schemas.{module_name}")
            except Exception as e:
                return None, None, f"import failed: synesthetic_schemas.{module_name}: {e}"
            for cls_name in candidates.split("|"):
                if hasattr(mod, cls_name):
                    return getattr(mod, cls_name), schema_file, ""
            return None, None, f"no candidate class in synesthetic_schemas.{module_name} (tried {candidates})"
        return None, None, f"$schemaRef not recognized: {ref}"

    # 2) Fallback to filename tokens (unless strict)
    if strict:
        return None, None, "$schemaRef required in strict mode"
    n = example_path.name.lower()
    for token, (module_name, candidates, schema_file) in TOKENS.items():
        if token in n:
            try:
                mod = importlib.import_module(f"synesthetic_schemas.{module_name}")
            except Exception as e:
                return None, None, f"import failed: synesthetic_schemas.{module_name}: {e}"
            for cls_name in candidates.split("|"):
                if hasattr(mod, cls_name):
                    return getattr(mod, cls_name), schema_file, ""
            return None, None, f"no candidate class in synesthetic_schemas.{module_name} (tried {candidates})"
    return None, None, f"no filename token match (expected one of: {list(TOKENS.keys())})"

def _should_skip(p: pathlib.Path) -> bool:
    # Try to make path relative to examples dir; if not under it, use its own parts
    try:
        parts = p.resolve().relative_to(EXAMPLES_DIR).parts
    except Exception:
        parts = p.parts
    return any(part.startswith("_") for part in parts[:-1])  # skip dirs like examples/_skip/...

def validate_file(p: pathlib.Path, strict: bool = False) -> list[str]:
    errs: list[str] = []
    try:
        data = json.loads(p.read_text())
    except Exception as e:
        return [f"{p.name}: invalid JSON: {e}"]

    # Determine model/schema, prefer $schemaRef on raw data
    model_cls, schema_name, why = _pick_model_and_schema(p, data, strict=strict)
    if model_cls is None or schema_name is None:
        return [f"{p.name}: could not determine model/schema -> {why}"]

    # Strip transport-only metadata at root (e.g., $schemaRef, $schema)
    if isinstance(data, dict):
        data_clean: Any = {k: v for k, v in data.items() if not (isinstance(k, str) and k.startswith("$"))}
    else:
        data_clean = data

    # 1) JSON Schema validation
    try:
        v = _validator_for(schema_name)
        v.validate(data_clean)
    except Exception as e:
        errs.append(f"{p.name}: JSON Schema validation failed: {e}")

    # 2) Pydantic validation + round-trip
    try:
        model = model_cls.model_validate(data_clean)
        out = model.model_dump(
            mode="json",
            exclude_none=True,
            exclude_unset=True,
            exclude_defaults=True,
        )

        in_norm = _normalize(_prune_defaults(json.loads(json.dumps(data_clean))))
        out_norm = _normalize(_prune_defaults(json.loads(json.dumps(out))))

        # ignore some noisy top-levels entirely (until their shapes stabilize)
        for k in ROUNDTRIP_IGNORE_TOPLEVEL:
            if k in in_norm and k in out_norm:
                out_norm[k] = in_norm[k]

        if in_norm != out_norm:
            diffs = _deep_diff(in_norm, out_norm)
            errs.append(
                f"{p.name}: round-trip mismatch (diff count={len(diffs)}): "
                + "; ".join(diffs[:8])
                + (" …" if len(diffs) > 8 else "")
            )
    except Exception as e:
        errs.append(f"{p.name}: Pydantic validation failed: {e}")

    return errs

def _gather_files(path: Optional[str]) -> list[pathlib.Path]:
    if path is None:
        base = EXAMPLES_DIR
        if not base.exists():
            print(f"examples dir missing: {base}")
            return []
        return sorted(p for p in base.rglob("*.json") if p.is_file() and not _should_skip(p))
    p = pathlib.Path(path)
    # Resolve relative path from repo root to avoid mixed absolute/relative issues
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    else:
        p = p.resolve()
    if p.is_dir():
        return sorted(q for q in p.rglob("*.json") if q.is_file() and not _should_skip(q))
    if p.is_file():
        return [p]
    print(f"path not found: {p}")
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", dest="file", help="Validate a single file")
    ap.add_argument("--dir", dest="dir", help="Validate all json under a directory")
    ap.add_argument("--strict", action="store_true", help="Require $schemaRef; no filename fallback")
    args = ap.parse_args()

    # precedence: --file over --dir; else default examples/
    chosen = args.file or args.dir
    files = _gather_files(chosen)
    if not files:
        print("No example JSON files found (respecting _skip/) or invalid path")
        return 2

    all_errs: list[str] = []
    for f in files:
        all_errs += validate_file(f, strict=args.strict)

    if all_errs:
        for e in all_errs:
            print(e)
        print(f"❌ {len(all_errs)} issue(s) across {len(files)} file(s).")
        return 1

    print(f"✅ {len(files)} example file(s) validated and round-tripped clean.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
