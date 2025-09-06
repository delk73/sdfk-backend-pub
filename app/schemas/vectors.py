from pydantic import BaseModel
from typing import Union


class Vec2(BaseModel):
    x: float
    y: float


class Vec3(BaseModel):
    x: float
    y: float
    z: float


class Vec4(BaseModel):
    x: float
    y: float
    z: float
    w: float = 1.0


UniformValue = Union[float, int, bool, Vec2, Vec3, Vec4, str]


class UniformBase(BaseModel):
    name: str
    type: str
    stage: str
    default: float


class Uniform(UniformBase):
    pass
