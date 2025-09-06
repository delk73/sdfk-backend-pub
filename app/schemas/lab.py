from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field

ComponentType = Literal["shader", "audio", "haptic"]


class ShaderCandidate(BaseModel):
    input_parameters: List[Dict[str, Any]] = Field(default_factory=list)
    glsl: str = ""
    notes: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "input_parameters": [],
                    "glsl": "// stub: generated GLSL here",
                    "notes": None,
                }
            ]
        }
    }


class LabGenerateRequest(BaseModel):
    asset_id: int
    prompt: Optional[str] = None
    seed: Optional[int] = None
    constraints: Optional[Dict[str, Any]] = None
    component_type: Optional[ComponentType] = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "component_type": "shader",
                    "asset_id": 1,
                    "prompt": "make it blue",
                    "seed": 42,
                    "constraints": {"style": "minimal"},
                }
            ]
        }
    }


class LabGenerateResponse(BaseModel):
    patch_id: str
    asset: Dict[str, Any]
    candidate: Optional[ShaderCandidate] = None
    meta_info: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "patch_id": "abc123",
                    "asset": {"id": 1},
                    "candidate": {
                        "input_parameters": [],
                        "glsl": "// stub: generated GLSL here",
                        "notes": None,
                    },
                    "meta_info": {"seed": 42},
                }
            ]
        }
    }


class LabAuditRequest(BaseModel):
    asset: Dict[str, Any]
    component_type: Optional[ComponentType] = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [{"component_type": "shader", "asset": {"id": 1}}]
        }
    }


class LabAuditResponse(BaseModel):
    score: float
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    critique: Optional[str] = None
    improvement_prompt: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "score": 0.9,
                    "issues": [],
                    "warnings": [],
                    "critique": "looks good",
                    "improvement_prompt": "add detail",
                }
            ]
        }
    }


class LabCombinedResponse(BaseModel):
    patch_id: str
    asset: Dict[str, Any]
    candidate: Optional[ShaderCandidate] = None
    audit: LabAuditResponse
    meta_info: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "patch_id": "abc123",
                    "asset": {"id": 1},
                    "candidate": {
                        "input_parameters": [],
                        "glsl": "// stub: generated GLSL here",
                        "notes": None,
                    },
                    "audit": {
                        "score": 0.9,
                        "issues": [],
                        "warnings": [],
                    },
                    "meta_info": {},
                }
            ]
        }
    }


# Backwards compatibility
LabGenerateAndAuditResponse = LabCombinedResponse


class LabCombinedRequest(BaseModel):
    asset_id: int
    prompt: Optional[str] = None
    seed: Optional[int] = None
    constraints: Optional[Dict[str, Any]] = None
    component_type: Optional[ComponentType] = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "component_type": "shader",
                    "asset_id": 1,
                    "prompt": "make it blue",
                    "seed": 42,
                    "constraints": {"style": "minimal"},
                }
            ]
        }
    }
