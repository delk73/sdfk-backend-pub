from __future__ import annotations

from typing import Any, Callable, Optional

import jsonpatch
from fastapi import HTTPException
from pydantic import ValidationError


def apply_patch(
    original: dict,
    patch_ops: list[dict],
    validator: Optional[Callable[[dict], Any]] = None,
) -> dict:
    """Apply JSON Patch operations and validate the result.

    Args:
        original: The source dictionary to patch.
        patch_ops: List of JSON Patch operations.
        validator: Optional callable used to validate the patched result.

    Returns:
        The patched dictionary.

    Raises:
        HTTPException: If patch operations are invalid or validation fails.
    """
    try:
        patched = jsonpatch.JsonPatch(patch_ops).apply(original, in_place=False)
    except jsonpatch.JsonPatchException as exc:  # pragma: no cover - invalid ops
        raise HTTPException(status_code=422, detail="Invalid patch operations") from exc

    if validator is not None:
        try:
            validator(patched)
        except (ValueError, ValidationError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - unexpected error
            exception_type = type(exc).__name__
            raise HTTPException(
                status_code=422,
                detail=f"Validation failed: {exception_type} - {exc}",
            ) from exc

    return patched


__all__ = ["apply_patch"]
