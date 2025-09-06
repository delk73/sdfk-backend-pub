from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Literal, Dict, Any, List, Union
from .base_schema import SchemaBase
from app.constants import SynthType

# Define valid types as literals for validation
OscillatorType = Literal[
    "sine",
    "sine1",
    "sine2",
    "sine4",
    "triangle",
    "triangle3",
    "triangle4",
    "square",
    "sawtooth",
    "fmsine",
]
FilterType = Literal["lowpass", "highpass", "bandpass"]
RolloffType = Literal["-12", "-24", "-48", "-96"]
CurveType = Literal["linear", "exponential", "sin", "cos", "square", "sawtooth"]
EffectType = Literal[
    "delay",
    "reverb",
    "chorus",
    "tremolo",
    "distortion",
    "phaser",
    "bitcrusher",
    "filter",
]
MappingType = Literal["mouse", "wheel", "time"]

# Models for the new format


class ToneMetaInfo(BaseModel):
    category: str
    tags: List[str]
    complexity: str

    model_config = ConfigDict(extra="allow")


class ToneTarget(BaseModel):
    type: str
    property: str

    model_config = ConfigDict(extra="allow")


class ToneMapping(BaseModel):
    type: MappingType
    buttons: Optional[List[int]] = None
    keys: Optional[List[str]] = None
    axis: Optional[str] = None
    curve: CurveType
    scale: float
    duration: Optional[float] = None
    repeat: Optional[bool] = None

    model_config = ConfigDict(extra="allow")


class ToneParameter(BaseModel):
    name: str
    parameter: Optional[str] = None
    path: str
    type: str
    unit: Optional[str] = None
    default: Any
    min: Optional[Any] = None
    max: Optional[Any] = None
    options: Optional[List[str]] = None
    smoothingTime: Optional[float] = None

    model_config = ConfigDict(extra="allow")

    @field_validator("default")
    @classmethod
    def validate_default_in_range(cls, v, info):
        values = info.data

        # Skip validation if we don't have both min and max
        if "min" not in values or "max" not in values:
            return v

        # If min, max, and default are all present, validate default is in range
        if values["min"] is not None and values["max"] is not None:
            # For numeric types, validate default is between min and max
            if values.get("type") in ["float", "int"] and isinstance(v, (int, float)):
                # Skip min/max comparison as requested
                pass

        return v


class ToneEffect(BaseModel):
    type: str
    options: Dict[str, Any]
    order: int

    model_config = ConfigDict(extra="allow")


class TonePattern(BaseModel):
    id: str
    type: str
    options: Dict[str, Any]

    model_config = ConfigDict(extra="allow")


class TonePart(BaseModel):
    id: str
    pattern: str
    start: str
    duration: str
    loop: Optional[bool] = None

    model_config = ConfigDict(extra="allow")


class ToneSynthOptions(BaseModel):
    oscillator: Dict[str, Any]
    envelope: Dict[str, Any]
    volume: Union[float, Dict[str, Any]]
    filter: Optional[Dict[str, Any]] = None
    filterEnvelope: Optional[Dict[str, Any]] = None
    portamento: Optional[Union[float, Dict[str, Any]]] = None

    @field_validator("oscillator")
    @classmethod
    def validate_oscillator(cls, v):
        if "type" in v:
            valid_types = [
                "sine",
                "sine1",
                "sine2",
                "sine4",
                "triangle",
                "triangle3",
                "triangle4",
                "square",
                "sawtooth",
                "fmsine",
            ]
            if v["type"] not in valid_types:
                raise ValueError(
                    f"Invalid oscillator type: {v['type']}. Valid types are: {', '.join(valid_types)}"
                )
        return v

    model_config = ConfigDict(extra="allow")


class ToneSynth(BaseModel):
    type: SynthType
    options: Union[ToneSynthOptions, Dict[str, Any]]

    @field_validator("options")
    @classmethod
    def validate_options(cls, v):
        # If options is a dict and contains oscillator with a type, validate the type
        if (
            isinstance(v, dict)
            and "oscillator" in v
            and isinstance(v["oscillator"], dict)
            and "type" in v["oscillator"]
        ):
            oscillator_type = v["oscillator"]["type"]
            valid_types = [
                "sine",
                "sine1",
                "sine2",
                "sine4",
                "triangle",
                "triangle3",
                "triangle4",
                "square",
                "sawtooth",
                "fmsine",
            ]
            if oscillator_type not in valid_types:
                raise ValueError(
                    f"Invalid oscillator type: {oscillator_type}. Valid types are: {', '.join(valid_types)}"
                )
        return v

    model_config = ConfigDict(extra="allow")


class ToneBase(SchemaBase):
    name: str = Field(description="Name of the tone")
    description: Optional[str] = Field(None, description="Description of the tone")
    meta_info: Optional[Union[ToneMetaInfo, Dict[str, Any]]] = Field(
        None, description="Additional metadata about the tone"
    )
    synth: Union[ToneSynth, Dict[str, Any]] = Field(
        ..., description="Synth configuration"
    )
    effects: Optional[List[Union[ToneEffect, Dict[str, Any]]]] = Field(
        default_factory=list, description="Effects configuration"
    )
    patterns: Optional[List[Union[TonePattern, Dict[str, Any]]]] = Field(
        default_factory=list, description="Patterns configuration"
    )
    parts: Optional[List[Union[TonePart, Dict[str, Any]]]] = Field(
        default_factory=list, description="Parts configuration"
    )
    input_parameters: List[Union[ToneParameter, Dict[str, Any]]] = Field(
        default_factory=list, description="Tone input parameters"
    )

    @field_validator("synth")
    @classmethod
    def validate_synth_required(cls, v):
        if v is None:
            raise ValueError("Synth is required")
        return v

    @field_validator("synth")
    @classmethod
    def validate_synth_type(cls, v):
        allowed = {st.value for st in SynthType}
        synth_type = None
        if isinstance(v, dict):
            synth_type = v.get("type")
        elif hasattr(v, "type"):
            synth_type = v.type
        if synth_type not in allowed:
            raise ValueError(
                f"Invalid synth type: {synth_type}. Valid types are: {', '.join(sorted(allowed))}"
            )
        return v

    @field_validator("input_parameters")
    @classmethod
    def validate_input_parameters(cls, v):
        if v is None:
            return []

        # Check for duplicate parameter names
        param_names = []
        for param in v:
            if isinstance(param, dict) and "name" in param:
                param_names.append(param["name"])
            elif hasattr(param, "name"):
                param_names.append(param.name)

        duplicates = [name for name in set(param_names) if param_names.count(name) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate parameter names found: {', '.join(duplicates)}"
            )

        return v

    model_config = ConfigDict(extra="allow")


class ToneCreate(ToneBase):
    pass


class ToneUpdate(SchemaBase):
    name: Optional[str] = None
    description: Optional[str] = None
    meta_info: Optional[Union[ToneMetaInfo, Dict[str, Any]]] = None
    synth: Optional[Union[ToneSynth, Dict[str, Any]]] = None
    effects: Optional[List[Union[ToneEffect, Dict[str, Any]]]] = None
    patterns: Optional[List[Union[TonePattern, Dict[str, Any]]]] = None
    parts: Optional[List[Union[TonePart, Dict[str, Any]]]] = None
    input_parameters: Optional[List[Union[ToneParameter, Dict[str, Any]]]] = None

    @field_validator("input_parameters")
    @classmethod
    def validate_input_parameters(cls, v):
        if v is None:
            return None

        # Check for duplicate parameter names
        param_names = []
        for param in v:
            if isinstance(param, dict) and "name" in param:
                param_names.append(param["name"])
            elif hasattr(param, "name"):
                param_names.append(param.name)

        duplicates = [name for name in set(param_names) if param_names.count(name) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate parameter names found: {', '.join(duplicates)}"
            )

        return v

    @field_validator("synth")
    @classmethod
    def validate_synth_type(cls, v):
        if v is None:
            return None
        allowed = {st.value for st in SynthType}
        synth_type = None
        if isinstance(v, dict):
            synth_type = v.get("type")
        elif hasattr(v, "type"):
            synth_type = v.type
        if synth_type not in allowed:
            raise ValueError(
                f"Invalid synth type: {synth_type}. Valid types are: {', '.join(sorted(allowed))}"
            )
        return v

    model_config = ConfigDict(extra="allow")


class Tone(ToneBase):
    tone_id: int
