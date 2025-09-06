from pydantic import Field, ConfigDict, model_validator
from typing import Optional, Dict, Any, List
from .base_schema import SchemaBase


class DeviceOptionValue(SchemaBase):
    value: float = Field(description="Value of the device option")
    unit: str = Field(description="Unit of measurement for the option")


class DeviceConfig(SchemaBase):
    type: str = Field(description="Type of haptic device")
    options: Dict[str, DeviceOptionValue] = Field(
        description="Device-specific configuration options"
    )


class HapticParameter(SchemaBase):
    name: str = Field(description="Name of the parameter")
    parameter: str = Field(description="The parameter")
    path: str = Field(description="Path to the parameter")
    type: str = Field(description="Data type of the parameter")
    unit: str = Field(description="Unit of measurement")
    default: Any = Field(description="Default value")
    min: Optional[float] = Field(default=None, description="Minimum allowed value")
    max: Optional[float] = Field(default=None, description="Maximum allowed value")
    step: Optional[float] = Field(default=None, description="Step increment value")
    smoothingTime: Optional[float] = Field(
        default=None, description="Smoothing time in seconds"
    )
    options: Optional[List[str]] = Field(
        default=None, description="Available options for enum types"
    )


class HapticBase(SchemaBase):
    name: str = Field(description="Name of the haptic configuration")
    description: Optional[str] = Field(
        default=None, description="Description of the haptic configuration"
    )
    meta_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata about the haptic configuration",
        examples=[
            {
                "category": "haptic",
                "tags": ["vibration", "feedback"],
                "complexity": "medium",
            }
        ],
    )
    device: DeviceConfig = Field(description="Device configuration")
    input_parameters: List[HapticParameter] = Field(
        description="List of input parameters"
    )

    @model_validator(mode="after")
    def normalize_complexity(cls, data: "HapticBase") -> "HapticBase":
        meta = data.meta_info
        if isinstance(meta, dict) and "complexity" in meta:
            value = meta["complexity"]
            if not isinstance(value, str):
                meta["complexity"] = str(value)
        return data


class HapticCreate(HapticBase):
    pass


class HapticUpdate(SchemaBase):
    name: Optional[str] = None
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    device: Optional[DeviceConfig] = None
    input_parameters: Optional[List[HapticParameter]] = None


class Haptic(HapticBase):
    haptic_id: int

    model_config = ConfigDict(from_attributes=True)
