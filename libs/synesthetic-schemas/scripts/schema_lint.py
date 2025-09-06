#!/usr/bin/env python
# ruff: noqa
"""
Schema lint: ensure unique $id and shallow $ref resolvability.

Checks:
- No duplicate $id across jsonschema/*.schema.json
- All $ref targets resolve:
  - internal refs (#/...) resolve within the same document
  - absolute refs to https://schemas.synesthetic.dev/<ver>/<file> exist in the store
  - relative refs like "./control.schema.json" exist in jsonschema/

Exit codes: 0 clean, 1 problems, 2 setup error
"""
from __future__ import annotations
import json
import pathlib
import sys
from typing import Any, Dict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "jsonschema"


def loadj(p: pathlib.Path) -> Dict[str, Any]:
    return json.loads(p.read_text())


def _walk(node: Any):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _resolve_internal(root: Dict[str, Any], ref: str) -> bool:
    path = ref[2:].split("/")
    cur: Any = root
    for seg in path:
        if not isinstance(cur, dict) or seg not in cur:
            return False
        cur = cur[seg]
    return True


def lint() -> int:
    if not SCHEMAS.exists():
        print(f"missing jsonschema dir: {SCHEMAS}", file=sys.stderr)
        return 2

    files = sorted(SCHEMAS.glob("*.schema.json"))
    store: Dict[str, Dict[str, Any]] = {}
    ids: Dict[str, pathlib.Path] = {}
    errs: list[str] = []

    # load all
    for p in files:
        data = loadj(p)
        store[p.name] = data
        sid = data.get("$id")
        if isinstance(sid, str):
            if sid in ids:
                errs.append(f"duplicate $id: {sid} in {ids[sid].name} and {p.name}")
            else:
                ids[sid] = p

    # helper to test presence by absolute URL
    def has_abs(url: str) -> bool:
        # expect .../<name>.schema.json
        name = url.rsplit("/", 1)[-1]
        return name in store

    for p in files:
        data = store[p.name]
        for node in _walk(data):
            ref = node.get("$ref") if isinstance(node, dict) else None
            if not isinstance(ref, str):
                continue
            if ref.startswith("#/"):
                if not _resolve_internal(data, ref):
                    errs.append(f"unresolved internal $ref in {p.name}: {ref}")
            elif ref.endswith(".schema.json") and (ref.startswith("http://") or ref.startswith("https://")):
                if not has_abs(ref):
                    errs.append(f"missing absolute $ref target in store for {p.name}: {ref}")
            elif ref.endswith(".schema.json"):
                # treat as local file in jsonschema/
                target = SCHEMAS / pathlib.Path(ref).name
                if not target.exists():
                    errs.append(f"missing local $ref file for {p.name}: {ref}")

    for e in errs:
        print(e)
    if errs:
        print(f"❌ schema-lint: {len(errs)} issue(s)")
        return 1
    print("✅ schema-lint: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(lint())

