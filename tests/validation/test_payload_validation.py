"""
Test FastAPI's native validation error handling (422 responses).

This test suite ensures that validation errors return proper 422 status codes
with complete error detail lists, not truncated 400 responses.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestPayloadValidation:
    """Test that validation errors return 422 with full error details."""

    def test_tones_validation_returns_422_list(self):
        """POST /tones/ with invalid payload should return 422 with detail list."""
        # Send completely invalid payload - missing required fields
        invalid_payload = {
            "invalid_field": "should not be here",
            "name": "",  # Empty name should fail validation
            # Missing required fields like description, synth, etc.
        }

        response = client.post("/tones/", json=invalid_payload)

        # Should return 422 (not 400)
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

        # Response should have detail field
        error_data = response.json()
        assert (
            "detail" in error_data
        ), f"Missing 'detail' field in response: {error_data}"

        # Detail should be a list (FastAPI's default format)
        detail = error_data["detail"]
        assert isinstance(
            detail, list
        ), f"Expected detail to be a list, got {type(detail)}: {detail}"

        # Should have at least one error
        assert (
            len(detail) >= 1
        ), f"Expected at least one validation error, got: {detail}"

        # Each error should have the standard FastAPI validation error format
        for error in detail:
            assert isinstance(error, dict), f"Each error should be a dict, got: {error}"
            assert "loc" in error, f"Missing 'loc' field in error: {error}"
            assert "msg" in error, f"Missing 'msg' field in error: {error}"
            assert "type" in error, f"Missing 'type' field in error: {error}"

    def test_tones_validation_with_invalid_types_returns_422(self):
        """POST /tones/ with wrong field types should return 422 with detail list."""
        invalid_payload = {
            "name": 123,  # Should be string
            "description": [],  # Should be string
            "synth": "not_a_dict",  # Should be dict/object
            "effects": "not_a_list",  # Should be list
        }

        response = client.post("/tones/", json=invalid_payload)

        # Should return 422 (not 400)
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

        # Response should have detail as a list
        error_data = response.json()
        assert "detail" in error_data
        detail = error_data["detail"]
        assert isinstance(detail, list)
        assert len(detail) >= 1

        # Should have multiple validation errors for different fields
        error_fields = [
            error.get("loc", [])[-1] for error in detail if error.get("loc")
        ]
        assert (
            len(set(error_fields)) >= 2
        ), f"Expected errors for multiple fields, got: {error_fields}"

    def test_controls_validation_returns_422_list(self):
        """POST /controls/ with invalid payload should return 422 with detail list."""
        invalid_payload = {
            "name": None,  # Should be string
            "description": 123,  # Should be string
            "control_parameters": "not_a_dict",  # Should be dict
        }

        response = client.post("/controls/", json=invalid_payload)

        # Should return 422 (not 400)
        assert (
            response.status_code == 422
        ), f"Expected 422, got {response.status_code}: {response.text}"

        # Response should have detail as a list
        error_data = response.json()
        assert "detail" in error_data
        detail = error_data["detail"]
        assert isinstance(detail, list)
        assert len(detail) >= 1

    def test_generic_validation_error_format(self):
        """Test that validation errors follow FastAPI's standard format."""
        # Use any endpoint that has validation - tones endpoint
        invalid_payload = {"completely": "wrong", "structure": True}

        response = client.post("/tones/", json=invalid_payload)

        assert response.status_code == 422
        error_data = response.json()

        # Verify standard FastAPI error format
        assert "detail" in error_data
        detail = error_data["detail"]
        assert isinstance(detail, list)

        # Each error should follow standard format
        for error in detail:
            assert "loc" in error  # Location of the error
            assert "msg" in error  # Human-readable message
            assert "type" in error  # Error type code

            # loc should be a list indicating the path to the error
            assert isinstance(error["loc"], list)
            assert len(error["loc"]) >= 1

            # msg should be a string
            assert isinstance(error["msg"], str)
            assert len(error["msg"]) > 0

            # type should be a string
            assert isinstance(error["type"], str)
            assert len(error["type"]) > 0

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/tones/",
            "/controls/",
            "/modulations/",
        ],
    )
    def test_multiple_endpoints_return_422_not_400(self, endpoint):
        """Test that various endpoints return 422 (not 400) for validation errors."""
        invalid_payload = {"invalid": "data", "wrong": "format"}

        response = client.post(endpoint, json=invalid_payload)

        # Should return 422, never 400 for validation errors
        assert (
            response.status_code == 422
        ), f"Endpoint {endpoint} returned {response.status_code} instead of 422"

        # Should have proper error structure
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)
