"""Agent that orchestrates configuration, state mirroring and modulation."""

from __future__ import annotations

from typing import Dict

from .base_agent import BaseAgent
from .config_agent import ConfigAgent
from .state_mirror_agent import StateMirrorAgent
from .modulation_agent import ModulationAgent


class OrchestrationAgent(BaseAgent):
    """Compose agents to simulate a full lifecycle."""

    def __init__(self, example_file: str) -> None:
        super().__init__()
        self.config_agent = ConfigAgent(example_file)
        self.state_mirror = StateMirrorAgent()
        self.modulation_agent = ModulationAgent(self.state_mirror)

    async def run(self, steps: int = 3, dt: float = 1.0) -> Dict[str, float]:
        """Run the orchestration for a fixed number of steps."""
        await self.config_agent.start()
        asset = self.config_agent.asset

        initial_state: Dict[str, float] = {}
        if asset and asset.control_parameters:
            for param in asset.control_parameters:
                key = param.get("parameter")
                initial_state[key] = param.get("default", 0.0)
        await self.state_mirror.start(initial_state)

        mods: Dict[str, Dict[str, float]] = {}
        if asset and asset.modulations:
            for m in asset.modulations:
                mods[m["target"]] = {
                    "frequency": m.get("frequency", 1.0),
                    "amplitude": m.get("amplitude", 1.0),
                    "offset": m.get("offset", 0.0),
                }
        self.modulation_agent.configure(mods)
        await self.modulation_agent.start()

        for _ in range(steps):
            await self.modulation_agent.step(dt)

        await self.modulation_agent.stop()
        await self.state_mirror.stop()
        await self.config_agent.stop()

        return self.state_mirror.state
