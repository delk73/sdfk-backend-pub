"""Tests for the synesthetic assets router"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import event
from app import models
from tests.fixtures.factories import (
    create_control,
    create_haptic,
    create_modulation,
    create_shader,
    create_shader_lib,
    create_synesthetic_asset,
    create_complete_synesthetic_asset,
    create_tone,
)
from app.main import app
from uuid import UUID, uuid4
import app.security as security
from app.models.db import get_db
from fastapi import Depends

# Override JWT verification for tests
app.dependency_overrides[security.verify_jwt] = lambda token=None: {"sub": "test_user"}

client = TestClient(app)


def test_asset_lifecycle(client, clean_db):
    """Create, update, and delete a synesthetic asset."""
    asset_data = {
        "name": "Lifecycle Asset",
        "description": "Lifecycle test",
    }

    # Create
    create_resp = client.post("/synesthetic-assets/", json=asset_data)
    assert create_resp.status_code == 200
    asset_id = create_resp.json()["synesthetic_asset_id"]

    # Update
    update_data = {
        "name": "Lifecycle Updated",
        "description": "Lifecycle test updated",
    }
    update_resp = client.put(f"/synesthetic-assets/{asset_id}", json=update_data)
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == update_data["name"]

    # Delete
    del_resp = client.delete(f"/synesthetic-assets/{asset_id}")
    assert del_resp.status_code == 200

    # Verify deletion
    get_resp = client.get(f"/synesthetic-assets/{asset_id}")
    assert get_resp.status_code == 404


def test_create_synesthetic_asset(db: Session = Depends(get_db)):
    """Test creating a synesthetic asset"""
    asset_data = {
        "name": "Test Asset",
        "description": "A test synesthetic asset",
        "meta_info": {"category": "test", "tags": ["test", "asset"]},
    }

    response = client.post("/synesthetic-assets/", json=asset_data)
    assert response.status_code == 200
    data = response.json()

    # Verify the response contains the expected fields
    assert data["name"] == asset_data["name"]
    assert data["description"] == asset_data["description"]
    assert "meta_info" in data


def test_get_synesthetic_asset(db: Session = Depends(get_db)):
    """Test retrieving a synesthetic asset"""
    # First create an asset
    asset_data = {"name": "Get Test Asset", "description": "A test synesthetic asset"}

    create_response = client.post("/synesthetic-assets/", json=asset_data)
    assert create_response.status_code == 200
    asset_id = create_response.json()["synesthetic_asset_id"]

    # Now get the asset
    get_response = client.get(f"/synesthetic-assets/{asset_id}")
    assert get_response.status_code == 200
    data = get_response.json()

    # Verify the data
    assert data["name"] == "Get Test Asset"
    assert data["description"] == "A test synesthetic asset"


def test_update_synesthetic_asset(db: Session = Depends(get_db)):
    """Test updating a synesthetic asset"""
    # First create an asset
    asset_data = {
        "name": "Update Test Asset",
        "description": "A test synesthetic asset",
    }

    create_response = client.post("/synesthetic-assets/", json=asset_data)
    assert create_response.status_code == 200
    asset_id = create_response.json()["synesthetic_asset_id"]

    # Now update the asset
    update_data = {
        "name": "Updated Asset",
        "description": "An updated synesthetic asset",
    }

    update_response = client.put(f"/synesthetic-assets/{asset_id}", json=update_data)
    assert update_response.status_code == 200
    updated_data = update_response.json()

    # Verify the updated data
    assert updated_data["name"] == "Updated Asset"
    assert updated_data["description"] == "An updated synesthetic asset"


def test_delete_synesthetic_asset(db: Session = Depends(get_db)):
    """Test deleting a synesthetic asset"""
    # First create an asset
    asset_data = {
        "name": "Delete Test Asset",
        "description": "A test synesthetic asset",
    }

    create_response = client.post("/synesthetic-assets/", json=asset_data)
    assert create_response.status_code == 200
    asset_id = create_response.json()["synesthetic_asset_id"]

    # Now delete the asset
    delete_response = client.delete(f"/synesthetic-assets/{asset_id}")
    assert delete_response.status_code == 200

    # Verify the asset is deleted
    get_response = client.get(f"/synesthetic-assets/{asset_id}")
    assert get_response.status_code == 404


def test_get_synesthetic_assets_offset():
    """Test retrieving synesthetic assets with offset and limit"""
    # Create several assets
    for i in range(5):
        asset_data = {
            "name": f"Offset Asset {i}",
            "description": f"Asset {i} for offset test",
        }
        response = client.post("/synesthetic-assets/", json=asset_data)
        assert response.status_code == 200
    # Get first 2 assets
    response = client.get("/synesthetic-assets/offset/?offset=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    # Get next 2 assets
    response2 = client.get("/synesthetic-assets/offset/?offset=2&limit=2")
    assert response2.status_code == 200
    data2 = response2.json()
    assert isinstance(data2, list)
    assert len(data2) == 2
    # Ensure no overlap in asset names
    names1 = {a["name"] for a in data}
    names2 = {a["name"] for a in data2}
    assert names1.isdisjoint(names2)


def test_query_efficiency_multiple_assets(client, clean_db):
    """Ensure listing multiple assets issues fewer queries with eager loading."""

    # Create multiple complete assets directly in the database
    for i in range(3):
        shader_lib = create_shader_lib(clean_db, name=f"ShaderLib {i}")
        shader = create_shader(
            clean_db, name=f"Shader {i}", shader_lib_id=shader_lib.shaderlib_id
        )
        control = create_control(clean_db, name=f"Control {i}")
        tone = create_tone(clean_db, name=f"Tone {i}")
        haptic = create_haptic(clean_db, name=f"Haptic {i}")
        modulation = create_modulation(clean_db, name=f"Modulation {i}")
        create_synesthetic_asset(
            clean_db,
            name=f"Asset {i}",
            shader_id=shader.shader_id,
            control_id=control.control_id,
            tone_id=tone.tone_id,
            haptic_id=haptic.haptic_id,
            modulation_id=modulation.modulation_id,
        )

    # Baseline naive approach simulating the old per-asset queries
    naive_queries: list[str] = []

    def before_naive(conn, cursor, statement, parameters, context, executemany):
        naive_queries.append(statement)

    from sqlalchemy.orm import sessionmaker

    baseline_session = sessionmaker(bind=clean_db.bind)()
    event.listen(clean_db.bind, "before_cursor_execute", before_naive)
    assets = baseline_session.query(models.SynestheticAsset).offset(0).limit(3).all()
    for asset in assets:
        if asset.shader_id:
            _ = asset.shader
        if asset.control_id:
            _ = asset.control
        if asset.tone_id:
            _ = asset.tone
        if asset.haptic_id:
            _ = asset.haptic
    event.remove(clean_db.bind, "before_cursor_execute", before_naive)
    baseline_session.close()
    naive_count = len(naive_queries)

    # Actual API call
    route_queries: list[str] = []

    def before_route(conn, cursor, statement, parameters, context, executemany):
        route_queries.append(statement)

    event.listen(clean_db.bind, "before_cursor_execute", before_route)
    resp = client.get("/synesthetic-assets/offset/?offset=0&limit=3")
    assert resp.status_code == 200
    event.remove(clean_db.bind, "before_cursor_execute", before_route)
    route_count = len(route_queries)

    assert route_count < naive_count


def test_update_asset_shader_endpoint(client, clean_db):
    """Update a shader via the asset-scoped endpoint."""
    objs = create_complete_synesthetic_asset(clean_db)
    asset_id = objs["asset"].synesthetic_asset_id

    resp = client.put(
        f"/synesthetic-assets/{asset_id}/shader",
        json={"vertex_shader": "asset update"},
    )
    assert resp.status_code == 200
    assert resp.json()["shader"]["vertex_shader"] == "asset update"

    nested = client.get(f"/synesthetic-assets/nested/{asset_id}")
    assert nested.json()["shader"]["vertex_shader"] == "asset update"


def test_update_asset_tone_endpoint(client, clean_db):
    """Update a tone via the asset-scoped endpoint."""
    objs = create_complete_synesthetic_asset(clean_db)
    asset_id = objs["asset"].synesthetic_asset_id

    resp = client.put(
        f"/synesthetic-assets/{asset_id}/tone",
        json={"name": "Updated Tone"},
    )
    assert resp.status_code == 200
    assert resp.json()["tone"]["name"] == "Updated Tone"

    nested = client.get(f"/synesthetic-assets/nested/{asset_id}")
    assert nested.json()["tone"]["name"] == "Updated Tone"


def test_update_asset_haptic_endpoint(client, clean_db):
    """Update a haptic via the asset-scoped endpoint."""
    objs = create_complete_synesthetic_asset(clean_db)
    asset_id = objs["asset"].synesthetic_asset_id

    resp = client.put(
        f"/synesthetic-assets/{asset_id}/haptic",
        json={"description": "Updated Haptic"},
    )
    assert resp.status_code == 200
    assert resp.json()["haptic"]["description"] == "Updated Haptic"

    nested = client.get(f"/synesthetic-assets/nested/{asset_id}")
    assert nested.json()["haptic"]["description"] == "Updated Haptic"


## Patch preview removed; repository serves CRUD only
def _removed_test_preview_nested_asset():
    objs = create_complete_synesthetic_asset(clean_db)
    asset = objs["asset"]

    asset.meta_info = {"version": 1}
    clean_db.commit()

    patch_ops = [{"op": "replace", "path": "/tone/name", "value": "Patched Tone"}]
    patch_id = uuid4().hex
    ring_storage.put(
        patch_id,
        "tone",
        {
            "asset_id": asset.synesthetic_asset_id,
            "component_type": "tone",
            "base_version": 1,
            "patch": patch_ops,
        },
    )

    resp = client.get(
        f"/synesthetic-assets/nested/{asset.synesthetic_asset_id}?preview_patch_id={patch_id}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tone"]["name"] == "Patched Tone"
    assert data["preview"]["patch_id"] == patch_id
    entry = (
        clean_db.query(models.PatchIndex)
        .filter(models.PatchIndex.patch_id == UUID(patch_id))
        .first()
    )
    assert entry is not None and entry.state == "previewed"


def test_nested_asset_returns_without_preview(client, clean_db):
    objs = create_complete_synesthetic_asset(clean_db)
    asset_id = objs["asset"].synesthetic_asset_id
    resp = client.get(f"/synesthetic-assets/nested/{asset_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "preview" not in data


def _removed_test_preview_patch_not_found():
    objs = create_complete_synesthetic_asset(clean_db)
    asset_id = objs["asset"].synesthetic_asset_id
    resp = client.get(f"/synesthetic-assets/nested/{asset_id}?preview_patch_id=999")
    assert resp.status_code == 404


def _removed_test_preview_version_mismatch():
    objs = create_complete_synesthetic_asset(clean_db)
    asset = objs["asset"]
    asset.meta_info = {"version": 1}
    clean_db.commit()

    patch_id = uuid4().hex
    ring_storage.put(
        patch_id,
        "shader",
        {
            "asset_id": asset.synesthetic_asset_id,
            "component_type": "shader",
            "base_version": 2,
            "patch": [],
        },
    )

    resp = client.get(
        f"/synesthetic-assets/nested/{asset.synesthetic_asset_id}?preview_patch_id={patch_id}"
    )
    assert resp.status_code == 409


def _removed_test_preview_invalid_patch():
    objs = create_complete_synesthetic_asset(clean_db)
    asset = objs["asset"]
    asset.meta_info = {"version": 1}
    clean_db.commit()

    patch_ops = [{"op": "replace", "path": "/vertex_shader", "value": "no main"}]
    patch_id = uuid4().hex
    ring_storage.put(
        patch_id,
        "shader",
        {
            "asset_id": asset.synesthetic_asset_id,
            "component_type": "shader",
            "base_version": 1,
            "patch": patch_ops,
        },
    )

    resp = client.get(
        f"/synesthetic-assets/nested/{asset.synesthetic_asset_id}?preview_patch_id={patch_id}"
    )
    assert resp.status_code == 422


def _removed_test_preview_component_missing():
    asset = create_synesthetic_asset(clean_db)
    shader = create_shader(clean_db)
    asset.shader_id = shader.shader_id
    asset.meta_info = {"version": 1}
    clean_db.commit()

    patch_id = uuid4().hex
    ring_storage.put(
        patch_id,
        "tone",
        {
            "asset_id": asset.synesthetic_asset_id,
            "component_type": "tone",
            "base_version": 1,
            "patch": [],
        },
    )

    resp = client.get(
        f"/synesthetic-assets/nested/{asset.synesthetic_asset_id}?preview_patch_id={patch_id}"
    )
    assert resp.status_code == 404


def _removed_test_apply_patch_updates_component():
    objs = create_complete_synesthetic_asset(clean_db)
    asset = objs["asset"]
    asset.meta_info = {"version": 1}
    clean_db.commit()

    patch_ops = [{"op": "replace", "path": "/tone/name", "value": "Patched Tone"}]
    patch_id = uuid4().hex
    ring_storage.put(
        patch_id,
        "tone",
        {
            "asset_id": asset.synesthetic_asset_id,
            "component_type": "tone",
            "base_version": 1,
            "patch": patch_ops,
        },
    )

    # preview to create index entry
    client.get(
        f"/synesthetic-assets/nested/{asset.synesthetic_asset_id}?preview_patch_id={patch_id}"
    )

    resp = client.put(
        f"/synesthetic-assets/apply/{asset.synesthetic_asset_id}/{patch_id}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tone"]["name"] == "Patched Tone"
    entry = (
        clean_db.query(models.PatchIndex)
        .filter(models.PatchIndex.patch_id == UUID(patch_id))
        .first()
    )
    assert entry is not None and entry.state == "applied"


def _removed_test_apply_patch_not_found():
    objs = create_complete_synesthetic_asset(clean_db)
    asset_id = objs["asset"].synesthetic_asset_id
    resp = client.put(f"/synesthetic-assets/apply/{asset_id}/missing")
    assert resp.status_code == 404


def _removed_test_apply_version_mismatch():
    objs = create_complete_synesthetic_asset(clean_db)
    asset = objs["asset"]
    asset.meta_info = {"version": 1}
    clean_db.commit()

    patch_id = uuid4().hex
    ring_storage.put(
        patch_id,
        "shader",
        {
            "asset_id": asset.synesthetic_asset_id,
            "component_type": "shader",
            "base_version": 2,
            "patch": [],
        },
    )
    client.get(
        f"/synesthetic-assets/nested/{asset.synesthetic_asset_id}?preview_patch_id={patch_id}"
    )
    resp = client.put(
        f"/synesthetic-assets/apply/{asset.synesthetic_asset_id}/{patch_id}"
    )
    assert resp.status_code == 409


def _removed_test_apply_component_missing():
    asset = create_synesthetic_asset(clean_db)
    shader = create_shader(clean_db)
    asset.shader_id = shader.shader_id
    asset.meta_info = {"version": 1}
    clean_db.commit()

    patch_id = uuid4().hex
    ring_storage.put(
        patch_id,
        "tone",
        {
            "asset_id": asset.synesthetic_asset_id,
            "component_type": "tone",
            "base_version": 1,
            "patch": [],
        },
    )
    client.get(
        f"/synesthetic-assets/nested/{asset.synesthetic_asset_id}?preview_patch_id={patch_id}"
    )
    resp = client.put(
        f"/synesthetic-assets/apply/{asset.synesthetic_asset_id}/{patch_id}"
    )
    assert resp.status_code == 404
