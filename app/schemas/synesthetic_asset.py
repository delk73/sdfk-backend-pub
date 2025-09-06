from pydantic import Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base_schema import SchemaBase
from synesthetic_schemas.shader import Shader as ShaderCreate
from synesthetic_schemas.control_bundle import ControlBundle as ControlCreate
from synesthetic_schemas.tone import Tone as ToneCreate
from synesthetic_schemas.haptic import Haptic as HapticCreate
from synesthetic_schemas.modulation import Modulation
from synesthetic_schemas.rule_bundle import RuleBundle as RuleBundleSchema


class SynestheticAssetBase(SchemaBase):
    name: str = Field(
        min_length=1,
        description="Name of the synesthetic asset",
        examples=["Circle Pulsar"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the asset's purpose",
        examples=[
            "A circle that pulses and changes color and sound frequency based on user controls"
        ],
    )
    meta_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata about the asset",
        examples=[
            {
                "category": "visual",
                "tags": ["geometric", "reactive", "audio"],
                "complexity": "medium",
            }
        ],
    )
    shader_id: Optional[int] = None
    control_id: Optional[int] = None
    tone_id: Optional[int] = None
    haptic_id: Optional[int] = None
    rule_bundle_id: Optional[int] = None
    modulation_id: Optional[int] = None
    modulations: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Array of modulations for this asset",
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
            }
        ],
    )


class SynestheticAssetCreate(SynestheticAssetBase):
    pass


class SynestheticAssetUpdate(SchemaBase):
    name: Optional[str] = None
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    shader_id: Optional[int] = None
    control_id: Optional[int] = None
    tone_id: Optional[int] = None
    haptic_id: Optional[int] = None
    modulation_id: Optional[int] = None
    modulations: Optional[List[Dict[str, Any]]] = None


class SynestheticAsset(SynestheticAssetBase):
    synesthetic_asset_id: int
    created_at: datetime
    updated_at: datetime
    shader: Optional["NestedShaderResponse"] = None
    control: Optional["NestedControlResponse"] = None
    tone: Optional["NestedToneResponse"] = None
    haptic: Optional["NestedHapticResponse"] = None
    modulation: Optional[Modulation] = None
    control_parameters: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(from_attributes=True)


class NestedSynestheticAssetCreate(SchemaBase):
    name: str = Field(
        description="Name of the synesthetic asset", examples=["Circle Pulsar"]
    )
    description: Optional[str] = Field(
        default=None, description="Description of the asset's purpose"
    )
    meta_info: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata about the asset"
    )
    shader: Optional[ShaderCreate] = None
    control: Optional[ControlCreate] = None
    tone: Optional[ToneCreate] = None
    haptic: Optional[HapticCreate] = None
    modulation: Optional[Modulation] = None
    control_parameters: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Array of control mappings for this asset",
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
    modulations: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Array of modulations for this asset",
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
                "min": 0.0,
                "max": 1.0,
            },
        ],
    )


class NestedShaderResponse(SchemaBase):
    name: str
    vertex_shader: str
    fragment_shader: str
    shader_lib_id: Optional[int] = None
    uniforms: Optional[List[Dict[str, Any]]] = []
    input_parameters: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None


class NestedControlResponse(SchemaBase):
    name: str
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    control_parameters: Optional[List[Dict[str, Any]]] = None


class NestedToneResponse(SchemaBase):
    name: str
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    synth: Dict[str, Any]
    effects: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    patterns: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    parts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    input_parameters: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class NestedHapticResponse(SchemaBase):
    name: str
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    device: Optional[Dict[str, Any]] = None
    input_parameters: Optional[List[Dict[str, Any]]] = None


class NestedSynestheticAsset(SchemaBase):
    synesthetic_asset_id: int
    name: str
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    shader: Optional[NestedShaderResponse] = None
    control: Optional[NestedControlResponse] = None
    tone: Optional[NestedToneResponse] = None
    haptic: Optional[NestedHapticResponse] = None
    modulation: Optional[Modulation] = None
    rule_bundle: Optional[RuleBundleSchema] = None
    control_parameters: Optional[List[Dict[str, Any]]] = None
    modulations: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(from_attributes=True)


class SynestheticAssetResponse(SchemaBase):
    """
    Clean response schema for synesthetic assets, without all the nullable fields
    that might not be present in the response.
    """

    synesthetic_asset_id: int
    name: str
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    # IDs are only included if they exist
    shader_id: Optional[int] = None
    control_id: Optional[int] = None
    tone_id: Optional[int] = None
    haptic_id: Optional[int] = None

    # Modulations are added when they exist
    modulations: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",  # Ignore extra fields that aren't defined in the schema
    )


class NestedSynestheticAssetResponse(SchemaBase):
    """
    Clean response schema for nested synesthetic assets, with properly nested components.
    When a nested component is included, its ID is omitted to avoid duplication.
    """

    synesthetic_asset_id: int
    name: str
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    # These IDs are only included when the nested object is NOT present
    shader_id: Optional[int] = None
    control_id: Optional[int] = None
    tone_id: Optional[int] = None
    haptic_id: Optional[int] = None
    rule_bundle_id: Optional[int] = None

    # Include related objects (when present, the corresponding ID field should be ignored)
    shader: Optional[NestedShaderResponse] = None
    control: Optional[NestedControlResponse] = None
    tone: Optional[NestedToneResponse] = None
    haptic: Optional[NestedHapticResponse] = None
    rule_bundle: Optional[RuleBundleSchema] = None

    # Controls and modulations as direct arrays
    control_parameters: Optional[List[Dict[str, Any]]] = None
    modulations: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",  # Ignore extra fields that aren't defined in the schema
    )


class PreviewNestedAssetResponse(NestedSynestheticAssetResponse):
    class PatchPreviewMetadata(SchemaBase):
        patch_id: str
        component_type: str
        base_version: int
        applied: bool
        created_at: datetime

    preview: PatchPreviewMetadata | None = None


class GeneratedNestedAssetResponse(NestedSynestheticAssetResponse):
    """Response model for generated component patches."""

    patch_id: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "synesthetic_asset_id": 1,
                "name": "Generated Asset",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00",
                "patch_id": "abc123",
            }
        },
    )


class SynestheticAssetNestedPatched(NestedSynestheticAssetResponse):
    """Nested asset response with patch identifier."""

    patch_id: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")
