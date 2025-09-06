"""
Tests for the GenericAssetAgent that can handle any synesthetic asset structure.
"""

import pytest
from tests.agents.generic_asset_agent import GenericAssetAgent


@pytest.mark.asyncio
async def test_generic_agent_example7():
    """Test generic agent with Example7."""
    agent = GenericAssetAgent("SynestheticAsset_Example7.json")
    await agent.start()

    assert agent.config_agent.asset is not None
    # Example7 has embedded components with rich structure, so it should be nested
    assert agent.asset_structure == "nested"

    results = await agent.run_full_diagnostic()
    assert isinstance(results, dict)
    assert "asset_structure" in results
    assert results["asset_structure"] == "nested"

    await agent.stop()


@pytest.mark.asyncio
async def test_generic_agent_example1():
    """Test generic agent with Example1."""
    agent = GenericAssetAgent("SynestheticAsset_Example1.json")
    await agent.start()

    assert agent.config_agent.asset is not None

    results = await agent.run_full_diagnostic()
    assert isinstance(results, dict)
    assert "overall_status" in results

    await agent.stop()


@pytest.mark.asyncio
async def test_generic_agent_detects_structure():
    """Test that generic agent correctly detects asset structure."""
    agent = GenericAssetAgent("SynestheticAsset_Example7.json")
    await agent.start()

    # Example7 has embedded components with rich structure, so it should be nested
    assert agent.asset_structure in ["nested", "mixed"]

    await agent.stop()


@pytest.mark.asyncio
async def test_generic_agent_validation_categories():
    """Test that generic agent runs all validation categories."""
    agent = GenericAssetAgent("SynestheticAsset_Example7.json")
    await agent.start()

    results = await agent.run_full_diagnostic()

    # Should have core validation results
    assert "shader_validation" in results
    assert "asset_structure" in results
    assert "total_issues" in results
    assert "overall_status" in results

    # Should have structure-specific validations
    if results["asset_structure"] == "flat":
        assert "flat_validation" in results
    elif results["asset_structure"] == "nested":
        assert "nested_validation" in results
        assert "cross_asset_modulation_validation" in results

    await agent.stop()


@pytest.mark.asyncio
async def test_generic_agent_issue_tracking():
    """Test that generic agent properly tracks and categorizes issues."""
    agent = GenericAssetAgent("SynestheticAsset_Example7.json")
    await agent.start()

    results = await agent.run_full_diagnostic()

    # Should track issues properly
    assert "total_issues" in results
    assert "issues_by_severity" in results
    assert "all_issues" in results

    # If there are issues, they should be properly categorized
    if results["total_issues"] > 0:
        assert len(results["all_issues"]) == results["total_issues"]

        for issue in results["all_issues"]:
            assert "category" in issue
            assert "severity" in issue
            assert "message" in issue
            assert "location" in issue

    await agent.stop()
