from typing import List, Optional, Tuple
import json
from app.models import SynestheticAsset

ASSET_GENERATION_SYSTEM_PROMPT = (
    "You are a multimodal asset generator. Respond ONLY with valid JSON "
    "following the SynestheticAsset schema. Include sections for 'shader', "
    "'tone', 'haptic', 'control', and 'modulations'. "
    "Use canonical Tone.js structure for the tone object. Do not include any "
    "explanations, markdown, or code fences."
)


def asset_to_prompt_block(asset: SynestheticAsset) -> str:
    """Serialize ``asset`` to a JSON string for prompt examples."""

    data = asset.to_dict()
    return json.dumps(data, ensure_ascii=False)


def build_asset_prompt(
    prompt: str,
    retrieved: List[SynestheticAsset] | None = None,
    tags: Optional[List[str]] = None,
    complexity: Optional[str] = None,
) -> Tuple[str, str]:
    """Construct a system and user prompt with retrieved examples prepended."""

    examples = []
    for asset in retrieved or []:
        examples.append(asset_to_prompt_block(asset))

    user_parts = []
    if examples:
        user_parts.append("\n".join(examples))
    user_parts.append(prompt)
    if tags:
        user_parts.append("Tags: " + ", ".join(tags))
    if complexity:
        user_parts.append(f"Complexity: {complexity}")
    user_prompt = "\n".join(user_parts)
    return ASSET_GENERATION_SYSTEM_PROMPT, user_prompt
