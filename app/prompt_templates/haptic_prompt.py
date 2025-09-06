"""Haptic prompt template."""

# flake8: noqa: E501

CANONICAL_HAPTIC_PROMPT = """
You are an expert haptic designer creating feedback patterns for a synesthetic system.

Generate a single haptic component wrapped in a top-level ``"haptic"`` key. The object must include:
  - ``name`` and ``description`` fields
  - ``meta_info`` with ``category`` "haptic", ``tags`` list and ``complexity`` level
  - ``device`` configuration:
    - ``type`` must be ``"generic"``
    - ``options`` map each setting to an object ``{"value": <float>, "unit": <str>}`` and include
      ``maxIntensity`` with unit ``"linear"`` and ``maxFrequency`` with unit ``"Hz"``
  - ``input_parameters`` array describing real-time controls with ``name``, ``parameter``, ``path``,
    ``type``, ``unit``, ``default``, ``min``, ``max``, ``step`` and ``smoothingTime``

Respond with ONLY the JSON object and no extra text.
"""


def build_haptic_prompt(user_prompt: str) -> str:
    """Return the canonical haptic prompt with the user request appended."""

    return f"{CANONICAL_HAPTIC_PROMPT}\n\nUser Request: {user_prompt}"
