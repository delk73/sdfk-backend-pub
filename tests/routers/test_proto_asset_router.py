from app.proto import asset_pb2
from tests.fixtures.factories import create_complete_synesthetic_asset


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


def test_create_get_update_delete_proto_asset(clean_db, client):
    # create
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

    # get
    resp = client.get(f"/protobuf-assets/{asset_id}")
    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("Content-Disposition", "")
    fetched = from_proto(resp.content)
    assert fetched.name == example["name"]

    # update
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

    # delete
    resp = client.delete(f"/protobuf-assets/{asset_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


def test_create_from_synesthetic_asset(clean_db, client):
    objs = create_complete_synesthetic_asset(clean_db)
    syn_asset = objs["asset"]

    resp = client.post(
        f"/protobuf-assets/from-synesthetic/{syn_asset.synesthetic_asset_id}"
    )
    assert resp.status_code == 200
    proto = from_proto(resp.content)
    assert proto.name == syn_asset.name

    # verify the asset can be retrieved with the same id
    get_resp = client.get(f"/protobuf-assets/{syn_asset.synesthetic_asset_id}")
    assert get_resp.status_code == 200
    fetched = from_proto(get_resp.content)
    assert fetched.name == syn_asset.name
