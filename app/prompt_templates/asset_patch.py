"""Prompt builder for Gemini JSON patch generation."""

import json
from typing import Dict

CANONICAL_PATCH_PROMPT = (
    "You are a JSON editing assistant. Given the current asset and the user request, "
    "respond ONLY with a JSON object of the form:\n"
    "{{\n"
    '  "patches": [\n'
    '    {{"op": "add|remove|replace", '
    '"path": "<json-pointer>", '
    '"value": <any>, '
    '"comment": "<optional>", '
    '"confidence": <0-1>}}\n'
    "  ]\n"
    "}}\n"
    "Current asset:\n"
    "{asset_json}\n"
    "User request:\n"
    "{user_prompt}"
)


def build_asset_patch_prompt(asset: Dict, user_prompt: str) -> str:
    """Fill the canonical patch prompt template with the asset and user text."""
    asset_json = json.dumps(asset, indent=2)
    return CANONICAL_PATCH_PROMPT.format(asset_json=asset_json, user_prompt=user_prompt)
