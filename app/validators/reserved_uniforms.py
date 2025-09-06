"""Shared reserved shader uniforms."""

from __future__ import annotations

from typing import Dict

# Mapping of reserved uniform names to their type and stage. Both server-side
# validation and tooling (e.g., lab_critic) import from this module to stay in
# sync.
RESERVED_UNIFORMS: Dict[str, Dict[str, str]] = {
    "u_time": {"type": "float", "stage": "fragment"},
    "u_resolution": {"type": "vec2", "stage": "fragment"},
    "u_backgroundColor": {"type": "vec3", "stage": "fragment"},
    "u_gridSize": {"type": "float", "stage": "fragment"},
    "u_gridColor": {"type": "vec3", "stage": "fragment"},
}
