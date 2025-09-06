#!/usr/bin/env python
# ruff: noqa
from __future__ import annotations
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "version.json"


SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def read_version() -> str:
    return json.loads(VERSION_FILE.read_text())["schemaVersion"]


def write_version(v: str) -> None:
    VERSION_FILE.write_text(json.dumps({"schemaVersion": v}, indent=2) + "\n")


def bump(current: str, part: str) -> str:
    m = SEMVER_RE.match(current)
    if not m:
        raise ValueError(f"current version not semver: {current}")
    major, minor, patch = map(int, m.groups())
    if part == "major":
        return f"{major+1}.0.0"
    if part == "minor":
        return f"{major}.{minor+1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch+1}"
    raise ValueError("part must be one of: major, minor, patch")


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Bump schema version and normalize schemas")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--set", dest="set_version", help="Set exact version (e.g., 0.7.1)")
    g.add_argument("--bump", dest="bump_part", choices=["major", "minor", "patch"], help="Bump semver part")
    args = ap.parse_args()

    cur = read_version()
    if args.set_version:
        newv = args.set_version
    else:
        newv = bump(cur, args.bump_part)

    if not SEMVER_RE.match(newv):
        print(f"invalid semver: {newv}", file=sys.stderr)
        return 2

    write_version(newv)
    print(f"version.json updated: {cur} → {newv}")

    # Normalize (write) to propagate $id/x-schema-version and update absolute $ref versions
    rc = run([sys.executable, str(ROOT / "scripts" / "normalize_schemas.py")])
    if rc != 0:
        return rc

    # Optionally run codegen to update generated files; keep it explicit
    print("Done. Run `make codegen-py codegen-ts validate` and commit changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

