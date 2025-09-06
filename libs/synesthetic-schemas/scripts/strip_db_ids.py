#!/usr/bin/env python
from __future__ import annotations
import json, pathlib, sys

SCHEMAS = pathlib.Path("jsonschema")

def cleanse(p: pathlib.Path) -> bool:
    data = json.loads(p.read_text())
    props = data.get("properties")
    req = set(data.get("required", []))
    changed = False

    if isinstance(props, dict):
        for k in list(props.keys()):
            if k.endswith("_id"):
                props.pop(k, None)
                if k in req:
                    req.remove(k)
                changed = True

    if changed:
        data["required"] = sorted(req) if req else []
        if not data["required"]:
            data.pop("required", None)
        p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return changed

def main() -> int:
    touched = 0
    for fp in sorted(SCHEMAS.glob("*.schema.json")):
        if cleanse(fp):
            print(f"stripped *_id fields: {fp.name}")
            touched += 1
    print(f"done. files updated: {touched}")
    return 0

if __name__ == "__main__":
    sys.exit(main())