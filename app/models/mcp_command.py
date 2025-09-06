"""
MCP Command Log Model

SQLAlchemy model for recording MCP command invocations, providing an audit trail
for debugging, analytics, and AI-agent transparency.
"""

from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from uuid import uuid4
from . import Base
from .serializer_mixin import SerializerMixin


class MCPCommandLog(Base, SerializerMixin):
    """
    Log entry for MCP command executions.

    Records all MCP asset operations with payload, result, and status for
    debugging, auditing, and future replay capabilities.
    """

    __tablename__ = "mcp_command_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    request_id = Column(String, nullable=False, index=True)
    asset_id = Column(
        String, nullable=True, index=True
    )  # Optional - for asset-specific operations
    command_type = Column(
        String, nullable=False, index=True
    )  # e.g. "create_asset", "update_param"
    payload = Column(JSON, nullable=False)  # Request payload as JSON
    result = Column(
        JSON, nullable=True
    )  # Response result as JSON (null for pending/error)
    status = Column(
        String, nullable=False, default="pending", index=True
    )  # "pending", "success", "error"

    id_field = "id"

    def to_dict(self):
        data = super().to_dict()
        data["id"] = str(self.id)
        if data.get("timestamp"):
            data["timestamp"] = data["timestamp"].isoformat()
        return data
