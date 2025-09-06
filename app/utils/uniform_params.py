"""Utilities for mapping shader uniforms to input parameters."""

from __future__ import annotations

from typing import List

from synesthetic_schemas.shader import UniformDef, InputParameter

DEFAULT_MIN = -10.0
DEFAULT_MAX = 10.0
DEFAULT_STEP = 0.001
DEFAULT_SMOOTHING_TIME = 0.1


def uniforms_to_input_parameters(uniforms: List[UniformDef]) -> List[InputParameter]:
    """Convert uniforms into input parameters.

    Each resulting :class:`InputParameter` uses the uniform's name and type
    while applying standard defaults for range and smoothing.

    Args:
        uniforms: List of :class:`UniformDef` objects.

    Returns:
        A list of :class:`InputParameter` objects.
    """

    return [
        InputParameter(
            name=uniform.name,
            parameter=uniform.name,
            path=uniform.name,
            type=uniform.type,
            default=float(uniform.default),
            min=DEFAULT_MIN,
            max=DEFAULT_MAX,
            step=DEFAULT_STEP,
            smoothingTime=DEFAULT_SMOOTHING_TIME,
        )
        for uniform in uniforms
    ]


__all__ = ["uniforms_to_input_parameters"]
