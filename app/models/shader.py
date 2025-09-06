"""Database model representing a GLSL shader asset."""

from typing import Any, Dict, List, Optional

from sqlalchemy import Integer, String, Text, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .serializer_mixin import SerializerMixin


class Shader(Base, SerializerMixin):
    __tablename__ = "shaders"

    shader_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSON), nullable=True
    )
    vertex_shader: Mapped[str] = mapped_column(Text, nullable=False)
    fragment_shader: Mapped[str] = mapped_column(Text, nullable=False)
    shader_lib_id: Mapped[Optional[int]] = mapped_column(Integer)
    uniforms: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )
    input_parameters: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )

    id_field = "shader_id"
