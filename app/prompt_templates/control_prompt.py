"""Control prompt template."""

CANONICAL_CONTROL_PROMPT = """
You are an expert interaction designer creating control mappings for a synesthetic system.

Generate a control component wrapped in a top-level ``"control"`` key.
Respond ONLY with JSON.
"""


def build_control_prompt(user_prompt: str) -> str:
    """Return the canonical control prompt with the user's request appended."""
    return f"{CANONICAL_CONTROL_PROMPT}\n\nUser Request: {user_prompt}"
