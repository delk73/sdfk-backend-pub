from __future__ import annotations

from sqlalchemy.orm import Session
from uuid import UUID

from app import models


def record_preview(
    db: Session,
    patch_id: str,
    asset_id: int,
    component_type: str,
    blob_uri: str,
) -> models.PatchIndex:
    """Insert a preview record into ``patch_index``.

    Args:
        db: Database session.
        patch_id: Identifier of the patch.
        asset_id: Asset the patch targets.
        component_type: Component type being patched.
        blob_uri: Storage URI of the patch.

    Returns:
        The created ``PatchIndex`` instance.
    """
    entry = (
        db.query(models.PatchIndex)
        .filter(models.PatchIndex.patch_id == UUID(patch_id))
        .first()
    )

    if entry is None:
        entry = models.PatchIndex(
            patch_id=UUID(patch_id),
            asset_id=asset_id,
            component_type=component_type,
            state="previewed",
            blob_uri=blob_uri,
        )
        db.add(entry)
    else:
        entry.state = "previewed"
        entry.blob_uri = blob_uri

    db.commit()
    db.refresh(entry)
    return entry


def record_generated(
    db: Session,
    patch_id: str,
    asset_id: int,
    component_type: str,
    blob_uri: str,
    base_version: int,
) -> models.PatchIndex:
    """Insert a generated record into ``patch_index``.

    Args:
        db: Database session.
        patch_id: Identifier of the patch.
        asset_id: Asset the patch targets.
        component_type: Component type being patched.
        blob_uri: Storage URI of the patch.
        base_version: Version of the asset the patch was generated from.

    Returns:
        The created ``PatchIndex`` instance.
    """
    entry = (
        db.query(models.PatchIndex)
        .filter(models.PatchIndex.patch_id == UUID(patch_id))
        .first()
    )

    if entry is None:
        entry = models.PatchIndex(
            patch_id=UUID(patch_id),
            asset_id=asset_id,
            component_type=component_type,
            base_version=base_version,
            state="generated",
            blob_uri=blob_uri,
        )
        db.add(entry)
    else:
        entry.state = "generated"
        entry.blob_uri = blob_uri
        entry.base_version = base_version

    db.commit()
    db.refresh(entry)
    return entry


__all__ = ["record_preview", "record_generated", "mark_applied", "mark_rated"]


def mark_applied(db: Session, patch_id: str) -> models.PatchIndex:
    """Set ``patch_index.state`` to ``'applied'`` for ``patch_id``."""
    entry = (
        db.query(models.PatchIndex)
        .filter(models.PatchIndex.patch_id == UUID(patch_id))
        .first()
    )
    if entry is None:
        raise ValueError(f"patch {patch_id} not found")
    entry.state = "applied"
    db.commit()
    db.refresh(entry)
    return entry


def mark_rated(db: Session, patch_id: str) -> models.PatchIndex:
    """Set ``patch_index.state`` to ``'rated'`` for ``patch_id``."""
    entry = (
        db.query(models.PatchIndex)
        .filter(models.PatchIndex.patch_id == UUID(patch_id))
        .first()
    )
    if entry is None:
        raise ValueError(f"patch {patch_id} not found")
    entry.state = "rated"
    db.commit()
    db.refresh(entry)
    return entry
