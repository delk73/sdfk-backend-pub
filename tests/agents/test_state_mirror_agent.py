import pytest

from tests.agents.state_mirror_agent import StateMirrorAgent


@pytest.mark.asyncio
async def test_state_mirror_update_broadcast():
    agent = StateMirrorAgent()
    await agent.start({"value": 0})

    captured = []
    agent.subscribe(lambda s: captured.append(s.copy()))

    agent.update("value", 1)
    assert agent.state["value"] == 1
    assert captured[-1]["value"] == 1
    await agent.stop()
