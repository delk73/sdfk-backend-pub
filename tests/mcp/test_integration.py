"""
MCP Integration Tests

End-to-end integration tests to verify the complete MCP asset workflow
including schema validation, logging, and error handling consistency.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.models import MCPCommandLog

# Override JWT verification for tests
import app.security as security

app.dependency_overrides[security.verify_jwt] = lambda token=None: {"sub": "test_user"}

client = TestClient(app)


def test_complete_mcp_workflow():
    """Test complete MCP workflow from asset creation to validation."""

    # Mock request ID for consistent testing
    mock_request_id = "integration_test_123"

    # Comprehensive patching of all request ID import paths
    patches = [
        patch(
            "app.middleware.request_id.get_current_request_id",
            return_value=mock_request_id,
        ),
        patch(
            "app.routers.mcp.asset.get_current_request_id", return_value=mock_request_id
        ),
        patch(
            "app.services.mcp_logger.get_current_request_id",
            return_value=mock_request_id,
        ),
    ]

    # Start all patches
    [p.start() for p in patches]

    try:

        # Step 1: Create an asset
        create_response = client.post(
            "/mcp/asset/create",
            json={
                "name": "Integration Test Asset",
                "description": "Asset for integration testing",
                "tone": {
                    "name": "Integration Tone",
                    "synth": {"type": "Tone.MonoSynth"},
                },
                "shader": {
                    "name": "Integration Shader",
                    "fragment_shader": "void main() { gl_FragColor = vec4(1.0); }",
                },
            },
        )

        assert create_response.status_code == 200
        create_data = create_response.json()
        assert create_data["request_id"] == mock_request_id

        asset_id = create_data["result"]["asset_id"]

        # Step 2: Update a parameter
        update_response = client.post(
            "/mcp/asset/update",
            json={"asset_id": asset_id, "path": "shader.u_time", "value": 5.0},
        )

        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data["request_id"] == mock_request_id
        assert update_data["result"]["new_value"] == 5.0

        # Step 3: Apply modulation
        modulation_response = client.post(
            "/mcp/asset/modulate",
            json={
                "asset_id": asset_id,
                "modulation_id": "integration_mod",
                "definition": {
                    "id": "integration_mod",
                    "target": "shader.u_r",
                    "type": "additive",
                    "waveform": "sine",
                    "frequency": 1.0,
                },
            },
        )

        assert modulation_response.status_code == 200
        modulation_data = modulation_response.json()
        assert modulation_data["request_id"] == mock_request_id

        # Step 4: Validate asset structure
        validation_response = client.post(
            "/mcp/asset/validate",
            json={
                "asset_blob": {
                    "name": "Validation Test",
                    "shader": {"fragment_shader": "void main() {}"},
                    "tone": {"synth": {"type": "Tone.Synth"}},
                }
            },
        )

        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        assert validation_data["request_id"] == mock_request_id
        assert validation_data["result"]["valid"] is True

    finally:
        # Stop all patches
        for p in patches:
            p.stop()


def test_error_handling_consistency():
    """Test that error handling is consistent across all MCP endpoints."""

    mock_request_id = "error_test_456"

    # Comprehensive patching of all request ID import paths
    patches = [
        patch(
            "app.middleware.request_id.get_current_request_id",
            return_value=mock_request_id,
        ),
        patch(
            "app.routers.mcp.asset.get_current_request_id", return_value=mock_request_id
        ),
        patch(
            "app.services.mcp_logger.get_current_request_id",
            return_value=mock_request_id,
        ),
    ]

    # Start all patches
    [p.start() for p in patches]

    try:

        # Test 404 errors
        not_found_response = client.post(
            "/mcp/asset/update",
            json={
                "asset_id": "nonexistent_asset",
                "path": "shader.u_time",
                "value": 1.0,
            },
        )

        assert not_found_response.status_code == 404
        error_data = not_found_response.json()
        assert error_data["detail"]["request_id"] == mock_request_id
        assert "Asset not found" in error_data["detail"]["error"]

        # Test 422 validation errors
        validation_error_response = client.post(
            "/mcp/asset/create", json={"invalid_field": "value"}
        )

        assert validation_error_response.status_code == 422
        # FastAPI validation errors have a different structure
        assert "detail" in validation_error_response.json()

        # Test 409 conflict errors
        conflict_response = client.post(
            "/mcp/asset/modulate",
            json={
                "asset_id": "asset_test",
                "modulation_id": "duplicate_mod",
                "definition": {"id": "duplicate_mod"},
            },
        )

        assert conflict_response.status_code == 409
        conflict_data = conflict_response.json()
        assert conflict_data["detail"]["request_id"] == mock_request_id
        assert "already exists" in conflict_data["detail"]["error"]

    finally:
        # Stop all patches
        for p in patches:
            p.stop()


def test_request_id_propagation():
    """Test that request_id is properly propagated through all operations."""

    mock_request_id = "propagation_test_789"

    # Comprehensive patching of all request ID import paths
    patches = [
        patch(
            "app.middleware.request_id.get_current_request_id",
            return_value=mock_request_id,
        ),
        patch(
            "app.routers.mcp.asset.get_current_request_id", return_value=mock_request_id
        ),
        patch(
            "app.services.mcp_logger.get_current_request_id",
            return_value=mock_request_id,
        ),
    ]

    # Start all patches
    [p.start() for p in patches]

    try:

        # Test successful operations
        success_endpoints = [
            (
                "/mcp/asset/create",
                {
                    "name": "Propagation Test",
                    "tone": {"name": "Test", "synth": {"type": "Tone.Synth"}},
                    "shader": {"name": "Test", "fragment_shader": "void main() {}"},
                },
            ),
            (
                "/mcp/asset/update",
                {"asset_id": "asset_test", "path": "shader.u_time", "value": 1.0},
            ),
            (
                "/mcp/asset/validate",
                {
                    "asset_blob": {
                        "name": "Test Asset",
                        "shader": {"fragment_shader": "void main() {}"},
                        "tone": {"synth": {"type": "Tone.Synth"}},
                    }
                },
            ),
        ]

        for endpoint, data in success_endpoints:
            response = client.post(endpoint, json=data)
            assert response.status_code == 200
            response_data = response.json()
            assert "request_id" in response_data
            assert response_data["request_id"] == mock_request_id

    finally:
        # Stop all patches
        for p in patches:
            p.stop()


def test_command_logging_integration(clean_db):
    """Test that command logging works properly across all MCP operations."""

    mock_request_id = "logging_test_abc"

    # Comprehensive patching of all request ID import paths
    patches = [
        patch(
            "app.middleware.request_id.get_current_request_id",
            return_value=mock_request_id,
        ),
        patch(
            "app.routers.mcp.asset.get_current_request_id", return_value=mock_request_id
        ),
        patch(
            "app.services.mcp_logger.get_current_request_id",
            return_value=mock_request_id,
        ),
    ]

    # Start all patches
    [p.start() for p in patches]

    try:

        # Perform various operations
        operations = [
            (
                "create_asset",
                "/mcp/asset/create",
                {
                    "name": "Logging Test Asset",
                    "tone": {"name": "Test", "synth": {"type": "Tone.Synth"}},
                    "shader": {"name": "Test", "fragment_shader": "void main() {}"},
                },
            ),
            (
                "update_param",
                "/mcp/asset/update",
                {"asset_id": "asset_test", "path": "shader.u_time", "value": 2.5},
            ),
            (
                "validate_asset",
                "/mcp/asset/validate",
                {
                    "asset_blob": {
                        "name": "Valid Test",
                        "shader": {"fragment_shader": "void main() {}"},
                        "tone": {"synth": {"type": "Tone.Synth"}},
                    }
                },
            ),
        ]

        for command_type, endpoint, data in operations:
            response = client.post(endpoint, json=data)
            assert response.status_code == 200

            # Check that log entry was created
            logs = (
                clean_db.query(MCPCommandLog)
                .filter(
                    MCPCommandLog.command_type == command_type,
                    MCPCommandLog.request_id == mock_request_id,
                )
                .all()
            )

            assert len(logs) >= 1
            log_entry = logs[-1]
            assert log_entry.status == "success"
            assert log_entry.request_id == mock_request_id
            assert log_entry.payload is not None
            assert log_entry.result is not None

    finally:
        # Stop all patches
        for p in patches:
            p.stop()


def test_mcp_asset_ping_health():
    """Test MCP asset ping endpoint for health checking."""
    response = client.get("/mcp/asset/ping")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "MCP asset router live"

    # Ping should not require authentication or special headers
    # and should always return the same response


def test_parallel_request_isolation():
    """Test that parallel requests maintain proper request_id isolation."""

    # Simulate multiple concurrent requests with different request IDs
    request_ids = ["parallel_1", "parallel_2", "parallel_3"]

    for req_id in request_ids:
        # Comprehensive patching of all request ID import paths
        patches = [
            patch(
                "app.middleware.request_id.get_current_request_id", return_value=req_id
            ),
            patch("app.routers.mcp.asset.get_current_request_id", return_value=req_id),
            patch(
                "app.services.mcp_logger.get_current_request_id", return_value=req_id
            ),
        ]

        # Start all patches
        [p.start() for p in patches]

        try:
            response = client.post(
                "/mcp/asset/validate",
                json={
                    "asset_blob": {
                        "name": f"Parallel Test {req_id}",
                        "shader": {"fragment_shader": "void main() {}"},
                        "tone": {"synth": {"type": "Tone.Synth"}},
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["request_id"] == req_id

            # Each request should maintain its own context
            assert data["request_id"] != "no-request-id"

        finally:
            # Stop all patches
            for p in patches:
                p.stop()
