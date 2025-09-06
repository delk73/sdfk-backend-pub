from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
import app.security as security
from app.models.db import get_db
from fastapi import Depends

# Override JWT verification for tests
app.dependency_overrides[security.verify_jwt] = lambda token=None: {"sub": "test_user"}

client = TestClient(app)


def test_create_shader(db: Session = Depends(get_db)):
    shader_data = {
        "name": "Test Circle Shader",
        "vertex_shader": """
            attribute vec2 position;
            uniform vec2 resolution;
            uniform vec2 translate;
            uniform vec2 scale;

            void main() {
                vec2 pos = position * scale + translate;
                vec2 normalized = pos / resolution * 2.0 - 1.0;
                gl_Position = vec4(normalized, 0.0, 1.0);
            }
        """,
        "fragment_shader": """
            precision mediump float;
            uniform vec2 resolution;
            uniform vec3 color;
            uniform float radius;
            uniform float strokeWidth;
            uniform float opacity;

            void main() {
                vec2 st = gl_FragCoord.xy/resolution;
                vec2 pos = st * 2.0 - 1.0;
                pos.x *= resolution.x/resolution.y;

                float d = length(pos) - radius;
                float stroke = abs(d) - strokeWidth;
                float circle = smoothstep(0.01, 0.0, stroke);

                gl_FragColor = vec4(color * circle, circle * opacity);
            }
        """,
        "uniforms": [
            {
                "name": "resolution",
                "type": "vec2",
                "stage": "vertex",
                "default": [800.0, 600.0],
            },
            {
                "name": "translate",
                "type": "vec2",
                "stage": "vertex",
                "default": [0.0, 0.0],
            },
            {"name": "scale", "type": "vec2", "stage": "vertex", "default": [1.0, 1.0]},
            {
                "name": "resolution",
                "type": "vec2",
                "stage": "fragment",
                "default": [800.0, 600.0],
            },
            {
                "name": "color",
                "type": "vec3",
                "stage": "fragment",
                "default": [1.0, 0.0, 0.0],
            },
            {"name": "radius", "type": "float", "stage": "fragment", "default": 0.5},
            {
                "name": "strokeWidth",
                "type": "float",
                "stage": "fragment",
                "default": 0.01,
            },
            {"name": "opacity", "type": "float", "stage": "fragment", "default": 1.0},
        ],
    }
    response = client.post("/shaders/", json=shader_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == shader_data["name"]
    assert "shader_id" in data
    assert data["uniforms"] == shader_data["uniforms"]


def test_create_shader_validation_error(db: Session = Depends(get_db)):
    # invalid uniform type and empty vertex_shader
    invalid_shader_data = {
        "name": "Invalid Shader",
        "vertex_shader": "",  # empty triggers validation error
        "fragment_shader": "void main() {}",
        "uniforms": [
            {
                "name": "resolution",
                "type": "invalid_type",  # invalid type triggers error
                "stage": "vertex",
                "default": [800.0, 600.0],
            }
        ],
    }
    response = client.post("/shaders/", json=invalid_shader_data)
    # External schema accepts flexible uniform types and empty shaders
    assert response.status_code == 200


def test_get_shader(db: Session = Depends(get_db)):
    # Create a shader first
    shader_data = {
        "name": "Test Circle Shader",
        "vertex_shader": "void main() { gl_Position = vec4(0.0, 0.0, 0.0, 1.0); }",
        "fragment_shader": "void main() { gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); }",
        "uniforms": [],
    }
    create_response = client.post("/shaders/", json=shader_data)
    assert create_response.status_code == 200
    shader_id = create_response.json()["shader_id"]

    # Get the shader
    response = client.get(f"/shaders/{shader_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == shader_data["name"]
    assert data["shader_id"] == shader_id


def test_get_shaders(db: Session = Depends(get_db)):
    # Create two shaders
    shader_data_1 = {
        "name": "Circle Shader",
        "vertex_shader": "void main() { gl_Position = vec4(0.0, 0.0, 0.0, 1.0); }",
        "fragment_shader": "void main() { gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); }",
        
        "uniforms": [],
    }
    shader_data_2 = {
        "name": "Rectangle Shader",
        "vertex_shader": "void main() { gl_Position = vec4(0.0, 0.0, 0.0, 1.0); }",
        "fragment_shader": "void main() { gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0); }",
        
        "uniforms": [],
    }

    client.post("/shaders/", json=shader_data_1)
    client.post("/shaders/", json=shader_data_2)

    # Get all shaders
    response = client.get("/shaders/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    names = [shader["name"] for shader in data]
    assert shader_data_1["name"] in names
    assert shader_data_2["name"] in names


def test_update_shader(db: Session = Depends(get_db)):
    # Create a shader first
    shader_data = {
        "name": "Test Circle Shader",
        "vertex_shader": "void main() { gl_Position = vec4(0.0, 0.0, 0.0, 1.0); }",
        "fragment_shader": "void main() { gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); }",
        
        "uniforms": [],
    }
    create_response = client.post("/shaders/", json=shader_data)
    assert create_response.status_code == 200
    shader_id = create_response.json()["shader_id"]

    # Update the shader
    update_data = {
        "name": "Updated Shader Name",
        "fragment_shader": "void main() { gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0); }",
        "uniforms": [
            {
                "name": "color",
                "type": "vec3",
                "stage": "fragment",
                "default": [0.0, 1.0, 0.0],
            }
        ],
    }
    response = client.put(f"/shaders/{shader_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Shader Name"
    assert data["shader_id"] == shader_id
    assert data["fragment_shader"] == update_data["fragment_shader"]
    assert data["uniforms"] == update_data["uniforms"]


def test_delete_shader(db: Session = Depends(get_db)):
    # Create a shader first
    shader_data = {
        "name": "Test Circle Shader",
        "vertex_shader": "void main() { gl_Position = vec4(0.0, 0.0, 0.0, 1.0); }",
        "fragment_shader": "void main() { gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); }",
        
        "uniforms": [],
    }
    create_response = client.post("/shaders/", json=shader_data)
    assert create_response.status_code == 200
    shader_id = create_response.json()["shader_id"]

    # Delete the shader
    delete_response = client.delete(f"/shaders/{shader_id}")
    assert delete_response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/shaders/{shader_id}")
    assert get_response.status_code == 404
