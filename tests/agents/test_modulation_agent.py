import math
import pytest

from tests.agents.state_mirror_agent import StateMirrorAgent
from tests.agents.modulation_agent import ModulationAgent


@pytest.mark.asyncio
async def test_modulation_agent_step():
    mirror = StateMirrorAgent()
    await mirror.start({"x": 0.0})
    agent = ModulationAgent(mirror)
    agent.configure({"x": {"frequency": 1.0, "amplitude": 1.0, "offset": 0.0}})
    await agent.start()
    await agent.step(dt=0)
    assert math.isclose(mirror.state["x"], 0.0, abs_tol=1e-6)
    await agent.step(dt=0.25)  # quarter period
    assert pytest.approx(1.0, rel=1e-2) == mirror.state["x"]
    await agent.stop()
