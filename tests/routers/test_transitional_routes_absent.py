import re
from app.main import app

BAN_PATH = [
    r"/preview($|/)",
    r"/previews($|/)",
    r"/applyPreview($|/)",
    r"/cancelPreview($|/)",
    r"/v0($|/)",
    r"/legacy($|/)",
]
ban_path_rx = [re.compile(p) for p in BAN_PATH]

def is_banned(path: str) -> bool:
    if any(rx.search(path) for rx in ban_path_rx):
        return True
    if re.search(r"inputParameters|shaderLibId|synestheticAssetId", path):
        return True
    return False

def test_no_transitional_routes_exposed():
    offenders = []
    for r in app.routes:
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", []) or []
        if not path or not methods:
            continue
        for m in methods:
            if m in {"HEAD", "OPTIONS", "TRACE"}:
                continue
            if is_banned(path):
                offenders.append((m, path))
    assert not offenders, f"Transitional routes present: {offenders}"
