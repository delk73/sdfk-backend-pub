"""Example model used for baseline CRUD functionality tests."""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from . import Base


class Item(Base):
    __tablename__ = "Item"

    item_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    createdAt = Column(DateTime, default=datetime.now(timezone.utc))
