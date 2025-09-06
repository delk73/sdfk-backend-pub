import pytest

from tests.agents.config_agent import ConfigAgent
from app.schemas.synesthetic_asset import NestedSynestheticAssetCreate


@pytest.mark.asyncio
async def test_config_agent_load():
    agent = ConfigAgent("SynestheticAsset_Example1.json")
    await agent.start()
    assert isinstance(agent.asset, NestedSynestheticAssetCreate)
    assert agent.asset.name == "Circle Harmony2"
    await agent.stop()
