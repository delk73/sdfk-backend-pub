"""Central validation error handlers for the API."""

from __future__ import annotations

from typing import Sequence

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


def _format_errors(errors: Sequence[dict]) -> list[dict]:
    items: list[dict] = []
    for err in errors:
        loc = list(err.get("loc", ()))
        if not loc or loc[0] != "body":
            loc = ["body", *loc]
        items.append(
            {
                "loc": loc,
                "msg": err.get("msg", ""),
                "type": err.get("type", "value_error"),
                "code": err.get("type", "value_error"),
            }
        )
    return items


async def validation_exception_handler(
    request: Request, exc: ValidationError | RequestValidationError
) -> JSONResponse:
    """Return a FastAPI-style 422 response with optional error codes."""

    return JSONResponse(
        status_code=422,
        content={"detail": _format_errors(exc.errors())},
    )


def add_api_error_handlers(app: FastAPI) -> None:
    """Register validation error handlers on the given app."""

    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

