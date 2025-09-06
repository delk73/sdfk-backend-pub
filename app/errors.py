"""
MCP Error Handling

Enhanced error handling module for MCP operations ensuring request_id
is properly included in all error responses for traceability.
"""

from fastapi import HTTPException
from typing import Dict, Any, Optional, Union, List
from app.middleware.request_id import get_current_request_id


class MCPHTTPException(HTTPException):
    """
    Enhanced HTTPException that automatically includes request_id in error details.

    This exception ensures that all MCP errors are traceable via request_id
    for debugging and audit purposes.
    """

    def __init__(
        self,
        status_code: int,
        detail: Union[str, Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None,
    ):
        # Get request_id from context if not provided
        if request_id is None:
            request_id = get_current_request_id()

        # Structure error detail with request_id
        if isinstance(detail, str):
            structured_detail = {
                "error": detail,
                "request_id": request_id,
                "message": detail,
            }
        elif isinstance(detail, dict):
            # Ensure request_id is included in dict-based details
            structured_detail = detail.copy()
            structured_detail["request_id"] = request_id
        else:
            structured_detail = {
                "error": "Unknown error",
                "request_id": request_id,
                "message": str(detail) if detail else "Unknown error",
            }

        super().__init__(
            status_code=status_code, detail=structured_detail, headers=headers
        )


def create_mcp_error(
    status_code: int,
    error: str,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs,
) -> MCPHTTPException:
    """
    Create a standardized MCP error with request_id.

    Args:
        status_code: HTTP status code
        error: Error type/category
        message: Human-readable error message
        request_id: Request ID (auto-detected if not provided)
        **kwargs: Additional error context fields

    Returns:
        MCPHTTPException with structured error detail

    Example:
        raise create_mcp_error(
            status_code=404,
            error="Asset not found",
            message="Asset asset_123 does not exist",
            asset_id="asset_123"
        )
    """
    if request_id is None:
        request_id = get_current_request_id()

    detail = {
        "error": error,
        "request_id": request_id,
        "message": message or error,
        **kwargs,
    }

    return MCPHTTPException(status_code=status_code, detail=detail)


def create_validation_error(
    message: str,
    validation_errors: List[str],
    request_id: Optional[str] = None,
    **kwargs,
) -> MCPHTTPException:
    """
    Create a standardized validation error (422) with request_id.

    Args:
        message: Main validation error message
        validation_errors: List of specific validation failures
        request_id: Request ID (auto-detected if not provided)
        **kwargs: Additional error context

    Returns:
        MCPHTTPException with 422 status and validation details
    """
    return create_mcp_error(
        status_code=422,
        error="Validation failed",
        message=message,
        validation_errors=validation_errors,
        request_id=request_id,
        **kwargs,
    )


def create_not_found_error(
    resource_type: str, resource_id: str, request_id: Optional[str] = None, **kwargs
) -> MCPHTTPException:
    """
    Create a standardized not found error (404) with request_id.

    Args:
        resource_type: Type of resource (e.g., "Asset", "Modulation")
        resource_id: ID of the missing resource
        request_id: Request ID (auto-detected if not provided)
        **kwargs: Additional error context

    Returns:
        MCPHTTPException with 404 status and resource details
    """
    return create_mcp_error(
        status_code=404,
        error=f"{resource_type} not found",
        message=f"{resource_type} {resource_id} does not exist",
        resource_type=resource_type.lower(),
        resource_id=resource_id,
        request_id=request_id,
        **kwargs,
    )


def create_conflict_error(
    resource_type: str,
    resource_id: str,
    reason: str,
    request_id: Optional[str] = None,
    **kwargs,
) -> MCPHTTPException:
    """
    Create a standardized conflict error (409) with request_id.

    Args:
        resource_type: Type of resource causing conflict
        resource_id: ID of the conflicting resource
        reason: Reason for the conflict
        request_id: Request ID (auto-detected if not provided)
        **kwargs: Additional error context

    Returns:
        MCPHTTPException with 409 status and conflict details
    """
    return create_mcp_error(
        status_code=409,
        error=f"{resource_type} already exists",
        message=f"{resource_type} {resource_id} {reason}",
        resource_type=resource_type.lower(),
        resource_id=resource_id,
        reason=reason,
        request_id=request_id,
        **kwargs,
    )


def create_internal_error(
    message: str = "Internal server error", request_id: Optional[str] = None, **kwargs
) -> MCPHTTPException:
    """
    Create a standardized internal server error (500) with request_id.

    Args:
        message: Error message
        request_id: Request ID (auto-detected if not provided)
        **kwargs: Additional error context

    Returns:
        MCPHTTPException with 500 status
    """
    return create_mcp_error(
        status_code=500,
        error="Internal server error",
        message=message,
        request_id=request_id,
        **kwargs,
    )


def handle_mcp_exception(
    e: Exception, request_id: Optional[str] = None
) -> MCPHTTPException:
    """
    Convert any exception to a traceable MCP error.

    Args:
        e: Exception to convert
        request_id: Request ID (auto-detected if not provided)

    Returns:
        MCPHTTPException with appropriate status and request_id
    """
    if isinstance(e, HTTPException):
        # Already an HTTP exception, just ensure request_id is included
        if isinstance(e.detail, dict):
            if "request_id" not in e.detail:
                e.detail["request_id"] = request_id or get_current_request_id()
            return MCPHTTPException(status_code=e.status_code, detail=e.detail)
        else:
            return create_mcp_error(
                status_code=e.status_code, error=str(e.detail), request_id=request_id
            )
    else:
        # Convert generic exception to internal error
        return create_internal_error(
            message=str(e), exception_type=type(e).__name__, request_id=request_id
        )


# Common error patterns for MCP operations
class MCPErrors:
    """Predefined error factories for common MCP scenarios."""

    @staticmethod
    def asset_not_found(asset_id: str, **kwargs) -> MCPHTTPException:
        """Asset not found error."""
        return create_not_found_error("Asset", asset_id, asset_id=asset_id, **kwargs)

    @staticmethod
    def invalid_parameter_path(
        path: str, valid_paths: List[str], **kwargs
    ) -> MCPHTTPException:
        """Invalid parameter path error."""
        return create_mcp_error(
            status_code=422,
            error="Invalid parameter path",
            message=f"Parameter path '{path}' is not valid",
            path=path,
            valid_paths=valid_paths,
            **kwargs,
        )

    @staticmethod
    def modulation_already_exists(
        asset_id: str, modulation_id: str, **kwargs
    ) -> MCPHTTPException:
        """Modulation already exists error."""
        return create_conflict_error(
            "Modulation",
            modulation_id,
            f"already applied to asset {asset_id}",
            asset_id=asset_id,
            modulation_id=modulation_id,
            **kwargs,
        )

    @staticmethod
    def asset_validation_failed(
        validation_errors: List[str], **kwargs
    ) -> MCPHTTPException:
        """Asset validation failed error."""
        return create_validation_error(
            "Asset configuration is invalid", validation_errors, **kwargs
        )
