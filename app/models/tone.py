"""Model describing a tone and its associated synthesis parameters."""

from typing import Any, Dict, List, Optional

from sqlalchemy import Integer, String, Text, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .serializer_mixin import SerializerMixin


class Tone(Base, SerializerMixin):
    __tablename__ = "tones"

    tone_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    synth: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSON), nullable=True
    )
    input_parameters: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )
    effects: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    patterns: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )
    parts: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    meta_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSON), nullable=True
    )

    id_field = "tone_id"
