"""
Quick test runner for Example7 agent testing.
Use this for fast iteration on Example7 debugging.
"""

import asyncio
import logging

from .example7_agent import Example7Agent

logger = logging.getLogger(__name__)


async def quick_test_example7():
    """Quick test function for Example7."""
    agent = Example7Agent(debug_mode=True)

    await agent.start()
    results = await agent.run_full_diagnostic()
    await agent.stop()

    return results


def print_summary(results):
    """Log a concise summary of test results."""
    status = results["overall_status"]
    issues = results["total_issues"]

    status_emoji = "✅" if status == "success" else "⚠️" if status == "warning" else "❌"

    logger.info("%s Example7 Status: %s", status_emoji, status.upper())
    logger.info("📊 Total Issues: %s", issues)

    if issues > 0:
        logger.info("🔍 Issue Categories:")
        for issue in results["all_issues"]:
            logger.info("  • %s: %s", issue["category"], issue["message"])


if __name__ == "__main__":
    # For direct running in the agents directory
    logging.basicConfig(level=logging.INFO)
    results = asyncio.run(quick_test_example7())
    print_summary(results)
