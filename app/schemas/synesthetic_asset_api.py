from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class PatchPreviewMetadata(BaseModel):
    patch_id: str
    component_type: str
    base_version: int
    applied: bool
    created_at: str


class PreviewNestedAssetAPI(BaseModel):
    synesthetic_asset_id: int
    name: str
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    created_at: Any
    updated_at: Any

    # Components as permissive dicts for preview flexibility
    shader: Optional[Dict[str, Any]] = None
    control: Optional[Dict[str, Any]] = None
    tone: Optional[Dict[str, Any]] = None
    haptic: Optional[Dict[str, Any]] = None
    rule_bundle: Optional[Dict[str, Any]] = None

    # Direct arrays
    control_parameters: Optional[List[Dict[str, Any]]] = None
    modulations: Optional[List[Dict[str, Any]]] = None

    # Preview metadata (optional)
    preview: Optional[PatchPreviewMetadata] = None

    model_config = {
        "extra": "ignore",
        "json_schema_extra": {
            "examples": [
                {
                    "synesthetic_asset_id": 1,
                    "name": "Example Asset",
                    "preview": {
                        "patch_id": "abc123",
                        "component_type": "shader",
                        "base_version": 0,
                        "applied": False,
                        "created_at": "2025-01-01T00:00:00Z",
                    },
                }
            ]
        },
    }

