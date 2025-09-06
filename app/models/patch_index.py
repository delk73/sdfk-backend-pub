"""Model tracking lifecycle state for generated patches."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from . import Base
from .serializer_mixin import SerializerMixin


class PatchIndex(Base, SerializerMixin):
    """Metadata entry for stored patches."""

    __tablename__ = "patch_index"

    patch_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id = Column(Integer, nullable=False)
    component_type = Column(String, nullable=False)
    base_version = Column(Integer, nullable=True)
    state = Column(String, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    blob_uri = Column(String, nullable=False)

    id_field = "patch_id"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["patch_id"] = str(self.patch_id)
        if data.get("created_at"):
            data["created_at"] = data["created_at"].isoformat()
        return data
