from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, security
import app.models.db as db
from app.services import store_embedding, query_similar
from app.logging import get_logger

from app.schema_version import require_schema_version


router = APIRouter(tags=["embeddings"], dependencies=[Depends(security.verify_jwt)])
logger = get_logger(__name__)


@router.post("/", response_model=schemas.PatchEmbedding)
def create_embedding(
    embedding: schemas.PatchEmbeddingCreate,
    db_session: Session = Depends(db.get_db),
    _: None = Depends(require_schema_version),
):
    store_embedding(embedding.patch_id, embedding.embedding)
    obj = (
        db_session.query(models.PatchEmbedding)
        .filter(models.PatchEmbedding.patch_id == embedding.patch_id)
        .first()
    )
    if obj is None:
        logger.error("Failed to store embedding", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    return obj


@router.get("/{patch_id}", response_model=schemas.PatchEmbedding)
def read_embedding(
    patch_id: str,
    db_session: Session = Depends(db.get_db),
):
    obj = (
        db_session.query(models.PatchEmbedding)
        .filter(models.PatchEmbedding.patch_id == patch_id)
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return obj


@router.put("/{patch_id}", response_model=schemas.PatchEmbedding)
def update_embedding(
    patch_id: str,
    embedding: schemas.PatchEmbeddingCreate,
    db_session: Session = Depends(db.get_db),
    _: None = Depends(require_schema_version),
):
    store_embedding(patch_id, embedding.embedding)
    obj = (
        db_session.query(models.PatchEmbedding)
        .filter(models.PatchEmbedding.patch_id == patch_id)
        .first()
    )
    return obj


@router.delete("/{patch_id}", response_model=schemas.EmbeddingDeleteResponse)
def delete_embedding(
    patch_id: str,
    db_session: Session = Depends(db.get_db),
    _: None = Depends(require_schema_version),
):
    obj = (
        db_session.query(models.PatchEmbedding)
        .filter(models.PatchEmbedding.patch_id == patch_id)
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Embedding not found")
    db_session.delete(obj)
    db_session.commit()
    return schemas.EmbeddingDeleteResponse(status="deleted")


@router.post("/query", response_model=list[str])
def query_embeddings(
    request: schemas.EmbeddingQuery,
):
    return query_similar(request.embedding, top_k=request.top_k)
