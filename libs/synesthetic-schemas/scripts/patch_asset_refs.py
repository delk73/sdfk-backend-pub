#!/usr/bin/env python
# ruff: noqa
from __future__ import annotations
import json, pathlib, sys
from typing import Any, Dict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "jsonschema" / "synesthetic-asset.schema.json"

# single-source version
BASE_URL = "https://schemas.synesthetic.dev"
try:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.lib.version import schema_version  # type: ignore
    VERSION = schema_version()
except Exception:
    VERSION = "0.1.0"

REF_MAP = {
  "#/$defs/NestedShaderResponse":     f"{BASE_URL}/{VERSION}/shader.schema.json",
  "#/$defs/NestedToneResponse":       f"{BASE_URL}/{VERSION}/tone.schema.json",
  "#/$defs/NestedHapticResponse":     f"{BASE_URL}/{VERSION}/haptic.schema.json",
  "#/$defs/NestedControlResponse":    f"{BASE_URL}/{VERSION}/control.schema.json",
  "#/$defs/NestedModulationResponse": f"{BASE_URL}/{VERSION}/modulation.schema.json",
}

def walk(node: Any) -> None:
    if isinstance(node, dict):
        if "$ref" in node and node["$ref"] in REF_MAP:
            node["$ref"] = REF_MAP[node["$ref"]]
        for v in node.values():
            walk(v)
    elif isinstance(node, list):
        for v in node:
            walk(v)

def main() -> int:
    data: Dict[str, Any] = json.loads(SCHEMA.read_text())
    walk(data)
    # optional: drop now-useless $defs.*Response blocks if they exist
    defs = data.get("$defs") or data.get("definitions")
    if isinstance(defs, dict):
        for k in list(defs.keys()):
            if k.startswith("Nested") and k.endswith("Response"):
                defs.pop(k, None)
    SCHEMA.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print("patched:", SCHEMA.name)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
