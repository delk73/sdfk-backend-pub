from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Optional
from fastapi import Header, HTTPException, Request, status, Depends
from app.config import settings


VERSION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "libs",
    "synesthetic-schemas",
    "version.json",
)


@lru_cache(maxsize=1)
def get_schema_version() -> str:
    """Return the synesthetic_schemas version string.

    Reads libs/synesthetic-schemas/version.json and returns schemaVersion.
    Falls back to "0.0.0" if not found or invalid.
    """

    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            version = data.get("schemaVersion") or data.get("version")
            if isinstance(version, str) and version:
                return version
    except Exception:
        pass
    return "0.0.0"


SCHEMA_VERSION: str = get_schema_version()


def check_schema_header(header_value: Optional[str]) -> None:
    """Optionally enforce schema version if header is provided.

    If X-Schema-Version header is present and mismatched, raise 409.
    If absent, allow request (backwards-compatible behavior).
    """

    if header_value and header_value != SCHEMA_VERSION:
        # Let error handlers format the response
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "SchemaVersionMismatch",
                "message": "Client schema version does not match server",
                "expected": SCHEMA_VERSION,
                "received": header_value,
            },
        )


def require_schema_version(
    request: Request,
    x_schema_version: Optional[str] = Header(None, alias="X-Schema-Version"),
) -> None:
    """Enforce schema version for write operations.

    - For write methods (POST, PUT, PATCH, DELETE), require header and exact match.
    - Raises 428 Precondition Required on missing or mismatched versions.
    - Read methods are not expected to declare this dependency.
    """

    # In testing mode, skip enforcement entirely to keep unit/integration
    # tests focused on route behavior rather than version headers.
    if settings.TESTING:
        return

    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        if not x_schema_version or x_schema_version != SCHEMA_VERSION:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail={
                    "error": "SchemaVersionMismatch",
                    "message": "Client schema version does not match server",
                    "expected": SCHEMA_VERSION,
                    "received": x_schema_version or "",
                },
            )
