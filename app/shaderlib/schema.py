from __future__ import annotations

"""Pydantic models for ShaderLib v1."""

from typing import Dict, List, Optional, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator, ConfigDict
from pydantic_core import InitErrorDetails, PydanticCustomError


DefReserved = [
    "u_time",
    "u_resolution",
    "u_backgroundColor",
    "u_gridSize",
    "u_gridColor",
    "u_px",
    "u_py",
]


def verror(path: List[object], msg: str, code: str | None = None) -> dict:
    """Return FastAPI style error detail item with optional code."""
    item = {"loc": ["body", *path], "msg": msg, "type": "value_error"}
    if code:
        item["code"] = code
    return item


class InputParam(BaseModel):
    name: str
    parameter: str
    path: str
    type: Literal["float", "int", "bool"]
    default: float | int | bool
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    smoothingTime: Optional[float] = None

    @model_validator(mode="after")
    def _validate_numeric(self) -> "InputParam":
        t = self.type
        if t == "float":
            if self.step is None or self.step <= 0 or self.step > 0.01:
                raise PydanticCustomError(
                    "INVALID_STEP", "for float, step must be >0 and ≤ 0.01"
                )
            if self.smoothingTime is None or self.smoothingTime <= 0:
                raise PydanticCustomError(
                    "INVALID_SMOOTHING", "for float, smoothingTime > 0 required"
                )
        elif t == "int":
            if (
                self.step is None
                or not float(self.step).is_integer()
                or self.step <= 0
            ):
                raise PydanticCustomError(
                    "INVALID_STEP", "for int, step must be integer ≥ 1"
                )
            for attr in ("default", "min", "max"):
                v = getattr(self, attr)
                if v is None or not float(v).is_integer():
                    raise PydanticCustomError(
                        "INVALID_INT", f"{attr} must be integer"
                    )
            if self.smoothingTime is None or self.smoothingTime <= 0:
                raise PydanticCustomError(
                    "INVALID_SMOOTHING", "for int, smoothingTime > 0 required"
                )
        else:  # bool
            if self.step is not None:
                raise PydanticCustomError(
                    "INVALID_BOOL_FIELD", "for bool, step not allowed"
                )
            if self.smoothingTime is not None:
                raise PydanticCustomError(
                    "INVALID_BOOL_FIELD", "for bool, smoothingTime not allowed"
                )
            if self.min is not None or self.max is not None:
                raise PydanticCustomError(
                    "INVALID_BOOL_FIELD", "for bool, min/max not allowed"
                )
        if t in ("float", "int") and self.min is not None and self.max is not None:
            if self.min > self.max:
                raise PydanticCustomError(
                    "INVALID_RANGE", "min must be ≤ max"
                )
        return self


class HelperRequires(BaseModel):
    uniforms: Optional[List[str]] = None
    inputParametersSpec: Optional[List[InputParam]] = None


class Helper(BaseModel):
    glsl: str
    stage: Literal["fragment", "vertex", "any"] = "any"
    requires: Optional[HelperRequires] = None


class Templates(BaseModel):
    fragment_shader: Optional[str] = None
    input_parameters: Optional[List[InputParam]] = None


class ShaderLib(BaseModel):
    name: str
    version: Optional[str] = None
    reservedUniforms: List[str] = Field(default_factory=lambda: DefReserved.copy())
    baseInputParametersSpec: List[InputParam]
    helpers: Dict[str, Helper]
    templates: Optional[Templates] = None

    @model_validator(mode="after")
    def _check_collisions(self) -> "ShaderLib":
        errors: List[InitErrorDetails] = []

        # reserved uniforms uniqueness
        seen_ru: set[str] = set()
        for i, u in enumerate(self.reservedUniforms):
            if u in seen_ru:
                errors.append(
                    InitErrorDetails(
                        loc=("reservedUniforms", i),
                        input=u,
                        ctx={},
                        type=PydanticCustomError(
                            "COLLISION_RESERVED_UNIFORM",
                            f"duplicate reserved uniform '{u}'",
                        ),
                    )
                )
            seen_ru.add(u)

        # base input params uniqueness and required controls
        seen_params: set[str] = set()
        for i, p in enumerate(self.baseInputParametersSpec):
            if p.parameter in seen_params:
                errors.append(
                    InitErrorDetails(
                        loc=("baseInputParametersSpec", i, "parameter"),
                        input=p.parameter,
                        ctx={},
                        type=PydanticCustomError(
                            "COLLISION_BASE_PARAMETER",
                            f"duplicate parameter '{p.parameter}'",
                        ),
                    )
                )
            seen_params.add(p.parameter)
        for required in ("u_px", "u_py"):
            if required not in seen_params:
                errors.append(
                    InitErrorDetails(
                        loc=("baseInputParametersSpec",),
                        input=None,
                        ctx={},
                        type=PydanticCustomError(
                            "MISSING_BASE_PARAMETER",
                            f"missing control for '{required}'",
                        ),
                    )
                )

        reserved_set = set(self.reservedUniforms)
        for hname, helper in self.helpers.items():
            req = helper.requires
            if req and req.uniforms:
                seen_u: set[str] = set()
                for i, u in enumerate(req.uniforms):
                    if u in reserved_set:
                        errors.append(
                            InitErrorDetails(
                                loc=("helpers", hname, "requires", "uniforms", i),
                                input=u,
                                ctx={},
                                type=PydanticCustomError(
                                    "COLLISION_RESERVED_UNIFORM",
                                    f"duplicates reserved uniform '{u}'",
                                ),
                            )
                        )
                    if u in seen_u:
                        errors.append(
                            InitErrorDetails(
                                loc=("helpers", hname, "requires", "uniforms", i),
                                input=u,
                                ctx={},
                                type=PydanticCustomError(
                                    "COLLISION_HELPER_UNIFORM",
                                    f"duplicate uniform '{u}'",
                                ),
                            )
                        )
                    seen_u.add(u)
            if req and req.inputParametersSpec:
                seen_hp: set[str] = set()
                for j, ip in enumerate(req.inputParametersSpec):
                    param = ip.parameter
                    if param in reserved_set:
                        errors.append(
                            InitErrorDetails(
                                loc=(
                                    "helpers",
                                    hname,
                                    "requires",
                                    "inputParametersSpec",
                                    j,
                                    "parameter",
                                ),
                                input=param,
                                ctx={},
                                type=PydanticCustomError(
                                    "COLLISION_RESERVED_UNIFORM",
                                    f"duplicates reserved uniform '{param}'",
                                ),
                            )
                        )
                    if param in seen_params:
                        errors.append(
                            InitErrorDetails(
                                loc=(
                                    "helpers",
                                    hname,
                                    "requires",
                                    "inputParametersSpec",
                                    j,
                                    "parameter",
                                ),
                                input=param,
                                ctx={},
                                type=PydanticCustomError(
                                    "COLLISION_BASE_PARAMETER",
                                    f"duplicates base parameter '{param}'",
                                ),
                            )
                        )
                    if param in seen_hp:
                        errors.append(
                            InitErrorDetails(
                                loc=(
                                    "helpers",
                                    hname,
                                    "requires",
                                    "inputParametersSpec",
                                    j,
                                    "parameter",
                                ),
                                input=param,
                                ctx={},
                                type=PydanticCustomError(
                                    "COLLISION_HELPER_PARAMETER",
                                    f"duplicate parameter '{param}'",
                                ),
                            )
                        )
                    seen_hp.add(param)
        if errors:
            raise ValidationError.from_exception_data(self.__class__.__name__, errors)
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "ExampleLib",
                    "version": "1",
                    "reservedUniforms": DefReserved,
                    "baseInputParametersSpec": [
                        {
                            "name": "positionX",
                            "parameter": "u_px",
                            "path": "u_px",
                            "type": "float",
                            "default": 0.0,
                            "min": -1.0,
                            "max": 1.0,
                            "step": 0.01,
                            "smoothingTime": 0.05,
                        },
                        {
                            "name": "positionY",
                            "parameter": "u_py",
                            "path": "u_py",
                            "type": "float",
                            "default": 0.0,
                            "min": -1.0,
                            "max": 1.0,
                            "step": 0.01,
                            "smoothingTime": 0.05,
                        },
                    ],
                    "helpers": {
                        "sdHexagon": {
                            "glsl": "float sdHexagon(vec2 p){return 0.;}",
                            "stage": "fragment",
                            "requires": {
                                "uniforms": ["u_r"],
                                "inputParametersSpec": [
                                    {
                                        "name": "radius",
                                        "parameter": "u_r",
                                        "path": "u_r",
                                        "type": "float",
                                        "default": 0.5,
                                        "min": 0.1,
                                        "max": 2.0,
                                        "step": 0.01,
                                        "smoothingTime": 0.05,
                                    }
                                ],
                            },
                        }
                    },
                }
            ]
        }
    )
