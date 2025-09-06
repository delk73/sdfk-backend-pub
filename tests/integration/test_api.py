"""Integration tests for the API functionality."""

import logging
import os
import json

import pytest

from app.cache import cache
from app.load_examples import load_examples
from app.main import app

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def mock_cache(monkeypatch):
    cache_store = {}
    monkeypatch.setattr(cache, "get", lambda key: cache_store.get(key))
    monkeypatch.setattr(
        cache,
        "set",
        lambda key, value, expire=3600: cache_store.update({key: json.dumps(value)}),
    )


def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SDFK Backend API"}


@pytest.fixture
def examples_env():
    """Create a temporary directory with example files"""
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    examples_dir = os.path.join(current_dir, "app", "examples")

    # Store the original EXAMPLES_DIR value
    original_examples_dir = os.getenv("EXAMPLES_DIR")

    # Set the EXAMPLES_DIR to point to our examples
    os.environ["EXAMPLES_DIR"] = examples_dir

    yield examples_dir

    # Restore the original EXAMPLES_DIR
    if original_examples_dir:
        os.environ["EXAMPLES_DIR"] = original_examples_dir
    else:
        if "EXAMPLES_DIR" in os.environ:
            del os.environ["EXAMPLES_DIR"]


def test_load_examples_workflow(clean_db, examples_env, client):
    """Integration test for loading example data through the API"""
    # Ensure the examples directory exists and contains our test files
    assert os.path.exists(examples_env), f"Examples directory not found: {examples_env}"
    example_files = os.listdir(examples_env)
    assert len(example_files) > 0, "No example files found in examples directory"

    # Run the load_examples function
    success, errors = load_examples(client)

    # DEBUG: Log detailed error information
    logger.debug("Total errors: %d", len(errors))
    for i, error in enumerate(errors):
        logger.debug("Error %d:", i + 1)
        logger.debug("  Filename: %s", getattr(error, "filename", "Unknown"))
        logger.debug("  Message: %s", getattr(error, "message", "Unknown"))
        logger.debug("  Details: %s", getattr(error, "details", "Unknown"))
        logger.debug("  Full error: %s", error)
        logger.debug("-" * 50)

    # We expect the overall operation to succeed
    assert success is True, f"Failed to load examples: {errors}"

    # We expect some known errors due to mouse mappings and modulation schema
    assert len(errors) <= 20, f"Unexpected number of errors: {errors}"
    if errors:
        error_files = [error.filename for error in errors]
        assert all(
            filename
            in [
                "Control_Example.json",
                "SynestheticAsset_Example1.json",
                "SynestheticAsset_Example2.json",
                "SynestheticAsset_Example7.json",
                "synesthetic_modulation",
            ]
            for filename in error_files
        ), f"Unexpected errors in files: {error_files}"

    # Verify the data was loaded correctly
    response = client.get("/shader_libs/")
    assert response.status_code == 200
    shader_libs = response.json()
    assert len(shader_libs) > 0, "No shader libraries were loaded"
    assert any(lib["name"] == "ExampleLib" for lib in shader_libs)

    # Verify shader examples loaded
    response = client.get("/shaders/")
    assert response.status_code == 200
    shaders = response.json()
    assert len(shaders) > 0, "No shaders were loaded"

    # Verify tone examples loaded
    response = client.get("/tones/")
    assert response.status_code == 200
    tones = response.json()
    assert len(tones) > 0, "No tones were loaded"

    # Verify synesthetic asset examples loaded
    response = client.get("/synesthetic-assets/")
    assert response.status_code == 200
    assets = response.json()
    assert len(assets) > 0, "No synesthetic assets were loaded"

    # Verify specific assets were created with expected data
    response = client.get("/shaders/")
    assert response.status_code == 200
    shaders = response.json()
    assert any(shader["name"] == "Test Circle" for shader in shaders)
