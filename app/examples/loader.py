"""Deterministic example loader for tests."""

import json
import pathlib

from app.shaderlib.schema import ShaderLib

EXAMPLES_DIR = pathlib.Path(__file__).parent


def load_examples(register_fn) -> bool:
    """Load the canonical ShaderLib example and register it."""
    p = EXAMPLES_DIR / "ShaderLib_Example.json"
    data = json.loads(p.read_text())
    lib = ShaderLib.model_validate(data)
    register_fn(lib)
    return True

