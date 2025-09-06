"""Custom FastAPI exception handlers with consistent JSON responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
from app.logging import get_logger
from app.utils.errors import json_error
from typing import Any

logger = get_logger(__name__)


async def custom_http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Handles HTTPExceptions raised directly in the application."""

    detail_content: Any

    if isinstance(exc.detail, Exception):
        detail_content = str(exc.detail)
    elif exc.detail is None:
        # Provide a generic message based on status code class if detail is None
        if 400 <= exc.status_code < 500:
            detail_content = "Client error"
        elif 500 <= exc.status_code < 600:
            detail_content = "Server error"
        else:
            detail_content = "Error"
    else:
        # If exc.detail is not an Exception and not None, use it as is.
        # This assumes it's a str or List[dict] compatible with ErrorResponse.detail.
        detail_content = exc.detail

    return json_error(
        request=request, status_code=exc.status_code, detail=detail_content
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handles FastAPI RequestValidationErrors (Pydantic validation errors)."""
    # exc.errors() gives a list of dicts, e.g.:
    # [{"loc": ["body", "my_field"], "msg": "Field required", "type": "missing"}]
    # This matches our ErrorDetail structure if we adapt it slightly or ensure ErrorResponse can take it.

    # Convert Pydantic's error dicts to our ErrorDetail model structure if needed,
    # or ensure ErrorResponse.detail can directly take List[dict].
    # Our ErrorResponse takes Union[str, List[ErrorDetail]].
    # exc.errors() returns List[Dict[str, Any]] which should be compatible with List[ErrorDetail]
    # if the keys match (loc, msg, type).

    error_details = exc.errors()

    # Per user: "RequestValidationError must retain list-of-dicts, just with request_id added."
    # json_error will wrap this list of dicts into the "detail" field of ErrorResponse
    # and add request_id.
    return json_error(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=error_details,  # Pass the list of error dicts directly
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for all other unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # For truly unhandled exceptions, return a generic 500 error.
    return json_error(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected internal error occurred.",
    )


def add_error_handlers(app: Any) -> None:
    """Adds all custom error handlers to the FastAPI application."""
    app.add_exception_handler(HTTPException, custom_http_exception_handler)
    app.add_exception_handler(
        RequestValidationError, request_validation_exception_handler
    )
    # The global_exception_handler is already added in main.py with
    # app.add_exception_handler(Exception, global_exception_handler)
    # We just need to ensure it uses the new json_error format, which it does now.
    # No, main.py calls `app.add_exception_handler(Exception, global_exception_handler)`.
    # We should keep that registration but ensure our `global_exception_handler` uses `json_error`.
    # The one in main.py needs to be this new one.
    # For now, we assume main.py will be updated or this file is the source of truth.
    # Let's remove the old global_exception_handler registration from main.py later if we add it here.
    # The mission prompt said: "Global handler installation via add_error_handlers()"
    # So, we will add the generic Exception handler here as well.
    app.add_exception_handler(Exception, global_exception_handler)
