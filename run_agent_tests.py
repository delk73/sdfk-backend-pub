#!/usr/bin/env python3
"""
Standalone Python script to run agent tests for all examples.
This avoids shell complexity and provides better error isolation.
"""

from tests.agents.config_agent import ConfigAgent
from tests.agents.orchestration_agent import OrchestrationAgent
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Tuple

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class ExampleTester:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.results = {"passed": 0, "warnings": 0, "failed": 0, "details": []}

    async def test_example(self, example_file: str) -> Tuple[str, str]:
        """Test a single example file. Returns (status, details)."""
        try:
            print(f"🔧 Loading configuration for {example_file}...")
            config_agent = ConfigAgent(example_file)
            await config_agent.start()

            if not config_agent.asset:
                return "error", "❌ Failed to load asset configuration"

            asset = config_agent.asset
            details = [
                f"✅ Loaded: {asset.name}",
                f"📋 Description: {asset.description}",
            ]

            # Basic validation checks
            validation_issues = []

            # Check shader configuration
            if hasattr(asset, "shader") and asset.shader:
                if (
                    hasattr(asset.shader, "fragment_shader")
                    and asset.shader.fragment_shader
                ):
                    details.append("✅ Shader fragment code present")
                else:
                    validation_issues.append("Missing shader fragment code")
            else:
                details.append("ℹ️  No shader configuration")

            # Check control parameters
            if hasattr(asset, "control_parameters") and asset.control_parameters:
                param_count = len(asset.control_parameters)
                details.append(f"✅ Found {param_count} control parameters")

                # Check for duplicate parameter names
                param_names = []
                for param in asset.control_parameters:
                    if hasattr(param, "parameter"):
                        param_names.append(param.parameter)
                    elif isinstance(param, dict):
                        param_names.append(param.get("parameter", "unknown"))

                duplicates = [
                    name for name in param_names if param_names.count(name) > 1
                ]
                if duplicates:
                    validation_issues.append(f"Duplicate parameters: {duplicates}")
            else:
                details.append("⚠️  No control parameters defined")

            # Check modulations
            if hasattr(asset, "modulations") and asset.modulations:
                mod_count = len(asset.modulations)
                details.append(f"✅ Found {mod_count} modulations")
            else:
                details.append("ℹ️  No modulations defined")

            # Run orchestration test only for synesthetic assets
            if example_file.startswith("SynestheticAsset_"):
                details.append("🎭 Running orchestration simulation...")
                orchestration_agent = OrchestrationAgent(example_file)
                final_state = await orchestration_agent.run(steps=3, dt=0.1)

                details.append(
                    f"✅ Simulation completed with {len(final_state)} state variables"
                )
                if final_state:
                    state_keys = list(final_state.keys())
                    details.append(f"📊 Final state keys: {state_keys}")
            else:
                details.append("ℹ️  Skipping orchestration (not a synesthetic asset)")

            await config_agent.stop()

            # Report validation issues
            if validation_issues:
                details.append("⚠️  Validation warnings:")
                for issue in validation_issues:
                    details.append(f"   - {issue}")
                return "warning", "\n".join(details)
            else:
                details.append("✅ All validations passed")
                return "success", "\n".join(details)

        except Exception as e:
            error_detail = f"❌ Test failed: {e}"
            if self.debug_mode:
                import traceback

                error_detail += f"\n{traceback.format_exc()}"
            return "error", error_detail

    async def run_all_tests(self) -> Dict:
        """Run tests for all example files."""
        examples_dir = Path("app/examples")
        example_files = [
            f.name for f in examples_dir.glob("*.json") if "hold" not in f.name
        ]
        example_files.sort()

        print(f"🔍 Testing {len(example_files)} examples with generic agent system...")
        print("Found examples to test:")
        for example_file in example_files:
            print(f"  • {example_file}")

        print("\nStarting agent tests...")

        for example_file in example_files:
            print(f"\n🧪 Testing: {example_file}")

            status, details = await self.test_example(example_file)

            # Update counters
            if status == "success":
                print("  ✅ PASSED")
                self.results["passed"] += 1
            elif status == "warning":
                print("  ⚠️  PASSED WITH WARNINGS")
                self.results["warnings"] += 1
            else:
                print("  ❌ FAILED")
                self.results["failed"] += 1

            # Store details
            self.results["details"].append(
                {"file": example_file, "status": status, "details": details}
            )

            # Show details if debug mode or failed
            if self.debug_mode or status == "error":
                print(f"Details for {example_file}:")
                for line in details.split("\n"):
                    print(f"    {line}")

        return self.results

    def print_summary(self):
        """Print test summary."""
        total = (
            self.results["passed"] + self.results["warnings"] + self.results["failed"]
        )

        print("\n📊 AGENT TEST SUMMARY")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"⚠️  Warnings: {self.results['warnings']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📝 Total: {total}")

        if self.results["failed"] > 0:
            print("\n⚠️  Some examples failed testing.")
            print("Failed examples:")
            for result in self.results["details"]:
                if result["status"] == "error":
                    print(f"  • {result['file']}")


async def main():
    """Main entry point."""
    debug_mode = "--debug" in sys.argv or os.getenv("AGENTS_DEBUG") == "true"

    print("🤖 Running Agent-Based Example Diagnostics")
    print("=" * 50)

    tester = ExampleTester(debug_mode=debug_mode)

    try:
        results = await tester.run_all_tests()
        tester.print_summary()

        # Exit with appropriate code
        if results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if debug_mode:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
