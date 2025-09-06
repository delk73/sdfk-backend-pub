from fastapi.testclient import TestClient
import os
import json
import glob
from app.main import app
from app import security

# Override JWT verification for tests
app.dependency_overrides[security.verify_jwt] = lambda token=None: {"sub": "test_user"}

client = TestClient(app)


def test_create_haptic():
    """Test creating a haptic component"""
    haptic_data = {
        "name": "Test Pulse Feedback",
        "description": "Test pulsing haptic feedback",
        "meta_info": {
            "category": "haptic",
            "tags": ["pulse", "vibration", "dynamic"],
            "complexity": "medium",
        },
        "device": {
            "type": "generic",
            "options": {
                "maxIntensity": {"value": 1.0, "unit": "linear"},
                "maxFrequency": {"value": 250.0, "unit": "Hz"},
                "defaultDuration": {"value": 0.25, "unit": "s"},
            },
        },
        "input_parameters": [
            {
                "name": "Intensity",
                "parameter": "haptic.intensity",
                "path": "haptic.intensity",
                "type": "float",
                "unit": "linear",
                "default": 0.7,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.1,
            },
            {
                "name": "Frequency",
                "parameter": "haptic.frequency",
                "path": "haptic.frequency",
                "type": "float",
                "unit": "Hz",
                "default": 150.0,
                "min": 20.0,
                "max": 250.0,
                "step": 1,
                "smoothingTime": 0.1,
            },
        ],
    }
    response = client.post("/haptics/", json=haptic_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == haptic_data["name"]
    assert data["meta_info"] == haptic_data["meta_info"]
    assert "haptic_id" in data


def test_get_haptic():
    """Test retrieving a haptic component"""
    # Create a haptic first
    haptic_data = {
        "name": "Test Pulse Feedback",
        "description": "Test pulsing haptic feedback",
        "meta_info": {
            "category": "haptic",
            "tags": ["pulse", "vibration", "dynamic"],
            "complexity": "medium",
        },
        "device": {
            "type": "generic",
            "options": {
                "maxIntensity": {"value": 1.0, "unit": "linear"},
                "maxFrequency": {"value": 250.0, "unit": "Hz"},
                "defaultDuration": {"value": 0.25, "unit": "s"},
            },
        },
        "input_parameters": [
            {
                "name": "haptic.intensity",
                "parameter": "haptic.intensity",
                "path": "haptic.intensity",
                "type": "float",
                "unit": "linear",
                "default": 0.7,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.1,
            }
        ],
    }
    create_response = client.post("/haptics/", json=haptic_data)
    assert create_response.status_code == 200
    haptic_id = create_response.json()["haptic_id"]

    # Get the haptic
    response = client.get(f"/haptics/{haptic_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == haptic_data["name"]
    assert data["haptic_id"] == haptic_id


def test_update_haptic():
    """Test updating a haptic component"""
    # Create a haptic first
    haptic_data = {
        "name": "Test Pulse Feedback",
        "description": "Test pulsing haptic feedback",
        "meta_info": {
            "category": "haptic",
            "tags": ["pulse", "vibration", "dynamic"],
            "complexity": "medium",
        },
        "device": {
            "type": "generic",
            "options": {
                "maxIntensity": {"value": 1.0, "unit": "linear"},
                "maxFrequency": {"value": 250.0, "unit": "Hz"},
                "defaultDuration": {"value": 0.25, "unit": "s"},
            },
        },
        "input_parameters": [
            {
                "name": "Intensity",
                "parameter": "haptic.intensity",
                "path": "haptic.intensity",
                "type": "float",
                "unit": "linear",
                "default": 0.7,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.1,
            }
        ],
    }
    create_response = client.post("/haptics/", json=haptic_data)
    assert create_response.status_code == 200
    haptic_id = create_response.json()["haptic_id"]

    # Update the haptic
    update_data = {
        "name": "Updated Pulse Feedback",
        "meta_info": {
            "category": "haptic",
            "complexity": "high",
            "tags": ["pulse", "dynamic", "advanced"],
        },
    }
    response = client.put(f"/haptics/{haptic_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["meta_info"] == update_data["meta_info"]


def test_create_haptic_numeric_complexity():
    """Ensure numeric complexity values are stored as strings."""

    haptic_data = {
        "name": "Numeric Complexity",
        "description": "Test numeric complexity normalization",
        "meta_info": {
            "category": "haptic",
            "tags": ["test"],
            "complexity": 5,
        },
        "device": {
            "type": "generic",
            "options": {
                "maxIntensity": {"value": 1.0, "unit": "linear"},
                "maxFrequency": {"value": 250.0, "unit": "Hz"},
                "defaultDuration": {"value": 0.25, "unit": "s"},
            },
        },
        "input_parameters": [],
    }

    response = client.post("/haptics/", json=haptic_data)
    assert response.status_code == 200
    data = response.json()
    assert data["meta_info"]["complexity"] == "5"


def test_delete_haptic():
    """Test deleting a haptic component"""
    # Create a haptic first
    haptic_data = {
        "name": "Test Pulse Feedback",
        "description": "Test pulsing haptic feedback",
        "meta_info": {
            "category": "haptic",
            "tags": ["pulse", "vibration", "dynamic"],
            "complexity": "medium",
        },
        "device": {
            "type": "generic",
            "options": {
                "maxIntensity": {"value": 1.0, "unit": "linear"},
                "maxFrequency": {"value": 250.0, "unit": "Hz"},
                "defaultDuration": {"value": 0.25, "unit": "s"},
            },
        },
        "input_parameters": [
            {
                "name": "Intensity",
                "parameter": "haptic.intensity",
                "path": "haptic.intensity",
                "type": "float",
                "unit": "linear",
                "default": 0.7,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.1,
            }
        ],
    }
    create_response = client.post("/haptics/", json=haptic_data)
    assert create_response.status_code == 200
    haptic_id = create_response.json()["haptic_id"]

    # Delete the haptic
    delete_response = client.delete(f"/haptics/{haptic_id}")
    assert delete_response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/haptics/{haptic_id}")
    assert get_response.status_code == 404


def test_haptic_example_files_format():
    """Test that all haptic example files conform to the expected format."""
    examples_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "examples"
    )

    # Find all haptic example files
    haptic_example_files = glob.glob(os.path.join(examples_dir, "Haptic_Example*.json"))
    synesthetic_asset_files = glob.glob(
        os.path.join(examples_dir, "SynestheticAsset_Example*.json")
    )

    assert len(haptic_example_files) > 0, "No haptic example files found"

    # Validate standalone haptic examples
    for file_path in haptic_example_files:
        with open(file_path, "r") as f:
            data = json.load(f)

        # Check required fields
        assert "name" in data, f"Missing 'name' field in {file_path}"
        assert "meta_info" in data, f"Missing 'meta_info' field in {file_path}"
        assert "device" in data, f"Missing 'device' field in {file_path}"
        assert (
            "input_parameters" in data
        ), f"Missing 'input_parameters' field in {file_path}"

        # Check meta_info structure
        assert (
            "category" in data["meta_info"]
        ), f"Missing 'category' in meta_info in {file_path}"
        assert (
            "tags" in data["meta_info"]
        ), f"Missing 'tags' in meta_info in {file_path}"
        assert (
            "complexity" in data["meta_info"]
        ), f"Missing 'complexity' in meta_info in {file_path}"

        # Check device structure
        assert "type" in data["device"], f"Missing 'type' in device in {file_path}"
        assert (
            "options" in data["device"]
        ), f"Missing 'options' in device in {file_path}"

        # Check for new device options structure
        for option_key, option_value in data["device"]["options"].items():
            assert isinstance(
                option_value, dict
            ), f"Option {option_key} should be a dictionary with value and unit in {file_path}"
            assert (
                "value" in option_value
            ), f"Missing 'value' in option {option_key} in {file_path}"
            assert (
                "unit" in option_value
            ), f"Missing 'unit' in option {option_key} in {file_path}"

        # Check parameters structure
        assert isinstance(
            data["input_parameters"], list
        ), f"'input_parameters' should be a list in {file_path}"
        for param in data["input_parameters"]:
            assert (
                "parameter" in param
            ), f"Missing 'parameter' in parameter in {file_path}"
            assert "type" in param, f"Missing 'type' in parameter in {file_path}"
            assert "unit" in param, f"Missing 'unit' in parameter in {file_path}"
            assert "default" in param, f"Missing 'default' in parameter in {file_path}"
            if param["type"] in ["float", "int"]:
                assert "min" in param, f"Missing 'min' in parameter in {file_path}"
                assert "max" in param, f"Missing 'max' in parameter in {file_path}"

    # Validate haptic sections in synesthetic asset examples
    for file_path in synesthetic_asset_files:
        with open(file_path, "r") as f:
            data = json.load(f)

        if "haptic" in data:
            haptic_data = data["haptic"]

            # Check required fields
            assert (
                "name" in haptic_data
            ), f"Missing 'name' field in haptic section in {file_path}"
            assert (
                "device" in haptic_data
            ), f"Missing 'device' field in haptic section in {file_path}"
            assert (
                "input_parameters" in haptic_data
            ), f"Missing 'input_parameters' field in haptic section in {file_path}"

            # Check device structure
            assert (
                "type" in haptic_data["device"]
            ), f"Missing 'type' in device in haptic section in {file_path}"
            assert (
                "options" in haptic_data["device"]
            ), f"Missing 'options' in device in haptic section in {file_path}"

            # Check parameters structure
            assert isinstance(
                haptic_data["input_parameters"], list
            ), f"'input_parameters' should be a list in haptic section in {file_path}"
            for param in haptic_data["input_parameters"]:
                assert (
                    "parameter" in param
                ), f"Missing 'parameter' in parameter in {file_path}"
                assert "type" in param, f"Missing 'type' in parameter in {file_path}"
                assert "unit" in param, f"Missing 'unit' in parameter in {file_path}"
                assert (
                    "default" in param
                ), f"Missing 'default' in parameter in {file_path}"
                if param["type"] in ["float", "int"]:
                    assert "min" in param, f"Missing 'min' in parameter in {file_path}"
                    assert "max" in param, f"Missing 'max' in parameter in {file_path}"
