import pytest

from tests.agents.base_agent import BaseAgent


@pytest.mark.asyncio
async def test_base_agent_start_stop():
    agent = BaseAgent()
    await agent.start()
    assert agent.running
    await agent.stop()
    assert not agent.running
