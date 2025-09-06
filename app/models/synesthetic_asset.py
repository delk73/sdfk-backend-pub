"""Composite asset linking tones, shaders, controls, and other resources."""

from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableList
from . import Base
from .timestamp_mixin import TimestampMixin


class SynestheticAsset(Base, TimestampMixin):
    __tablename__ = "synesthetic_assets"

    synesthetic_asset_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    meta_info: Mapped[Dict[str, Any]] = mapped_column(JSON)
    is_canonical: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    quality_tags: Mapped[List[str]] = mapped_column(
        MutableList.as_mutable(JSON), default=list
    )
    tone_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tones.tone_id"))
    control_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("controls.control_id")
    )
    shader_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("shaders.shader_id")
    )
    haptic_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("haptics.haptic_id")
    )
    modulation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("modulations.modulation_id")
    )
    rule_bundle_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("rule_bundles.id"), nullable=True
    )

    tone = relationship("Tone")
    control = relationship("Control")
    shader = relationship("Shader")
    haptic = relationship("Haptic")
    modulation = relationship("Modulation")
    rule_bundle = relationship(
        "RuleBundle",
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    def to_dict(self):
        result = {
            "synesthetic_asset_id": self.synesthetic_asset_id,
            "name": self.name,
            "description": self.description,
            "meta_info": self.meta_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_canonical": self.is_canonical,
            "quality_tags": self.quality_tags,
        }

        if self.tone:
            result["tone"] = self.tone.to_dict()

        if self.control:
            result["control"] = self.control.to_dict()

        if self.shader:
            result["shader"] = self.shader.to_dict()

        if self.haptic:
            result["haptic"] = self.haptic.to_dict()

        if self.modulation:
            result["modulation"] = self.modulation.to_dict()

        return result
