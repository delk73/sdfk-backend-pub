"""Pydantic model for patch index entries."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, ConfigDict

from .base_schema import SchemaBase


class PatchIndex(SchemaBase):
    """Serialized representation of a stored patch."""

    patch_id: UUID = Field(description="Unique patch identifier")
    asset_id: int = Field(description="Associated asset ID")
    component_type: str = Field(description="Component that was patched")
    base_version: int | None = Field(
        default=None, description="Asset version patch is based on"
    )
    state: str = Field(description="Current lifecycle state")
    created_at: datetime = Field(description="When the patch was created")
    blob_uri: str = Field(description="Location of archived patch data")

    model_config = ConfigDict(from_attributes=True)
