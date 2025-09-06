"""Container for reusable shader code snippets."""

from sqlalchemy import Column, Integer, String, JSON
from . import Base
from .timestamp_mixin import TimestampMixin
from .serializer_mixin import SerializerMixin


class ShaderLib(Base, TimestampMixin, SerializerMixin):
    __tablename__ = "shader_libs"

    shaderlib_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    definition = Column(JSON, nullable=False)

    id_field = "shaderlib_id"

    def to_dict(self) -> dict:
        data = dict(self.definition)
        data.update(
            {
                "shaderlib_id": self.shaderlib_id,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )
        return data
