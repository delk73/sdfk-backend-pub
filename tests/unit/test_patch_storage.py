import time

import pytest

from app.patch_storage import JsonLinesPatchStorage, InMemoryRingBufferStorage


def test_jsonlines_patch_storage_put_get(tmp_path):
    storage = JsonLinesPatchStorage(base_dir=tmp_path / "bronze/patches")
    patch_id = "p1"
    patch = {"ops": [{"op": "replace", "path": "/foo", "value": 1}]}
    uri = storage.put(patch_id, "shader", patch)
    assert uri.startswith("file://")
    assert (tmp_path / "bronze/patches").exists()
    retrieved = storage.get(patch_id)
    assert retrieved == patch


def test_ring_buffer_put_get_expiry(monkeypatch):
    storage = InMemoryRingBufferStorage(ttl_seconds=0.1)
    patch_id = "p2"
    patch = {"a": 1}
    storage.put(patch_id, "tone", patch)
    assert storage.get(patch_id) == patch
    time.sleep(0.11)
    with pytest.raises(KeyError):
        storage.get(patch_id)
