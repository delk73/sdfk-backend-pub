import os
import pytest
from app.proto import asset_pb2
from app.load_examples import load_examples


@pytest.fixture
def examples_env():
    """Use the repository example directory for loading"""
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    examples_dir = os.path.join(current_dir, "app", "examples")

    original_examples_dir = os.getenv("EXAMPLES_DIR")
    os.environ["EXAMPLES_DIR"] = examples_dir

    yield examples_dir

    if original_examples_dir:
        os.environ["EXAMPLES_DIR"] = original_examples_dir
    elif "EXAMPLES_DIR" in os.environ:
        del os.environ["EXAMPLES_DIR"]


example = {
    "name": "Proto Asset Example",
    "description": "example",
    "shader": {
        "name": "s",
        "vertex_shader": "v",
        "fragment_shader": "f",
        "shader_lib_id": 1,
        "uniforms": [],
    },
    "tone": {
        "name": "t",
        "synth": {"type": "Tone.Synth", "volume": 0, "detune": 0, "portamento": 0},
    },
}


def to_proto(data: dict) -> bytes:
    from app.utils.proto_converter import asset_to_proto

    return asset_to_proto(data).SerializeToString()


def from_proto(data: bytes) -> asset_pb2.Asset:
    obj = asset_pb2.Asset()
    obj.ParseFromString(data)
    return obj


def test_proto_asset_crud(clean_db, client):
    resp = client.post(
        "/protobuf-assets/",
        data=to_proto(example),
        headers={"Content-Type": "application/x-protobuf"},
    )
    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("Content-Disposition", "")
    created = from_proto(resp.content)
    assert created.name == example["name"]

    asset_id = 1

    resp = client.get(f"/protobuf-assets/{asset_id}")
    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("Content-Disposition", "")
    fetched = from_proto(resp.content)
    assert fetched.name == example["name"]

    updated = example.copy()
    updated["description"] = "new"
    resp = client.put(
        f"/protobuf-assets/{asset_id}",
        data=to_proto(updated),
        headers={"Content-Type": "application/x-protobuf"},
    )
    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("Content-Disposition", "")
    u = from_proto(resp.content)
    assert u.description == "new"

    resp = client.delete(f"/protobuf-assets/{asset_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


def test_load_examples_loads_proto_assets(clean_db, examples_env, client):
    """Ensure protobuf examples are generated from synesthetic assets"""
    success, errors = load_examples(client)
    assert success, f"Failed to load examples: {errors}"

    syn_resp = client.get("/synesthetic-assets/")
    assert syn_resp.status_code == 200
    assets = syn_resp.json()
    for asset in assets:
        aid = asset["synesthetic_asset_id"]
        p_resp = client.get(f"/protobuf-assets/{aid}")
        assert p_resp.status_code == 200
        proto = from_proto(p_resp.content)
        assert proto.name == asset["name"]
