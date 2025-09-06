from app.utils.proto_converter import asset_to_proto, proto_to_asset
from app.proto import asset_pb2

example_asset = {
    "name": "Circle Harmony2",
    "description": (
        "A circular pattern that pulses with polyphonic audio sequences, "
        "enriched with effects, and synchronized haptic feedback"
    ),
    "shader": {
        "name": "CircleSDF",
        "vertex_shader": "void main() { gl_Position = vec4(position, 1.0); }",
        "fragment_shader": (
            "uniform vec2 u_resolution; uniform float u_time; uniform float u_px; "
            "uniform float u_py; uniform float u_r; float circleSDF(vec2 p, float r) { "
            "return length(p) - r; } void main() { vec2 st = gl_FragCoord.xy / u_resolution.xy; "
            "st = st * 2.0 - 1.0; st.x *= u_resolution.x / u_resolution.y; "
            "vec2 p = st - vec2(u_px, u_py); float d = circleSDF(p, u_r); "
            "vec3 color = vec3(1.0 - smoothstep(-0.05, 0.05, d)); "
            "color *= mix(vec3(0.3, 0.7, 1.0), vec3(1.0, 0.4, 0.6), "
            "sin(u_time + d * 10.0) * 0.5 + 0.5); gl_FragColor = vec4(color, 1.0); }"
        ),
        "shader_lib_id": 1,
        "uniforms": [
            {"name": "u_time", "type": "float", "stage": "fragment", "default": 0.0}
        ],
    },
    "tone": {
        "name": "Canonical Tone.Synth",
        "synth": {
            "type": "Tone.Synth",
            "volume": -12,
            "detune": 0,
            "portamento": 0.05,
            "envelope": {
                "attack": 0.05,
                "attackCurve": "exponential",
                "decay": 0.2,
                "decayCurve": "exponential",
                "sustain": 0.2,
                "release": 1.5,
                "releaseCurve": "exponential",
            },
            "oscillator": {
                "type": "amtriangle",
                "modulationType": "sine",
                "harmonicity": 0.5,
                "partials": [],
                "phase": 0,
            },
        },
    },
}


def test_round_trip():
    proto_obj = asset_to_proto(example_asset)
    assert isinstance(proto_obj, asset_pb2.Asset)
    back_to_json = proto_to_asset(proto_obj)
    assert back_to_json["name"] == example_asset["name"]
    assert back_to_json["shader"]["name"] == example_asset["shader"]["name"]
    assert (
        back_to_json["tone"]["synth"]["type"] == example_asset["tone"]["synth"]["type"]
    )
