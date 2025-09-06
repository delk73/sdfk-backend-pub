"""Shared shader uniform definitions for tests."""

from __future__ import annotations

from typing import Any, Dict, List


def reserved_uniforms() -> List[Dict[str, Any]]:
    """Return a fresh list of reserved uniform definitions."""
    return [
        {"name": "u_time", "type": "float", "stage": "fragment", "default": 0.0},
        {
            "name": "u_resolution",
            "type": "vec2",
            "stage": "fragment",
            "default": [0, 0],
        },
        {
            "name": "u_backgroundColor",
            "type": "vec3",
            "stage": "fragment",
            "default": [0, 0, 0],
        },
        {"name": "u_gridSize", "type": "float", "stage": "fragment", "default": 0.0},
        {
            "name": "u_gridColor",
            "type": "vec3",
            "stage": "fragment",
            "default": [0, 0, 0],
        },
    ]
