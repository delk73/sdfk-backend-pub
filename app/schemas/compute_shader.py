from __future__ import annotations

from typing import List, Optional, Dict, Any

from pydantic import Field, field_validator

from .base_schema import SchemaBase
from .shader import UniformDef, InputParameter


class ComputeShaderBase(SchemaBase):
    """Base fields for compute shaders."""

    name: str = Field(description="Name of the compute shader")
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    compute_shader: str = Field(description="GLSL compute shader code")
    shader_lib_id: Optional[int] = None
    uniforms: Optional[List[UniformDef]] = None
    input_parameters: Optional[List[InputParameter]] = None

    @field_validator("compute_shader")
    @classmethod
    def validate_compute_shader(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("compute_shader cannot be empty")
        return v


class ComputeShaderCreate(ComputeShaderBase):
    """Schema for creating compute shaders."""


class ComputeShaderUpdate(SchemaBase):
    name: Optional[str] = None
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    compute_shader: Optional[str] = None
    shader_lib_id: Optional[int] = None
    uniforms: Optional[List[UniformDef]] = None
    input_parameters: Optional[List[InputParameter]] = None


class ComputeShader(ComputeShaderBase):
    shader_id: int
