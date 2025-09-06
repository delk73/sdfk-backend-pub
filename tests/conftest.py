"""Common test fixtures for SDFK Backend"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ensure project root is in PYTHONPATH
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set test environment variables BEFORE importing app
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}?check_same_thread=False"
os.environ.setdefault("TESTING", "1")
os.environ["OLLAMA_API_URL"] = "http://localhost:11434"

from app.models.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.schema_version import SCHEMA_VERSION  # noqa: E402
from app.security import verify_jwt  # noqa: E402
from tests.fixtures.factories import (  # noqa: E402
    create_shader_lib,
    create_shader,
    create_control,
    create_tone,
    create_haptic,
    create_modulation,
    create_synesthetic_asset,
    create_complete_synesthetic_asset,
)


@pytest.fixture(scope="session")
def engine():
    """Create database engine for testing"""
    engine = create_engine(
        os.environ["DATABASE_URL"], connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a fresh database session for each test"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def clean_db(db_session):
    """Ensure database is clean before each test"""
    tables = [
        "mcp_command_log",
        "synesthetic_assets",
        "controls",
        "tones",
        "shaders",
        "shader_libs",
        "haptics",
        "modulations",
        "patch_ratings",
        "patch_embeddings",
        "proto_assets",
        "patch_index",
    ]
    for table in tables:
        db_session.execute(text(f"DELETE FROM {table}"))
    db_session.commit()
    return db_session


## Ring buffer patch storage removed


@pytest.fixture(scope="function")
def client(db_session):
    """Test client with database session override"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    # Include required schema version header for write operations by default
    c = TestClient(app, headers={"X-Schema-Version": SCHEMA_VERSION})
    try:
        yield c
    finally:
        c.close()
        app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """Test client with authentication"""

    def override_auth():
        return {"sub": "test_user"}

    app.dependency_overrides[verify_jwt] = override_auth
    return client


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: long-running tests")
    config.addinivalue_line("markers", "external: requires external services")


def pytest_collection_modifyitems(config, items):
    if os.getenv("GEMINI_ENABLED") != "1":
        skip_external = pytest.mark.skip(reason="GEMINI_ENABLED not set")
        for item in items:
            if "external" in item.keywords:
                item.add_marker(skip_external)


@pytest.fixture
def auth_token():
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0X3VzZXIifQ.KxXbz5wn4uJg0dap2dOZ"


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def tone_legacy_data():
    return {
        "name": "Legacy Tone",
        "config": {
            "frequency_range": [110, 440],
            "sensitivity": 0.9,
            "smoothing": 0.25,
        },
    }


# New fixtures using factories


@pytest.fixture
def shader_lib(clean_db):
    """Create a test shader library."""
    return create_shader_lib(clean_db)


@pytest.fixture
def shader(clean_db, shader_lib):
    """Create a test shader with a shader library."""
    return create_shader(clean_db, shader_lib_id=shader_lib.shader_lib_id)


@pytest.fixture
def control(clean_db):
    """Create a test control."""
    return create_control(clean_db)


@pytest.fixture
def tone(clean_db):
    """Create a test tone."""
    return create_tone(clean_db)


@pytest.fixture
def haptic(clean_db):
    """Create a test haptic."""
    return create_haptic(clean_db)


@pytest.fixture
def modulation(clean_db):
    """Create a test modulation."""
    return create_modulation(clean_db)


@pytest.fixture
def synesthetic_asset(clean_db, shader, control, tone, haptic, modulation):
    """Create a test synesthetic asset with all components."""
    return create_synesthetic_asset(
        clean_db,
        shader_id=shader.shader_id,
        control_id=control.control_id,
        tone_id=tone.tone_id,
        haptic_id=haptic.haptic_id,
        modulation_id=modulation.modulation_id,
    )


@pytest.fixture
def complete_asset(clean_db):
    """Create a complete synesthetic asset with all related components."""
    return create_complete_synesthetic_asset(clean_db)


@pytest.fixture
def example_dir():
    """Create a temporary directory with example files."""
    temp_dir = tempfile.mkdtemp()

    # Copy example files to temp directory
    examples_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "app", "examples"
    )
    for filename in os.listdir(examples_dir):
        if filename.endswith(".json"):
            src = os.path.join(examples_dir, filename)
            dst = os.path.join(temp_dir, filename)
            shutil.copy2(src, dst)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def examples_env():
    """Set up environment for example files"""
    current_dir = os.path.dirname(os.path.dirname(__file__))
    examples_dir = os.path.join(current_dir, "app", "examples")

    original_examples_dir = os.getenv("EXAMPLES_DIR")
    os.environ["EXAMPLES_DIR"] = examples_dir

    yield examples_dir

    if original_examples_dir:
        os.environ["EXAMPLES_DIR"] = original_examples_dir
    else:
        if "EXAMPLES_DIR" in os.environ:
            del os.environ["EXAMPLES_DIR"]
