"""Model defining modulation sequences for dynamic parameter control."""

from typing import Any, Dict, List

from sqlalchemy import Integer, String, Text, JSON
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .serializer_mixin import SerializerMixin


class Modulation(Base, SerializerMixin):
    __tablename__ = "modulations"

    modulation_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    meta_info: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    modulations: Mapped[List[Dict[str, Any]]] = mapped_column(
        MutableList.as_mutable(JSON), nullable=False
    )  # Store the modulations directly as a list

    id_field = "modulation_id"
