from pydantic import Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import Field, field_validator, model_validator
from .base_schema import SchemaBase
from app.shaderlib import ShaderLib as ShaderLibSchema


class UniformDef(SchemaBase):
    name: str
    type: str
    stage: str
    default: Any

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed_types = {"vec2", "vec3", "vec4", "float", "int", "bool"}
        if v not in allowed_types:
            raise ValueError(f"Invalid uniform type: {v}")
        return v

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v):
        allowed_stages = {"vertex", "fragment"}
        if v not in allowed_stages:
            raise ValueError(f"Invalid stage: {v}")
        return v


class InputParameter(SchemaBase):
    name: str
    parameter: str
    path: str
    type: str
    default: float
    min: float
    max: float
    step: Optional[float] = None
    smoothingTime: Optional[float] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed_types = {"float", "int", "bool", "vec2", "vec3", "vec4"}
        if v not in allowed_types:
            raise ValueError(f"Invalid parameter type: {v}")
        return v

    @model_validator(mode="after")
    def validate_range(self) -> "InputParameter":
        if self.min >= self.max:
            raise ValueError(f"Parameter {self.name}: min must be less than max")
        if not (self.min <= self.default <= self.max):
            raise ValueError(
                f"Parameter {self.name}: default must be between min and max"
            )
        return self


class ShaderBase(SchemaBase):
    name: str = Field(description="Name of the shader", examples=["Circle Shader"])
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata about the shader",
        examples=[
            {"category": "visual", "tags": ["circle", "sdf"], "complexity": "low"}
        ],
    )
    vertex_shader: str = Field(
        description="GLSL vertex shader code", examples=["// vertex shader example"]
    )
    fragment_shader: str = Field(
        description="GLSL fragment shader code", examples=["// fragment shader example"]
    )
    shader_lib_id: Optional[int] = None
    uniforms: Optional[List[UniformDef]] = None
    input_parameters: Optional[List[InputParameter]] = None

    @field_validator("vertex_shader")
    @classmethod
    def validate_vertex_shader(cls, v):
        if not v.strip():
            raise ValueError("vertex_shader cannot be empty")
        return v

    @field_validator("fragment_shader")
    @classmethod
    def validate_fragment_shader(cls, v):
        if not v.strip():
            raise ValueError("fragment_shader cannot be empty")
        return v


class ShaderCreate(ShaderBase):
    pass


class ShaderUpdate(SchemaBase):
    name: Optional[str] = None
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    vertex_shader: Optional[str] = None
    fragment_shader: Optional[str] = None
    shader_lib_id: Optional[int] = None
    uniforms: Optional[List[UniformDef]] = None
    input_parameters: Optional[List[InputParameter]] = None


class Shader(ShaderBase):
    shader_id: int


class ShaderLibCreate(ShaderLibSchema):
    model_config = SchemaBase.model_config

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        return {"name": data["name"], "definition": data}


class ShaderLib(ShaderLibSchema):
    shaderlib_id: int
    created_at: datetime
    updated_at: datetime
    model_config = SchemaBase.model_config
