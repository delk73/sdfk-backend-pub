"""
MCP Asset CRUD Test Suite

Comprehensive tests for MCP asset control surface validating schema conformance,
error handling, and logging behaviors for all asset operation endpoints.

This test harness validates:
- 200/404/409/422 status codes with proper error messages
- request_id presence in all responses
- Command logging for successful operations
- Schema validation for all endpoints
- OpenAPI spec compliance
"""

import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import MCPCommandLog

# Override JWT verification for tests
import app.security as security

app.dependency_overrides[security.verify_jwt] = lambda token=None: {"sub": "test_user"}

client = TestClient(app)


@pytest.fixture
def mock_request_id():
    """Generate a mock request ID for testing."""
    return f"test_req_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def mock_request_id_context(mock_request_id):
    """Mock the request ID context by overriding the middleware behavior."""
    # Patch the UUID generation in the middleware to use our test ID
    with patch("uuid.uuid4") as mock_uuid:
        # Set up a mock UUID that returns our test request ID (without test_req_ prefix)
        mock_uuid_obj = MagicMock()
        mock_uuid_obj.__str__ = MagicMock(return_value=mock_request_id)
        mock_uuid.return_value = mock_uuid_obj

        # Also patch the function calls for direct usage
        with patch(
            "app.routers.mcp.asset.get_current_request_id", return_value=mock_request_id
        ), patch(
            "app.services.mcp_logger.get_current_request_id",
            return_value=mock_request_id,
        ):
            yield mock_request_id


class TestMCPAssetCreate:
    """Test suite for MCP asset creation endpoint."""

    def test_create_asset_success(self, clean_db: Session, mock_request_id_context):
        """Test successful asset creation with all components."""
        request_data = {
            "name": "Test Harmony",
            "description": "A test synesthetic asset",
            "tone": {
                "name": "Test Tone",
                "synth": {
                    "type": "Tone.MonoSynth",
                    "volume": -12,
                    "oscillator": {"type": "sine"},
                },
            },
            "shader": {
                "name": "Test Shader",
                "fragment_shader": "void main() { gl_FragColor = vec4(1.0); }",
                "uniforms": [{"name": "u_time", "type": "float", "default": 0.0}],
            },
            "haptic": {
                "name": "Test Haptic",
                "device": {"type": "gamepad"},
                "parameters": [],
            },
            "tags": ["test", "validation"],
        }

        response = client.post("/mcp/asset/create", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "request_id" in data
        assert "asset_id" in data
        assert "status" in data
        assert data["status"] == "success"
        assert "result" in data

        # Verify result details
        result = data["result"]
        assert "asset_id" in result
        assert "components" in result
        assert result["components"]["tone"] is True
        assert result["components"]["shader"] is True
        assert result["components"]["haptic"] is True

        # Verify command logging
        logs = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.command_type == "create_asset")
            .all()
        )

        assert len(logs) >= 1
        log_entry = logs[-1]  # Get the most recent
        assert log_entry.status == "success"
        assert log_entry.payload["name"] == "Test Harmony"
        assert log_entry.result["status"] == "created"

    def test_create_asset_minimal_data(
        self, clean_db: Session, mock_request_id_context
    ):
        """Test asset creation with minimal required data."""
        request_data = {
            "name": "Minimal Asset",
            "tone": {"name": "Basic Tone", "synth": {"type": "Tone.Synth"}},
            "shader": {"name": "Basic Shader", "fragment_shader": "void main() {}"},
        }

        response = client.post("/mcp/asset/create", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "asset_id" in data["result"]

        # Verify optional components are handled correctly
        result = data["result"]
        assert result["components"]["tone"] is True
        assert result["components"]["shader"] is True
        assert result["components"]["haptic"] is False  # Not provided

    def test_create_asset_invalid_payload_missing_name(self, mock_request_id_context):
        """Test asset creation with missing required name field."""
        request_data = {
            "tone": {"name": "Test", "synth": {"type": "Tone.Synth"}},
            "shader": {"name": "Test", "fragment_shader": "void main() {}"},
        }

        response = client.post("/mcp/asset/create", json=request_data)

        assert response.status_code == 422
        error_data = response.json()

        # Verify error structure
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)

        # Check that validation error mentions the missing field
        error_messages = [str(error) for error in error_data["detail"]]
        assert any("name" in msg.lower() for msg in error_messages)

    def test_create_asset_invalid_payload_wrong_types(self, mock_request_id_context):
        """Test asset creation with incorrect field types."""
        request_data = {
            "name": 123,  # Should be string
            "tone": "not_a_dict",  # Should be dict
            "shader": {"name": "Test", "fragment_shader": "void main() {}"},
        }

        response = client.post("/mcp/asset/create", json=request_data)

        assert response.status_code == 422
        error_data = response.json()

        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)

    def test_create_asset_request_id_in_response(self, mock_request_id_context):
        """Test that request_id is present in successful responses."""
        request_data = {
            "name": "Request ID Test",
            "tone": {"name": "Test", "synth": {"type": "Tone.Synth"}},
            "shader": {"name": "Test", "fragment_shader": "void main() {}"},
        }

        response = client.post("/mcp/asset/create", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "request_id" in data
        assert data["request_id"] == mock_request_id_context


class TestMCPAssetUpdate:
    """Test suite for MCP asset parameter update endpoint."""

    def test_update_param_success(self, clean_db: Session, mock_request_id_context):
        """Test successful parameter update."""
        request_data = {
            "asset_id": "asset_test123",
            "path": "shader.u_time",
            "value": 1.5,
        }

        response = client.post("/mcp/asset/update", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "request_id" in data
        assert "result" in data

        result = data["result"]
        assert result["asset_id"] == "asset_test123"
        assert result["path"] == "shader.u_time"
        assert result["new_value"] == 1.5
        assert result["updated"] is True

        # Verify command logging
        logs = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.command_type == "update_param")
            .all()
        )

        assert len(logs) >= 1
        log_entry = logs[-1]
        assert log_entry.status == "success"
        assert log_entry.asset_id == "asset_test123"

    def test_update_param_asset_not_found(self, mock_request_id_context):
        """Test parameter update with nonexistent asset."""
        request_data = {
            "asset_id": "nonexistent_asset123",
            "path": "shader.u_time",
            "value": 1.0,
        }

        response = client.post("/mcp/asset/update", json=request_data)

        assert response.status_code == 404
        error_data = response.json()

        assert "detail" in error_data
        detail = error_data["detail"]

        assert detail["error"] == "Asset not found"
        assert "request_id" in detail
        assert detail["asset_id"] == "nonexistent_asset123"
        assert "message" in detail

    def test_update_param_invalid_path(self, mock_request_id_context):
        """Test parameter update with invalid parameter path."""
        request_data = {
            "asset_id": "asset_test123",
            "path": "invalid.parameter.path",
            "value": 1.0,
        }

        response = client.post("/mcp/asset/update", json=request_data)

        assert response.status_code == 422
        error_data = response.json()

        detail = error_data["detail"]
        assert detail["error"] == "Invalid parameter path"
        assert "request_id" in detail
        assert detail["path"] == "invalid.parameter.path"
        assert "valid_paths" in detail
        assert isinstance(detail["valid_paths"], list)

    def test_update_param_missing_fields(self, mock_request_id_context):
        """Test parameter update with missing required fields."""
        request_data = {
            "asset_id": "asset_test123"
            # Missing path and value
        }

        response = client.post("/mcp/asset/update", json=request_data)

        assert response.status_code == 422
        error_data = response.json()

        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)

    def test_update_param_type_validation(self, mock_request_id_context):
        """Test parameter update with various value types."""
        test_cases = [
            {"value": 1.5, "expected_type": float},
            {"value": 42, "expected_type": int},
            {"value": True, "expected_type": bool},
            {"value": "test_string", "expected_type": str},
        ]

        for case in test_cases:
            request_data = {
                "asset_id": "asset_test123",
                "path": "shader.u_time",
                "value": case["value"],
            }

            response = client.post("/mcp/asset/update", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["result"]["new_value"] == case["value"]


class TestMCPAssetModulation:
    """Test suite for MCP asset modulation endpoint."""

    def test_apply_modulation_success(self, clean_db: Session, mock_request_id_context):
        """Test successful modulation application."""
        request_data = {
            "asset_id": "asset_test123",
            "modulation_id": "sine_wave_mod",
            "definition": {
                "id": "sine_wave_mod",
                "target": "shader.u_r",
                "type": "additive",
                "waveform": "sine",
                "frequency": 0.5,
                "amplitude": 0.1,
                "min": 0.0,
                "max": 1.0,
            },
        }

        response = client.post("/mcp/asset/modulate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "request_id" in data

        result = data["result"]
        assert result["asset_id"] == "asset_test123"
        assert result["modulation_id"] == "sine_wave_mod"
        assert result["applied"] is True
        assert "definition" in result

        # Verify command logging
        logs = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.command_type == "apply_modulation")
            .all()
        )

        assert len(logs) >= 1
        log_entry = logs[-1]
        assert log_entry.status == "success"
        assert log_entry.asset_id == "asset_test123"

    def test_apply_modulation_asset_not_found(self, mock_request_id_context):
        """Test modulation application to nonexistent asset."""
        request_data = {
            "asset_id": "nonexistent_asset123",
            "modulation_id": "test_mod",
            "definition": {
                "id": "test_mod",
                "target": "shader.u_r",
                "min": 0.0,
                "max": 1.0,
            },
        }

        response = client.post("/mcp/asset/modulate", json=request_data)

        assert response.status_code == 404
        error_data = response.json()

        detail = error_data["detail"]
        assert detail["error"] == "Asset not found"
        assert "request_id" in detail
        assert detail["asset_id"] == "nonexistent_asset123"

    def test_apply_modulation_duplicate_conflict(self, mock_request_id_context):
        """Test applying duplicate modulation returns 409 conflict."""
        request_data = {
            "asset_id": "asset_test123",
            "modulation_id": "duplicate_mod",
            "definition": {
                "id": "duplicate_mod",
                "target": "shader.u_r",
                "min": 0.0,
                "max": 1.0,
            },
        }

        response = client.post("/mcp/asset/modulate", json=request_data)

        assert response.status_code == 409
        error_data = response.json()

        detail = error_data["detail"]
        assert detail["error"] == "Modulation already exists"
        assert "request_id" in detail
        assert detail["asset_id"] == "asset_test123"
        assert detail["modulation_id"] == "duplicate_mod"

    def test_apply_modulation_invalid_payload(self, mock_request_id_context):
        """Test modulation application with invalid payload structure."""
        request_data = {
            "asset_id": "asset_test123",
            "modulation_id": "",  # Empty modulation_id
            "definition": "not_a_dict",  # Should be dict
        }

        response = client.post("/mcp/asset/modulate", json=request_data)

        assert response.status_code == 422
        error_data = response.json()

        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)


class TestMCPAssetValidation:
    """Test suite for MCP asset validation endpoint."""

    def test_validate_asset_success(self, clean_db: Session, mock_request_id_context):
        """Test successful asset validation."""
        request_data = {
            "asset_blob": {
                "name": "Valid Asset",
                "shader": {
                    "fragment_shader": "void main() { gl_FragColor = vec4(1.0); }",
                    "uniforms": [],
                },
                "tone": {"synth": {"type": "Tone.Synth"}},
            }
        }

        response = client.post("/mcp/asset/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "request_id" in data

        result = data["result"]
        assert result["valid"] is True
        assert result["validation_passed"] is True
        assert "components_found" in result
        assert "name" in result["components_found"]

        # Verify command logging
        logs = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.command_type == "validate_asset")
            .all()
        )

        assert len(logs) >= 1
        log_entry = logs[-1]
        assert log_entry.status == "success"

    def test_validate_asset_missing_name(self, mock_request_id_context):
        """Test asset validation with missing name."""
        request_data = {
            "asset_blob": {
                "shader": {"fragment_shader": "void main() {}"},
                "tone": {"synth": {"type": "Tone.Synth"}},
            }
        }

        response = client.post("/mcp/asset/validate", json=request_data)

        assert response.status_code == 422
        error_data = response.json()

        detail = error_data["detail"]
        assert detail["error"] == "Validation failed"
        assert "request_id" in detail
        assert "validation_errors" in detail
        assert "Asset name is required" in detail["validation_errors"]

    def test_validate_asset_missing_components(self, mock_request_id_context):
        """Test asset validation with missing required components."""
        request_data = {
            "asset_blob": {
                "name": "Invalid Asset"
                # Missing shader and tone
            }
        }

        response = client.post("/mcp/asset/validate", json=request_data)

        assert response.status_code == 422
        error_data = response.json()

        detail = error_data["detail"]
        assert detail["error"] == "Validation failed"
        assert "validation_errors" in detail
        assert any("shader or tone" in error for error in detail["validation_errors"])

    def test_validate_asset_invalid_structure(self, mock_request_id_context):
        """Test asset validation with invalid asset_blob structure."""
        request_data = {"asset_blob": "not_a_dict"}  # Should be dict

        response = client.post("/mcp/asset/validate", json=request_data)

        assert response.status_code == 422
        error_data = response.json()

        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)


class TestMCPAssetPing:
    """Test suite for MCP asset ping endpoint."""

    def test_ping_endpoint(self):
        """Test the ping endpoint returns expected response."""
        response = client.get("/mcp/asset/ping")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "MCP asset router live"


class TestMCPErrorHandling:
    """Test suite for MCP error handling and request_id propagation."""

    def test_request_id_in_all_error_responses(self, mock_request_id_context):
        """Test that request_id is present in all error response types."""
        error_test_cases = [
            {
                "endpoint": "/mcp/asset/update",
                "data": {
                    "asset_id": "nonexistent_asset123",
                    "path": "shader.u_time",
                    "value": 1.0,
                },
                "expected_status": 404,
            },
            {
                "endpoint": "/mcp/asset/update",
                "data": {
                    "asset_id": "asset_test123",
                    "path": "invalid.path",
                    "value": 1.0,
                },
                "expected_status": 422,
            },
            {
                "endpoint": "/mcp/asset/modulate",
                "data": {
                    "asset_id": "asset_test123",
                    "modulation_id": "duplicate_mod",
                    "definition": {},
                },
                "expected_status": 409,
            },
            {
                "endpoint": "/mcp/asset/validate",
                "data": {"asset_blob": {"name": ""}},
                "expected_status": 422,
            },
        ]

        for test_case in error_test_cases:
            response = client.post(test_case["endpoint"], json=test_case["data"])

            assert response.status_code == test_case["expected_status"]
            error_data = response.json()

            # All errors should have request_id in detail
            if "detail" in error_data and isinstance(error_data["detail"], dict):
                assert "request_id" in error_data["detail"]
                assert error_data["detail"]["request_id"] == mock_request_id_context

    def test_schema_validation_error_structure(self, mock_request_id_context):
        """Test that schema validation errors have proper structure."""
        # Test with completely invalid payload
        response = client.post("/mcp/asset/create", json={"invalid": "payload"})

        assert response.status_code == 422
        error_data = response.json()

        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)

        # Each validation error should have proper structure
        for error in error_data["detail"]:
            assert "loc" in error  # Field location
            assert "msg" in error  # Error message
            assert "type" in error  # Error type


class TestMCPCommandLogging:
    """Test suite for MCP command logging integration."""

    def test_logging_on_success_paths(self, clean_db: Session, mock_request_id_context):
        """Test that successful operations create proper log entries."""
        # Test create asset logging
        create_data = {
            "name": "Log Test Asset",
            "tone": {"name": "Test", "synth": {"type": "Tone.Synth"}},
            "shader": {"name": "Test", "fragment_shader": "void main() {}"},
        }

        response = client.post("/mcp/asset/create", json=create_data)
        assert response.status_code == 200

        # Check log entry
        logs = (
            clean_db.query(MCPCommandLog)
            .filter(
                MCPCommandLog.command_type == "create_asset",
                MCPCommandLog.request_id == mock_request_id_context,
            )
            .all()
        )

        assert len(logs) >= 1
        log_entry = logs[-1]
        assert log_entry.status == "success"
        assert log_entry.payload["name"] == "Log Test Asset"
        assert log_entry.result is not None
        assert log_entry.result["status"] == "created"

    def test_logging_preserves_request_context(
        self, clean_db: Session, mock_request_id_context
    ):
        """Test that logging preserves request context across operations."""
        operations = [
            {
                "endpoint": "/mcp/asset/create",
                "data": {
                    "name": "Context Test",
                    "tone": {"name": "Test", "synth": {"type": "Tone.Synth"}},
                    "shader": {"name": "Test", "fragment_shader": "void main() {}"},
                },
                "command_type": "create_asset",
            },
            {
                "endpoint": "/mcp/asset/update",
                "data": {
                    "asset_id": "asset_test123",
                    "path": "shader.u_time",
                    "value": 2.0,
                },
                "command_type": "update_param",
            },
            {
                "endpoint": "/mcp/asset/validate",
                "data": {
                    "asset_blob": {
                        "name": "Valid Asset",
                        "shader": {"fragment_shader": "void main() {}"},
                        "tone": {"synth": {"type": "Tone.Synth"}},
                    }
                },
                "command_type": "validate_asset",
            },
        ]

        for operation in operations:
            response = client.post(operation["endpoint"], json=operation["data"])
            assert response.status_code == 200

            # Verify log entry has correct request_id
            logs = (
                clean_db.query(MCPCommandLog)
                .filter(
                    MCPCommandLog.command_type == operation["command_type"],
                    MCPCommandLog.request_id == mock_request_id_context,
                )
                .all()
            )

            assert len(logs) >= 1
            log_entry = logs[-1]
            assert log_entry.request_id == mock_request_id_context


class TestMCPOpenAPICompliance:
    """Test suite for OpenAPI specification compliance."""

    def test_openapi_endpoints_documented(self):
        """Test that all MCP endpoints are documented in OpenAPI spec."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        spec = response.json()
        paths = spec.get("paths", {})

        # Verify all MCP endpoints are documented
        expected_endpoints = [
            "/mcp/asset/ping",
            "/mcp/asset/create",
            "/mcp/asset/update",
            "/mcp/asset/modulate",
            "/mcp/asset/validate",
        ]

        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Endpoint {endpoint} not found in OpenAPI spec"

    def test_openapi_schemas_documented(self):
        """Test that MCP request schemas are documented."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        spec = response.json()
        components = spec.get("components", {})
        schemas = components.get("schemas", {})

        expected_schemas = [
            "CreateAssetRequest",
            "UpdateParamRequest",
            "ApplyModulationRequest",
            "ValidateAssetRequest",
        ]

        for schema in expected_schemas:
            assert schema in schemas, f"Schema {schema} not found in OpenAPI spec"

    def test_openapi_responses_have_examples(self):
        """Test that MCP endpoints have proper response documentation."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        spec = response.json()
        paths = spec.get("paths", {})

        # Check that create endpoint has proper response definition
        create_path = paths.get("/mcp/asset/create", {})
        post_method = create_path.get("post", {})
        responses = post_method.get("responses", {})

        # Should have 200 response defined
        assert "200" in responses
        assert "422" in responses  # Validation error

        # Verify response structure documentation
        success_response = responses["200"]
        assert "description" in success_response
