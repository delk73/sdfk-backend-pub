"""
MCP Asset Request Models

Canonical request schemas for MCP asset operations providing type-safe,
validated, and OpenAPI-documented interfaces for external systems.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List, Union


# Response Models for OpenAPI Documentation


class MCPBaseResponse(BaseModel):
    """Base response model for all MCP operations."""

    request_id: str = Field(
        description="Unique request identifier for tracing",
        examples=["req_abc123def456"],
    )
    status: str = Field(description="Operation status", examples=["success"])
    message: str = Field(
        description="Human-readable status message",
        examples=["Operation completed successfully"],
    )


class CreateAssetResult(BaseModel):
    """Result payload for asset creation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "asset_a1b2c3d4",
                "status": "created",
                "components": {"tone": True, "shader": True, "haptic": False},
            }
        }
    )

    asset_id: str = Field(
        description="Generated unique identifier for the created asset",
        examples=["asset_a1b2c3d4"],
    )
    status: str = Field(description="Creation status", examples=["created"])
    components: Dict[str, bool] = Field(
        description="Map of component types to presence flags",
        examples=[{"tone": True, "shader": True, "haptic": False}],
    )


class CreateAssetResponse(MCPBaseResponse):
    """Response model for asset creation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "req_abc123def456",
                "asset_id": "asset_a1b2c3d4",
                "status": "success",
                "message": "Asset created successfully",
                "result": {
                    "asset_id": "asset_a1b2c3d4",
                    "status": "created",
                    "components": {"tone": True, "shader": True, "haptic": False},
                },
            }
        }
    )

    asset_id: str = Field(
        description="Generated unique identifier for the created asset",
        examples=["asset_a1b2c3d4"],
    )
    result: CreateAssetResult = Field(description="Detailed creation result")


class UpdateParamResult(BaseModel):
    """Result payload for parameter updates."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "asset_123",
                "path": "shader.u_time",
                "old_value": 0.0,
                "new_value": 1.5,
                "updated": True,
            }
        }
    )

    asset_id: str = Field(
        description="Asset identifier that was updated", examples=["asset_123"]
    )
    path: str = Field(
        description="Parameter path that was updated", examples=["shader.u_time"]
    )
    old_value: Union[str, float, int, bool] = Field(
        description="Previous parameter value", examples=[0.0]
    )
    new_value: Union[str, float, int, bool] = Field(
        description="New parameter value", examples=[1.5]
    )
    updated: bool = Field(
        description="Whether the update was successful", examples=[True]
    )


class UpdateParamResponse(MCPBaseResponse):
    """Response model for parameter updates."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "req_def456ghi789",
                "status": "success",
                "message": "Parameter updated successfully",
                "result": {
                    "asset_id": "asset_123",
                    "path": "shader.u_time",
                    "old_value": 0.0,
                    "new_value": 1.5,
                    "updated": True,
                },
            }
        }
    )

    result: UpdateParamResult = Field(description="Detailed update result")


class ApplyModulationResult(BaseModel):
    """Result payload for modulation application."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "asset_123",
                "modulation_id": "radius_pulse",
                "definition": {
                    "id": "radius_pulse",
                    "target": "shader.u_r",
                    "type": "additive",
                    "waveform": "triangle",
                    "frequency": 0.5,
                    "amplitude": 0.1,
                },
                "applied": True,
            }
        }
    )

    asset_id: str = Field(
        description="Asset identifier that was modulated", examples=["asset_123"]
    )
    modulation_id: str = Field(
        description="Modulation identifier that was applied", examples=["radius_pulse"]
    )
    definition: Dict[str, Any] = Field(
        description="Applied modulation definition",
        examples=[
            {
                "id": "radius_pulse",
                "target": "shader.u_r",
                "type": "additive",
                "waveform": "triangle",
                "frequency": 0.5,
                "amplitude": 0.1,
            }
        ],
    )
    applied: bool = Field(
        description="Whether the modulation was successfully applied", examples=[True]
    )


class ApplyModulationResponse(MCPBaseResponse):
    """Response model for modulation application."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "req_ghi789jkl012",
                "status": "success",
                "message": "Modulation applied successfully",
                "result": {
                    "asset_id": "asset_123",
                    "modulation_id": "radius_pulse",
                    "definition": {
                        "id": "radius_pulse",
                        "target": "shader.u_r",
                        "type": "additive",
                        "waveform": "triangle",
                        "frequency": 0.5,
                        "amplitude": 0.1,
                    },
                    "applied": True,
                },
            }
        }
    )

    result: ApplyModulationResult = Field(description="Detailed modulation result")


class ValidateAssetResult(BaseModel):
    """Result payload for asset validation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "valid": True,
                "components_found": ["name", "shader", "tone"],
                "validation_passed": True,
            }
        }
    )

    valid: bool = Field(
        description="Whether the asset configuration is valid", examples=[True]
    )
    components_found: List[str] = Field(
        description="List of components found in the asset blob",
        examples=[["name", "shader", "tone"]],
    )
    validation_passed: bool = Field(
        description="Whether validation checks passed", examples=[True]
    )


class ValidateAssetResponse(MCPBaseResponse):
    """Response model for asset validation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "req_jkl012mno345",
                "status": "success",
                "message": "Asset validation passed",
                "result": {
                    "valid": True,
                    "components_found": ["name", "shader", "tone"],
                    "validation_passed": True,
                },
            }
        }
    )

    result: ValidateAssetResult = Field(description="Detailed validation result")


class PingResponse(BaseModel):
    """Response model for ping endpoint."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "MCP asset router live"}}
    )

    status: str = Field(
        description="Router status message", examples=["MCP asset router live"]
    )


class CreateAssetRequest(BaseModel):
    """Request model for creating a new synesthetic asset via MCP."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Circle Harmony",
                "description": "A circular pattern with synchronized audio and haptic feedback",
                "tone": {
                    "name": "Dreamy Pluck",
                    "synth": {
                        "type": "Tone.PolySynth",
                        "polyphony": 4,
                        "volume": -10,
                        "voice": {
                            "type": "Tone.MonoSynth",
                            "options": {
                                "oscillator": {"type": "square"},
                                "envelope": {
                                    "attack": 0.05,
                                    "decay": 0.3,
                                    "sustain": 0.2,
                                    "release": 1.2,
                                },
                            },
                        },
                    },
                },
                "shader": {
                    "name": "CircleSDF",
                    "fragment_shader": (
                        "uniform float u_time; void main() { "
                        "gl_FragColor = vec4(sin(u_time), 0.5, 1.0, 1.0); }"
                    ),
                    "uniforms": [
                        {
                            "name": "u_time",
                            "type": "float",
                            "stage": "fragment",
                            "default": 0.0,
                        }
                    ],
                },
                "haptic": {
                    "name": "Pulse Feedback",
                    "device": {
                        "type": "gamepad",
                        "options": {"intensity": {"value": 0.7, "unit": "percentage"}},
                    },
                    "parameters": [
                        {
                            "name": "intensity",
                            "parameter": "intensity",
                            "path": "haptic.intensity",
                            "type": "float",
                        }
                    ],
                },
                "tags": ["geometric", "interactive", "multimodal"],
            }
        }
    )

    name: str = Field(
        description="Name of the synesthetic asset",
        min_length=1,
        examples=["Circle Harmony"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional description of the asset's purpose and behavior",
        examples=["A circular pattern with synchronized audio and haptic feedback"],
    )
    tone: Dict[str, Any] = Field(
        description="Tone/audio configuration for the asset",
        examples=[
            {
                "name": "Dreamy Pluck",
                "synth": {"type": "Tone.PolySynth", "polyphony": 4},
            }
        ],
    )
    shader: Dict[str, Any] = Field(
        description="Shader configuration for visual rendering",
        examples=[
            {
                "name": "CircleSDF",
                "fragment_shader": (
                    "uniform float u_time; void main() { "
                    "gl_FragColor = vec4(sin(u_time), 0.5, 1.0, 1.0); }"
                ),
            }
        ],
    )
    haptic: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional haptic feedback configuration",
        examples=[{"name": "Pulse Feedback", "device": {"type": "gamepad"}}],
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional tags for categorization and discovery",
        examples=[["geometric", "interactive", "multimodal"]],
    )


class UpdateParamRequest(BaseModel):
    """Request model for updating a parameter value within an asset."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"asset_id": "asset_123", "path": "shader.u_time", "value": 1.5}
        }
    )

    asset_id: str = Field(
        description="Unique identifier of the asset to update",
        min_length=1,
        examples=["asset_123"],
    )
    path: str = Field(
        description="Dot-notation path to the parameter (e.g., 'shader.u_time', 'tone.volume')",
        min_length=1,
        examples=["shader.u_time"],
    )
    value: Union[str, float, int, bool] = Field(
        description="New value for the parameter", examples=[1.5]
    )


class ApplyModulationRequest(BaseModel):
    """Request model for applying a modulation to an asset parameter."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_id": "asset_123",
                "modulation_id": "radius_pulse",
                "definition": {
                    "id": "radius_pulse",
                    "target": "shader.u_r",
                    "type": "additive",
                    "waveform": "triangle",
                    "frequency": 0.5,
                    "amplitude": 0.1,
                    "offset": 0.5,
                    "phase": 0.0,
                    "scale": 1.0,
                    "scaleProfile": "linear",
                    "min": 0.0,
                    "max": 1.0,
                },
            }
        }
    )

    asset_id: str = Field(
        description="Unique identifier of the asset to modulate",
        min_length=1,
        examples=["asset_123"],
    )
    modulation_id: str = Field(
        description="Unique identifier for this modulation",
        min_length=1,
        examples=["radius_pulse"],
    )
    definition: Dict[str, Any] = Field(
        description="Modulation definition including target, waveform, and parameters",
        examples=[
            {
                "id": "radius_pulse",
                "target": "shader.u_r",
                "type": "additive",
                "waveform": "triangle",
                "frequency": 0.5,
                "amplitude": 0.1,
                "offset": 0.5,
                "phase": 0.0,
                "scale": 1.0,
                "scaleProfile": "linear",
                "min": 0.0,
                "max": 1.0,
            }
        ],
    )


class ValidateAssetRequest(BaseModel):
    """Request model for validating an asset configuration blob."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "asset_blob": {
                    "name": "Test Asset",
                    "shader": {
                        "fragment_shader": "void main() { gl_FragColor = vec4(1.0); }",
                        "uniforms": [],
                    },
                    "tone": {"synth": {"type": "Tone.Synth"}},
                }
            }
        }
    )

    asset_blob: Dict[str, Any] = Field(
        description="Complete asset configuration to validate",
        examples=[
            {
                "name": "Test Asset",
                "shader": {
                    "fragment_shader": "void main() { gl_FragColor = vec4(1.0); }",
                    "uniforms": [],
                },
                "tone": {"synth": {"type": "Tone.Synth"}},
            }
        ],
    )
