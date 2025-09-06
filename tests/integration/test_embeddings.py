"""Integration tests for embedding service."""

from app.services.embedding_service import (
    clear_embeddings,
    get_embedding,
    query_similar,
    store_embedding,
)
from tests.fixtures.factories import (
    create_shader_lib,
    create_shader,
    create_synesthetic_asset,
)
from app.models import PatchIndex
from uuid import uuid4
import pytest

# Ensure database tables are initialized before using embedding helpers
pytestmark = pytest.mark.usefixtures("engine")


def setup_function() -> None:
    clear_embeddings()


def teardown_function() -> None:
    clear_embeddings()


def test_store_and_retrieve_embedding() -> None:
    """Embeddings can be stored and retrieved by patch ID."""

    pid = str(uuid4())
    store_embedding(pid, [0.1, 0.2, 0.3])
    result = get_embedding(pid)
    assert result is not None
    assert result.to_list() == pytest.approx([0.1, 0.2, 0.3])


def test_query_similar_returns_closest() -> None:
    """Most similar embedding is returned first."""

    p1 = str(uuid4())
    p2 = str(uuid4())
    store_embedding(p1, [1.0, 0.0])
    store_embedding(p2, [0.0, 1.0])

    matches = query_similar([0.9, 0.1], top_k=1)
    assert matches == [p1]


def test_query_similar_respects_top_k() -> None:
    """Query returns the specified number of results ordered by similarity."""

    p1 = str(uuid4())
    p2 = str(uuid4())
    p3 = str(uuid4())
    store_embedding(p1, [1.0, 0.0])
    store_embedding(p2, [0.0, 1.0])
    store_embedding(p3, [0.5, 0.5])

    matches = query_similar([1.0, 0.0], top_k=2)
    assert matches == [p1, p3]


def test_query_similar_filters_by_shader(clean_db) -> None:
    shader_lib = create_shader_lib(clean_db)
    shader_a = create_shader(clean_db, shader_lib_id=shader_lib.shaderlib_id)
    shader_b = create_shader(clean_db, shader_lib_id=shader_lib.shaderlib_id)
    asset_a = create_synesthetic_asset(clean_db, shader_id=shader_a.shader_id)
    asset_b = create_synesthetic_asset(clean_db, shader_id=shader_b.shader_id)
    patch_a_id = uuid4()
    patch_b_id = uuid4()
    clean_db.add_all(
        [
            PatchIndex(
                patch_id=patch_a_id,
                asset_id=asset_a.synesthetic_asset_id,
                component_type="shader",
                state="applied",
                blob_uri="file",
            ),
            PatchIndex(
                patch_id=patch_b_id,
                asset_id=asset_b.synesthetic_asset_id,
                component_type="shader",
                state="applied",
                blob_uri="file",
            ),
        ]
    )
    clean_db.commit()

    store_embedding(str(patch_a_id), [1.0, 0.0])
    store_embedding(str(patch_b_id), [0.0, 1.0])

    matches = query_similar([1.0, 0.0], shader_id=shader_a.shader_id)
    assert matches == [str(patch_a_id)]


def test_query_similar_filters_by_asset(clean_db) -> None:
    shader_lib = create_shader_lib(clean_db)
    shader = create_shader(clean_db, shader_lib_id=shader_lib.shaderlib_id)
    asset = create_synesthetic_asset(clean_db, shader_id=shader.shader_id)
    patch_id = uuid4()
    clean_db.add(
        PatchIndex(
            patch_id=patch_id,
            asset_id=asset.synesthetic_asset_id,
            component_type="shader",
            state="applied",
            blob_uri="file",
        )
    )
    clean_db.commit()

    store_embedding(str(patch_id), [1.0, 0.0])

    matches = query_similar([1.0, 0.0], asset_id=asset.synesthetic_asset_id)
    assert matches == [str(patch_id)]
