"""Prompt moderation utilities."""

from fastapi import HTTPException

BANNED_TERMS = {"banned"}


def moderate_prompt(prompt: str) -> str:
    """Validate ``prompt`` against :data:`BANNED_TERMS`.

    Args:
        prompt: User-provided prompt.

    Returns:
        The original prompt if no banned terms are present.

    Raises:
        HTTPException: If the prompt contains banned content.
    """
    lowered = prompt.lower()
    for term in BANNED_TERMS:
        if term in lowered:
            raise HTTPException(
                status_code=400, detail="Prompt contains disallowed content"
            )
    return prompt
