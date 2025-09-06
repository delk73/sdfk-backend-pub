"""Agent that applies LFO-style modulations to state values."""

from __future__ import annotations

import math
from typing import Dict

from .base_agent import BaseAgent
from .state_mirror_agent import StateMirrorAgent


class ModulationAgent(BaseAgent):
    """Apply sinusoidal modulation to parameters in a state mirror."""

    def __init__(self, mirror: StateMirrorAgent) -> None:
        super().__init__()
        self.mirror = mirror
        self.config: Dict[str, Dict[str, float]] = {}
        self.time = 0.0

    def configure(self, config: Dict[str, Dict[str, float]]) -> None:
        """Set modulation configuration."""
        self.config = config

    async def step(self, dt: float = 1.0) -> None:
        if not self.running:
            return
        self.time += dt
        for param, opts in self.config.items():
            freq = opts.get("frequency", 1.0)
            amp = opts.get("amplitude", 1.0)
            offset = opts.get("offset", 0.0)
            value = offset + amp * math.sin(2 * math.pi * freq * self.time)
            self.mirror.update(param, value)
