"""
MCP Logger Service

Utility service for logging MCP command executions. Provides structured logging
for all MCP asset operations, enabling debugging, auditing, and replay capabilities.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models import MCPCommandLog
from ..models.db import get_db
from ..middleware.request_id import get_current_request_id
from ..logging import get_logger

logger = get_logger(__name__)


def log_mcp_command(
    command_type: str,
    payload: Dict[str, Any],
    result: Optional[Dict[str, Any]] = None,
    status: str = "pending",
    request_id: Optional[str] = None,
    asset_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[str]:
    """
    Log an MCP command execution.

    Args:
        command_type: Type of MCP command (e.g., "create_asset", "update_param")
        payload: Original request payload as dictionary
        result: Command execution result (optional, can be updated later)
        status: Execution status ("pending", "success", "error")
        request_id: Request ID for correlation (auto-detected if not provided)
        asset_id: Asset ID if command is asset-specific (optional)
        db: Database session (will create one if not provided)

    Returns:
        Log entry ID as string, or None if logging failed

    Example:
        # Log a command execution
        log_id = log_mcp_command(
            command_type="create_asset",
            payload={"name": "Test Asset", "tone": {...}},
            status="pending",
            asset_id="asset_123"
        )

        # Later, update with result
        update_mcp_log(log_id, result={"status": "created"}, status="success")
    """
    try:
        # Use provided request_id or get current one
        if request_id is None:
            request_id = get_current_request_id()

        # Use provided db session or create a new one
        should_close_db = False
        if db is None:
            db = next(get_db())
            should_close_db = True

        try:
            # Create log entry
            log_entry = MCPCommandLog(
                request_id=request_id,
                asset_id=asset_id,
                command_type=command_type,
                payload=payload,
                result=result,
                status=status,
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            logger.info(
                f"MCP command logged: {command_type} with status {status}",
                extra={
                    "command_type": command_type,
                    "status": status,
                    "asset_id": asset_id,
                    "log_id": str(log_entry.id),
                },
            )

            return str(log_entry.id)

        finally:
            if should_close_db:
                db.close()

    except SQLAlchemyError as e:
        if db:
            db.rollback()
        logger.error(
            f"Failed to log MCP command {command_type}: Database error",
            exc_info=True,
            extra={
                "command_type": command_type,
                "status": status,
                "asset_id": asset_id,
                "error": str(e),
            },
        )
        return None

    except (ValueError, TypeError) as e:
        logger.error(
            f"Failed to log MCP command {command_type}: Invalid data",
            exc_info=True,
            extra={
                "command_type": command_type,
                "status": status,
                "asset_id": asset_id,
                "error": str(e),
            },
        )
        return None


def update_mcp_log(
    log_id: str,
    result: Optional[Dict[str, Any]] = None,
    status: Optional[str] = None,
    db: Optional[Session] = None,
) -> bool:
    """
    Update an existing MCP command log entry.

    Args:
        log_id: ID of the log entry to update
        result: Updated command execution result (optional)
        status: Updated execution status (optional)
        db: Database session (will create one if not provided)

    Returns:
        True if update was successful, False otherwise

    Example:
        # Update a log entry with successful result
        success = update_mcp_log(
            log_id="550e8400-e29b-41d4-a716-446655440000",
            result={"asset_id": "asset_123", "components": ["tone", "shader"]},
            status="success"
        )
    """
    try:
        # Use provided db session or create a new one
        should_close_db = False
        if db is None:
            db = next(get_db())
            should_close_db = True

        try:
            # Find the log entry - convert string UUID to UUID object
            try:
                uuid_obj = UUID(log_id) if isinstance(log_id, str) else log_id
            except ValueError:
                logger.warning(f"Invalid UUID format for log_id: {log_id}")
                return False

            log_entry = (
                db.query(MCPCommandLog).filter(MCPCommandLog.id == uuid_obj).first()
            )

            if not log_entry:
                logger.warning(f"MCP log entry not found: {log_id}")
                return False

            # Update fields if provided
            if result is not None:
                log_entry.result = result

            if status is not None:
                log_entry.status = status

            db.commit()

            logger.info(
                f"MCP log updated: {log_id}",
                extra={
                    "log_id": log_id,
                    "updated_status": status,
                    "has_result": result is not None,
                },
            )

            return True

        finally:
            if should_close_db:
                db.close()

    except SQLAlchemyError as e:
        if db:
            db.rollback()
        logger.error(
            f"Failed to update MCP log {log_id}: Database error",
            exc_info=True,
            extra={"log_id": log_id, "error": str(e)},
        )
        return False

    except (ValueError, TypeError) as e:
        logger.error(
            f"Failed to update MCP log {log_id}: Invalid data",
            exc_info=True,
            extra={"log_id": log_id, "error": str(e)},
        )
        return False


def get_mcp_logs_by_request(
    request_id: str, db: Optional[Session] = None
) -> list[MCPCommandLog]:
    """
    Retrieve all MCP command logs for a specific request.

    Args:
        request_id: Request ID to search for
        db: Database session (will create one if not provided)

    Returns:
        List of MCPCommandLog entries for the request
    """
    try:
        # Use provided db session or create a new one
        should_close_db = False
        if db is None:
            db = next(get_db())
            should_close_db = True

        try:
            logs = (
                db.query(MCPCommandLog)
                .filter(MCPCommandLog.request_id == request_id)
                .order_by(MCPCommandLog.timestamp)
                .all()
            )

            return logs

        finally:
            if should_close_db:
                db.close()

    except SQLAlchemyError as e:
        logger.error(
            f"Failed to retrieve MCP logs for request {request_id}: Database error",
            exc_info=True,
            extra={"request_id": request_id, "error": str(e)},
        )
        return []

    except (ValueError, TypeError) as e:
        logger.error(
            f"Failed to retrieve MCP logs for request {request_id}: Invalid data",
            exc_info=True,
            extra={"request_id": request_id, "error": str(e)},
        )
        return []


def get_mcp_logs_by_asset(
    asset_id: str, db: Optional[Session] = None
) -> list[MCPCommandLog]:
    """
    Retrieve all MCP command logs for a specific asset.

    Args:
        asset_id: Asset ID to search for
        db: Database session (will create one if not provided)

    Returns:
        List of MCPCommandLog entries for the asset
    """
    try:
        # Use provided db session or create a new one
        should_close_db = False
        if db is None:
            db = next(get_db())
            should_close_db = True

        try:
            logs = (
                db.query(MCPCommandLog)
                .filter(MCPCommandLog.asset_id == asset_id)
                .order_by(MCPCommandLog.timestamp)
                .all()
            )

            return logs

        finally:
            if should_close_db:
                db.close()

    except SQLAlchemyError as e:
        logger.error(
            f"Failed to retrieve MCP logs for asset {asset_id}: Database error",
            exc_info=True,
            extra={"asset_id": asset_id, "error": str(e)},
        )
        return []


def get_validation_queue(db: Optional[Session] = None) -> list[MCPCommandLog]:
    """Return all generate_asset logs awaiting validation."""
    try:
        should_close_db = False
        if db is None:
            db = next(get_db())
            should_close_db = True

        try:
            logs = (
                db.query(MCPCommandLog)
                .filter(MCPCommandLog.command_type == "generate_asset")
                .order_by(MCPCommandLog.timestamp)
                .all()
            )

            pending = []
            for log in logs:
                result = log.result or {}
                if result.get("status") == "pending_validation":
                    pending.append(log)

            return pending

        finally:
            if should_close_db:
                db.close()

    except SQLAlchemyError as e:
        logger.error(
            "Failed to retrieve validation queue: Database error",
            exc_info=True,
            extra={"error": str(e)},
        )
        return []


def get_log_by_id(log_id: str, db: Optional[Session] = None) -> Optional[MCPCommandLog]:
    """Retrieve a single MCP log entry by ID."""
    try:
        should_close_db = False
        if db is None:
            db = next(get_db())
            should_close_db = True

        try:
            uuid_obj = UUID(log_id) if isinstance(log_id, str) else log_id
            log = db.query(MCPCommandLog).filter(MCPCommandLog.id == uuid_obj).first()
            return log
        finally:
            if should_close_db:
                db.close()

    except SQLAlchemyError as e:
        logger.error(
            "Failed to retrieve MCP log",
            exc_info=True,
            extra={"log_id": log_id, "error": str(e)},
        )
        return None


def set_validation_status(
    log_id: str, status: str, db: Optional[Session] = None
) -> bool:
    """Update the validation status for a generated asset."""
    try:
        should_close_db = False
        if db is None:
            db = next(get_db())
            should_close_db = True

        try:
            log = get_log_by_id(log_id, db)
            if not log or not log.result:
                return False

            result = dict(log.result)
            result["status"] = status
            log.result = result
            db.commit()
            return True
        finally:
            if should_close_db:
                db.close()
    except SQLAlchemyError as e:
        logger.error(
            "Failed to update validation status",
            exc_info=True,
            extra={"log_id": log_id, "error": str(e)},
        )
        if db:
            db.rollback()
        return False
    except (ValueError, TypeError) as e:
        logger.error(
            "Failed to update validation status: Invalid data",
            exc_info=True,
            extra={"log_id": log_id, "error": str(e)},
        )
        if db:
            db.rollback()
        return False
