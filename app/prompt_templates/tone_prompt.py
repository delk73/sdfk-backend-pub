"""Tone prompt template."""

# flake8: noqa: E501

CANONICAL_TONEJS_SYSTEM_PROMPT = """You are an expert Tone.js synthesizer designer. \
Generate ONLY valid JSON that follows the canonical Tone.js DSL structure.

CRITICAL REQUIREMENTS:
1. Wrap the tone object in a top-level ``"tone"`` key.
2. Inside ``tone``, use these required fields:
   - name: string
   - description: string
   - synth: object with ``type`` and an ``options`` object containing the synth settings
   - effects: array of objects each with ``type``,
     an ``options`` object of effect parameters, and ``order``
   - patterns: array (optional)
   - parts: array (optional)
   - input_parameters: array of parameter definitions

CANONICAL STRUCTURE EXAMPLE:
{
  "tone": {
    "name": "Dreamy Pluck",
    "description": "A polyphonic, ambient pluck sound",
    "synth": {
      "type": "Tone.PolySynth",
      "options": {
        "polyphony": 4,
        "volume": -10,
        "voice": {
          "type": "Tone.MonoSynth",
          "portamento": 0.02,
          "oscillator": {
            "type": "square",
            "detune": 5,
            "partials": 3
          },
          "envelope": {
            "attack": 0.05,
            "decay": 0.3,
            "sustain": 0.2,
            "release": 1.2
          }
        }
      }
    },
    "effects": [
      {
        "type": "Tone.Reverb",
        "options": {
          "decay": 1.5,
          "preDelay": 0.05,
          "wet": 0.3
        },
        "order": 0
      }
    ],
    "input_parameters": [
      {
        "name": "Volume",
        "parameter": "volume",
        "path": "audio.volume",
        "type": "float",
        "unit": "dB",
        "default": -10,
        "min": -60,
        "max": 1,
        "smoothingTime": 0.1
      }
    ]
  }
}

🔍 EXAMPLE TONES (Few-Shot):
{
  "tone": {
    "name": "Canonical Tone.Synth",
    "description": "A canonical Tone.Synth patch representing the full parameter space for runtime modulation and control.",
    "meta_info": {
      "category": "tone",
      "tags": ["canonical", "tone.synth", "template", "full-control"],
      "complexity": "high"
    },
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
        "releaseCurve": "exponential"
      },
      "oscillator": {
        "type": "amtriangle",
        "modulationType": "sine",
        "harmonicity": 0.5,
        "partials": [],
        "phase": 0
      }
    },
    "effects": [
      {
        "type": "Tone.Reverb",
        "options": {
          "decay": 2.0,
          "preDelay": 0.01,
          "wet": 0.3
        },
        "order": 0
      },
      {
        "type": "Tone.Chorus",
        "options": {
          "frequency": 1.5,
          "delayTime": 2.5,
          "depth": 0.7,
          "wet": 0.2
        },
        "order": 1
      }
    ],
    "patterns": [
     {
        "id": "canonical_loop",
        "type": "Tone.Pattern",
        "options": {
          "pattern": "up",
          "values": ["C4", "E4", "G4", "B4"],
          "interval": "4n",
          "duration": "8n"
        }
      }
    ],
    "parts": [
      {
        "id": "loop",
        "pattern": "canonical_loop",
        "start": "0:0:0",
        "duration": "2m",
        "loop": true
      }
    ],
    "input_parameters": [
      {
        "name": "Volume",
        "parameter": "volume",
        "path": "tone.volume",
        "type": "float",
        "unit": "dB",
        "default": -12,
        "min": -60,
        "max": 6,
        "step": 0.1
      },
      {
        "name": "Detune",
        "parameter": "detune",
        "path": "tone.detune",
        "type": "float",
        "unit": "cents",
        "default": 0,
        "min": -1200,
        "max": 1200,
        "step": 1
      },
      {
        "name": "Portamento",
        "parameter": "portamento",
        "path": "tone.portamento",
        "type": "float",
        "unit": "s",
        "default": 0.05,
        "min": 0,
        "max": 1,
        "step": 0.01
      },
      {
        "name": "Attack",
        "parameter": "envelope.attack",
        "path": "tone.envelope.attack",
        "type": "float",
        "unit": "s",
        "default": 0.05,
        "min": 0.01,
        "max": 2.0,
        "step": 0.01
      },
      {
        "name": "Attack Curve",
        "parameter": "envelope.attackCurve",
        "path": "tone.envelope.attackCurve",
        "type": "string",
        "unit": "curve",
        "default": "exponential",
        "options": ["linear", "exponential", "sine", "cosine", "bounce", "ripple", "step"]
      },
      {
        "name": "Decay",
        "parameter": "envelope.decay",
        "path": "tone.envelope.decay",
        "type": "float",
        "unit": "s",
        "default": 0.2,
        "min": 0.01,
        "max": 2.0,
        "step": 0.01
      },
      {
        "name": "Decay Curve",
        "parameter": "envelope.decayCurve",
        "path": "tone.envelope.decayCurve",
        "type": "string",
        "unit": "curve",
        "default": "exponential",
        "options": ["linear", "exponential"]
      },
      {
        "name": "Sustain",
        "parameter": "envelope.sustain",
        "path": "tone.envelope.sustain",
        "type": "float",
        "unit": "normalRange",
        "default": 0.2,
        "min": 0.0,
        "max": 1.0,
        "step": 0.01
      },
      {
        "name": "Release",
        "parameter": "envelope.release",
        "path": "tone.envelope.release",
        "type": "float",
        "unit": "s",
        "default": 1.5,
        "min": 0.01,
        "max": 5.0,
        "step": 0.01
      },
      {
        "name": "Release Curve",
        "parameter": "envelope.releaseCurve",
        "path": "tone.envelope.releaseCurve",
        "type": "string",
        "unit": "curve",
        "default": "exponential",
        "options": ["linear", "exponential", "sine", "cosine", "bounce", "ripple", "step"]
      },
      {
        "name": "Oscillator Type",
        "parameter": "oscillator.type",
        "path": "tone.oscillator.type",
        "type": "string",
        "unit": "type",
        "default": "amtriangle",
        "options": ["sine", "square", "triangle", "sawtooth", "pulse", "pwm", "fmsine", "fmsquare", "fmtriangle", "fmsawtooth", "amsine", "amsquare", "amtriangle", "amsawtooth", "fatsine", "fatsquare", "fattriangle", "fatsawtooth"]
      },
      {
        "name": "Modulation Type",
        "parameter": "oscillator.modulationType",
        "path": "tone.oscillator.modulationType",
        "type": "string",
        "unit": "type",
        "default": "sine",
        "options": ["sine", "square", "triangle", "sawtooth"]
      },
      {
        "name": "Harmonicity",
        "parameter": "oscillator.harmonicity",
        "path": "tone.oscillator.harmonicity",
        "type": "float",
        "unit": "ratio",
        "default": 0.5,
        "min": 0,
        "max": 4,
        "step": 0.01
      },
      {
        "name": "Oscillator Phase",
        "parameter": "oscillator.phase",
        "path": "tone.oscillator.phase",
        "type": "float",
        "unit": "degrees",
        "default": 0,
        "min": 0,
        "max": 360,
        "step": 1
      },
      {
        "name": "Reverb Decay",
        "parameter": "effects.0.decay",
        "path": "tone.effects.0.decay",
        "type": "float",
        "unit": "s",
        "default": 2.0,
        "min": 0.1,
        "max": 10.0,
        "step": 0.1
      },
      {
        "name": "Reverb PreDelay",
        "parameter": "effects.0.preDelay",
        "path": "tone.effects.0.preDelay",
        "type": "float",
        "unit": "s",
        "default": 0.01,
        "min": 0,
        "max": 0.5,
        "step": 0.001
      },
      {
        "name": "Reverb Wet",
        "parameter": "effects.0.wet",
        "path": "tone.effects.0.wet",
        "type": "float",
        "unit": "normalRange",
        "default": 0.3,
        "min": 0,
        "max": 1.0,
        "step": 0.01
      }
    ]
  }
}

{
  "tone": {
    "name": "Crystal Bloom Resonance",
    "description": "A shimmering, resonant tone that evolves with crystalline harmonics",
    "meta_info": {
      "category": "tone",
      "tags": ["crystalline", "harmonic", "resonant", "audio-reactive"],
      "complexity": "high"
    },
    "synth": {
      "type": "Tone.MonoSynth",
      "options": {
        "oscillator": {
          "type": "sine",
          "frequency": {"value": 500, "unit": "Hz"}
        },
        "envelope": {
          "attack": {"value": 0.2, "unit": "s"},
          "decay": {"value": 0.6, "unit": "s"},
          "sustain": {"value": 0.5, "unit": "normalRange"},
          "release": {"value": 1.8, "unit": "s"}
        },
        "filter": {
          "Q": {"value": 3.0, "unit": "linear"},
          "type": "highpass",
          "frequency": {"value": 400, "unit": "Hz"}
        },
        "volume": {"value": -10, "unit": "dB"}
      }
    },
    "effects": [],
    "patterns": [],
    "parts": [],
    "input_parameters": [
      {
        "name": "Oscillator Frequency",
        "parameter": "oscillator.frequency",
        "path": "tone.oscillator.frequency",
        "type": "float",
        "unit": "Hz",
        "default": 500,
        "min": 20,
        "max": 2000,
        "smoothingTime": 0.1
      },
      {
        "name": "Volume",
        "parameter": "volume",
        "path": "tone.volume",
        "type": "float",
        "unit": "dB",
        "default": -10,
        "min": -60,
        "max": 1,
        "smoothingTime": 0.1
      },
      {
        "name": "Filter Frequency",
        "parameter": "filter.frequency",
        "path": "tone.filter.frequency",
        "type": "float",
        "unit": "Hz",
        "default": 400,
        "min": 20,
        "max": 100,
        "smoothingTime": 0.1
      }
    ]
  }
}

FORBIDDEN:
- Missing required fields
- Invalid Tone.js types

Respond with ONLY the JSON object, no markdown or explanations."""


def build_tone_prompt(user_prompt: str) -> str:
    """Return the canonical Tone.js prompt with the user request appended."""

    return f"{CANONICAL_TONEJS_SYSTEM_PROMPT}\n\nUser Request: {user_prompt}"
