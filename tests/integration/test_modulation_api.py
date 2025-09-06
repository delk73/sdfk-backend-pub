"""
Integration tests for the modulation API endpoints.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_create_modulation(auth_client: TestClient, clean_db: Session):
    """Test creating a modulation."""
    # Test data
    modulation_data = {
        "name": "API Test Modulations",
        "description": "Test modulation set created via API",
        "meta_info": {"category": "modulation", "tags": ["test", "api"]},
        "modulations": [
            {
                "id": "api_test_modulation",
                "target": "visual.u_time",
                "type": "additive",
                "waveform": "sine",
                "frequency": 0.5,
                "amplitude": 0.5,
                "offset": 0.0,
                "phase": 0.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }

    # Create modulation
    response = auth_client.post("/modulations/", json=modulation_data)

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"

    # Validate response data
    data = response.json()
    assert data["name"] == modulation_data["name"]
    assert data["description"] == modulation_data["description"]
    assert data["meta_info"] == modulation_data["meta_info"]
    assert len(data["modulations"]) == 1
    assert data["modulations"][0]["id"] == modulation_data["modulations"][0]["id"]
    assert "modulation_id" in data

    # Store modulation_id for later tests
    modulation_id = data["modulation_id"]

    # Get the created modulation
    response = auth_client.get(f"/modulations/{modulation_id}")

    # Check response
    assert response.status_code == 200

    # Validate response data
    data = response.json()
    assert data["name"] == modulation_data["name"]
    assert data["modulation_id"] == modulation_id


def test_get_modulations(auth_client: TestClient, modulation: Session):
    """Test getting all modulations."""
    # Get all modulations
    response = auth_client.get("/modulations/")

    # Check response
    assert response.status_code == 200

    # Validate response data
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # Check that our test modulation is in the list
    assert any(item["name"] == "Test Modulations" for item in data)


def test_update_modulation(auth_client: TestClient, modulation: Session):
    """Test updating a modulation."""
    # Get the modulation ID
    modulation_id = modulation.modulation_id

    # Update data
    update_data = {
        "name": "Updated Test Modulations",
        "description": "Updated test modulation set",
        "meta_info": {"category": "updated", "tags": ["updated"]},
        "modulations": [
            {
                "id": "updated_test_modulation",
                "target": "visual.u_updated",
                "type": "multiplicative",
                "waveform": "triangle",
                "frequency": 1.0,
                "amplitude": 1.0,
                "offset": 1.0,
                "phase": 1.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }

    # Update modulation
    response = auth_client.put(f"/modulations/{modulation_id}", json=update_data)

    # Check response
    assert response.status_code == 200, f"Response: {response.text}"

    # Validate response data
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["meta_info"] == update_data["meta_info"]
    assert len(data["modulations"]) == 1
    assert data["modulations"][0]["id"] == update_data["modulations"][0]["id"]
    assert data["modulation_id"] == modulation_id

    # Get the updated modulation
    response = auth_client.get(f"/modulations/{modulation_id}")

    # Check response
    assert response.status_code == 200

    # Validate response data
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["modulation_id"] == modulation_id


def test_delete_modulation(auth_client: TestClient, modulation: Session):
    """Test deleting a modulation."""
    # Get the modulation ID
    modulation_id = modulation.modulation_id

    # Delete modulation
    response = auth_client.delete(f"/modulations/{modulation_id}")

    # Check response
    assert response.status_code == 200

    # Try to get the deleted modulation
    response = auth_client.get(f"/modulations/{modulation_id}")

    # Check that it's not found
    assert response.status_code == 404


def test_full_modulation_lifecycle(auth_client: TestClient, clean_db: Session):
    """Test the full lifecycle of a modulation: create, get, update, delete."""
    # Test data
    modulation_data = {
        "name": "Lifecycle Test Modulations",
        "description": "Test modulation set for lifecycle testing",
        "meta_info": {"category": "lifecycle", "tags": ["test", "lifecycle"]},
        "modulations": [
            {
                "id": "lifecycle_test_modulation",
                "target": "visual.u_lifecycle",
                "type": "additive",
                "waveform": "sine",
                "frequency": 0.5,
                "amplitude": 0.5,
                "offset": 0.0,
                "phase": 0.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }

    # 1. Create modulation
    response = auth_client.post("/modulations/", json=modulation_data)
    assert response.status_code == 200

    data = response.json()
    modulation_id = data["modulation_id"]

    # 2. Get the created modulation
    response = auth_client.get(f"/modulations/{modulation_id}")
    assert response.status_code == 200
    assert response.json()["name"] == modulation_data["name"]

    # 3. Update the modulation
    update_data = {
        "name": "Updated Lifecycle Test Modulations",
        "modulations": [
            {
                "id": "updated_lifecycle_test_modulation",
                "target": "visual.u_updated_lifecycle",
                "type": "multiplicative",
                "waveform": "triangle",
                "frequency": 1.0,
                "amplitude": 1.0,
                "offset": 1.0,
                "phase": 1.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }

    response = auth_client.put(f"/modulations/{modulation_id}", json=update_data)
    assert response.status_code == 200

    # 4. Get the updated modulation
    response = auth_client.get(f"/modulations/{modulation_id}")
    assert response.status_code == 200
    assert response.json()["name"] == update_data["name"]

    # 5. Delete the modulation
    response = auth_client.delete(f"/modulations/{modulation_id}")
    assert response.status_code == 200

    # 6. Verify it's deleted
    response = auth_client.get(f"/modulations/{modulation_id}")
    assert response.status_code == 404
