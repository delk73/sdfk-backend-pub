from __future__ import annotations

"""Router for toggling application cache."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.cache import set_cache_enabled
from app.config import settings
from app.schema_version import require_schema_version

router = APIRouter()


class CacheStatus(BaseModel):
    cache_enabled: bool


@router.get("/cache", response_model=CacheStatus)
async def get_cache_status() -> CacheStatus:
    """Return whether caching is enabled."""

    return CacheStatus(cache_enabled=settings.CACHE_ENABLED)


@router.post("/cache", response_model=CacheStatus)
async def set_cache_status(status: CacheStatus, _: None = Depends(require_schema_version)) -> CacheStatus:
    """Enable or disable caching at runtime."""

    set_cache_enabled(status.cache_enabled)
    return CacheStatus(cache_enabled=settings.CACHE_ENABLED)
