import uuid
import contextvars
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store request ID for the current request
request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar("request_id")


def get_current_request_id() -> str:
    """Get the current request ID from context, or return 'no-request-id' if not available."""
    try:
        return request_id_context.get()
    except LookupError:
        return "no-request-id"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that adds a unique request ID to each request."""

    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state for easy access
        request.state.request_id = request_id

        # Set in context variable for logging
        token = request_id_context.set(request_id)

        try:
            # Process the request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response
        finally:
            # Clean up context
            request_id_context.reset(token)
