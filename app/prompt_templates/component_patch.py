"""Patch prompt builders for individual asset components."""

from __future__ import annotations

import json
import textwrap
from typing import Any, Dict

from .tone_prompt import CANONICAL_TONEJS_SYSTEM_PROMPT
from .haptic_prompt import CANONICAL_HAPTIC_PROMPT
from .control_prompt import CANONICAL_CONTROL_PROMPT
from .modulation_prompt import CANONICAL_MODULATION_PROMPT
from .shader_prompt import CANONICAL_SHADER_PROMPT


def _escape(text: str) -> str:
    """Escape braces for ``str.format`` usage."""
    return text.replace("{", "{{").replace("}", "}}")


def _build_patch_prompt(rules: str, asset: Dict[str, Any], user_prompt: str) -> str:
    """Return a generic patch prompt using ``rules`` as DSL guidance."""
    template = textwrap.dedent(
        f"""
        You are a JSON editing assistant updating a component definition.
        Use JSON Patch operations so the final object follows the canonical DSL rules below.
        Respond ONLY with a JSON object of the form:
        {{{{
          "patches": [
            {{{{"op": "add|remove|replace",
              "path": "<json-pointer>",
              "value": <any>,
              "comment": "<optional>",
              "confidence": <0-1>}}}}
          ]
        }}}}
        DSL Rules:
        {_escape(rules)}
        Current component:
        {{asset_json}}
        User request:
        {{user_prompt}}
        """
    )
    asset_json = json.dumps(asset, indent=2)
    return template.format(asset_json=asset_json, user_prompt=user_prompt)


def build_tone_patch_prompt(asset: Dict[str, Any], user_prompt: str) -> str:
    """Return the Tone patch prompt."""
    return _build_patch_prompt(CANONICAL_TONEJS_SYSTEM_PROMPT, asset, user_prompt)


def build_haptic_patch_prompt(asset: Dict[str, Any], user_prompt: str) -> str:
    """Return the haptic patch prompt."""
    return _build_patch_prompt(CANONICAL_HAPTIC_PROMPT, asset, user_prompt)


def build_control_patch_prompt(asset: Dict[str, Any], user_prompt: str) -> str:
    """Return the control patch prompt."""
    return _build_patch_prompt(CANONICAL_CONTROL_PROMPT, asset, user_prompt)


def build_modulation_patch_prompt(asset: Dict[str, Any], user_prompt: str) -> str:
    """Return the modulation patch prompt."""
    return _build_patch_prompt(CANONICAL_MODULATION_PROMPT, asset, user_prompt)


def build_shader_patch_prompt(asset: Dict[str, Any], user_prompt: str) -> str:
    """Return the shader patch prompt."""
    return _build_patch_prompt(CANONICAL_SHADER_PROMPT, asset, user_prompt)


__all__ = [
    "build_tone_patch_prompt",
    "build_haptic_patch_prompt",
    "build_control_patch_prompt",
    "build_modulation_patch_prompt",
    "build_shader_patch_prompt",
]
