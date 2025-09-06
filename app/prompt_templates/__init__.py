"""Prompt template helpers for language model integration."""

from .asset_generation import build_asset_prompt
from .asset_patch import build_asset_patch_prompt
from .shader_prompt import build_shader_prompt
from .tone_prompt import build_tone_prompt
from .haptic_prompt import build_haptic_prompt
from .control_prompt import build_control_prompt
from .modulation_prompt import build_modulation_prompt
from .synesthetic_asset_prompt import build_synesthetic_asset_prompt
from .component_patch import (
    build_control_patch_prompt,
    build_haptic_patch_prompt,
    build_modulation_patch_prompt,
    build_shader_patch_prompt,
    build_tone_patch_prompt,
)

__all__ = [
    "build_asset_prompt",
    "build_asset_patch_prompt",
    "build_shader_prompt",
    "build_tone_prompt",
    "build_haptic_prompt",
    "build_control_prompt",
    "build_modulation_prompt",
    "build_synesthetic_asset_prompt",
    "build_tone_patch_prompt",
    "build_haptic_patch_prompt",
    "build_control_patch_prompt",
    "build_modulation_patch_prompt",
    "build_shader_patch_prompt",
]
