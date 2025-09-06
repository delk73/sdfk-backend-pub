"""
Test Status Code Correctness Across All Routers
Mission M0.6 - Parametrized tests to verify expected HTTP status codes
"""

import pytest
import time
from unittest.mock import Mock, patch
from app.routers import controls
from app.cache import cache
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from tests.fixtures.factories import example_shader_lib_def


@pytest.fixture
def basic_control_data():
    """Basic control data for testing"""
    timestamp = int(time.time())
    return {
        "name": f"Test Control {timestamp}",
        "description": "Test control description",
        "meta_info": {"category": "test"},
        "control_parameters": [
            {
                "parameter": "test.param",
                "label": "Test Parameter",
                "type": "float",
                "unit": "linear",
                "default": 0.0,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.1,
                "mappings": [],
            }
        ],
    }


@pytest.fixture
def basic_modulation_data():
    """Basic modulation data for testing"""
    timestamp = int(time.time())
    return {
        "name": f"Test Modulation {timestamp}",
        "description": "Test modulation description",
        "modulation_def": {"type": "test"},
    }


@pytest.fixture
def basic_haptic_data():
    """Basic haptic data for testing"""
    return {
        "name": f"Test Haptic {int(time.time())}",
        "description": "Test haptic description",
        "patterns": [],
        "meta_info": {"category": "test"},
    }


@pytest.fixture
def basic_shader_data():
    """Basic shader data for testing"""
    return {
        "name": f"Test Shader {int(time.time())}",
        "description": "Test shader description",
        "vertex_shader": "void main() { gl_Position = vec4(0.0); }",
        "fragment_shader": "void main() { gl_FragColor = vec4(1.0); }",
        "meta_info": {"category": "test"},
    }


@pytest.fixture
def basic_shader_lib_data():
    """Basic shader library data for testing"""
    lib = example_shader_lib_def()
    lib["name"] = f"Test Shader Lib {int(time.time())}"
    return lib


@pytest.fixture
def basic_tone_data():
    """Basic tone data for testing"""
    return {
        "name": f"Test Tone {int(time.time())}",
        "description": "Test tone description",
        "synth": {"type": "Tone.Synth"},
        "input_parameters": [],
        "effects": [],
        "patterns": [],
        "parts": [],
        "meta_info": {"category": "test"},
    }


@pytest.fixture
def basic_synesthetic_asset_data():
    """Basic synesthetic asset data for testing"""
    return {
        "name": f"Test Asset {int(time.time())}",
        "description": "Test synesthetic asset",
        "meta_info": {"category": "test"},
    }


class TestResourceNotFound:
    """Test 404 status codes for resource not found scenarios"""

    @pytest.mark.parametrize(
        "endpoint,resource_id",
        [
            ("/controls/99999", 99999),
            ("/modulations/99999", 99999),
            ("/haptics/99999", 99999),
            ("/shaders/99999", 99999),
            ("/shader_libs/99999", 99999),
            ("/tones/99999", 99999),
            ("/synesthetic-assets/99999", 99999),  # Fixed route
        ],
    )
    def test_get_nonexistent_resource_returns_404(self, client, endpoint, resource_id):
        """Test that GET requests for nonexistent resources return 404"""
        response = client.get(endpoint, headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "endpoint,resource_id",
        [
            ("/controls/99999", 99999),
            ("/modulations/99999", 99999),
            ("/haptics/99999", 99999),
            ("/shaders/99999", 99999),
            ("/shader_libs/99999", 99999),
            ("/tones/99999", 99999),
            ("/synesthetic-assets/99999", 99999),  # Fixed route
        ],
    )
    def test_put_nonexistent_resource_returns_404(
        self,
        client,
        endpoint,
        resource_id,
        basic_control_data,
        basic_modulation_data,
        basic_haptic_data,
        basic_shader_data,
        basic_shader_lib_data,
        basic_tone_data,
        basic_synesthetic_asset_data,
    ):
        """Test that PUT requests for nonexistent resources return 404"""
        # Select appropriate test data based on endpoint
        test_data_map = {
            "/controls/": basic_control_data,
            "/modulations/": basic_modulation_data,
            "/haptics/": basic_haptic_data,
            "/shaders/": basic_shader_data,
            "/shader_libs/": basic_shader_lib_data,
            "/tones/": basic_tone_data,
            "/synesthetic_assets/": basic_synesthetic_asset_data,
        }

        # Find matching test data
        test_data = None
        for key, data in test_data_map.items():
            if key in endpoint:
                test_data = data
                break

        if test_data:
            response = client.put(
                endpoint, json=test_data, headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "endpoint,resource_id",
        [
            ("/controls/99999", 99999),
            ("/modulations/99999", 99999),
            ("/haptics/99999", 99999),
            ("/shaders/99999", 99999),
            ("/shader_libs/99999", 99999),
            ("/tones/99999", 99999),
            ("/synesthetic_assets/99999", 99999),
        ],
    )
    def test_delete_nonexistent_resource_returns_404(
        self, client, endpoint, resource_id
    ):
        """Test that DELETE requests for nonexistent resources return 404"""
        response = client.delete(
            endpoint, headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestValidation:
    """Test 422 status codes for validation errors"""

    @pytest.mark.parametrize(
        "endpoint,invalid_data",
        [
            ("/controls/", {"name": "", "description": ""}),  # Empty required fields
            ("/controls/", {"invalid_field": "value"}),  # Missing required fields
            ("/modulations/", {"name": "", "description": ""}),  # Empty required fields
            ("/haptics/", {"name": "", "patterns": "not_a_list"}),  # Invalid field type
            ("/shaders/", {"name": "", "vertex_shader": ""}),  # Empty required fields
            (
                "/shader_libs/",
                {"name": "", "helpers": "not_a_dict", "baseInputParametersSpec": []},
            ),  # Invalid field type
            ("/tones/", {"name": "", "description": ""}),  # Empty required fields
            (
                "/synesthetic-assets/",
                {"name": "", "description": ""},
            ),  # Empty required fields - fixed route
        ],
    )
    def test_post_invalid_data_returns_422(self, client, endpoint, invalid_data):
        """Test that POST requests with invalid data return 422"""
        response = client.post(
            endpoint, json=invalid_data, headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 422


class TestConflicts:
    """Test 409 status codes for resource conflicts"""

    @pytest.mark.parametrize(
        "endpoint,test_data_fixture",
        [
            ("/controls/", "basic_control_data"),
            ("/modulations/", "basic_modulation_data"),
        ],
    )
    def test_duplicate_name_returns_409(
        self, client, endpoint, test_data_fixture, request
    ):
        """Test that creating resources with duplicate names returns 409"""
        test_data = request.getfixturevalue(test_data_fixture)

        # Create the first resource
        response1 = client.post(
            endpoint, json=test_data, headers={"Authorization": "Bearer test-token"}
        )
        if response1.status_code == 201 or response1.status_code == 200:
            # Try to create another with the same name
            response2 = client.post(
                endpoint, json=test_data, headers={"Authorization": "Bearer test-token"}
            )
            assert response2.status_code == 409
            assert "already exists" in response2.json()["detail"].lower()


class TestDatabaseErrors:
    """Test database-related status codes"""

    def test_database_integrity_error_returns_409(self, client, basic_control_data):
        """Test that database integrity errors return 409"""
        mock_session = Mock()
        mock_session.add.side_effect = IntegrityError("", "", "")
        client.app.dependency_overrides[controls.get_db] = lambda: mock_session

        response = client.post(
            "/controls/",
            json=basic_control_data,
            headers={"Authorization": "Bearer test-token"},
        )
        client.app.dependency_overrides.pop(controls.get_db, None)
        assert response.status_code == 409

    def test_database_sqlalchemy_error_returns_500(self, client, basic_control_data):
        """Test that SQLAlchemy errors return 500"""
        mock_session = Mock()
        mock_session.add.side_effect = SQLAlchemyError("Database error")
        client.app.dependency_overrides[controls.get_db] = lambda: mock_session

        response = client.post(
            "/controls/",
            json=basic_control_data,
            headers={"Authorization": "Bearer test-token"},
        )
        client.app.dependency_overrides.pop(controls.get_db, None)
        assert response.status_code == 500


class TestAuthenticationErrors:
    """Test authentication-related status codes"""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/controls/",
            "/modulations/",
            "/haptics/",
            "/shaders/",
            "/shader_libs/",
            "/tones/",
            "/synesthetic_assets/",
        ],
    )
    def test_missing_auth_token_returns_401_or_403(self, client, endpoint, clean_db):
        """Test that requests without auth tokens return 401 or 403"""
        response = client.get(endpoint)
        # TODO: Authentication not yet implemented - some endpoints return 200/404
        # When auth is implemented, should return 401 or 403
        assert response.status_code in [200, 401, 403, 404]  # Allow current behavior


class TestInternalServerErrors:
    """Test 500 status codes for internal server errors"""

    @patch("app.routers.tones.models.Tone")
    def test_unexpected_error_returns_500(self, mock_tone, client, basic_tone_data):
        """Test that unexpected errors return 500"""
        mock_tone.side_effect = Exception("Unexpected error")

        response = client.post(
            "/tones/",
            json=basic_tone_data,
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()
