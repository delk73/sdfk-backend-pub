from fastapi import APIRouter, Depends

from app import schemas, security
from app.services import similar_assets
from app.schema_version import require_schema_version

router = APIRouter(
    prefix="/search", tags=["search"], dependencies=[Depends(security.verify_jwt)]
)


@router.post("/assets", response_model=list[int])
def search_assets(
    query: schemas.EmbeddingQuery, _: None = Depends(require_schema_version)
) -> list[int]:
    """Return asset IDs most similar to ``query.embedding`` (client-supplied vector)."""
    return similar_assets(query.embedding, top_k=query.top_k)
