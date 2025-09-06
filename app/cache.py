"""Lightweight caching utilities used across the application."""

from __future__ import annotations

import json
import logging
from types import TracebackType
from typing import Any, Optional, Type

import redis

from app.config import settings


def set_cache_enabled(enabled: bool) -> None:
    """Toggle caching at runtime."""

    global cache
    settings.CACHE_ENABLED = enabled
    if enabled:
        cache = RedisCache(settings.REDIS_URL)
        logging.info("Cache enabled.")
    else:
        cache = NullCache()
        logging.info("Cache disabled.")


class NullCache:
    """No-op cache used when caching is disabled."""

    def get(self, key: str) -> Optional[Any]:
        logging.info("Cache is disabled, skipping lookup for key: %s", key)
        return None

    def set(self, key: str, value: Any, expire: int = 3600) -> None:
        logging.info("Cache is disabled, skipping storage for key: %s", key)

    def generate_key(self, *args: Any) -> str:
        return ":".join(str(arg) for arg in args)


class RedisCache:
    """Redis-backed cache used in production and development."""

    def __init__(self, url: str) -> None:
        self._client = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[str]:
        """Retrieve a cached value by key as a raw string."""

        value = self._client.get(key)
        if value is None:
            logging.debug("Redis cache miss for key: %s", key)
            return None

        logging.debug("Redis cache hit for key: %s", key)
        return value

    def set(self, key: str, value: Any, expire: int = 3600) -> None:
        """Store a value in the cache with an optional expiration time."""

        logging.debug("Storing in Redis cache for key: %s", key)
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self._client.set(key, value, ex=expire)

    def generate_key(self, *args: Any) -> str:
        """Generate a deterministic cache key from arbitrary arguments."""

        return ":".join(str(arg) for arg in args)

    def close(self) -> None:
        """Close the underlying Redis client and its connection pool."""

        self._client.close()
        self._client.connection_pool.disconnect()

    def __enter__(self) -> "RedisCache":
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


cache = RedisCache(settings.REDIS_URL) if settings.CACHE_ENABLED else NullCache()
