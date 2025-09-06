import pytest
from app.validators.shader import validate_shader_block
from tests.fixtures.reserved_uniforms import reserved_uniforms


def test_validate_shader_block_passes():
    shader = {
        "name": "Test",
        "shader_lib_id": 1,
        "vertex_shader": "uniform float u_time; void main() { gl_Position = vec4(0.0); }",
        "fragment_shader": "uniform float u_time; void main() { float t = u_time; }",
        "uniforms": reserved_uniforms(),
        "input_parameters": [
            {
                "name": "time",
                "parameter": "u_time",
                "path": "u_time",
                "type": "float",
                "default": 0.0,
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
            }
        ],
    }
    # Should not raise any exception
    validate_shader_block(shader)


def test_validate_shader_block_unused_uniform():
    shader = {
        "name": "Test",
        "shader_lib_id": 1,
        "vertex_shader": "void main() { }",
        "fragment_shader": "void main() { }",
        "uniforms": reserved_uniforms(),
        "input_parameters": [],
    }
    # v0.4 does not require uniforms to be used - should not raise any exception
    validate_shader_block(shader)


def test_validate_shader_block_missing_uniform():
    shader = {
        "name": "Test",
        "shader_lib_id": 1,
        "vertex_shader": "void main() { }",
        "fragment_shader": "void main() { float t = u_missing; }",
        "uniforms": reserved_uniforms(),
        "input_parameters": [],
    }
    # Should not raise any exception - missing uniforms are allowed in v0.4
    validate_shader_block(shader)


def test_old_schema_rejected():
    old_shader = {
        "name": "Legacy",
        "shader_lib_id": 1,
        "shaders": {"vertex": "void main(){}", "fragment": "void main(){}"},
        "uniforms": [],
        "input_parameters": [],
    }
    with pytest.raises(ValueError):
        validate_shader_block(old_shader)
