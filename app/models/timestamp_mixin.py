"""Mixin providing timestamp columns for creation and updates."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime


class TimestampMixin:
    """Add ``created_at`` and ``updated_at`` columns."""

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
