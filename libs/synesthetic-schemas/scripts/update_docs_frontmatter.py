#!/usr/bin/env python3
# ruff: noqa
from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path
import json
from typing import List

ROOT = Path(__file__).resolve().parents[1]


def load_schema_version() -> str:
    v = json.loads((ROOT / "version.json").read_text()).get("schemaVersion")
    if not isinstance(v, str) or not v:
        raise SystemExit("schemaVersion missing in version.json")
    return v


def ensure_frontmatter(path: Path, version: str, owner: str, last_reviewed: str | None) -> None:
    text = path.read_text(encoding="utf-8")
    # Detect existing frontmatter at top: starts with --- and next ---
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    v_tag = f"v{version}" if not version.startswith("v") else version
    today = last_reviewed or dt.date.today().isoformat()

    if m:
        fm = m.group(1)
        # Replace or insert version/owner; keep lastReviewed if present
        def upsert(key: str, value: str, block: str) -> str:
            if re.search(rf"^{key}:[^\n]*$", block, flags=re.MULTILINE):
                return re.sub(rf"^{key}:[^\n]*$", f"{key}: {value}", block, flags=re.MULTILINE)
            return block + f"\n{key}: {value}"

        fm = upsert("version", v_tag, fm)
        fm = upsert("owner", owner, fm)
        if not re.search(r"^lastReviewed:\s*", fm, flags=re.MULTILINE):
            fm = fm + f"\nlastReviewed: {today}"
        new = f"---\n{fm.strip()}\n---\n" + text[m.end():]
        path.write_text(new, encoding="utf-8")
        return

    # No frontmatter — prepend a new one
    fm = "\n".join([
        "---",
        f"version: {v_tag}",
        f"lastReviewed: {today}",
        f"owner: {owner}",
        "---",
        "",
    ])
    path.write_text(fm + text, encoding="utf-8")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Ensure docs frontmatter is present and up-to-date")
    ap.add_argument("files", nargs="*", type=Path, help="Markdown files to update")
    ap.add_argument("--version", dest="version", help="Schema version (X.Y.Z). Defaults to version.json")
    ap.add_argument("--owner", default="delk73")
    ap.add_argument("--last-reviewed", dest="last_reviewed", default=None)
    args = ap.parse_args(argv)

    version = args.version or load_schema_version()
    # If no files provided, scan repo for Markdown (excluding generated outputs)
    if args.files:
        files = list(args.files)
    else:
        files = [
            p for p in ROOT.rglob("*.md")
            if not (p.match("meta/output/*.md") or p.match("meta/SSOT_AUDIT.md"))
        ]
    for f in sorted(files):
        if f.exists():
            ensure_frontmatter(f, version, args.owner, args.last_reviewed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main([]))
