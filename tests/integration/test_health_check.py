"""Integration tests for health check endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthCheckEndpoints:
    """Test suite for health check endpoints."""

    def test_ping_endpoint(self):
        """Test basic ping endpoint."""
        response = client.get("/ping")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "message" in data
        assert "request_id" in data

        # Verify content
        assert data["status"] == "ok"
        assert data["message"] == "pong"
        assert isinstance(data["request_id"], str)
        assert len(data["request_id"]) > 0

    def test_health_check_endpoint_structure(self):
        """Test comprehensive health check endpoint structure."""
        response = client.get("/health")

        # Should return either 200 (healthy) or 503 (degraded)
        assert response.status_code in [200, 503]
        data = response.json()

        # Verify top-level structure
        assert "status" in data
        assert "request_id" in data
        assert "timestamp" in data
        assert "services" in data
        assert "environment" in data

        # Verify status values
        assert data["status"] in ["healthy", "degraded"]

        # Verify request_id
        assert isinstance(data["request_id"], str)
        assert len(data["request_id"]) > 0

        # Verify timestamp format (ISO format)
        assert "T" in data["timestamp"]
        assert data["timestamp"].endswith("Z") or data["timestamp"].endswith(
            "+00:00"
        ), f"Invalid timestamp format: {data['timestamp']}"

        # Verify services structure
        services = data["services"]
        assert isinstance(services, dict)

        # Check expected services are present
        expected_services = ["database", "mcp"]
        for service in expected_services:
            assert service in services, f"Service {service} not in health check"

            service_data = services[service]
            assert "status" in service_data
            assert "details" in service_data

            # Status should be one of expected values
            assert service_data["status"] in [
                "healthy",
                "unhealthy",
                "unreachable",
                "not_configured",
                "configured",
                "misconfigured",
            ]

    def test_health_check_database_service(self):
        """Test that health check properly tests database connection."""
        response = client.get("/health")
        data = response.json()

        database_service = data["services"]["database"]

        # Database should be tested
        assert "status" in database_service
        assert "details" in database_service

        # In test environment, database should be healthy
        # (assuming test.sh sets up the database properly)
        if database_service["status"] == "healthy":
            assert "connected" in database_service["details"].lower()
        else:
            # If unhealthy, should have error details
            assert (
                "failed" in database_service["details"].lower()
                or "error" in database_service["details"].lower()
            )

    def test_health_check_mcp_service(self):
        """Test that health check properly tests MCP router."""
        response = client.get("/health")
        data = response.json()

        mcp_service = data["services"]["mcp"]

        # MCP should be tested
        assert "status" in mcp_service
        assert "details" in mcp_service

        # MCP router should be available in normal operation
        expected_statuses = ["healthy", "unhealthy"]
        assert mcp_service["status"] in expected_statuses

    def test_health_check_environment_info(self):
        """Test that health check includes environment information."""
        response = client.get("/health")
        data = response.json()

        environment = data["environment"]

        # Should include testing flag
        assert "testing" in environment
        assert isinstance(environment["testing"], bool)

    def test_health_check_degraded_status(self):
        """Test health check behavior when services are degraded."""
        response = client.get("/health")
        data = response.json()

        # If status is degraded, should include unhealthy services list
        if data["status"] == "degraded":
            assert "unhealthy_services" in data
            assert isinstance(data["unhealthy_services"], list)
            assert len(data["unhealthy_services"]) > 0

            # Verify HTTP status code is 503 for degraded services
            assert response.status_code == 503
        else:
            # If healthy, HTTP status should be 200
            assert response.status_code == 200

    def test_health_check_response_time(self):
        """Test that health check responds within reasonable time."""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        response_time = end_time - start_time

        # Health check should respond within 10 seconds
        assert response_time < 10.0, f"Health check took too long: {response_time}s"

        # Should be successful (200 or 503)
        assert response.status_code in [200, 503]

    def test_multiple_health_checks_consistent(self):
        """Test that multiple health checks return consistent results."""
        responses = []

        # Make multiple requests
        for _ in range(3):
            response = client.get("/health")
            responses.append(response.json())

        # All responses should have same basic structure
        for response_data in responses:
            assert "status" in response_data
            assert "services" in response_data

        # Service statuses should be consistent (not flapping)
        first_services = responses[0]["services"]
        for response_data in responses[1:]:
            current_services = response_data["services"]

            for service_name in first_services:
                if service_name in current_services:
                    first_status = first_services[service_name]["status"]
                    current_status = current_services[service_name]["status"]
                    assert current_status == first_status

    def test_health_check_openapi_documentation(self):
        """Test that health check endpoint is documented in OpenAPI."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        spec = response.json()
        paths = spec.get("paths", {})

        # Verify health endpoint is documented
        assert "/health" in paths, "Health check endpoint not documented in OpenAPI"

        health_spec = paths["/health"]
        assert "get" in health_spec, "GET method not documented for health endpoint"

        get_spec = health_spec["get"]
        assert "responses" in get_spec, "Responses not documented"

        # Should document both success and error responses
        responses = get_spec["responses"]
        assert "200" in responses, "Success response not documented"
        assert (
            "503" in responses or "default" in responses
        ), "Error response not documented"
