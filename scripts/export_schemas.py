# scripts/export_schemas.py
# ruff: noqa
# flake8: noqa
# pylint: skip-file
"""
Dump Pydantic schemas -> JSON Schema files.
Run: PYTHONPATH=. python scripts/export_schemas.py --out /tmp/syn-schema-dump
"""

from __future__ import annotations
import argparse, json, pathlib, sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---- IMPORT *SCHEMAS* (Pydantic), NOT DB MODELS ----
from synesthetic_schemas.synesthetic_asset import SynestheticAsset
from synesthetic_schemas.shader import Shader
from synesthetic_schemas.tone import Tone
from synesthetic_schemas.haptic import Haptic
from synesthetic_schemas.control import Control
from synesthetic_schemas.modulation import Modulation
from synesthetic_schemas.rule_bundle import RuleBundle, Rule 

MODELS: dict[str, Any] = {
    "synesthetic-asset": SynestheticAsset,
    "shader": Shader,
    "tone": Tone,
    "haptic": Haptic,
    "control": Control,
    "modulation": Modulation,
    "rule-bundle": RuleBundle,
    "rule": Rule,     
}

def emit_schema(model: Any) -> dict[str, Any]:
    # Pydantic v2
    if hasattr(model, "model_json_schema"):
        return model.model_json_schema()
    # Pydantic v1
    if hasattr(model, "schema"):
        return model.schema()
    raise TypeError(f"{model.__module__}.{model.__name__} is not a Pydantic model")

def clean(schema: dict[str, Any]) -> dict[str, Any]:
    name = str(schema.get("title", "schema")).lower().replace(" ", "-")
    schema.setdefault("$id", f"https://schemas.synesthetic.dev/{name}.schema.json")
    schema.pop("description", None)
    return schema

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="schemas_out")
    args = ap.parse_args()

    out = (REPO_ROOT / args.out)
    out.mkdir(parents=True, exist_ok=True)

    for name, model in MODELS.items():
        s = clean(emit_schema(model))
        (out / f"{name}.schema.json").write_text(json.dumps(s, indent=2, sort_keys=True))
        print(f"wrote {name}.schema.json")

if __name__ == "__main__":
    sys.exit(main())
