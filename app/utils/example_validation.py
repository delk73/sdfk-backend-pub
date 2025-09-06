import json
from typing import Any, Optional, Tuple, Type

from pydantic import BaseModel, ValidationError

from app.schemas import (
    NestedSynestheticAssetCreate,
    ShaderLibCreate,
)
from synesthetic_schemas.shader import Shader as ShaderCreate
from synesthetic_schemas.tone import Tone as ToneCreate
from synesthetic_schemas.control_bundle import ControlBundle as ControlCreate
from synesthetic_schemas.haptic import Haptic as HapticCreate


def load_example_file(path: str) -> Any:
    """Load and parse an example JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def detect_schema(data: Any) -> Optional[Type[BaseModel]]:
    """Attempt to detect the appropriate schema for given example data."""
    if not isinstance(data, dict):
        return None

    if all(key in data for key in ("shader", "tone")):
        return NestedSynestheticAssetCreate
    if "helpers" in data and "baseInputParametersSpec" in data:
        return ShaderLibCreate
    if "fragment_shader" in data or "vertex_shader" in data:
        return ShaderCreate
    if "control_parameters" in data:
        return ControlCreate
    if "synth" in data:
        return ToneCreate
    if "device" in data and "input_parameters" in data:
        return HapticCreate

    return None


def validate_data(data: dict, schema_type: Type[BaseModel]) -> Tuple[bool, str]:
    """Validate example data against the given Pydantic schema."""
    try:
        # Allow top-level schema metadata used by SSOT examples
        payload = dict(data)
        payload.pop("$schemaRef", None)
        schema_type(**payload)
        return True, ""
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            location = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            error_details.append(f"At {location}: {msg}")
        return False, "\n".join(error_details)
    except Exception as e:  # pragma: no cover - unexpected errors
        return False, f"Unexpected error: {str(e)}"
