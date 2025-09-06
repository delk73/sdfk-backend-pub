"""Utility functions for processing LLM text outputs."""


def strip_code_fences(text: str) -> str:
    """Remove Markdown triple backtick fences from ``text``.

    Args:
        text: The raw string returned by an LLM.

    Returns:
        The string without surrounding code fences.
    """
    if not text:
        return text

    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        stripped = stripped[3:-3].strip()
        if stripped.startswith("json"):
            stripped = stripped[4:].lstrip()
    return stripped
