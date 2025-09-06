"""Model storing vector embeddings for synesthetic assets."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from typing import List, Optional

from sqlalchemy import (
    Integer,
    ForeignKey,
    Index,
    String,
    DateTime,
    JSON,
)
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.env import load_env
from . import Base

load_env()


class AssetEmbedding(Base):
    """Vector embedding associated with a synesthetic asset."""

    __tablename__ = "asset_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("synesthetic_assets.synesthetic_asset_id"),
        index=True,
        nullable=False,
    )
    _dim_env = os.getenv("EMBEDDING_DIM")
    _dimension = int(_dim_env) if _dim_env else None
    embedding: Mapped[List[float]] = mapped_column(Vector(_dimension), nullable=False)
    tags: Mapped[List[str]] = mapped_column(MutableList.as_mutable(JSON), default=list)
    structure: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


if AssetEmbedding._dimension:
    Index(
        "ix_asset_embeddings_embedding_ivfflat",
        AssetEmbedding.embedding,
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
