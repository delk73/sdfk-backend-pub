from fastapi.testclient import TestClient
from app.main import app
from app import security
from sqlalchemy.orm import Session
from app.models.db import get_db
from fastapi import Depends

# Override JWT verification for tests
app.dependency_overrides[security.verify_jwt] = lambda token=None: {"sub": "test_user"}

client = TestClient(app)


def test_create_shader(db: Session = Depends(get_db)):
    """Test shader creation"""
    shader_data = {
        "name": "Test Shader",
        "vertex_shader": "void main() {}",
        "fragment_shader": "void main() {}",
        "uniforms": [
            {"name": "test", "type": "float", "stage": "vertex", "default": 0.0}
        ],
    }
    response = client.post("/shaders/", json=shader_data)
    assert response.status_code == 200


def test_shader_with_invalid_uniform_stage():
    """Test shader creation with invalid uniform stage"""
    shader_data = {
        "name": "Invalid Uniform Stage",
        "vertex_shader": "void main() {}",
        "fragment_shader": "void main() {}",
        "uniforms": [
            {
                "name": "test",
                "type": "float",
                "stage": "invalid",  # Invalid stage
                "default": 0.0,
            }
        ],
    }
    response = client.post("/shaders/", json=shader_data)
    # External schema does not constrain stage; accept as valid
    assert response.status_code == 200


def test_shader_uniform_default_array():
    """Test shader uniform with array default value"""
    shader_data = {
        "name": "Array Default Value",
        "vertex_shader": "void main() {}",
        "fragment_shader": "void main() {}",
        "uniforms": [
            {
                "name": "test",
                "type": "vec2",
                "stage": "vertex",
                "default": [1.0, 2.0],  # Array default value
            }
        ],
    }
    response = client.post("/shaders/", json=shader_data)
    assert response.status_code == 200
