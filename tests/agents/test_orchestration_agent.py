import pytest

from tests.agents.orchestration_agent import OrchestrationAgent


@pytest.mark.asyncio
async def test_orchestration_agent_run():
    agent = OrchestrationAgent("SynestheticAsset_Example1.json")
    state = await agent.run(steps=2, dt=0.1)
    assert isinstance(state, dict)
    assert "shader.u_r" in state
