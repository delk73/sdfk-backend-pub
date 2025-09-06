"""Model for storing binary proto assets directly in the database."""

from sqlalchemy import Column, Integer, String, LargeBinary, Text
from . import Base
from .timestamp_mixin import TimestampMixin


class ProtoAsset(Base, TimestampMixin):
    __tablename__ = "proto_assets"

    proto_asset_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    proto_blob = Column(LargeBinary, nullable=False)
