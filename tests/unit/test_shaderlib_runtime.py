import pytest
from fastapi import HTTPException

from app.shaderlib import (
    ShaderLib,
    collect_effective_inputs,
    check_template_demonstrates_helper,
)
from tests.fixtures.factories import example_shader_lib_def


def test_merge_happy():
    lib = ShaderLib.model_validate(example_shader_lib_def())
    merged = collect_effective_inputs(lib, "sdHexagon")
    assert merged["uniforms"][-1] == "u_r"
    assert merged["inputParametersSpec"][-1]["parameter"] == "u_r"


def test_merge_collision():
    lib = ShaderLib.model_validate(example_shader_lib_def())
    lib.helpers["sdHexagon"].requires.inputParametersSpec[0].parameter = "u_px"
    with pytest.raises(HTTPException) as exc:
        collect_effective_inputs(lib, "sdHexagon")
    assert exc.value.status_code == 422
    assert exc.value.detail[0]["code"] == "COLLISION_BASE_PARAMETER"


def test_template_warning():
    lib_def = example_shader_lib_def()
    lib_def["helpers"]["sdHexagon"]["requires"]["uniforms"].append("u_extra")
    lib = ShaderLib.model_validate(lib_def)
    info = check_template_demonstrates_helper(lib, "sdHexagon")
    assert info["warnings"]
