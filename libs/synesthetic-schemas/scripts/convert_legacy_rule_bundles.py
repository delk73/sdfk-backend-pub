#!/usr/bin/env python
# ruff: noqa
from __future__ import annotations
import json, pathlib, argparse
from typing import Any, Dict

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"

def loadj(p: pathlib.Path) -> Dict[str, Any]:
    return json.loads(p.read_text())

def savej(p: pathlib.Path, data: Dict[str, Any]) -> None:
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

def is_legacy(rb: Any) -> bool:
    return isinstance(rb, dict) and "rules" not in rb and ("type" in rb or "gridSize" in rb)

def convert(rb: Dict[str, Any]) -> Dict[str, Any]:
    name = rb.get("name", "SDF Grid Rules")
    grid = rb.get("gridSize", 8)
    cooldown = rb.get("cooldown", 100)
    threshold = rb.get("threshold", [0.02, 0.02, 0.02, 0.02])
    scale = rb.get("scale", [1.0, 1.0, 1.0, 1.0])
    curve = rb.get("curve", ["linear", "exp", "sigmoid", "linear"])
    groups = rb.get("groups", {})
    g_audio = groups.get("audioTrigger", {})
    g_haptic = groups.get("hapticPulse", {})
    g_visual = groups.get("visualNudge", {})

    return {
      "name": name,
      "description": "Auto-converted from legacy sdfGrid bundle.",
      "meta_info": {
        "category": "rule_bundle",
        "tags": ["grid", "interaction", "multimodal", "mapping"],
        "complexity": "high"
      },
      "rules": [
        {
          "id": "grid_to_multimodal_mapping",
          "trigger": {"type": "grid_cell", "params": {"gridSize": grid, "cooldown": cooldown}},
          "execution": "client",
          "effects": [
            {
              "channel": "audioTrigger",
              "target": g_audio.get("parameter", "audio.poly.trigger"),
              "op": "triggerAttackRelease",
              "value": {
                "note": "<grid.note>",
                "duration": g_audio.get("duration", "8n"),
                "velocity": {
                  "source": "grid.pressure",
                  "scale": (scale[0] if isinstance(scale, list) and scale else 1.0),
                  "curve": (curve[0] if isinstance(curve, list) and curve else "linear"),
                  "threshold": (threshold[0] if isinstance(threshold, list) and threshold else 0.02),
                },
              },
            },
            {
              "channel": "hapticPulse",
              "target": g_haptic.get("parameter", "haptic.intensity"),
              "op": "set",
              "value": {"source": "grid.pressure", "scale": (scale[1] if isinstance(scale, list) and len(scale)>1 else 1.0)},
            },
            {
              "channel": "visualNudge",
              "target": g_visual.get("parameter", "shader.u_r"),
              "op": "add",
              "value": {"source": "grid.pressure", "scale": g_visual.get("offset", 0.1)},
            },
          ],
        }
      ],
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    changed = 0
    for p in sorted(EXAMPLES.rglob("*.json")):
        try:
            data = loadj(p)
        except Exception:
            continue
        rb = data.get("rule_bundle")
        if is_legacy(rb):
            new_rb = convert(rb)  # build new bundle
            if args.write:
                data["rule_bundle"] = new_rb
                savej(p, data)
                print(f"converted: {p.name}")
            else:
                print(f"[DRY] would convert: {p.name}")
            changed += 1
    print(f"{'converted' if args.write else 'would convert'} {changed} file(s).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
