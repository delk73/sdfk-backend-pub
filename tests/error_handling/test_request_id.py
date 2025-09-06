import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ping_endpoint_has_request_id():
    """Test that /ping endpoint returns X-Request-ID header."""
    resp = client.get("/ping")
    assert resp.status_code == 200

    # Check that X-Request-ID header exists and is UUID-like
    request_id = resp.headers.get("X-Request-ID")
    assert request_id is not None, "X-Request-ID header missing"

    # Validate it's a valid UUID format
    try:
        uuid.UUID(request_id)
    except ValueError:
        pytest.fail(f"X-Request-ID '{request_id}' is not a valid UUID")


def test_ping_endpoint_echoes_request_id_in_body():
    """Test that request_id is echoed in response body."""
    resp = client.get("/ping")
    response_data = resp.json()
    request_id = resp.headers.get("X-Request-ID")
    assert response_data.get("request_id") == request_id
