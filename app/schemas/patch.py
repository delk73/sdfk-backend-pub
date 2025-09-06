"""Schemas for shader patch queue and ratings."""

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import Field

from .base_schema import SchemaBase
from .synesthetic_asset import NestedSynestheticAssetResponse


class PatchSection(str, Enum):
    """Valid asset components that can be patched."""

    ASSET = "asset"
    SHADER = "shader"
    TONE = "tone"
    CONTROL = "control"
    HAPTIC = "haptic"
    MODULATIONS = "modulations"


class PatchRatingBase(SchemaBase):
    """Base fields for patch rating objects."""

    patch_id: str = Field(..., description="Identifier of the rated patch")
    rating: int = Field(..., ge=1, le=5, description="Rating score from 1 to 5")
    comment: Optional[str] = Field(default=None, description="Optional feedback")


class PatchRatingCreate(PatchRatingBase):
    """Request body for submitting a patch rating."""


class PatchRatingScore(SchemaBase):
    """Minimal payload for rating a patch."""

    patch_id: str = Field(description="Identifier of the rated patch")
    rating: int = Field(ge=1, le=5, description="Rating score from 1 to 5")

    model_config = {
        "json_schema_extra": {"example": {"patch_id": "abc123", "rating": 5}}
    }


class PatchRating(PatchRatingBase):
    """Patch rating returned from the API."""

    patch_rating_id: int
    created_at: datetime


class GeneratedPatch(SchemaBase):
    """Patch data staged in storage backends."""

    patch_id: str = Field(description="Unique patch identifier")
    patch: List[dict[str, Any]] = Field(description="JSON patch operations")


class GeneratedComponentPatch(GeneratedPatch):
    """Patch response including helper URLs."""

    preview_url: str = Field(description="URL to preview the patch")
    apply_url: str = Field(description="URL to apply the patch")

    model_config = {
        "json_schema_extra": {
            "example": {
                "patch_id": "abc123",
                "patch": [{"op": "replace", "path": "/tone/name", "value": "New"}],
                "preview_url": "/patches/abc123/preview",
                "apply_url": "/patches/abc123/apply",
            }
        }
    }


class GeneratedComponent(SchemaBase):
    """Patched asset response with patch identifier."""

    patched_asset: "NestedSynestheticAssetResponse" = Field(
        description="Asset with component patch applied"
    )
    patch_id: str = Field(description="Unique patch identifier")

    model_config = {
        "json_schema_extra": {
            "example": {
                "patched_asset": {"name": "Demo Asset"},
                "patch_id": "abc123",
            }
        }
    }
