"""Tests for ``uniforms_to_input_parameters`` utility."""

from synesthetic_schemas.shader import UniformDef, InputParameter
from app.utils.uniform_params import uniforms_to_input_parameters


def test_uniforms_to_input_parameters_basic():
    uniforms = [
        UniformDef(name="u_radius", type="float", stage="fragment", default=0.5),
        UniformDef(name="u_count", type="int", stage="vertex", default=2),
    ]

    params = uniforms_to_input_parameters(uniforms)

    assert len(params) == 2
    first = params[0]
    assert isinstance(first, InputParameter)
    assert first.name == "u_radius"
    assert first.parameter == "u_radius"
    assert first.path == "u_radius"
    assert first.type == "float"
    assert first.default == 0.5
    assert first.min == -10
    assert first.max == 10
    assert first.step == 0.001
    assert first.smoothingTime == 0.1


def test_uniforms_to_input_parameters_empty():
    assert uniforms_to_input_parameters([]) == []
