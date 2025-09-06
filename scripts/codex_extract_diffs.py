#!/usr/bin/env python3
from __future__ import annotations
import re, sys, pathlib

text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8") if len(sys.argv) > 1 else sys.stdin.read()

def body(name: str) -> str:
    m = re.search(rf"=== {name} BEGIN ===\n(.*?)\n=== {name} END ===", text, re.S)
    return m.group(1).strip() if m else ""

apply_diffs = body("APPLY DIFFS")
cleanup_diffs = body("CLEANUP DIFFS")

outdir = pathlib.Path("tmp"); outdir.mkdir(exist_ok=True)
(pa := outdir / "apply.patch").write_text(apply_diffs + ("\n" if apply_diffs and not apply_diffs.endswith("\n") else ""), encoding="utf-8")
(pc := outdir / "cleanup.patch").write_text(cleanup_diffs + ("\n" if cleanup_diffs and not cleanup_diffs.endswith("\n") else ""), encoding="utf-8")

print(f"Wrote {pa} ({len(apply_diffs)} bytes)")
print(f"Wrote {pc} ({len(cleanup_diffs)} bytes)")
