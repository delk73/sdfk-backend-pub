"""Mixin providing a generic ``to_dict`` method using SQLAlchemy inspection."""

from sqlalchemy.inspection import inspect


class SerializerMixin:
    """Add simple model-to-dictionary serialization."""

    id_field: str | None = None

    def to_dict(self) -> dict:
        data = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        if self.id_field:
            data["id"] = getattr(self, self.id_field)
        return data
