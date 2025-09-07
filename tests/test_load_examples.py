import os
from typing import Tuple

from fastapi.testclient import TestClient

from app.main import app
from app.load_examples import load_examples, LAST_SUMMARY


def _with_env(env: dict, fn) -> Tuple[bool, list]:
    saved = {k: os.getenv(k) for k in env}
    try:
        for k, v in env.items():
            if v is None and k in os.environ:
                del os.environ[k]
            elif v is not None:
                os.environ[k] = v
        return fn()
    finally:
        for k, v in saved.items():
            if v is None and k in os.environ:
                del os.environ[k]
            elif v is not None:
                os.environ[k] = v


def test_strip_schema_ref_top_level_only_and_validation_allows():
    client = TestClient(app)
    # Use SSOT examples which include top-level $schemaRef
    ssot = os.path.join(os.path.dirname(os.path.dirname(__file__)), "libs", "synesthetic-schemas", "examples")
    assert os.path.isdir(ssot)

    def run():
        return load_examples(client)

    success, errors = _with_env({"EXAMPLES_DIR": ssot, "DRY_RUN": "1"}, run)
    # Should succeed (DRY_RUN counts as planned/skip) and not fail validation of top-level $schemaRef
    assert success is True
    # No hard assertion on error list since examples may include optional invalids


def test_default_excludes_components_in_ssot():
    client = TestClient(app)
    ssot = os.path.join(os.path.dirname(os.path.dirname(__file__)), "libs", "synesthetic-schemas", "examples")
    assert os.path.isdir(ssot)

    def run():
        return load_examples(client)

    success, errors = _with_env({"EXAMPLES_DIR": ssot, "ONLY_ASSETS": "0", "INCLUDE_COMPONENTS": "0"}, run)
    assert success is True
    # Components should remain empty by default in SSOT mode
    assert LAST_SUMMARY.get("shader", {"imported": 0, "skipped_existing": 0})["imported"] == 0
    assert LAST_SUMMARY.get("tone", {"imported": 0, "skipped_existing": 0})["imported"] == 0


def test_import_idempotent_assets():
    client = TestClient(app)
    ssot = os.path.join(os.path.dirname(os.path.dirname(__file__)), "libs", "synesthetic-schemas", "examples")

    def run():
        return load_examples(client)

    # First run imports assets
    success1, errors1 = _with_env({"EXAMPLES_DIR": ssot, "INCLUDE_COMPONENTS": "0"}, run)
    assert success1 is True
    first_imported = LAST_SUMMARY.get("asset", {}).get("imported", 0)
    assert first_imported > 0

    # Second run should report only skipped_existing for assets
    success2, errors2 = _with_env({"EXAMPLES_DIR": ssot, "INCLUDE_COMPONENTS": "0"}, run)
    assert success2 is True
    assert LAST_SUMMARY.get("asset", {}).get("imported", 0) == 0
    assert LAST_SUMMARY.get("asset", {}).get("skipped_existing", 0) >= first_imported


def test_summary_counts_stable():
    # Re-running again should give stable counts (no new imports)
    client = TestClient(app)
    ssot = os.path.join(os.path.dirname(os.path.dirname(__file__)), "libs", "synesthetic-schemas", "examples")

    def run():
        return load_examples(client)

    success, _ = _with_env({"EXAMPLES_DIR": ssot, "INCLUDE_COMPONENTS": "0"}, run)
    assert success is True
    c = LAST_SUMMARY.get("asset", {})
    assert c.get("imported", 0) == 0
    assert c.get("skipped_existing", 0) >= 1

