import pytest
import json
from pydantic import ValidationError

from app.shaderlib import ShaderLib, InputParam
from tests.fixtures.factories import example_shader_lib_def


def test_float_step_too_large():
    lib = example_shader_lib_def()
    lib["baseInputParametersSpec"][0]["step"] = 0.02
    with pytest.raises(ValidationError) as exc:
        ShaderLib.model_validate(lib)
    assert any("step" in e["msg"] for e in exc.value.errors())


def test_int_step_invalid():
    ip = {
        "name": "count",
        "parameter": "u_i",
        "path": "u_i",
        "type": "int",
        "default": 1,
        "min": 0,
        "max": 10,
        "smoothingTime": 0.1,
    }
    with pytest.raises(ValidationError):
        InputParam.model_validate(ip)


def test_missing_smoothing_time():
    ip = {
        "name": "count",
        "parameter": "u_i",
        "path": "u_i",
        "type": "int",
        "default": 1,
        "min": 0,
        "max": 10,
        "step": 1,
    }
    with pytest.raises(ValidationError):
        InputParam.model_validate(ip)


def test_bool_with_step():
    ip = {
        "name": "flag",
        "parameter": "u_flag",
        "path": "u_flag",
        "type": "bool",
        "default": True,
        "step": 1,
    }
    with pytest.raises(ValidationError):
        InputParam.model_validate(ip)


def test_duplicate_reserved_uniform():
    lib = example_shader_lib_def()
    lib["reservedUniforms"].append("u_time")
    with pytest.raises(ValidationError):
        ShaderLib.model_validate(lib)


def test_helper_uniform_duplicates_reserved():
    lib = example_shader_lib_def()
    lib["helpers"]["sdHexagon"]["requires"]["uniforms"].append("u_time")
    with pytest.raises(ValidationError) as exc:
        ShaderLib.model_validate(lib)
    errs = exc.value.errors()
    assert any(e["type"] == "COLLISION_RESERVED_UNIFORM" for e in errs)


def test_helper_parameter_collision():
    lib = example_shader_lib_def()
    lib["helpers"]["sdHexagon"]["requires"]["inputParametersSpec"][0][
        "parameter"
    ] = "u_px"
    with pytest.raises(ValidationError) as exc:
        ShaderLib.model_validate(lib)
    errs = exc.value.errors()
    assert any(e["type"] == "COLLISION_BASE_PARAMETER" for e in errs)


def test_numeric_bounds_codes():
    bad_step = {
        "name": "bad",
        "parameter": "u_bad",
        "path": "u_bad",
        "type": "float",
        "default": 0.0,
        "min": 0.0,
        "max": 1.0,
        "step": 0,
        "smoothingTime": 0.1,
    }
    with pytest.raises(ValidationError) as exc:
        InputParam.model_validate(bad_step)
    assert exc.value.errors()[0]["type"] == "INVALID_STEP"

    bad_range = dict(bad_step)
    bad_range["step"] = 0.01
    bad_range["min"] = 1.0
    bad_range["max"] = 0.0
    with pytest.raises(ValidationError) as exc2:
        InputParam.model_validate(bad_range)
    assert exc2.value.errors()[0]["type"] == "INVALID_RANGE"


def test_example_lib_loads():
    path = "app/examples/ShaderLib_Example.json"
    data = json.loads(open(path).read())
    ShaderLib.model_validate(data)
