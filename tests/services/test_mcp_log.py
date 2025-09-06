"""
Tests for MCP Logger Service

Comprehensive tests for the MCP command logging system, verifying log creation,
updating, retrieval, and error handling.
"""

import uuid
from uuid import UUID
from unittest.mock import MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.services.mcp_logger import (
    log_mcp_command,
    update_mcp_log,
    get_mcp_logs_by_request,
    get_mcp_logs_by_asset,
)
from app.models import MCPCommandLog
from app.schemas.mcp import MCPCommandLogCreate, MCPCommandLogResponse


class TestMCPLogger:
    """Test suite for MCP logging service."""

    def test_log_mcp_command_success(self, clean_db: Session):
        """Test successful MCP command logging."""
        # Test data
        command_type = "create_asset"
        payload = {
            "name": "Test Asset",
            "tone": {"name": "Test Tone", "synth": {"type": "Tone.Synth"}},
            "shader": {"name": "Test Shader", "fragment_shader": "void main() {}"},
        }
        request_id = "test_request_123"
        asset_id = "asset_456"

        # Log the command
        log_id = log_mcp_command(
            command_type=command_type,
            payload=payload,
            status="pending",
            request_id=request_id,
            asset_id=asset_id,
            db=clean_db,
        )

        # Verify log_id was returned
        assert log_id is not None
        assert isinstance(log_id, str)

        # Verify log entry was created in database
        log_entry = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.id == UUID(log_id))
            .first()
        )
        assert log_entry is not None
        assert log_entry.command_type == command_type
        assert log_entry.payload == payload
        assert log_entry.request_id == request_id
        assert log_entry.asset_id == asset_id
        assert log_entry.status == "pending"
        assert log_entry.result is None
        assert log_entry.timestamp is not None

    def test_log_mcp_command_minimal_data(self, clean_db: Session):
        """Test logging with minimal required data."""
        command_type = "validate_asset"
        payload = {"asset_blob": {"name": "Test"}}

        log_id = log_mcp_command(
            command_type=command_type, payload=payload, db=clean_db
        )

        assert log_id is not None

        log_entry = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.id == UUID(log_id))
            .first()
        )
        assert log_entry.command_type == command_type
        assert log_entry.payload == payload
        assert log_entry.status == "pending"  # default status
        assert log_entry.asset_id is None
        assert (
            log_entry.request_id == "no-request-id"
        )  # fallback when no request context

    def test_log_mcp_command_with_result(self, clean_db: Session):
        """Test logging command with immediate result."""
        command_type = "update_param"
        payload = {"asset_id": "asset_123", "path": "shader.u_time", "value": 1.5}
        result = {"updated": True, "old_value": 0.0, "new_value": 1.5}

        log_id = log_mcp_command(
            command_type=command_type,
            payload=payload,
            result=result,
            status="success",
            db=clean_db,
        )

        assert log_id is not None

        log_entry = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.id == UUID(log_id))
            .first()
        )
        assert log_entry.result == result
        assert log_entry.status == "success"

    def test_update_mcp_log_success(self, clean_db: Session):
        """Test successful MCP log update."""
        # Create initial log entry
        log_id = log_mcp_command(
            command_type="create_asset",
            payload={"name": "Test Asset"},
            status="pending",
            db=clean_db,
        )

        # Update with result
        result = {"asset_id": "asset_789", "components": ["tone", "shader"]}
        success = update_mcp_log(
            log_id=log_id, result=result, status="success", db=clean_db
        )

        assert success is True

        # Verify update
        log_entry = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.id == UUID(log_id))
            .first()
        )
        assert log_entry.result == result
        assert log_entry.status == "success"

    def test_update_mcp_log_partial_update(self, clean_db: Session):
        """Test partial MCP log update (only status or only result)."""
        # Create initial log entry
        log_id = log_mcp_command(
            command_type="apply_modulation",
            payload={"asset_id": "asset_123", "modulation_id": "mod_456"},
            status="pending",
            db=clean_db,
        )

        # Update only status
        success = update_mcp_log(log_id=log_id, status="error", db=clean_db)

        assert success is True

        log_entry = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.id == UUID(log_id))
            .first()
        )
        assert log_entry.status == "error"
        assert log_entry.result is None  # Should remain unchanged

    def test_update_mcp_log_not_found(self, clean_db: Session):
        """Test updating non-existent log entry."""
        fake_log_id = str(uuid.uuid4())

        success = update_mcp_log(log_id=fake_log_id, status="success", db=clean_db)

        assert success is False

    def test_get_mcp_logs_by_request(self, clean_db: Session):
        """Test retrieving logs by request ID."""
        request_id = "test_request_multi"

        # Create multiple log entries for same request
        log_ids = []
        for i, command_type in enumerate(
            ["create_asset", "update_param", "apply_modulation"]
        ):
            log_id = log_mcp_command(
                command_type=command_type,
                payload={"step": i},
                request_id=request_id,
                asset_id=f"asset_{i}",
                db=clean_db,
            )
            log_ids.append(log_id)

        # Create log entry for different request
        log_mcp_command(
            command_type="validate_asset",
            payload={"other": "request"},
            request_id="other_request",
            db=clean_db,
        )

        # Retrieve logs for specific request
        logs = get_mcp_logs_by_request(request_id, db=clean_db)

        assert len(logs) == 3
        assert all(log.request_id == request_id for log in logs)

        # Verify ordering by timestamp
        command_types = [log.command_type for log in logs]
        assert command_types == ["create_asset", "update_param", "apply_modulation"]

    def test_get_mcp_logs_by_asset(self, clean_db: Session):
        """Test retrieving logs by asset ID."""
        asset_id = "asset_multi_ops"

        # Create multiple log entries for same asset
        operations = [
            "create_asset",
            "update_param",
            "apply_modulation",
            "update_param",
        ]
        log_ids = []
        for i, command_type in enumerate(operations):
            log_id = log_mcp_command(
                command_type=command_type,
                payload={"operation": i},
                request_id=f"req_{i}",
                asset_id=asset_id,
                db=clean_db,
            )
            log_ids.append(log_id)

        # Create log entry for different asset
        log_mcp_command(
            command_type="create_asset",
            payload={"other": "asset"},
            asset_id="other_asset",
            db=clean_db,
        )

        # Retrieve logs for specific asset
        logs = get_mcp_logs_by_asset(asset_id, db=clean_db)

        assert len(logs) == 4
        assert all(log.asset_id == asset_id for log in logs)

        # Verify ordering by timestamp
        command_types = [log.command_type for log in logs]
        assert command_types == operations

    def test_get_mcp_logs_empty_results(self, clean_db: Session):
        """Test retrieving logs when none exist."""
        # Test with non-existent request ID
        logs = get_mcp_logs_by_request("non_existent_request", db=clean_db)
        assert logs == []

        # Test with non-existent asset ID
        logs = get_mcp_logs_by_asset("non_existent_asset", db=clean_db)
        assert logs == []

    def test_log_mcp_command_database_error(self, clean_db: Session):
        """Test MCP logging with database error."""
        # Mock database session to raise SQLAlchemyError
        mock_db = MagicMock()
        mock_db.add.side_effect = SQLAlchemyError("Database connection failed")

        log_id = log_mcp_command(
            command_type="create_asset", payload={"name": "Test"}, db=mock_db
        )

        # Should return None on database error
        assert log_id is None

        # Verify rollback was called
        mock_db.rollback.assert_called_once()

    def test_update_mcp_log_database_error(self, clean_db: Session):
        """Test MCP log update with database error."""
        # Create a valid log entry first
        log_id = log_mcp_command(
            command_type="create_asset", payload={"name": "Test"}, db=clean_db
        )

        # Mock database session to raise SQLAlchemyError on commit
        mock_db = MagicMock()
        mock_entry = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_entry
        mock_db.commit.side_effect = SQLAlchemyError("Commit failed")

        success = update_mcp_log(log_id=log_id, status="success", db=mock_db)

        assert success is False

    def test_get_mcp_logs_database_error(self, clean_db: Session):
        """Test retrieving logs with database error."""
        # Mock database session to raise SQLAlchemyError
        mock_db = MagicMock()
        mock_db.query.side_effect = SQLAlchemyError("Query failed")

        # Both retrieval functions should return empty lists on error
        logs = get_mcp_logs_by_request("test_request", db=mock_db)
        assert logs == []

        logs = get_mcp_logs_by_asset("test_asset", db=mock_db)
        assert logs == []

    def test_log_mcp_command_invalid_data(self, monkeypatch):
        """Type errors during log creation should return None."""

        class FailingMCPCommandLog:
            def __init__(self, *args, **kwargs):
                raise TypeError("bad data")

        monkeypatch.setattr(
            "app.services.mcp_logger.MCPCommandLog", FailingMCPCommandLog
        )

        log_id = log_mcp_command(command_type="create_asset", payload={"name": "x"})

        assert log_id is None

    def test_mcp_command_log_to_dict(self, clean_db: Session):
        """Test MCPCommandLog model to_dict method."""
        log_id = log_mcp_command(
            command_type="create_asset",
            payload={"name": "Test Asset"},
            result={"status": "created"},
            status="success",
            request_id="test_req",
            asset_id="test_asset",
            db=clean_db,
        )

        log_entry = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.id == UUID(log_id))
            .first()
        )
        log_dict = log_entry.to_dict()

        # Verify all fields are present and correctly converted
        assert log_dict["id"] == str(log_entry.id)
        assert log_dict["timestamp"] == log_entry.timestamp.isoformat()
        assert log_dict["request_id"] == "test_req"
        assert log_dict["asset_id"] == "test_asset"
        assert log_dict["command_type"] == "create_asset"
        assert log_dict["payload"] == {"name": "Test Asset"}
        assert log_dict["result"] == {"status": "created"}
        assert log_dict["status"] == "success"

    def test_mcp_log_schema_validation(self):
        """Test Pydantic schema validation for MCP logs."""
        # Test MCPCommandLogCreate schema
        create_data = {
            "request_id": "req_123",
            "command_type": "create_asset",
            "payload": {"name": "Test"},
            "status": "pending",
        }

        log_create = MCPCommandLogCreate(**create_data)
        assert log_create.request_id == "req_123"
        assert log_create.command_type == "create_asset"
        assert log_create.payload == {"name": "Test"}
        assert log_create.status == "pending"
        assert log_create.asset_id is None
        assert log_create.result is None

    def test_mcp_log_schema_serialization(self, clean_db: Session):
        """Test serialization of MCPCommandLog to response schema."""
        # Create log entry
        log_id = log_mcp_command(
            command_type="update_param",
            payload={"asset_id": "asset_123", "path": "shader.u_time", "value": 2.0},
            result={"updated": True},
            status="success",
            request_id="req_456",
            asset_id="asset_123",
            db=clean_db,
        )

        # Retrieve and convert to response schema
        log_entry = (
            clean_db.query(MCPCommandLog)
            .filter(MCPCommandLog.id == UUID(log_id))
            .first()
        )
        response_schema = MCPCommandLogResponse.model_validate(log_entry)

        # Verify all fields are properly serialized
        assert str(response_schema.id) == log_id
        assert response_schema.request_id == "req_456"
        assert response_schema.asset_id == "asset_123"
        assert response_schema.command_type == "update_param"
        assert response_schema.payload == {
            "asset_id": "asset_123",
            "path": "shader.u_time",
            "value": 2.0,
        }
        assert response_schema.result == {"updated": True}
        assert response_schema.status == "success"
        assert response_schema.timestamp is not None
