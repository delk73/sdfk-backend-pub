from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any

from .base import PatchStorageBackend


class InMemoryRingBufferStorage(PatchStorageBackend):
    """Time-limited in-memory storage for recent patches."""

    def __init__(self, ttl_seconds: float = 3600, max_items: int = 1000) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._data: OrderedDict[str, tuple[dict[str, Any], float]] = OrderedDict()

    def _cleanup(self) -> None:
        now = time.time()
        while self._data and next(iter(self._data.values()))[1] < now:
            self._data.popitem(last=False)

    def put(self, patch_id: str, component_type: str, patch: dict[str, Any]) -> str:
        self._cleanup()
        if len(self._data) >= self.max_items:
            self._data.popitem(last=False)
        self._data[patch_id] = (patch, time.time() + self.ttl_seconds)
        return f"memory://{patch_id}"

    def get(self, patch_id: str) -> dict[str, Any]:
        self._cleanup()
        patch_tuple = self._data.get(patch_id)
        if patch_tuple is None:
            raise KeyError(patch_id)
        patch, expiry = patch_tuple
        if expiry < time.time():
            self._data.pop(patch_id, None)
            raise KeyError(patch_id)
        return patch
