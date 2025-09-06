"""Helpers for converting between JSON assets and protobuf format."""

from typing import Dict, Any
from app.proto import asset_pb2


def asset_to_proto(asset_json: Dict[str, Any]) -> asset_pb2.Asset:
    """Convert a JSON asset dictionary to its protobuf representation."""

    asset = asset_pb2.Asset()
    asset.name = asset_json.get("name", "")
    asset.description = asset_json.get("description", "")

    shader_json = asset_json.get("shader", {})
    shader = asset.shader
    shader.name = shader_json.get("name", "")
    shader.vertex_shader = shader_json.get("vertex_shader", "")
    shader.fragment_shader = shader_json.get("fragment_shader", "")
    if "shader_lib_id" in shader_json:
        shader.shader_lib_id = int(shader_json["shader_lib_id"])
    for u in shader_json.get("uniforms", []):
        uni = shader.uniforms.add()
        uni.name = str(u.get("name", ""))
        uni.type = str(u.get("type", ""))
        uni.stage = str(u.get("stage", ""))
        if "default" in u:
            uni.default_value = str(u["default"])

    tone_json = asset_json.get("tone", {})
    tone = asset.tone
    tone.name = tone_json.get("name", "")
    synth_json = tone_json.get("synth", {})
    tone_synth = tone.synth
    tone_synth.type = synth_json.get("type", "")
    tone_synth.volume = float(synth_json.get("volume", 0.0))
    tone_synth.detune = float(synth_json.get("detune", 0.0))
    tone_synth.portamento = float(synth_json.get("portamento", 0.0))
    env_json = synth_json.get("envelope", {})
    tone_synth.envelope.attack = float(env_json.get("attack", 0.0))
    tone_synth.envelope.attackCurve = env_json.get("attackCurve", "")
    tone_synth.envelope.decay = float(env_json.get("decay", 0.0))
    tone_synth.envelope.decayCurve = env_json.get("decayCurve", "")
    tone_synth.envelope.sustain = float(env_json.get("sustain", 0.0))
    tone_synth.envelope.release = float(env_json.get("release", 0.0))
    tone_synth.envelope.releaseCurve = env_json.get("releaseCurve", "")
    osc_json = synth_json.get("oscillator", {})
    tone_synth.oscillator.type = osc_json.get("type", "")
    tone_synth.oscillator.modulationType = osc_json.get("modulationType", "")
    tone_synth.oscillator.harmonicity = float(osc_json.get("harmonicity", 0.0))
    tone_synth.oscillator.partials.extend(
        [str(p) for p in osc_json.get("partials", [])]
    )
    tone_synth.oscillator.phase = float(osc_json.get("phase", 0.0))
    return asset


def proto_to_asset(proto_asset: asset_pb2.Asset) -> Dict[str, Any]:
    """Convert a protobuf Asset message into a plain dictionary."""
    asset_json: Dict[str, Any] = {
        "name": proto_asset.name,
        "description": proto_asset.description,
    }
    shader = proto_asset.shader
    asset_json["shader"] = {
        "name": shader.name,
        "vertex_shader": shader.vertex_shader,
        "fragment_shader": shader.fragment_shader,
        "shader_lib_id": shader.shader_lib_id,
        "uniforms": [
            {
                "name": u.name,
                "type": u.type,
                "stage": u.stage,
                "default": u.default_value,
            }
            for u in shader.uniforms
        ],
    }

    tone_synth = proto_asset.tone.synth
    asset_json["tone"] = {
        "name": proto_asset.tone.name,
        "synth": {
            "type": tone_synth.type,
            "volume": tone_synth.volume,
            "detune": tone_synth.detune,
            "portamento": tone_synth.portamento,
            "envelope": {
                "attack": tone_synth.envelope.attack,
                "attackCurve": tone_synth.envelope.attackCurve,
                "decay": tone_synth.envelope.decay,
                "decayCurve": tone_synth.envelope.decayCurve,
                "sustain": tone_synth.envelope.sustain,
                "release": tone_synth.envelope.release,
                "releaseCurve": tone_synth.envelope.releaseCurve,
            },
            "oscillator": {
                "type": tone_synth.oscillator.type,
                "modulationType": tone_synth.oscillator.modulationType,
                "harmonicity": tone_synth.oscillator.harmonicity,
                "partials": list(tone_synth.oscillator.partials),
                "phase": tone_synth.oscillator.phase,
            },
        },
    }
    return asset_json
