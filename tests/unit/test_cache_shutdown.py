"""Tests for cache shutdown behavior."""

from unittest.mock import MagicMock

import pytest

import app.cache as cache_module
from app.main import close_cache_client
from app.config import settings


@pytest.mark.asyncio
async def test_cache_client_closed_on_shutdown(monkeypatch) -> None:
    """Ensure Redis cache client closes during shutdown."""

    original_cache = cache_module.cache
    original_setting = settings.CACHE_ENABLED

    mock_client = MagicMock()
    mock_pool = MagicMock()
    mock_client.connection_pool = mock_pool
    monkeypatch.setattr(
        "redis.Redis.from_url", lambda url, decode_responses=True: mock_client
    )

    cache_module.set_cache_enabled(True)
    await close_cache_client()

    mock_client.close.assert_called_once()
    mock_pool.disconnect.assert_called_once()

    cache_module.cache = original_cache
    settings.CACHE_ENABLED = original_setting


@pytest.mark.asyncio
async def test_cache_shutdown_noop_when_disabled(monkeypatch) -> None:
    """Cache shutdown handler should no-op when caching disabled."""

    original_cache = cache_module.cache
    original_setting = settings.CACHE_ENABLED

    mock_cache = MagicMock()
    settings.CACHE_ENABLED = False
    cache_module.cache = mock_cache

    await close_cache_client()

    mock_cache.close.assert_not_called()

    cache_module.cache = original_cache
    settings.CACHE_ENABLED = original_setting
