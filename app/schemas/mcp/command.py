"""
MCP Command Log Schemas

Pydantic schemas for MCP command log entries, supporting serialization
and validation of logged command data.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class MCPCommandLogBase(BaseModel):
    """Base schema for MCP command log entries."""

    request_id: str = Field(description="Unique request identifier for correlation")
    asset_id: Optional[str] = Field(
        default=None, description="Asset ID if command is asset-specific"
    )
    command_type: str = Field(
        description="Type of MCP command (e.g., 'create_asset', 'update_param')"
    )
    payload: Dict[str, Any] = Field(description="Original request payload")
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Command execution result"
    )
    status: str = Field(
        default="pending",
        description="Execution status: 'pending', 'success', or 'error'",
    )


class MCPCommandLogCreate(MCPCommandLogBase):
    """Schema for creating new MCP command log entries."""


class MCPCommandLogUpdate(BaseModel):
    """Schema for updating existing MCP command log entries."""

    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Command execution result"
    )
    status: Optional[str] = Field(default=None, description="Updated execution status")


class MCPCommandLog(MCPCommandLogBase):
    """Complete MCP command log entry with database fields."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-06-04T15:30:45.123Z",
                "request_id": "req_123456",
                "asset_id": "asset_789",
                "command_type": "create_asset",
                "payload": {
                    "name": "Test Asset",
                    "tone": {"name": "Test Tone", "synth": {"type": "Tone.Synth"}},
                    "shader": {
                        "name": "Test Shader",
                        "fragment_shader": "void main() {}",
                    },
                },
                "result": {
                    "asset_id": "asset_789",
                    "status": "created",
                    "components": ["tone", "shader"],
                },
                "status": "success",
            }
        },
    )

    id: UUID = Field(description="Unique log entry identifier")
    timestamp: datetime = Field(description="When the command was logged")


class MCPCommandLogResponse(MCPCommandLog):
    """Response schema for MCP command log queries."""
