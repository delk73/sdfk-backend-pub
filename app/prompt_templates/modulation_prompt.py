"""Modulation prompt template."""

CANONICAL_MODULATION_PROMPT = """
You are a modulation designer working on dynamic parameter sequences for a synesthetic system.

Generate a modulation component wrapped in a top-level ``"modulation"`` key.
Respond ONLY with JSON.
"""


def build_modulation_prompt(user_prompt: str) -> str:
    """Return the canonical modulation prompt with the user's request appended."""
    return f"{CANONICAL_MODULATION_PROMPT}\n\nUser Request: {user_prompt}"
