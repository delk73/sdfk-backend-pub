"""Validation helpers for shader descriptors."""

from __future__ import annotations

import re
from typing import Any, Dict, cast


REQUIRED_TOP_LEVEL = {
    "name",
    "shader_lib_id",
    "vertex_shader",
    "fragment_shader",
    "uniforms",
    "input_parameters",
}

REQUIRED_STAGES = {"vertex", "fragment"}

ALLOWED_TYPES = {
    "float",
    "int",
    "bool",
    "vec2",
    "vec3",
    "vec4",
    "mat2",
    "mat3",
    "mat4",
    "sampler2D",
}

PRECISIONS = {"lowp", "mediump", "highp"}

from .reserved_uniforms import RESERVED_UNIFORMS


def _extract_uniforms(code: str) -> set[str]:
    return set(re.findall(r"u_[A-Za-z0-9_]+", code or ""))


def _base_length(u_type: str) -> int:
    if u_type in {"float", "int", "bool", "sampler2D"}:
        return 1
    if u_type == "vec2":
        return 2
    if u_type == "vec3":
        return 3
    if u_type == "vec4":
        return 4
    if u_type == "mat2":
        return 4
    if u_type == "mat3":
        return 9
    if u_type == "mat4":
        return 16
    raise ValueError(f"Invalid uniform type: {u_type}")


def validate_shader_block(shader: Dict[str, Any]) -> None:
    """Validate ``shader`` against the v0.4 DSL specification."""

    keys = set(shader.keys())
    missing = REQUIRED_TOP_LEVEL - keys
    extra = keys - REQUIRED_TOP_LEVEL
    if missing:
        raise ValueError(f"Missing top-level keys: {sorted(missing)}")
    if extra:
        raise ValueError(f"Unexpected top-level keys: {sorted(extra)}")

    stage_codes = {
        "vertex": shader.get("vertex_shader"),
        "fragment": shader.get("fragment_shader"),
    }
    for stage, code in stage_codes.items():
        if not isinstance(code, str):
            raise ValueError(f"{stage}_shader must be a string")
        if "void main" not in code:
            raise ValueError(f"{stage}_shader missing 'void main'")
    stage_keys = set(stage_codes)

    uniforms = shader.get("uniforms") or []
    if not isinstance(uniforms, list):
        raise ValueError("uniforms must be a list")
    names: set[str] = set()
    for u in uniforms:
        name = u.get("name")
        if not name or not isinstance(name, str):
            raise ValueError("Uniform missing name")
        if name in names:
            raise ValueError(f"Duplicate uniform name: {name}")
        names.add(name)

        utype = u.get("type")
        if not isinstance(utype, str):
            raise ValueError(f"Uniform {name} missing type")
        is_array = utype.endswith("[]")
        base_type = utype[:-2] if is_array else utype
        if base_type not in ALLOWED_TYPES:
            raise ValueError(f"Uniform {name} has invalid type {utype}")

        size = u.get("size")
        if is_array:
            if not isinstance(size, int) or size <= 0:
                raise ValueError(f"Uniform {name} array size must be > 0")
            size = cast(int, size)
        elif size is not None:
            raise ValueError(f"Uniform {name} has size field but is not an array")

        stage = u.get("stage")
        if stage not in stage_keys:
            raise ValueError(f"Uniform {name} references undefined stage '{stage}'")

        precision = u.get("precision")
        if precision is not None and precision not in PRECISIONS:
            raise ValueError(
                f"Uniform {name} precision must be one of {sorted(PRECISIONS)}"
            )

        default = u.get("default")
        expected_length = _base_length(base_type)
        if is_array:
            expected_length *= size
        if isinstance(default, list):
            if len(default) != expected_length:
                raise ValueError(
                    f"Uniform {name} default length {len(default)} != {expected_length}"
                )
        else:
            if expected_length != 1:
                raise ValueError(
                    f"Uniform {name} default must have {expected_length} values"
                )

        # Reserved uniform rules

        if name in RESERVED_UNIFORMS:
            spec = RESERVED_UNIFORMS[name]
            if base_type != spec["type"] or stage != spec["stage"]:
                raise ValueError(
                    f"Reserved uniform {name} must be type {spec['type']} and stage {spec['stage']}"
                )

    missing_reserved = set(RESERVED_UNIFORMS) - names
    if missing_reserved:
        raise ValueError(f"Missing reserved uniforms: {sorted(missing_reserved)}")

    params = shader.get("input_parameters") or []
    if not isinstance(params, list):
        raise ValueError("input_parameters must be a list")
    uniform_types = {
        u["name"]: u["type"] for u in uniforms if "name" in u and "type" in u
    }
    for p in params:
        parameter = p.get("parameter")
        if parameter not in uniform_types:
            raise ValueError(
                f"Input parameter {p.get('name')} references unknown uniform {parameter}"
            )
        base_type = uniform_types[parameter]
        base_type = base_type[:-2] if base_type.endswith("[]") else base_type
        if base_type not in {"float", "int", "bool"}:
            raise ValueError(
                f"Input parameter {p.get('name')} can only target scalar uniforms"
            )
        p_min = p.get("min")
        p_max = p.get("max")
        default = p.get("default")
        if p_min is None or p_max is None or default is None:
            raise ValueError(
                f"Input parameter {p.get('name')} must specify min, max and default"
            )
        if p_min > p_max:
            raise ValueError(f"Input parameter {p.get('name')}: min must be <= max")
        if not (p_min <= default <= p_max):
            raise ValueError(
                f"Input parameter {p.get('name')}: default must be between min and max"
            )
        step = p.get("step")
        if step is not None and step <= 0:
            raise ValueError(f"Input parameter {p.get('name')}: step must be > 0")
        smoothing_time = p.get("smoothingTime")
        if smoothing_time is not None and smoothing_time < 0:
            raise ValueError(
                f"Input parameter {p.get('name')}: smoothingTime must be >= 0"
            )

    # Ensure controllable uniforms (float/int) appear exactly once in parameters
    controllable_uniforms = [
        u["name"]
        for u in uniforms
        if u.get("name") not in RESERVED_UNIFORMS
        and (u.get("type", "").removesuffix("[]") in {"float", "int"})
    ]
    param_counts: Dict[str, int] = {}
    for p in params:
        param = p.get("parameter")
        if isinstance(param, str):
            param_counts[param] = param_counts.get(param, 0) + 1

    for uniform_name in controllable_uniforms:
        count = param_counts.get(uniform_name, 0)
        if count == 0:
            raise ValueError(
                f"Controllable uniform {uniform_name} missing from input_parameters"
            )
        if count > 1:
            raise ValueError(
                f"Controllable uniform {uniform_name} duplicated in input_parameters"
            )


def validate_compute_shader_block(shader: Dict[str, Any]) -> None:
    """Validate a compute shader block for uniform usage."""

    uniforms = shader.get("uniforms") or []
    params = shader.get("input_parameters") or []
    compute_code = shader.get("compute_shader", "")

    declared = {u.get("name") for u in uniforms if "name" in u}
    used = _extract_uniforms(compute_code)
    builtin = {"u_time", "u_resolution"}

    param_refs = {p.get("parameter") for p in params if "parameter" in p}
    missing = param_refs - declared
    if missing:
        raise ValueError(f"Input parameters reference undeclared uniforms: {missing}")

    unused = declared - used
    if unused:
        raise ValueError(f"Declared uniforms not used: {unused}")

    undeclared = used - declared - builtin
    if undeclared:
        raise ValueError(f"Shader uses undeclared uniforms: {undeclared}")
