"""Synesthetic asset prompt template."""

# flake8: noqa: E501

CANONICAL_SYNESTHETIC_ASSET_PROMPT = """You are an expert synesthetic asset designer creating canonical examples for a multimodal creative platform.

MISSION: Generate a UNIQUE, CANONICAL synesthetic asset that demonstrates a novel synesthetic concept through the integration of visual, audio, and haptic modalities.

CORE PRINCIPLES:
1. **Conceptual Uniqueness**: Each asset must represent a distinct synesthetic phenomenon
2. **Canonical Form**: Serve as the archetypal example of a specific cross-modal concept
3. **Parameter Diversity**: Explore different ranges and unusual parameter combinations
4. **Meaningful Integration**: Create purposeful connections between visual, audio, and haptic elements

REQUIRED JSON SCHEMA - Generate EXACTLY this structure:
{
  "name": "[Unique evocative name - NOT generic like Circle Harmony]",
  "description": "[Detailed description of the synesthetic concept]",
  "meta_info": {
    "category": "[multimodal|visual|audio|haptic]",
    "tags": ["[concept-specific tags]"],
    "complexity": "[simple|medium|high|extreme]"
  },
  "shader": {
    "name": "[Shader technique name]",
    "vertex_shader": "[Standard vertex shader or custom]",
    "fragment_shader": "[Complex GLSL fragment shader with uniforms]",
    "shader_lib_id": [1-5],
    "uniforms": [
      {
        "name": "[uniform name]",
        "type": "[float|vec2|vec3|vec4|int|bool]",
        "stage": "fragment",
        "default": [default value or array]
      }
    ],
    "input_parameters": [
      {
        "name": "[Parameter display name]",
        "parameter": "[uniform name]",
        "path": "[uniform name]",
        "type": "[float|int|bool]",
        "default": [value],
        "min": [min value],
        "max": [max value],
        "step": [step size],
        "smoothingTime": [0.05-0.5]
      }
    ]
  },
  "tone": {
    "name": "[Audio component name]",
    "description": "[Audio synthesis description]",
    "meta_info": {
      "category": "tone",
      "tags": ["[audio-specific tags]"],
      "complexity": "[simple|medium|high]"
    },
    "synth": {
      "type": "[Tone.Synth|Tone.PolySynth|Tone.MonoSynth|Tone.FMSynth|Tone.AMSynth|Tone.DuoSynth|Tone.MembraneSynth|Tone.MetalSynth|Tone.PluckSynth]",
      "volume": [-60 to 6],
      "detune": [-1200 to 1200],
      "portamento": [0 to 1],
      "envelope": {
        "attack": [0.01 to 2.0],
        "attackCurve": "[linear|exponential|sine|cosine|bounce|ripple|step]",
        "decay": [0.01 to 2.0],
        "decayCurve": "[linear|exponential]",
        "sustain": [0.0 to 1.0],
        "release": [0.01 to 5.0],
        "releaseCurve": "[linear|exponential|sine|cosine|bounce|ripple|step]"
      },
      "oscillator": {
        "type": "[sine|square|triangle|sawtooth|pulse|pwm|fmsine|fmsquare|fmtriangle|fmsawtooth|amsine|amsquare|amtriangle|amsawtooth|fatsine|fatsquare|fattriangle|fatsawtooth]",
        "modulationType": "[sine|square|triangle|sawtooth]",
        "harmonicity": [0 to 4],
        "partials": [],
        "phase": [0 to 360]
      }
    },
    "effects": [
      {
        "type": "[Tone.Reverb|Tone.Delay|Tone.Chorus|Tone.Phaser|Tone.Distortion|Tone.Filter|Tone.EQ3|Tone.Compressor|Tone.Limiter|Tone.Gate|Tone.Tremolo|Tone.Vibrato|Tone.PitchShift|Tone.FreqShift]",
        "options": {
          "[effect-specific parameters]": "[values]"
        },
        "order": [0-10]
      }
    ],
    "patterns": [
      {
        "id": "[pattern_id]",
        "type": "Tone.Pattern",
        "options": {
          "pattern": "[up|down|upDown|downUp|alternateUp|alternateDown|random|randomOnce]",
          "values": ["[note arrays like C4, E4, G4]"],
          "interval": "[timing like 4n, 8n, 16n]",
          "duration": "[note duration]"
        }
      }
    ],
    "parts": [
      {
        "id": "[part_id]",
        "pattern": "[pattern_id]",
        "start": "[0:0:0]",
        "duration": "[bars:beats:sixteenths]",
        "loop": true
      }
    ],
    "input_parameters": [
      {
        "name": "[Parameter name]",
        "parameter": "[path to parameter]",
        "path": "tone.[parameter path]",
        "type": "[float|string]",
        "unit": "[dB|cents|s|Hz|normalRange|curve|type|ratio|degrees]",
        "default": [value],
        "min": [min],
        "max": [max],
        "step": [step],
        "options": ["[for string types]"]
      }
    ]
  },
  "haptic": {
    "name": "[Haptic component name]",
    "description": "[Haptic feedback description]",
    "meta_info": {
      "category": "haptic",
      "tags": ["[haptic-specific tags]"],
      "complexity": "[simple|medium|high]"
    },
    "device": {
      "type": "[generic|actuator|speaker|motor]",
      "options": {
        "maxIntensity": {"value": [0.1-1.0], "unit": "linear"},
        "maxFrequency": {"value": [10-1000], "unit": "Hz"}
      }
    },
    "input_parameters": [
      {
        "name": "[Parameter name]",
        "parameter": "haptic.[parameter]",
        "path": "haptic.[parameter]",
        "type": "float",
        "unit": "[linear|Hz]",
        "default": [value],
        "min": [min],
        "max": [max],
        "step": [step],
        "smoothingTime": [0.05-0.5]
      }
    ]
  },
  "control": {
    "name": "[Control scheme name]",
    "description": "[Control interaction description]",
    "meta_info": {
      "category": "control",
      "tags": ["[control-specific tags]"],
      "complexity": "[simple|medium|high]"
    },
    "control_parameters": [
      {
        "parameter": "[target parameter path]",
        "label": "[Control label]",
        "type": "float",
        "unit": "linear",
        "default": [value],
        "min": [min],
        "max": [max],
        "step": [step],
        "smoothingTime": [timing],
        "mappings": [
          {
            "combo": {
              "mouseButtons": ["[left|right|middle]"],
              "keys": ["[Shift|Ctrl|Alt]"],
              "wheel": [true|false],
              "strict": true
            },
            "action": {
              "axis": "[mouse.x|mouse.y|mouse.wheel]",
              "sensitivity": [sensitivity value],
              "curve": "[linear|exponential|logarithmic]"
            }
          }
        ]
      }
    ]
  },
  "modulations": [
    {
      "id": "[modulation_id]",
      "target": "[parameter path]",
      "type": "[additive|multiplicative|replace]",
      "waveform": "[sine|triangle|square|sawtooth|noise]",
      "frequency": [0.01-10.0],
      "amplitude": [0.01-1.0],
      "offset": [center value],
      "phase": [0.0-1.0],
      "scale": [scaling factor],
      "scaleProfile": "[linear|exponential|logarithmic]",
      "min": [minimum output],
      "max": [maximum output]
    }
  ]
}

SYNESTHETIC EXPLORATION DOMAINS:
- Temporal-Spatial: rhythm patterns → geometric transformations
- Chromatic-Harmonic: color spaces → frequency relationships
- Textural-Timbral: surface qualities → audio texture synthesis
- Kinetic-Melodic: movement dynamics → musical phrase generation
- Luminous-Dynamic: brightness variations → amplitude modulation
- Spatial-Stereo: 3D positioning → audio spatialization

CREATIVE CONSTRAINTS:
- Use evocative, specific names (avoid generic terms like "Circle", "Harmony", "Basic")
- Explore diverse visual primitives: fractals, noise fields, fluid dynamics, particle systems
- Utilize varied synthesis techniques: FM, AM, additive, granular, physical modeling
- Design contextual haptic responses that enhance the synesthetic experience
- Create sophisticated control schemes with multi-modal input mappings
- Implement cross-modal modulations that reveal hidden parameter relationships

AVOID THESE PATTERNS:
- Basic oscillator types without modulation
- Generic naming conventions
- Single-modality focus
- Repetitive parameter ranges
- Static visual patterns

EXAMPLE CANONICAL CONCEPTS:
- "Neuroplastic Crystallization" - synaptic growth patterns with evolving harmonic structures
- "Quantum Tide Mechanics" - probability wave functions with spectral audio synthesis
- "Metamorphic Resonance" - geological transformation with mineral-based timbres
- "Bioluminescent Chorus" - organic light patterns with swarm-based polyphony
- "Architectural Phonemes" - spatial construction with linguistic audio synthesis

Generate a synesthetic asset that establishes a new canonical example of cross-modal interaction. Respond with ONLY the JSON object, no markdown or explanations."""

# Canonical Tone.js DSL system prompt that ensures flattened structure


def build_synesthetic_asset_prompt(concept: str | None = None) -> str:
    """Return the canonical synesthetic asset prompt, optionally focused on a concept."""

    if concept:
        return f"{CANONICAL_SYNESTHETIC_ASSET_PROMPT}\n\nFocus on this synesthetic concept: {concept}"
    return CANONICAL_SYNESTHETIC_ASSET_PROMPT
