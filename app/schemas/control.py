from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from .base_schema import SchemaBase


class AxisType(str, Enum):
    MOUSE_X = "mouse.x"
    MOUSE_Y = "mouse.y"
    MOUSE_WHEEL = "mouse.wheel"


class CurveType(str, Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    SINE = "sine"
    DISCRETE = "discrete"


class DataType(str, Enum):
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    STRING = "string"


class ComboType(BaseModel):
    mouseButtons: Optional[List[str]] = None
    wheel: Optional[bool] = None
    keys: Optional[List[str]] = None
    strict: bool = False

    @model_validator(mode="after")
    def validate_combo(self) -> "ComboType":
        # At least one input method must be specified
        if not any([self.mouseButtons, self.wheel is not None]):
            raise ValueError(
                "At least one input method (mouseButtons, wheel) must be specified"
            )
        return self


class ActionType(BaseModel):
    axis: AxisType
    sensitivity: float
    scale: float = 1.0
    curve: CurveType = CurveType.LINEAR


class Mapping(BaseModel):
    combo: ComboType
    action: ActionType


class Control(BaseModel):
    parameter: str = Field(min_length=1)
    label: str = Field(min_length=1)
    type: DataType
    unit: str = Field(min_length=1)
    default: Union[float, int, bool, str]
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    smoothingTime: float = 0.0
    options: Optional[List[str]] = None
    mappings: List[Mapping]

    @model_validator(mode="after")
    def validate_control(self) -> "Control":
        # Validate numeric ranges if type is float or int
        if self.type in [DataType.FLOAT, DataType.INT]:
            if self.min is None or self.max is None:
                raise ValueError(
                    f"Parameter {self.parameter}: min and max are required for numeric types"
                )

            if self.min >= self.max:
                raise ValueError(
                    f"Parameter {self.parameter}: min must be less than max"
                )

            if not (self.min <= self.default <= self.max):
                raise ValueError(
                    f"Parameter {self.parameter}: default must be between min and max"
                )

        # Validate string options
        if self.type == DataType.STRING:
            if not self.options:
                raise ValueError(
                    f"Parameter {self.parameter}: options are required for string type"
                )

            if self.default not in self.options:
                raise ValueError(
                    f"Parameter {self.parameter}: default must be one of the options"
                )

        return self


class ControlBase(SchemaBase):
    name: str = Field(description="Name of the control", min_length=1)
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata about the control",
        examples=[
            {
                "category": "control",
                "tags": ["interactive", "transform"],
                "complexity": "medium",
            }
        ],
    )
    control_parameters: List[Control] = Field(
        description="List of control parameters with their mappings",
        examples=[
            {
                "parameter": "visual.u_wave_x",
                "label": "Wave X",
                "type": "float",
                "unit": "linear",
                "default": 0.0,
                "min": -1.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.1,
                "mappings": [
                    {
                        "combo": {"mouseButtons": ["left"], "strict": True},
                        "action": {
                            "axis": "mouse.x",
                            "sensitivity": 0.002,
                            "scale": 1.0,
                            "curve": "linear",
                        },
                    }
                ],
            }
        ],
    )

    @model_validator(mode="after")
    def validate_controls(self) -> "ControlBase":
        # Validate that we have at least one control
        if not self.control_parameters:
            raise ValueError("At least one control parameter is required")

        return self


class ControlCreate(ControlBase):
    pass


class ControlResponse(ControlBase):
    control_id: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "control_id": 1,
                "name": "Example Controls",
                "description": "Interactive controls for shape transformation",
                "meta_info": {
                    "category": "control",
                    "tags": ["interactive", "transform"],
                    "complexity": "medium",
                },
                "control_parameters": [
                    {
                        "parameter": "visual.u_wave_x",
                        "label": "Wave X",
                        "type": "float",
                        "unit": "linear",
                        "default": 0.0,
                        "min": -1.0,
                        "max": 1.0,
                        "step": 0.01,
                        "smoothingTime": 0.1,
                        "mappings": [
                            {
                                "combo": {"mouseButtons": ["left"], "strict": True},
                                "action": {
                                    "axis": "mouse.x",
                                    "sensitivity": 0.002,
                                    "scale": 1.0,
                                    "curve": "linear",
                                },
                            }
                        ],
                    }
                ],
            }
        }
    }
