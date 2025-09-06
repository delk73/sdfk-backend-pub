"""Database model representing a generic control configuration."""

from typing import Any, Dict, List, Optional

from sqlalchemy import Integer, String, Text, JSON
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .serializer_mixin import SerializerMixin


class Control(Base, SerializerMixin):
    """Model representing a generic control configuration.

    The Control table stores a set of runtime-adjustable parameters along
    with metadata describing how user input is mapped to these parameters.

    Attributes:
        control_id: Primary key for the control entry.
        name: Unique, human-friendly name of the control set.
        description: Optional descriptive text explaining the purpose of the
            control.
        meta_info: JSON blob containing arbitrary metadata such as category
            or tags.
        control_parameters: Ordered list of parameter definitions and their
            input mappings.
    """

    __tablename__ = "controls"

    control_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    meta_info: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Store the control parameters directly as a list
    control_parameters: Mapped[List[Dict[str, Any]]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
    )

    id_field = "control_id"
