#!/usr/bin/env python3
"""
Example file diagnostic tool
For diagnosing issues with example files
"""

import os
import sys
import json

from app.schemas import (
    NestedSynestheticAssetCreate,
    ShaderLibCreate,
)
from synesthetic_schemas.shader import Shader as ShaderCreate
from synesthetic_schemas.tone import Tone as ToneCreate
from synesthetic_schemas.control_bundle import ControlBundle as ControlCreate
from synesthetic_schemas.haptic import Haptic as HapticCreate
from app.utils.example_validation import (
    load_example_file,
    detect_schema,
    validate_data,
)

from app.logging import get_logger

logger = get_logger(__name__)


def color_text(text, color=None, bold=False):
    """Simple colorize function that works on most terminals"""
    if not sys.stdout.isatty():
        return text

    colors = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "cyan": "\033[36m",
        "reset": "\033[0m",
    }

    bold_code = "\033[1m" if bold else ""
    color_code = colors.get(color, "")
    reset_code = colors["reset"]

    if not color_code and not bold:
        return text

    return f"{bold_code}{color_code}{text}{reset_code}"


def diagnose_file(file_path):
    """Run diagnostic checks on a specific example file"""
    if not os.path.exists(file_path):
        logger.error(
            color_text("ERROR: File not found: " + file_path, "red", True),
            exc_info=True,
        )
        return False

    filename = os.path.basename(file_path)
    logger.info(color_text(f"Diagnosing file: {filename}", bold=True))

    # Step 1: Basic file checks
    logger.info(color_text("\nStep 1: Basic file checks", "cyan", True))
    file_size = os.path.getsize(file_path)
    logger.info(f"File size: {file_size} bytes")

    if file_size == 0:
        logger.error(color_text("ERROR: File is empty", "red", True), exc_info=True)
        return False

    # Step 2: Parse JSON
    logger.info(color_text("\nStep 2: JSON parsing", "cyan", True))
    try:
        data = load_example_file(file_path)
        logger.info(color_text("✓ JSON syntax is valid", "green"))

        if isinstance(data, dict):
            top_level_keys = list(data.keys())
            logger.info(f"Top-level keys: {', '.join(top_level_keys)}")
        elif isinstance(data, list):
            logger.info(f"JSON contains an array with {len(data)} items")

    except json.JSONDecodeError as e:
        logger.error(
            color_text(
                f"ERROR: JSON syntax error at line {e.lineno}, column {e.colno}",
                "red",
                True,
            ),
            exc_info=True,
        )
        logger.error(f"Details: {e.msg}", exc_info=True)

        with open(file_path, "r") as f:
            lines = f.readlines()

        start_line = max(0, e.lineno - 3)
        end_line = min(len(lines), e.lineno + 2)

        for i in range(start_line, end_line):
            prefix = "→ " if i + 1 == e.lineno else "  "
            logger.info(f"{prefix}{i + 1:4d} | {lines[i].rstrip()}")

            if i + 1 == e.lineno:
                logger.info(f"       {' ' * e.colno}^")

        return False

    # Step 3: Determine schema type
    logger.info(color_text("\nStep 3: Determining schema type", "cyan", True))

    schema_types = {
        "ShaderLib_Example": ShaderLibCreate,
        "Shader_Example": ShaderCreate,
        "Tone_Example": ToneCreate,
        "Control_Example": ControlCreate,
        "Haptic_Example": HapticCreate,
        "SynestheticAsset_Example": NestedSynestheticAssetCreate,
    }

    schema_type = None
    for pattern, schema in schema_types.items():
        if pattern in filename:
            schema_type = schema
            logger.info(f"Schema type based on filename: {schema.__name__}")
            break

    if not schema_type:
        logger.warning(
            color_text(
                "WARNING: Could not determine schema type from filename", "yellow", True
            )
        )
        schema_type = detect_schema(data)
        if schema_type:
            logger.warning(
                color_text(f"Guessed schema type: {schema_type.__name__}", "yellow")
            )

    if not schema_type:
        logger.error(
            color_text("ERROR: Could not determine schema type", "red", True),
            exc_info=True,
        )
        return False

    # Step 4: Validate against schema
    logger.info(color_text("\nStep 4: Schema validation", "cyan", True))
    is_valid, error_msg = validate_data(data, schema_type)

    if is_valid:
        logger.info(color_text("✓ Schema validation passed", "green"))
    else:
        logger.error(
            color_text("ERROR: Schema validation failed", "red", True), exc_info=True
        )
        logger.error(error_msg, exc_info=True)

    # Step 5: Additional diagnostics
    logger.info(color_text("\nStep 5: Additional diagnostics", "cyan", True))

    if schema_type == NestedSynestheticAssetCreate:
        if "modulations" in data:
            logger.info("\n🔍 Checking modulation target references:")

            valid_shader_paths = []
            valid_tone_paths = []
            valid_haptic_paths = []
            valid_control_parameters = []

            # shader paths
            shader_data = data.get("shader")
            if shader_data and "input_parameters" in shader_data:
                for p in shader_data["input_parameters"]:
                    if isinstance(p, dict) and "path" in p:
                        valid_shader_paths.append(p["path"])

            # tone paths
            tone_data = data.get("tone")
            if tone_data and "input_parameters" in tone_data:
                for p in tone_data["input_parameters"]:
                    if isinstance(p, dict) and "path" in p:
                        valid_tone_paths.append(p["path"])

            # haptic paths
            haptic_data = data.get("haptic")
            if haptic_data and "input_parameters" in haptic_data:
                for p in haptic_data["input_parameters"]:
                    if isinstance(p, dict) and "path" in p:
                        valid_haptic_paths.append(p["path"])

            # control parameters
            control_data = data.get("control")
            if control_data and "control_parameters" in control_data:
                for p in control_data["control_parameters"]:
                    if isinstance(p, dict) and "parameter" in p:
                        valid_control_parameters.append(p["parameter"])

            all_valid_targets = set(
                valid_shader_paths
                + valid_tone_paths
                + valid_haptic_paths
                + valid_control_parameters
            )

            for i, mod in enumerate(data["modulations"]):
                target = mod.get("target")
                mod_id = mod.get("id", f"unnamed-{i}")

                if not target:
                    logger.warning(
                        color_text(
                            f"⚠️  WARNING: Modulation {i} ({mod_id}) has no 'target' specified.",
                            "yellow",
                        )
                    )
                    continue

                if target in all_valid_targets:
                    logger.info(
                        color_text(
                            f"✅ Modulation {i} ({mod_id}): target '{target}' is valid.",
                            "green",
                        )
                    )
                else:
                    logger.warning(
                        color_text(
                            (
                                f"⚠️  WARNING: Modulation {i} ({mod_id}) targets '{target}', but it's not found.\n"
                                f"Valid shader paths: {', '.join(valid_shader_paths) if valid_shader_paths else 'none'}\n"  # noqa: E501
                                f"Valid tone paths: {', '.join(valid_tone_paths) if valid_tone_paths else 'none'}\n"  # noqa: E501
                                f"Valid haptic paths: {', '.join(valid_haptic_paths) if valid_haptic_paths else 'none'}\n"  # noqa: E501
                                f"Valid control parameters: {', '.join(valid_control_parameters) if valid_control_parameters else 'none'}"  # noqa: E501
                            ),
                            "yellow",
                        )
                    )

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Diagnostic tool for example files")
    parser.add_argument("file", help="Path to the example file to diagnose")
    args = parser.parse_args()

    diagnose_file(args.file)
