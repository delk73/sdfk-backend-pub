from app.main import app


def test_no_lab_routes():
    paths = {r.path for r in app.routes}
    pattern = "/" + "lab"
    assert not any(p.startswith(pattern) for p in paths), paths
