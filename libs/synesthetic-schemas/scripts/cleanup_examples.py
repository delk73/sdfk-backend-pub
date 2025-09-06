#!/usr/bin/env python
# ruff: noqa
"""
Clean up example JSON files:

- Strip DB-ish keys that end with *_id (e.g., shader_lib_id) everywhere.
  (Keeps plain "id" fields intact.)
- If an example still uses the old wrapper:
      "control": { "control_parameters": [ ...controls... ] }
  and there's no top-level "controls", convert to:
      "controls": [ ...controls... ]
  and remove the wrapper. If "controls" already exists, we do nothing.

Usage:
  python scripts/cleanup_examples.py --dry-run   # show intended changes
  python scripts/cleanup_examples.py --write     # apply changes in-place
"""

from __future__ import annotations
import argparse
import json
import pathlib
from typing import Any, Dict

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"


def load_json(p: pathlib.Path) -> Dict[str, Any]:
    return json.loads(p.read_text())


def save_json(p: pathlib.Path, data: Dict[str, Any]) -> None:
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def strip_trailing_id_keys(node: Any) -> Any:
    """
    Recursively drop keys that end with `_id`. DO NOT drop plain "id".
    """
    if isinstance(node, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in node.items():
            if k != "id" and k.endswith("_id"):
                # drop DB-ish id fields like shader_lib_id
                continue
            cleaned[k] = strip_trailing_id_keys(v)
        return cleaned
    if isinstance(node, list):
        return [strip_trailing_id_keys(x) for x in node]
    return node


def normalize_controls_wrapper(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    If the doc has the *legacy* wrapper at top level:
        doc["control"] is a dict with "control_parameters": [...]
    and there is NOT already doc["controls"], convert to:
        doc["controls"] = control_parameters
        del doc["control"]
    Otherwise, leave as-is.
    """
    if "controls" in doc:
        # already using canonical array; nothing to do
        return doc

    ctl = doc.get("control")
    if isinstance(ctl, dict) and isinstance(ctl.get("control_parameters"), list):
        doc["controls"] = ctl["control_parameters"]
        del doc["control"]
    return doc


def process_file(p: pathlib.Path) -> tuple[bool, str]:
    """
    Returns (changed, message)
    """
    try:
        data = load_json(p)
    except Exception as e:
        return (False, f"{p.name}: skipped (invalid JSON: {e})")

    before = json.dumps(data, sort_keys=True)
    # IMPORTANT: do *not* invent/reshape anything else
    data = normalize_controls_wrapper(data)
    data = strip_trailing_id_keys(data)
    after = json.dumps(data, sort_keys=True)

    if before != after:
        save_json(p, json.loads(after))
        return (True, f"fixed: {p.name}")
    return (False, f"ok: {p.name} (no changes)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="Apply changes instead of dry-run")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change (default)")
    args = ap.parse_args()
    if not args.write:
        args.dry_run = True  # default to dry-run

    if not EXAMPLES_DIR.exists():
        print(f"examples dir missing: {EXAMPLES_DIR}")
        return 2

    changed = 0
    for p in sorted(EXAMPLES_DIR.rglob("*.json")):
        try:
            data = load_json(p)
        except Exception:
            print(f"{p.name}: skipped (invalid JSON)")
            continue

        # simulate and/or write
        before = json.dumps(data, sort_keys=True)
        data = normalize_controls_wrapper(data)
        data = strip_trailing_id_keys(data)
        after = json.dumps(data, sort_keys=True)

        if before != after:
            if args.write:
                save_json(p, json.loads(after))
                print(f"fixed: {p.name}")
            else:
                print(f"[DRY] would fix: {p.name}")
            changed += 1

    print(f"{'fixed' if args.write else 'would fix'} {changed} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
