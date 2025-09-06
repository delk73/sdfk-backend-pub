from app.services.embedding_service import (
    clear_embeddings,
    store_asset_embedding,
)
from tests.fixtures.factories import create_synesthetic_asset
import pytest

# Ensure tables exist before embedding operations
pytestmark = pytest.mark.usefixtures("engine")
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app import security  # noqa: E402
from app.routers import search as asset_search  # noqa: E402


app.dependency_overrides[security.verify_jwt] = lambda token=None: {"sub": "user"}
client = TestClient(app)


def setup_function() -> None:
    clear_embeddings()


def teardown_function() -> None:
    clear_embeddings()


def test_full_cycle_asset_search(clean_db):
    asset = create_synesthetic_asset(clean_db)
    store_asset_embedding(asset.synesthetic_asset_id, [0.5, 0.5])

    resp = client.post(
        "/search/assets",
        json={"embedding": [0.5, 0.5], "top_k": 1},
    )
    assert resp.status_code == 200
    assert resp.json() == [asset.synesthetic_asset_id]
