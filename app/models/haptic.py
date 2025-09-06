"""Database model for storing haptic feedback configurations."""

from typing import Any, Dict, List, Optional

from sqlalchemy import Integer, String, Text, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .serializer_mixin import SerializerMixin


class Haptic(Base, SerializerMixin):
    __tablename__ = "haptics"

    haptic_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    meta_info: Mapped[Dict[str, Any]] = mapped_column(JSON)
    device: Mapped[Dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON))
    input_parameters: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )

    id_field = "haptic_id"
