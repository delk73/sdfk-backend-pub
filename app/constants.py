from enum import Enum


class UniformType(str, Enum):
    """Supported uniform data types."""

    FLOAT = "float"
    VEC2 = "vec2"
    VEC3 = "vec3"
    VEC4 = "vec4"
    INT = "int"
    BOOL = "bool"
    SAMPLER2D = "sampler2D"


class UniformStage(str, Enum):
    """Stages in which a uniform can be used."""

    VERTEX = "vertex"
    FRAGMENT = "fragment"
    BOTH = "both"


UNIFORM_TYPE_DEFAULTS = {
    UniformType.FLOAT: 0.0,
    UniformType.VEC2: {"x": 0.0, "y": 0.0},
    UniformType.VEC3: {"x": 0.0, "y": 0.0, "z": 0.0},
    UniformType.VEC4: {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
    UniformType.INT: 0,
    UniformType.BOOL: False,
    UniformType.SAMPLER2D: None,
}


class SynthType(str, Enum):
    """Allowed Tone.js synth types."""

    SYNTH = "Tone.Synth"
    POLY_SYNTH = "Tone.PolySynth"
    MONO_SYNTH = "Tone.MonoSynth"
    FM_SYNTH = "Tone.FMSynth"
    AM_SYNTH = "Tone.AMSynth"
    DUO_SYNTH = "Tone.DuoSynth"
    MEMBRANE_SYNTH = "Tone.MembraneSynth"
    METAL_SYNTH = "Tone.MetalSynth"
    PLUCK_SYNTH = "Tone.PluckSynth"
