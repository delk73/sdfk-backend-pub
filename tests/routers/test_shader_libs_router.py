from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.fixtures.factories import create_shader_lib, example_shader_lib_def


def _setup_lib(db: Session) -> int:
    lib_def = example_shader_lib_def()
    row = create_shader_lib(db, **lib_def)
    return row.shaderlib_id


def test_effective_happy_path(db_session, auth_client):
    lib_id = _setup_lib(db_session)
    resp = auth_client.get(f"/shader_libs/{lib_id}/helpers/sdHexagon/effective")
    assert resp.status_code == 200
    data = resp.json()
    assert data["uniforms"] == [
        "u_time",
        "u_resolution",
        "u_backgroundColor",
        "u_gridSize",
        "u_gridColor",
        "u_px",
        "u_py",
        "u_r",
    ]
    assert data["inputParametersSpec"][0]["parameter"] == "u_px"
    assert data["inputParametersSpec"][1]["parameter"] == "u_py"
    assert data["inputParametersSpec"][2]["parameter"] == "u_r"
    assert data["template"]["valid"] is True


def test_effective_unknown_helper(db_session, auth_client):
    lib_id = _setup_lib(db_session)
    resp = auth_client.get(f"/shader_libs/{lib_id}/helpers/unknown/effective")
    assert resp.status_code == 422
    detail = resp.json()["detail"][0]
    assert detail["code"] == "HELPER_NOT_FOUND"


def test_effective_collision(db_session, auth_client):
    lib_def = example_shader_lib_def()
    lib_def["baseInputParametersSpec"].append(
        {
            "name": "radiusBase",
            "parameter": "u_r",
            "path": "u_r",
            "type": "float",
            "default": 0.5,
            "min": 0.1,
            "max": 2.0,
            "step": 0.01,
            "smoothingTime": 0.05,
        }
    )
    row = create_shader_lib(db_session, **lib_def)
    resp = auth_client.get(
        f"/shader_libs/{row.shaderlib_id}/helpers/sdHexagon/effective"
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"][0]
    assert "helpers" in ".".join(map(str, detail["loc"]))
    assert detail["code"] == "COLLISION_BASE_PARAMETER"


def test_openapi_includes_examples(client):
    """Ensure OpenAPI has 200 and 422 examples with code."""
    spec = client.get("/openapi.json").json()
    path = "/shader_libs/{id}/helpers/{name}/effective"
    op = spec["paths"][path]["get"]
    assert "200" in op["responses"] and "422" in op["responses"]
    example_200 = op["responses"]["200"]["content"]["application/json"]["example"]
    assert "uniforms" in example_200
    example_422 = (
        op["responses"]["422"]["content"]["application/json"]["example"]
    )
    assert "code" in example_422["detail"][0]
