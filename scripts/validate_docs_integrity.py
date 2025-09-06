#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
import sys

FENCE = re.compile(r"^```(?:\w+)?\s*$", re.M)

def main() -> int:
    bad: list[str] = []
    for p in Path("docs").rglob("*.md"):
        if "_refresh" in p.parts:
            continue
        text = p.read_text(encoding="utf-8")
        if len(FENCE.findall(text)) % 2 != 0:
            bad.append(f"Unbalanced code fences: {p}")
    if bad:
        print("DOC INTEGRITY FAIL:")
        for line in bad:
            print(line)
        return 1
    print("Doc integrity OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
