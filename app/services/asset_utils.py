"""Utilities for formatting and normalizing synesthetic assets.

This module now uses synesthetic-schemas models for nested serialization to
ensure request/response parity with the SSOT. Enum values and other strict
types are serialized using ``model_dump(mode=\"json\")`` for consistency.
"""

from typing import Any, Dict, List
import glob
import json
import os
from app import models, schemas

# SSOT models used for nested serialization
from synesthetic_schemas.shader import Shader as SSOTShader
from synesthetic_schemas.tone import Tone as SSOTTone
from synesthetic_schemas.haptic import Haptic as SSOTHaptic
from synesthetic_schemas.control_bundle import ControlBundle as SSOTControl
from synesthetic_schemas.rule_bundle import RuleBundle as SSOTRuleBundle
from app.logging import get_logger

logger = get_logger(__name__)

EXAMPLE_PATTERN = "SynestheticAsset_Example*.json"


def load_all_example_modulations(
    examples_dir: str | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Load modulations from all synesthetic asset example files."""
    if examples_dir is None:
        examples_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "examples"
        )
    pattern = os.path.join(examples_dir, EXAMPLE_PATTERN)
    modulations_map: Dict[str, List[Dict[str, Any]]] = {}
    for file_path in glob.glob(pattern):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            if data.get("name") and data.get("modulations"):
                modulations_map[data["name"]] = data["modulations"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "Non-critical error loading example file '%s': %s",
                os.path.basename(file_path),
                str(e),
            )
        except OSError as e:  # pragma: no cover - unexpected file errors
            logger.error(
                "Unexpected error while loading example file '%s': %s",
                os.path.basename(file_path),
                str(e),
                exc_info=True,
            )
    return modulations_map


def get_example_modulations(
    asset_name: str, examples_dir: str | None = None
) -> List[Dict[str, Any]] | None:
    """Return modulations from example files matching ``asset_name``."""
    if not asset_name:
        return None
    return load_all_example_modulations(examples_dir).get(asset_name)


def normalize_parameter(param: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a parameter dictionary to ensure consistent structure."""
    result = param.copy() if isinstance(param, dict) else {}
    if not isinstance(result, dict) or "type" not in result:
        return result
    param_type = result.get("type", "").lower()
    if param_type == "string":
        if "options" not in result or result["options"] is None:
            result["options"] = []
        result.pop("min", None)
        result.pop("max", None)
    elif param_type in ["float", "int"]:
        if "min" not in result or result["min"] is None:
            result["min"] = 0 if param_type == "int" else float("0.0")
        if "max" not in result or result["max"] is None:
            result["max"] = 100 if param_type == "int" else float("1.0")
        result.pop("options", None)
        if param_type == "float":
            for key in ["default", "min", "max", "step", "smoothingTime"]:
                if key in result and isinstance(result[key], (int, float)):
                    result[key] = float(f"{result[key]:.6f}")
    elif param_type == "bool":
        result.pop("min", None)
        result.pop("max", None)
        result.pop("options", None)
    if param_type in ["float", "int"] and (
        "step" not in result or result["step"] is None
    ):
        result["step"] = 1 if param_type == "int" else float("0.1")
    if "smoothingTime" not in result or result["smoothingTime"] is None:
        result["smoothingTime"] = float("0.0")
    if "mappings" in result and isinstance(result["mappings"], list):
        for mapping in result["mappings"]:
            if (
                isinstance(mapping, dict)
                and "combo" in mapping
                and isinstance(mapping["combo"], dict)
            ):
                combo = mapping["combo"]
                # SSOT expects wheel: Optional[bool], default to False when missing/None
                if "wheel" in combo and combo["wheel"] is None:
                    combo["wheel"] = False
                elif "wheel" not in combo:
                    combo["wheel"] = False
                if "keys" in combo and combo["keys"] is None:
                    combo["keys"] = []
                elif "keys" not in combo:
                    combo["keys"] = []
                if "mouseButtons" in combo and combo["mouseButtons"] is None:
                    combo["mouseButtons"] = []
                elif "mouseButtons" not in combo:
                    combo["mouseButtons"] = []
            if (
                isinstance(mapping, dict)
                and "action" in mapping
                and isinstance(mapping["action"], dict)
            ):
                action = mapping["action"]
                if "sensitivity" in action and isinstance(
                    action["sensitivity"], (int, float)
                ):
                    action["sensitivity"] = float(f"{action['sensitivity']:.6f}")
    return result


def normalize_parameters_list(
    params_list: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Normalize a list of parameters."""
    if not params_list:
        return []
    return [normalize_parameter(param) for param in params_list]


def normalize_parts(parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize parts data to ensure loop flags are boolean."""
    if not parts:
        return []
    normalized_parts = []
    for part in parts:
        normalized_part = part.copy()
        if "loop" in normalized_part:
            normalized_part["loop"] = bool(normalized_part["loop"])
        normalized_parts.append(normalized_part)
    return normalized_parts


def format_tone_response(tone: models.Tone) -> Dict[str, Any] | None:
    """Format a tone using SSOT model for serialization.

    Ensures list fields are present (not None) to satisfy response models.
    """
    if not tone:
        return None
    payload: Dict[str, Any] = {"name": tone.name}
    if tone.description:
        payload["description"] = tone.description
    if tone.synth:
        payload["synth"] = tone.synth
    if tone.input_parameters:
        payload["input_parameters"] = normalize_parameters_list(tone.input_parameters)
    if tone.effects:
        payload["effects"] = tone.effects
    if tone.patterns:
        payload["patterns"] = tone.patterns
    if tone.parts:
        payload["parts"] = normalize_parts(tone.parts)
    if tone.meta_info:
        payload["meta_info"] = tone.meta_info
    data = SSOTTone.model_validate(payload).model_dump(mode="json")
    # Ensure list fields are concrete lists for API responses
    if data.get("input_parameters") is None:
        data["input_parameters"] = []
    if data.get("effects") is None:
        data["effects"] = []
    if data.get("patterns") is None:
        data["patterns"] = []
    if data.get("parts") is None:
        data["parts"] = []
    return data


def format_control_response(control: models.Control) -> Dict[str, Any] | None:
    """Format a control bundle using SSOT model for serialization."""
    if not control:
        return None
    control_dict = control.to_dict() if hasattr(control, "to_dict") else {}
    payload: Dict[str, Any] = {"name": control.name}
    if control.description:
        payload["description"] = control.description
    if control.meta_info:
        payload["meta_info"] = control.meta_info
    if control_dict.get("control_parameters"):
        parameters = normalize_parameters_list(control_dict["control_parameters"])
        payload["control_parameters"] = parameters
    # SSOT forbids extras and requires control_parameters; allow validation to assert shape
    # SSOT requires control_parameters; default to [] when missing
    if "control_parameters" not in payload or payload["control_parameters"] is None:
        payload["control_parameters"] = []
    return SSOTControl.model_validate(payload).model_dump(mode="json")


def format_shader_response(shader: models.Shader) -> Dict[str, Any] | None:
    """Format a shader using SSOT model for serialization, including DB id."""
    if not shader:
        return None
    payload: Dict[str, Any] = {
        "name": shader.name,
        "vertex_shader": shader.vertex_shader,
        "fragment_shader": shader.fragment_shader,
    }
    # shader_lib_id intentionally omitted to align with external schema
    if shader.description:
        payload["description"] = shader.description
    if shader.meta_info:
        payload["meta_info"] = shader.meta_info
    if shader.uniforms:
        payload["uniforms"] = shader.uniforms
    if shader.input_parameters:
        payload["input_parameters"] = normalize_parameters_list(
            shader.input_parameters
        )
    data = SSOTShader.model_validate(payload).model_dump(mode="json")
    # Ensure list fields are concrete lists for API responses
    if data.get("input_parameters") is None:
        data["input_parameters"] = []
    if data.get("uniforms") is None:
        data["uniforms"] = []
    # Add DB identifier for API response wrappers
    data["shader_id"] = shader.shader_id
    return data


def format_haptic_response(haptic: models.Haptic) -> Dict[str, Any] | None:
    """Format a haptic using SSOT model for serialization.

    Ensures list fields are present (not None) to satisfy response models.
    """
    if not haptic:
        return None
    payload: Dict[str, Any] = {"name": haptic.name}
    if haptic.description:
        payload["description"] = haptic.description
    if haptic.meta_info:
        payload["meta_info"] = haptic.meta_info
    if haptic.device:
        payload["device"] = haptic.device
    if haptic.input_parameters:
        payload["input_parameters"] = normalize_parameters_list(
            haptic.input_parameters
        )
    # SSOT requires input_parameters; default to [] if missing
    if "input_parameters" not in payload or payload["input_parameters"] is None:
        payload["input_parameters"] = []
    data = SSOTHaptic.model_validate(payload).model_dump(mode="json")
    if data.get("input_parameters") is None:
        data["input_parameters"] = []
    return data


def format_asset_response(asset: models.SynestheticAsset) -> Dict[str, Any]:
    """Format a synesthetic asset for non-nested API responses."""
    response = {
        "synesthetic_asset_id": asset.synesthetic_asset_id,
        "name": asset.name,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
    }
    if asset.description:
        response["description"] = asset.description
    if asset.modulation and asset.modulation.modulations:
        response["modulations"] = asset.modulation.modulations
    if asset.meta_info:
        meta_info_copy = asset.meta_info.copy()
        meta_info_copy.pop("modulations", None)
        if meta_info_copy:
            response["meta_info"] = meta_info_copy
    if asset.shader_id:
        response["shader_id"] = asset.shader_id
    if asset.control_id:
        response["control_id"] = asset.control_id
    if asset.tone_id:
        response["tone_id"] = asset.tone_id
    if asset.haptic_id:
        response["haptic_id"] = asset.haptic_id
    return response


def format_nested_asset_response(
    asset: models.SynestheticAsset,
    shader: models.Shader | None = None,
    control: models.Control | None = None,
    tone: models.Tone | None = None,
    haptic: models.Haptic | None = None,
    modulations: List[Dict[str, Any]] | None = None,
    rule_bundle: models.RuleBundle | None = None,
) -> Dict[str, Any]:
    """Format a synesthetic asset with its related components nested."""
    response = {
        "synesthetic_asset_id": asset.synesthetic_asset_id,
        "name": asset.name,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
    }
    if asset.description:
        response["description"] = asset.description
    if asset.modulation and asset.modulation.modulations and not modulations:
        modulations = asset.modulation.modulations
    if asset.meta_info:
        meta_info = asset.meta_info.copy()
        meta_info.pop("modulations", None)
        if meta_info:
            response["meta_info"] = meta_info
    if modulations:
        response["modulations"] = modulations
    if rule_bundle:
        response["rule_bundle"] = SSOTRuleBundle.model_validate(rule_bundle).model_dump(
            mode="json"
        )
    elif asset.rule_bundle:
        response["rule_bundle"] = SSOTRuleBundle.model_validate(
            asset.rule_bundle
        ).model_dump(mode="json")

    if shader:
        shader_resp = format_shader_response(shader)
        if shader_resp:
            # Omit DB id when nesting component in asset response
            shader_resp.pop("shader_id", None)
            response["shader"] = shader_resp
    elif asset.shader_id:
        response["shader_id"] = asset.shader_id
    if control:
        ctrl_resp = format_control_response(control)
        if ctrl_resp:
            response["control"] = ctrl_resp
    elif asset.control_id:
        response["control_id"] = asset.control_id
    if tone:
        tone_resp = format_tone_response(tone)
        if tone_resp:
            response["tone"] = tone_resp
    elif asset.tone_id:
        response["tone_id"] = asset.tone_id
    if haptic:
        haptic_resp = format_haptic_response(haptic)
        if haptic_resp:
            response["haptic"] = haptic_resp
    elif asset.haptic_id:
        response["haptic_id"] = asset.haptic_id
    return response
