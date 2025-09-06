"""Application-wide logger factory with request ID correlation."""

import logging
import sys
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .middleware.request_id import get_current_request_id


from typing_extensions import override


class JSONFormatter(logging.Formatter):
    """Format log records as JSON strings."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "route"):
            log_record["route"] = record.route
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs each request using the JSON logger."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        logger = get_logger("sdfk.request")
        logger.info(
            "request completed",
            extra={"route": request.url.path, "status_code": response.status_code},
        )
        return response


class RequestIDLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that automatically adds request_id to all log records."""

    def process(self, msg, kwargs):
        # Add request_id to extra data
        extra = kwargs.get("extra", {})
        extra["request_id"] = get_current_request_id()
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str) -> RequestIDLoggerAdapter:
    """
    Get a logger with automatic request ID correlation.

    Args:
        name: Usually __name__ from the calling module

    Returns:
        LoggerAdapter that automatically includes request_id in logs

    Example:
        logger = get_logger(__name__)
        try:
            risky_operation()
        except ValueError:
            logger.error("Bad payload", exc_info=True)
            raise HTTPException(422, "Bad payload")
    """
    # Get standard logger
    base_logger = logging.getLogger(name)

    # Configure formatter if not already configured
    if not base_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.INFO)

    # Return adapter that adds request_id
    return RequestIDLoggerAdapter(base_logger, {})
