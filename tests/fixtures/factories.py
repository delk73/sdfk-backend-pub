"""
Test data factories for generating consistent test data.
"""

from typing import Dict, Any
import json
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import (
    Shader,
    Tone,
    Control,
    Haptic,
    SynestheticAsset,
    ShaderLib,
    Modulation,
    RuleBundle,
)


def create_shader_lib(db: Session, **kwargs) -> ShaderLib:
    """Create a shader library for testing."""
    lib = example_shader_lib_def()
    lib.update(kwargs)

    shader_lib = ShaderLib(name=lib["name"], definition=lib)

    db.add(shader_lib)
    db.commit()
    db.refresh(shader_lib)

    return shader_lib


def example_shader_lib_def() -> dict:
    """Canonical ShaderLib v1 example definition."""
    return {
        "name": "ExampleLib",
        "version": "1",
        "reservedUniforms": [
            "u_time",
            "u_resolution",
            "u_backgroundColor",
            "u_gridSize",
            "u_gridColor",
            "u_px",
            "u_py",
        ],
        "baseInputParametersSpec": [
            {
                "name": "positionX",
                "parameter": "u_px",
                "path": "u_px",
                "type": "float",
                "default": 0.0,
                "min": -1.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.05,
            },
            {
                "name": "positionY",
                "parameter": "u_py",
                "path": "u_py",
                "type": "float",
                "default": 0.0,
                "min": -1.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.05,
            },
        ],
        "helpers": {
            "sdHexagon": {
                "glsl": "float sdHexagon(vec2 p){return 0.;}",
                "stage": "fragment",
                "requires": {
                    "uniforms": ["u_r"],
                    "inputParametersSpec": [
                        {
                            "name": "radius",
                            "parameter": "u_r",
                            "path": "u_r",
                            "type": "float",
                            "default": 0.5,
                            "min": 0.1,
                            "max": 2.0,
                            "step": 0.01,
                            "smoothingTime": 0.05,
                        }
                    ],
                },
            }
        },
        "templates": {
            "fragment_shader": "// demo\nvoid main(){ sdHexagon(vec2(u_px,u_py)); }",
        },
    }


def create_shader(db: Session, **kwargs) -> Shader:
    """Create a shader for testing."""
    defaults = {
        "name": "Test Shader",
        "description": "A test shader",
        "meta_info": {"category": "test", "tags": ["test"]},
        "vertex_shader": "void main() { gl_Position = vec4(position, 1.0); }",
        "fragment_shader": "void main() { gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); }",
        "uniforms": [
            {"name": "u_time", "type": "float", "stage": "fragment", "default": 0.0}
        ],
        "input_parameters": [
            {
                "name": "time",
                "parameter": "u_time",
                "path": "u_time",
                "type": "float",
                "default": 0.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }

    # Override defaults with any provided kwargs
    data = {**defaults, **kwargs}

    shader = Shader(
        name=data["name"],
        description=data["description"],
        meta_info=data["meta_info"],
        vertex_shader=data["vertex_shader"],
        fragment_shader=data["fragment_shader"],
        uniforms=data["uniforms"],
        input_parameters=data["input_parameters"],
    )

    if "shader_lib_id" in data:
        shader.shader_lib_id = data["shader_lib_id"]

    db.add(shader)
    db.commit()
    db.refresh(shader)

    return shader


def create_control(db: Session, **kwargs) -> Control:
    """Create a control for testing."""
    defaults = {
        "name": "Test Controls",
        "description": "Test control mappings",
        "meta_info": {"category": "test", "tags": ["test"]},
        "control_parameters": [
            {
                "parameter": "visual.u_time",
                "label": "Time",
                "type": "float",
                "unit": "seconds",
                "default": 0.0,
                "min": 0.0,
                "max": 10.0,
                "step": 0.1,
                "smoothingTime": 0.1,
                "mappings": [
                    {
                        "combo": {"mouseButtons": ["left"], "strict": True},
                        "action": {
                            "axis": "mouse.x",
                            "sensitivity": 0.01,
                            "scale": 1.0,
                            "curve": "linear",
                        },
                    }
                ],
            }
        ],
    }

    # Override defaults with any provided kwargs
    data = {**defaults, **kwargs}

    control = Control(
        name=data["name"],
        description=data["description"],
        meta_info=data["meta_info"],
        control_parameters=data["control_parameters"],
    )

    db.add(control)
    db.commit()
    db.refresh(control)

    return control


def create_tone(db: Session, **kwargs) -> Tone:
    """Create a tone for testing."""
    defaults = {
        "name": "Test Tone",
        "description": "A test tone",
        "meta_info": {"category": "test", "tags": ["test"]},
        "synth": {
            "type": "Tone.MonoSynth",
            "options": {
                "oscillator": {
                    "type": "sine",
                    "frequency": {"value": 440, "unit": "Hz"},
                },
                "envelope": {
                    "attack": {"value": 0.1, "unit": "s"},
                    "decay": {"value": 0.2, "unit": "s"},
                    "sustain": {"value": 0.5, "unit": "normalRange"},
                    "release": {"value": 0.8, "unit": "s"},
                },
            },
        },
        "effects": [],
        "patterns": [],
        "parts": [],
        "input_parameters": [
            {
                "name": "frequency",
                "parameter": "tone.oscillator.frequency",
                "path": "oscillator.frequency",
                "type": "float",
                "unit": "Hz",
                "default": 440,
                "min": 20,
                "max": 20000,
                "smoothingTime": 0.1,
            }
        ],
    }

    # Override defaults with any provided kwargs
    data = {**defaults, **kwargs}

    tone = Tone(
        name=data["name"],
        description=data["description"],
        meta_info=data["meta_info"],
        synth=data["synth"],
        effects=data["effects"],
        patterns=data["patterns"],
        parts=data["parts"],
        input_parameters=data["input_parameters"],
    )

    db.add(tone)
    db.commit()
    db.refresh(tone)

    return tone


def create_haptic(db: Session, **kwargs) -> Haptic:
    """Create a haptic for testing."""
    defaults = {
        "name": "Test Haptic",
        "description": "A test haptic configuration",
        "meta_info": {"category": "test", "tags": ["test"]},
        "device": {
            "type": "generic",
            "options": {
                "maxIntensity": {"value": 1.0, "unit": "linear"},
                "maxFrequency": {"value": 200.0, "unit": "Hz"},
                "defaultDuration": {"value": 0.2, "unit": "s"},
            },
        },
        "input_parameters": [
            {
                "name": "intensity",
                "parameter": "haptic.intensity",
                "path": "intensity",
                "type": "float",
                "unit": "linear",
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.1,
            }
        ],
    }

    # Override defaults with any provided kwargs
    data = {**defaults, **kwargs}

    haptic = Haptic(
        name=data["name"],
        description=data["description"],
        meta_info=data["meta_info"],
        device=data["device"],
        input_parameters=data["input_parameters"],
    )

    db.add(haptic)
    db.commit()
    db.refresh(haptic)

    return haptic


def create_modulation(db: Session, **kwargs) -> Modulation:
    """Create a modulation for testing."""
    defaults = {
        "name": "Test Modulations",
        "description": "Test modulation set",
        "meta_info": {"category": "modulation", "tags": ["test"]},
        "modulations": [
            {
                "id": "test_modulation",
                "target": "visual.u_time",
                "type": "additive",
                "waveform": "sine",
                "frequency": 0.5,
                "amplitude": 0.5,
                "offset": 0.0,
                "phase": 0.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }

    # Override defaults with any provided kwargs
    data = {**defaults, **kwargs}

    modulation = Modulation(
        name=data["name"],
        description=data["description"],
        meta_info=data["meta_info"],
        modulations=data["modulations"],
    )

    db.add(modulation)
    db.commit()
    db.refresh(modulation)

    return modulation


def create_rule_bundle(db: Session, **kwargs) -> RuleBundle:
    """Create a rule bundle for testing."""
    defaults = {
        "name": "Test Bundle",
        "description": "A test rule bundle",
        "meta_info": {"category": "rule_bundle", "tags": []},
        "rules": [
            {
                "id": "r1",
                "trigger": {"type": "grid_cell", "params": {"gridSize": 8}},
                "execution": "client",
                "effects": [
                    {
                        "channel": "audioTrigger",
                        "target": "tone.synth",
                        "op": "triggerAttackRelease",
                        "value": {"note": "<grid.note>", "duration": "8n"},
                    }
                ],
            }
        ],
    }
    data = {**defaults, **kwargs}
    bundle = RuleBundle(
        name=data["name"],
        description=data["description"],
        meta_info=data["meta_info"],
        rules=data["rules"],
    )
    db.add(bundle)
    db.commit()
    db.refresh(bundle)
    return bundle


def create_synesthetic_asset(db: Session, **kwargs) -> SynestheticAsset:
    """Create a synesthetic asset for testing."""
    defaults = {
        "name": "Test Synesthetic Asset",
        "description": "A test synesthetic asset",
        "meta_info": {"category": "test", "tags": ["test"]},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    # Override defaults with any provided kwargs
    data = {**defaults, **kwargs}

    asset = SynestheticAsset(
        name=data["name"],
        description=data["description"],
        meta_info=data["meta_info"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )

    # Add optional relationships if provided
    if "shader_id" in data:
        asset.shader_id = data["shader_id"]

    if "control_id" in data:
        asset.control_id = data["control_id"]

    if "tone_id" in data:
        asset.tone_id = data["tone_id"]

    if "haptic_id" in data:
        asset.haptic_id = data["haptic_id"]

    if "modulation_id" in data:
        asset.modulation_id = data["modulation_id"]

    if "rule_bundle_id" in data:
        asset.rule_bundle_id = data["rule_bundle_id"]

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


def create_complete_synesthetic_asset(db: Session, **kwargs) -> Dict[str, Any]:
    """
    Create a complete synesthetic asset with all related components.
    Returns a dictionary with all created objects.
    """
    # Create all components
    shader_lib = create_shader_lib(db)

    shader = create_shader(db, shader_lib_id=shader_lib.shaderlib_id)
    control = create_control(db)
    tone = create_tone(db)
    haptic = create_haptic(db)
    modulation = create_modulation(db)

    # Create the synesthetic asset with references to all components
    asset = create_synesthetic_asset(
        db,
        shader_id=shader.shader_id,
        control_id=control.control_id,
        tone_id=tone.tone_id,
        haptic_id=haptic.haptic_id,
        modulation_id=modulation.modulation_id,
    )

    return {
        "asset": asset,
        "shader": shader,
        "shader_lib": shader_lib,
        "control": control,
        "tone": tone,
        "haptic": haptic,
        "modulation": modulation,
    }


def load_example_file(filename: str) -> Dict[str, Any]:
    """Load an example file from the examples directory."""
    examples_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "examples"
    )
    file_path = os.path.join(examples_dir, filename)

    with open(file_path, "r") as f:
        return json.load(f)
