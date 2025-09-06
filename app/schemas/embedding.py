"""Pydantic models for patch embeddings."""

from typing import List

from pydantic import Field, ConfigDict

from .base_schema import SchemaBase


class PatchEmbeddingBase(SchemaBase):
    """Base fields for patch embeddings."""

    patch_id: str = Field(..., description="Associated patch ID")
    embedding: List[float] = Field(..., description="Vector embedding values")


class PatchEmbeddingCreate(PatchEmbeddingBase):
    """Request body for creating or updating an embedding."""


class PatchEmbedding(PatchEmbeddingBase):
    """Patch embedding returned from the API."""


class EmbeddingQuery(SchemaBase):
    """Request model for similarity search."""

    embedding: List[float] = Field(..., description="Vector to compare")
    top_k: int = Field(5, description="Number of matches to return")


class EmbeddingDeleteResponse(SchemaBase):
    """Response model for deleting a patch embedding."""

    status: str = Field(..., description="Deletion status", examples=["deleted"])

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "deleted"}]})
