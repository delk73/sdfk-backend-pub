from typing import Any
from google.protobuf.message import Message

class Uniform(Message):
    name: str
    type: str
    stage: str
    default_value: str

class Shader(Message):
    name: str
    vertex_shader: str
    fragment_shader: str
    shader_lib_id: int
    uniforms: Any

class Envelope(Message):
    attack: float
    attackCurve: str
    decay: float
    decayCurve: str
    sustain: float
    release: float
    releaseCurve: str

class Oscillator(Message):
    type: str
    modulationType: str
    harmonicity: float
    partials: Any
    phase: float

class ToneSynth(Message):
    type: str
    volume: float
    detune: float
    portamento: float
    envelope: Envelope
    oscillator: Oscillator

class Tone(Message):
    name: str
    synth: ToneSynth

class Asset(Message):
    name: str
    description: str
    shader: Shader
    tone: Tone
