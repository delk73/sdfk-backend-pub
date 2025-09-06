from app.main import app
from fastapi.routing import APIRoute


def test_no_ai_routes():
    paths = {r.path for r in app.routes if isinstance(r, APIRoute)}
    assert not any(p.startswith("/llm/") or p.startswith("/ollama/") for p in paths)
    assert "/synesthetic-assets/{asset_id}/generate/{component_type}" not in paths
