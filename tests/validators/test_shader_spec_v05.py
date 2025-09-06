import pytest
from app.validators.shader import validate_shader_block
from tests.fixtures.reserved_uniforms import reserved_uniforms


def make_base_shader():
    return {
        "name": "ValidShader",
        "shader_lib_id": 1,
        "vertex_shader": "void main() {}",
        "fragment_shader": "void main() {}",
        "uniforms": reserved_uniforms()
        + [
            {"name": "u_r", "type": "float", "stage": "fragment", "default": 0.5},
        ],
        "input_parameters": [
            {
                "name": "radius",
                "parameter": "u_r",
                "path": "u_r",
                "type": "float",
                "default": 0.5,
                "min": 0.1,
                "max": 1.0,
                "step": 0.01,
            }
        ],
    }


def test_valid_shader_passes():
    shader = make_base_shader()
    validate_shader_block(shader)


def test_extra_top_level_key_fails():
    shader = make_base_shader()
    shader["extra"] = True
    with pytest.raises(ValueError, match="Unexpected top-level keys"):
        validate_shader_block(shader)


def test_missing_main_in_fragment_fails():
    shader = make_base_shader()
    shader["fragment_shader"] = "// no main"
    with pytest.raises(ValueError, match="fragment_shader missing 'void main'"):
        validate_shader_block(shader)


def test_uniform_array_missing_size_fails():
    shader = make_base_shader()
    shader["uniforms"].append(
        {"name": "u_vals", "type": "float[]", "stage": "fragment", "default": [0, 0]}
    )
    with pytest.raises(ValueError, match="array size"):
        validate_shader_block(shader)


def test_reserved_uniform_wrong_stage_fails():
    shader = make_base_shader()
    shader["uniforms"][0]["stage"] = "vertex"
    with pytest.raises(ValueError, match="Reserved uniform u_time"):
        validate_shader_block(shader)


def test_input_parameter_invalid_step_fails():
    shader = make_base_shader()
    shader["input_parameters"][0]["step"] = 0
    with pytest.raises(ValueError, match="step must be > 0"):
        validate_shader_block(shader)


def test_input_parameter_unknown_uniform_fails():
    shader = make_base_shader()
    shader["input_parameters"][0]["parameter"] = "u_missing"
    with pytest.raises(ValueError, match="unknown uniform"):
        validate_shader_block(shader)


@pytest.mark.parametrize(
    "missing",
    [
        "u_time",
        "u_resolution",
        "u_backgroundColor",
        "u_gridSize",
        "u_gridColor",
    ],
)
def test_missing_reserved_uniform_fails(missing):
    shader = make_base_shader()
    shader["uniforms"] = [u for u in shader["uniforms"] if u["name"] != missing]
    with pytest.raises(ValueError, match="Missing reserved uniforms"):
        validate_shader_block(shader)


def test_controllable_uniform_missing_parameter_fails():
    shader = make_base_shader()
    shader["uniforms"].append(
        {"name": "u_extra", "type": "float", "stage": "fragment", "default": 0.0}
    )
    with pytest.raises(ValueError, match="missing from input_parameters"):
        validate_shader_block(shader)


def test_controllable_uniform_duplicate_parameter_fails():
    shader = make_base_shader()
    shader["input_parameters"].append(shader["input_parameters"][0].copy())
    with pytest.raises(ValueError, match="duplicated in input_parameters"):
        validate_shader_block(shader)
