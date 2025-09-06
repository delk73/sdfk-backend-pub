from pydantic import Field, ConfigDict
from typing import Optional, Dict, Any, List, Literal
from .base_schema import SchemaBase


class ModulationItem(SchemaBase):
    id: str = Field(description="Unique identifier for the modulation")
    target: str = Field(
        description="Target parameter path (e.g., 'visual.u_wave_speed', 'tone.filter.frequency')"
    )
    type: Literal["additive", "multiplicative"] = Field(
        description="Type of modulation"
    )
    waveform: Literal["sine", "triangle", "square", "sawtooth"] = Field(
        description="Waveform type"
    )
    frequency: float = Field(description="Frequency of the modulation in Hz")
    amplitude: float = Field(description="Amplitude of the modulation")
    offset: float = Field(description="Offset/base value of the modulation")
    phase: float = Field(description="Phase offset in radians")
    min: Optional[float] = Field(
        default=None, description="Minimum allowable value for the modulation"
    )
    max: Optional[float] = Field(
        default=None, description="Maximum allowable value for the modulation"
    )
    scale: float = Field(
        default=1.0, description="Scaling factor applied to the modulation output"
    )
    scaleProfile: Literal["linear", "exponential", "logarithmic", "sine", "cosine"] = (
        Field(
            default="linear",
            description="Response profile to shape the modulation output",
        )
    )


class ModulationBase(SchemaBase):
    name: str = Field(description="Name of the modulation set")
    description: Optional[str] = Field(
        default=None, description="Description of the modulation set"
    )
    meta_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata about the modulation set",
        examples=[
            {
                "category": "modulation",
                "tags": ["multimodal", "dynamic"],
                "complexity": "medium",
            }
        ],
    )
    modulations: List[ModulationItem] = Field(
        description="List of modulations",
        examples=[
            {
                "id": "wave_speed_pulse",
                "target": "visual.u_wave_speed",
                "type": "additive",
                "waveform": "triangle",
                "frequency": 0.5,
                "amplitude": 0.5,
                "offset": 1.0,
                "phase": 0.0,
                "scale": 1.0,
                "scaleProfile": "linear",
                "min": 0.0,
                "max": 1.0,
            },
            {
                "id": "filter_sweep",
                "target": "tone.filter.frequency",
                "type": "additive",
                "waveform": "triangle",
                "frequency": 0.25,
                "amplitude": 400,
                "offset": 800,
                "phase": 0.0,
                "scale": 1.0,
                "scaleProfile": "exponential",
                "min": 0.0,
                "max": 1.0,
            },
            {
                "id": "haptic_pulse",
                "target": "haptic.intensity",
                "type": "additive",
                "waveform": "sine",
                "frequency": 1.0,
                "amplitude": 0.2,
                "offset": 0.6,
                "phase": 0.0,
                "scale": 1.0,
                "scaleProfile": "linear",
                "min": 0.0,
                "max": 1.0,
            },
        ],
    )


class ModulationCreate(ModulationBase):
    pass


class ModulationUpdate(SchemaBase):
    name: Optional[str] = None
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    modulations: Optional[List[ModulationItem]] = None


class Modulation(ModulationBase):
    modulation_id: int

    model_config = ConfigDict(from_attributes=True)
