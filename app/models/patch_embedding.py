"""Model storing vector embeddings for generated patches."""

from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import os

from app.env import load_env
from . import Base

load_env()


class PatchEmbedding(Base):
    """Vector embedding associated with a generated patch."""

    __tablename__ = "patch_embeddings"

    patch_id = Column(
        UUID(as_uuid=True), ForeignKey("patch_index.patch_id"), primary_key=True
    )
    # dimension of the vector is optional for SQLite but required for pgvector
    # indexes. Use the EMBEDDING_DIM env var when provided.
    _dim_env = os.getenv("EMBEDDING_DIM")
    _dimension = int(_dim_env) if _dim_env else None
    embedding = Column(Vector(_dimension), nullable=False)


# Index for efficient nearest-neighbor queries when using PostgreSQL.
# Only create the index when a dimension is specified to avoid errors with
# dimensionless vectors.
if PatchEmbedding._dimension:
    Index(
        "ix_patch_embeddings_embedding_ivfflat",
        PatchEmbedding.embedding,
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
