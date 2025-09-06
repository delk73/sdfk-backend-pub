"""SQLAlchemy model for rule bundles associated with assets."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import Integer, String, Text, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class RuleBundle(Base):
    """Container for a set of rules that can be attached to an asset."""

    __tablename__ = "rule_bundles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    meta_info: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    rules: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[sa.types.DateTime] = mapped_column(
        DateTime, server_default=sa.func.now()
    )
    updated_at: Mapped[sa.types.DateTime] = mapped_column(
        DateTime, server_default=sa.func.now(), onupdate=sa.func.now()
    )

    asset = relationship(
        "SynestheticAsset", back_populates="rule_bundle", uselist=False
    )


Index("ix_rule_bundle_name", RuleBundle.name)
