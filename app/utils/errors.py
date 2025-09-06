from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Optional, Any
import uuid


def json_error(
    request: Request,
    status_code: int,
    detail: Any,
    title: Optional[str] = None,
    error_type: Optional[str] = None,
) -> JSONResponse:
    """
    Creates a JSONResponse with the canonical error shape.
    Automatically includes the request_id from request.state.
    Recursively stringifies Exception instances in detail.
    """
    try:
        request_id_obj = request.state.request_id
    except AttributeError:
        request_id_obj = uuid.uuid4()

    def stringify_exceptions_in_detail(item: Any) -> Any:
        if isinstance(item, list):
            return [stringify_exceptions_in_detail(i) for i in item]
        elif isinstance(item, dict):
            return {k: stringify_exceptions_in_detail(v) for k, v in item.items()}
        elif isinstance(item, Exception):
            return str(item)
        return item

    processed_detail = stringify_exceptions_in_detail(detail)

    # Handle processed_detail - preserve dictionaries (like MCP error responses) and
    # other JSON-serializable types, but convert non-serializable types to strings
    if not isinstance(
        processed_detail, (str, list, dict, int, float, bool, type(None))
    ):
        # Only convert to string if it's not a JSON-serializable type
        processed_detail = str(processed_detail)

    content_payload = {"detail": processed_detail, "request_id": str(request_id_obj)}

    response_headers = {"X-Request-ID": str(request_id_obj)}
    if title:
        response_headers["X-Error-Title"] = title
    if error_type:
        response_headers["X-Error-Type"] = error_type

    return JSONResponse(
        status_code=status_code, content=content_payload, headers=response_headers
    )
