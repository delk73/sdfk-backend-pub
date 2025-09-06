"""Model capturing user ratings for shader patches."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from . import Base
from .serializer_mixin import SerializerMixin


class PatchRating(Base, SerializerMixin):
    """Database model storing evaluations of shader patches."""

    __tablename__ = "patch_ratings"

    patch_rating_id = Column(Integer, primary_key=True, autoincrement=True)
    patch_id = Column(
        UUID(as_uuid=True), ForeignKey("patch_index.patch_id"), nullable=False
    )
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patch = relationship("PatchIndex")

    id_field = "patch_rating_id"

    def to_dict(self) -> dict:
        data = super().to_dict()
        if data.get("patch_id"):
            data["patch_id"] = str(data["patch_id"])
        if data.get("created_at"):
            data["created_at"] = data["created_at"].isoformat()
        return data
