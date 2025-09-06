"""Database-backed embedding storage and similarity search."""

from typing import List, Optional
from uuid import UUID

from pgvector import Vector
import numpy as np

from app.models import (
    PatchEmbedding,
    AssetEmbedding,
    PatchIndex,
    SessionLocal,
    SynestheticAsset,
)


def clear_embeddings() -> None:
    """Remove all stored embeddings."""

    with SessionLocal() as db:
        db.query(PatchEmbedding).delete()
        db.query(AssetEmbedding).delete()
        db.commit()


def store_embedding(patch_id: str, embedding: List[float]) -> None:
    """Store an embedding for a patch."""

    with SessionLocal() as db:
        obj = db.query(PatchEmbedding).filter_by(patch_id=UUID(patch_id)).first()
        if obj is None:
            obj = PatchEmbedding(patch_id=UUID(patch_id), embedding=embedding)
            db.add(obj)
        else:
            obj.embedding = embedding
        db.commit()


def store_asset_embedding(
    asset_id: int,
    embedding: List[float],
    tags: List[str] | None = None,
    structure: str | None = None,
    model_version: str | None = None,
) -> None:
    """Store an embedding for a synesthetic asset."""

    with SessionLocal() as db:
        obj = db.query(AssetEmbedding).filter_by(asset_id=asset_id).first()
        if obj is None:
            obj = AssetEmbedding(
                asset_id=asset_id,
                embedding=embedding,
                tags=tags or [],
                structure=structure,
                model_version=model_version,
            )
            db.add(obj)
        else:
            obj.embedding = embedding
            if tags is not None:
                obj.tags = tags
            if structure is not None:
                obj.structure = structure
            if model_version is not None:
                obj.model_version = model_version
        db.commit()


def get_embedding(patch_id: str) -> Optional[Vector]:
    """Return the embedding for ``patch_id`` if present."""

    with SessionLocal() as db:
        obj = db.query(PatchEmbedding).filter_by(patch_id=UUID(patch_id)).first()
        return Vector(obj.embedding) if obj else None


def get_asset_embedding(asset_id: int) -> Optional[Vector]:
    """Return the embedding for ``asset_id`` if present."""

    with SessionLocal() as db:
        obj = db.query(AssetEmbedding).filter_by(asset_id=asset_id).first()
        return Vector(obj.embedding) if obj else None


def query_similar(
    embedding: List[float],
    top_k: int = 5,
    shader_id: int | None = None,
    asset_id: int | None = None,
) -> List[str]:
    """Return IDs of the ``top_k`` most similar embeddings."""

    with SessionLocal() as db:
        if db.bind.dialect.name != "postgresql":
            query = db.query(PatchEmbedding, PatchIndex.asset_id).join(PatchIndex)
            if shader_id is not None:
                query = query.join(
                    SynestheticAsset,
                    SynestheticAsset.synesthetic_asset_id == PatchIndex.asset_id,
                ).filter(SynestheticAsset.shader_id == shader_id)
            elif asset_id is not None:
                query = query.filter(PatchIndex.asset_id == asset_id)

            records = query.all()
            if not records:
                records = [(rec, None) for rec in db.query(PatchEmbedding).all()]

            if not records:
                return []

            target = np.array(embedding, dtype=float)
            vectors = np.array([rec.embedding for rec, _ in records], dtype=float)
            ids = [str(rec.patch_id) for rec, _ in records]

            denom = np.linalg.norm(vectors, axis=1) * np.linalg.norm(target)
            dots = vectors.dot(target)
            similarities = np.divide(
                dots, denom, out=np.zeros_like(dots, dtype=float), where=denom != 0
            )

            top_indices = np.argsort(-similarities)[:top_k]
            return [ids[i] for i in top_indices]

        query = db.query(
            PatchEmbedding.patch_id,
            PatchEmbedding.embedding.cosine_distance(embedding).label("dist"),
        ).join(PatchIndex)

        if shader_id is not None:
            query = query.join(
                SynestheticAsset,
                SynestheticAsset.synesthetic_asset_id == PatchIndex.asset_id,
            ).filter(SynestheticAsset.shader_id == shader_id)
        elif asset_id is not None:
            query = query.filter(PatchIndex.asset_id == asset_id)

        rows = query.order_by("dist").limit(top_k).all()

    return [str(row.patch_id) for row in rows]


def similar_assets(embedding: List[float], top_k: int = 5) -> List[int]:
    """Return IDs of assets with embeddings closest to ``embedding``."""

    with SessionLocal() as db:
        if db.bind.dialect.name != "postgresql":
            records = db.query(AssetEmbedding).all()
            if not records:
                return []

            target = np.array(embedding, dtype=float)
            vectors = np.array([rec.embedding for rec in records], dtype=float)
            ids = [rec.asset_id for rec in records]

            denom = np.linalg.norm(vectors, axis=1) * np.linalg.norm(target)
            dots = vectors.dot(target)
            similarities = np.divide(
                dots, denom, out=np.zeros_like(dots, dtype=float), where=denom != 0
            )

            top_indices = np.argsort(-similarities)[:top_k]
            return [ids[i] for i in top_indices]

        rows = (
            db.query(
                AssetEmbedding.asset_id,
                AssetEmbedding.embedding.cosine_distance(embedding).label("dist"),
            )
            .order_by("dist")
            .limit(top_k)
            .all()
        )

    return [row.asset_id for row in rows]


async def query_similar_assets(
    vector: list[float], tags: list[str] | None = None, top_k: int = 5
) -> list[SynestheticAsset]:
    """Return assets similar to the supplied embedding vector, filtered by ``tags`` if provided."""

    with SessionLocal() as db:
        if db.bind.dialect.name != "postgresql":
            records = db.query(AssetEmbedding).all()
            if tags:
                records = [r for r in records if all(t in (r.tags or []) for t in tags)]
            if not records:
                return []

            target = np.array(vector, dtype=float)
            vectors = np.array([rec.embedding for rec in records], dtype=float)
            ids = [rec.asset_id for rec in records]

            denom = np.linalg.norm(vectors, axis=1) * np.linalg.norm(target)
            dots = vectors.dot(target)
            similarities = np.divide(
                dots, denom, out=np.zeros_like(dots, dtype=float), where=denom != 0
            )

            top_indices = np.argsort(-similarities)[:top_k]
            asset_ids = [ids[i] for i in top_indices]
        else:
            query = db.query(
                AssetEmbedding.asset_id,
                AssetEmbedding.embedding.cosine_distance(vector).label("dist"),
            )
            if tags:
                query = query.filter(AssetEmbedding.tags.contains(tags))
            rows = query.order_by("dist").limit(top_k).all()
            asset_ids = [row.asset_id for row in rows]

        if not asset_ids:
            return []

        assets = (
            db.query(SynestheticAsset)
            .filter(SynestheticAsset.synesthetic_asset_id.in_(asset_ids))
            .all()
        )

    return assets
