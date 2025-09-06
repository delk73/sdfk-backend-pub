from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PatchStorageBackend(ABC):
    """Abstract storage backend for component patches."""

    @abstractmethod
    def put(self, patch_id: str, component_type: str, patch: dict[str, Any]) -> str:
        """Store a patch and return a URI or identifier."""

    @abstractmethod
    def get(self, patch_id: str) -> dict[str, Any]:
        """Retrieve a previously stored patch by id."""
