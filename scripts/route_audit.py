#!/usr/bin/env python3
import json, os, re, sys

os.environ.setdefault("DATABASE_URL", "sqlite:///tests/data/test.db")
from app.main import app

BAN_PATH = [
    r"/preview($|/)",
    r"/previews($|/)",
    r"/applyPreview($|/)",
    r"/cancelPreview($|/)",
    r"/v0($|/)",
    r"/legacy($|/)",
]
BAN_NAME = [r"libDef"]

ban_path_rx = [re.compile(p) for p in BAN_PATH]
ban_name_rx = [re.compile(p, re.I) for p in BAN_NAME]

def is_banned(path: str, name: str) -> bool:
    if any(rx.search(path) for rx in ban_path_rx):
        return True
    if any(rx.search(name or "") for rx in ban_name_rx):
        return True
    if re.search(r"inputParameters|shaderLibId|synestheticAssetId", path):
        return True
    return False

def main() -> None:
    hits = []
    for r in app.routes:
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", []) or []
        name = getattr(r, "name", "")
        if not path or not methods:
            continue
        for m in methods:
            if m in {"HEAD", "OPTIONS", "TRACE"}:
                continue
            if is_banned(path, name):
                hits.append({"method": m, "path": path, "name": name})
    print(json.dumps({"banned_routes": hits}, indent=2))
    strict = "--strict" in sys.argv
    if strict and hits:
        sys.exit(2)

if __name__ == "__main__":
    main()
