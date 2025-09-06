"""
Generic agent for testing and debugging any SynestheticAsset example.
This agent can handle both flat and nested asset structures.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from .config_agent import ConfigAgent
from .state_mirror_agent import StateMirrorAgent
from .modulation_agent import ModulationAgent

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue found in the asset."""

    category: str
    severity: str  # "error", "warning", "info"
    message: str
    location: str
    details: Optional[Dict[str, Any]] = None


class GenericAssetAgent(BaseAgent):
    """
    Generic agent for comprehensive testing of any synesthetic asset.
    Designed to catch issues in both flat and nested asset structures.
    """

    def __init__(self, example_filename: str, debug_mode: bool = True):
        super().__init__()
        self.example_filename = example_filename
        self.debug_mode = debug_mode
        self.config_agent = ConfigAgent(example_filename)
        self.state_mirror = StateMirrorAgent()
        self.modulation_agent = ModulationAgent(self.state_mirror)
        self.validation_issues: List[ValidationIssue] = []
        self.test_results: Dict[str, Any] = {}
        self.asset_structure = "unknown"  # "flat", "nested", "mixed"

    async def start(self) -> None:
        """Initialize the agent and load the asset configuration."""
        await super().start()
        await self.config_agent.start()

        if self.debug_mode and self.config_agent.asset:
            logger.debug("Loaded Asset: %s", self.config_agent.asset.name)
            logger.debug("Categories: %s", self.config_agent.asset.meta_info)
            self._detect_asset_structure()

    async def stop(self) -> None:
        """Clean up agent resources."""
        await self.config_agent.stop()
        await super().stop()

    def _detect_asset_structure(self) -> None:
        """Detect if the asset has flat or nested structure."""
        asset = self.config_agent.asset
        if not asset:
            return

        # Check for nested structures - multiple patterns:
        # 1. Assets array (collection-style nested)
        has_nested_assets = hasattr(asset, "assets") and asset.assets

        # 2. Embedded components (canonical nested style)
        has_embedded_components = False
        component_count = 0

        if hasattr(asset, "shader") and asset.shader:
            # Check if shader has nested structure (input_parameters, uniforms, etc.)
            shader = asset.shader
            if hasattr(shader, "input_parameters") or hasattr(shader, "uniforms"):
                has_embedded_components = True
                component_count += 1

        if hasattr(asset, "tone") and asset.tone:
            # Check if tone has nested structure (synth, effects, patterns, etc.)
            tone = asset.tone
            if (
                hasattr(tone, "synth")
                or hasattr(tone, "effects")
                or hasattr(tone, "input_parameters")
            ):
                has_embedded_components = True
                component_count += 1

        if hasattr(asset, "haptic") and asset.haptic:
            # Check if haptic has nested structure
            haptic = asset.haptic
            if hasattr(haptic, "device") or hasattr(haptic, "input_parameters"):
                has_embedded_components = True
                component_count += 1

        if hasattr(asset, "control") and asset.control:
            # Check if control has nested structure
            control = asset.control
            if hasattr(control, "control_parameters"):
                has_embedded_components = True
                component_count += 1

        # Determine structure type
        if has_nested_assets and has_embedded_components:
            self.asset_structure = "mixed"
        elif has_nested_assets:
            self.asset_structure = "nested"
        elif has_embedded_components and component_count >= 2:
            # Canonical nested: multiple embedded components with rich structure
            self.asset_structure = "nested"
        elif has_embedded_components:
            self.asset_structure = "flat"
        else:
            self.asset_structure = "empty"

        if self.debug_mode:
            logger.debug("Asset Structure: %s", self.asset_structure)
            if has_nested_assets:
                logger.debug("Nested Assets Count: %d", len(asset.assets))
            if has_embedded_components:
                logger.debug("Embedded Components Count: %d", component_count)

    def add_issue(
        self,
        category: str,
        severity: str,
        message: str,
        location: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a validation issue to the collection."""
        issue = ValidationIssue(category, severity, message, location, details)
        self.validation_issues.append(issue)

        if self.debug_mode:
            logger.debug(
                "[%s] %s in %s: %s",
                severity.upper(),
                category,
                location,
                message,
            )
            if details:
                logger.debug("  Details: %s", details)

    def _get_component_targets(
        self, component_data: Any, component_name: str, asset_prefix: str = ""
    ) -> set:
        """Extract valid parameter targets from a component."""
        valid_targets = set()

        if not component_data:
            return valid_targets

        # Handle both dict and Pydantic model access
        if hasattr(component_data, "input_parameters"):
            input_params = component_data.input_parameters or []
        elif (
            hasattr(component_data, "__dict__")
            and "input_parameters" in component_data.__dict__
        ):
            input_params = component_data.__dict__.get("input_parameters", [])
        elif isinstance(component_data, dict):
            input_params = component_data.get("input_parameters", [])
        else:
            # Try to access as attribute first, then as dict
            try:
                input_params = getattr(component_data, "input_parameters", [])
            except AttributeError:
                try:
                    input_params = component_data.get("input_parameters", [])
                except (AttributeError, TypeError):
                    input_params = []

        for param in input_params:
            # Handle both Pydantic objects and dicts
            if hasattr(param, "path"):
                param_path = param.path
                param_name = getattr(param, "parameter", None)
            elif hasattr(param, "parameter"):
                param_name = param.parameter
                param_path = getattr(param, "path", param_name)
            elif isinstance(param, dict):
                param_path = param.get("path")
                param_name = param.get("parameter")
            else:
                # Try attribute access
                try:
                    param_path = getattr(param, "path", None)
                    param_name = getattr(param, "parameter", None)
                except AttributeError:
                    continue

            if param_path:
                # Add asset prefix for nested structures
                if asset_prefix:
                    param_path = f"{asset_prefix}.{param_path}"

                # Add the direct parameter path (e.g., "u_r")
                valid_targets.add(param_path)

                # Also add the component-prefixed version (e.g., "shader.u_r")
                # This supports both path-based and component.parameter-based targeting
                if param_name and not param_path.startswith(f"{component_name}."):
                    prefixed_target = f"{component_name}.{param_name}"
                    if asset_prefix:
                        prefixed_target = f"{asset_prefix}.{prefixed_target}"
                    valid_targets.add(prefixed_target)

        return valid_targets

    async def validate_nested_structure(self) -> Dict[str, Any]:
        """Validate nested asset structure and relationships."""
        results = {"status": "success", "issues": []}
        asset = self.config_agent.asset

        if not asset or self.asset_structure not in ["nested", "mixed"]:
            return results

        # Handle collection-style nested assets (assets array)
        if hasattr(asset, "assets") and asset.assets:
            await self._validate_collection_nested_structure(asset, results)

        # Handle canonical nested structure (embedded components)
        await self._validate_canonical_nested_structure(asset, results)

        return results

    async def _validate_collection_nested_structure(
        self, asset: Any, results: Dict[str, Any]
    ) -> None:
        """Validate collection-style nested assets (assets array)."""
        if not hasattr(asset, "assets") or not asset.assets:
            return

        # Validate each nested asset
        for i, nested_asset in enumerate(asset.assets):
            nested_name = (
                nested_asset.name if hasattr(nested_asset, "name") else f"asset_{i}"
            )

            # Check for required components in nested assets
            has_shader = (
                nested_asset.shader if hasattr(nested_asset, "shader") else False
            )
            has_tone = nested_asset.tone if hasattr(nested_asset, "tone") else False
            has_haptic = (
                nested_asset.haptic if hasattr(nested_asset, "haptic") else False
            )

            if not any([has_shader, has_tone, has_haptic]):
                self.add_issue(
                    "structure",
                    "warning",
                    f"Nested asset '{nested_name}' has no components",
                    f"assets[{i}]",
                    {"asset_name": nested_name},
                )
                results["issues"].append("empty_nested_asset")

    async def _validate_canonical_nested_structure(
        self, asset: Any, results: Dict[str, Any]
    ) -> None:
        """Validate canonical nested structure (embedded components)."""
        component_validations = []

        # Validate embedded shader
        if hasattr(asset, "shader") and asset.shader:
            shader_issues = await self._validate_embedded_shader(asset.shader)
            component_validations.extend(shader_issues)

        # Validate embedded tone
        if hasattr(asset, "tone") and asset.tone:
            tone_issues = await self._validate_embedded_tone(asset.tone)
            component_validations.extend(tone_issues)

        # Validate embedded haptic
        if hasattr(asset, "haptic") and asset.haptic:
            haptic_issues = await self._validate_embedded_haptic(asset.haptic)
            component_validations.extend(haptic_issues)

        # Validate embedded control
        if hasattr(asset, "control") and asset.control:
            control_issues = await self._validate_embedded_control(asset.control)
            component_validations.extend(control_issues)

        # Check for cross-component parameter consistency
        await self._validate_cross_component_consistency(asset, results)

        if component_validations:
            results["issues"].extend(component_validations)
            results["status"] = "warning"

    async def _validate_embedded_shader(self, shader: Any) -> List[str]:
        """Validate embedded shader component."""
        issues = []

        # Check for required shader fields
        if not hasattr(shader, "fragment_shader") or not shader.fragment_shader:
            self.add_issue(
                "structure",
                "error",
                "Embedded shader missing fragment_shader",
                "shader.fragment_shader",
            )
            issues.append("missing_fragment_shader")

        # Check parameter consistency
        if hasattr(shader, "uniforms") and hasattr(shader, "input_parameters"):
            uniform_names = set()
            if shader.uniforms:
                for uniform in shader.uniforms:
                    name = (
                        uniform.name
                        if hasattr(uniform, "name")
                        else uniform.get("name")
                    )
                    if name:
                        uniform_names.add(name)

            if shader.input_parameters:
                for param in shader.input_parameters:
                    param_name = (
                        param.parameter
                        if hasattr(param, "parameter")
                        else param.get("parameter")
                    )
                    if param_name and param_name not in uniform_names:
                        self.add_issue(
                            "structure",
                            "warning",
                            f"Shader input parameter '{param_name}' has no corresponding uniform",
                            f"shader.input_parameters.{param_name}",
                        )
                        issues.append("orphaned_input_parameter")

        return issues

    async def _validate_embedded_tone(self, tone: Any) -> List[str]:
        """Validate embedded tone component."""
        issues = []

        # Check for synth configuration
        if not hasattr(tone, "synth") or not tone.synth:
            self.add_issue(
                "structure",
                "warning",
                "Embedded tone missing synth configuration",
                "tone.synth",
            )
            issues.append("missing_synth")

        return issues

    async def _validate_embedded_haptic(self, haptic: Any) -> List[str]:
        """Validate embedded haptic component."""
        issues = []

        # Check for device configuration
        if not hasattr(haptic, "device") or not haptic.device:
            self.add_issue(
                "structure",
                "warning",
                "Embedded haptic missing device configuration",
                "haptic.device",
            )
            issues.append("missing_device")

        return issues

    async def _validate_embedded_control(self, control: Any) -> List[str]:
        """Validate embedded control component."""
        issues = []

        # Check for control parameters
        if not hasattr(control, "control_parameters") or not control.control_parameters:
            self.add_issue(
                "structure",
                "warning",
                "Embedded control missing control_parameters",
                "control.control_parameters",
            )
            issues.append("missing_control_parameters")

        return issues

    async def _validate_cross_component_consistency(
        self, asset: Any, results: Dict[str, Any]
    ) -> None:
        """Validate consistency across embedded components."""
        # Check that modulation targets match available parameters
        if hasattr(asset, "modulations") and asset.modulations:
            valid_targets = set()

            # Collect all valid targets from embedded components
            for component_name in [
                "shader",
                "tone",
                "haptic",
                "control",
            ]:
                comp_data = getattr(asset, component_name, None)
                if comp_data:
                    targets = self._get_component_targets(comp_data, component_name)
                    valid_targets.update(targets)

            # Validate modulation targets
            for mod in asset.modulations:
                mod_target = mod.target if hasattr(mod, "target") else mod.get("target")
                mod_id = mod.id if hasattr(mod, "id") else mod.get("id")

                if mod_target and mod_target not in valid_targets:
                    self.add_issue(
                        "modulation",
                        "error",
                        f"Canonical nested modulation target '{mod_target}' does not exist",
                        f"modulations[{mod_id}]",
                        {
                            "target": mod_target,
                            "available_targets": sorted(list(valid_targets)),
                        },
                    )
                    results["issues"].append("invalid_canonical_modulation_target")
                    results["status"] = "error"

    async def validate_cross_asset_modulations(self) -> Dict[str, Any]:
        """Validate modulations that reference across nested assets."""
        results = {"status": "success", "issues": []}
        asset = self.config_agent.asset

        if not asset or self.asset_structure != "nested":
            return results

        # Build comprehensive target registry for nested structure
        all_valid_targets = set()

        # Add targets from root level
        for component_name in ["shader", "tone", "haptic"]:
            comp_data = getattr(asset, component_name, None)
            if comp_data:
                targets = self._get_component_targets(comp_data, component_name)
                all_valid_targets.update(targets)

        # Add targets from nested assets
        if hasattr(asset, "assets") and asset.assets:
            for i, nested_asset in enumerate(asset.assets):
                asset_name = (
                    nested_asset.name if hasattr(nested_asset, "name") else f"asset_{i}"
                )

                for component_name in ["shader", "tone", "haptic"]:
                    comp_data = getattr(nested_asset, component_name, None)
                    if comp_data:
                        targets = self._get_component_targets(
                            comp_data, component_name, asset_name
                        )
                        all_valid_targets.update(targets)

        # Check modulations at root level
        if asset.modulations:
            modulations = (
                asset.modulations
                if hasattr(asset, "modulations")
                else asset.get("modulations", [])
            )

            for mod in modulations:
                mod_target = mod.target if hasattr(mod, "target") else mod.get("target")
                mod_id = mod.id if hasattr(mod, "id") else mod.get("id")

                if mod_target and mod_target not in all_valid_targets:
                    self.add_issue(
                        "modulation",
                        "error",
                        f"Cross-asset modulation target '{mod_target}' does not exist",
                        f"modulations[{mod_id}]",
                        {
                            "target": mod_target,
                            "available_targets": sorted(list(all_valid_targets)),
                        },
                    )
                    results["issues"].append("invalid_cross_asset_target")
                    results["status"] = "error"

        # Check modulations in nested assets
        if hasattr(asset, "assets") and asset.assets:
            for i, nested_asset in enumerate(asset.assets):
                asset_name = (
                    nested_asset.name if hasattr(nested_asset, "name") else f"asset_{i}"
                )

                if hasattr(nested_asset, "modulations") and nested_asset.modulations:
                    for mod in nested_asset.modulations:
                        mod_target = (
                            mod.target if hasattr(mod, "target") else mod.get("target")
                        )
                        mod_id = mod.id if hasattr(mod, "id") else mod.get("id")

                        if mod_target and mod_target not in all_valid_targets:
                            self.add_issue(
                                "modulation",
                                "error",
                                f"Nested asset '{asset_name}' modulation target '{mod_target}' does not exist",
                                f"assets[{i}].modulations[{mod_id}]",
                                {
                                    "target": mod_target,
                                    "asset": asset_name,
                                    "available_targets": sorted(
                                        list(all_valid_targets)
                                    ),
                                },
                            )
                            results["issues"].append("invalid_nested_modulation_target")
                            results["status"] = "error"

        return results

    async def validate_flat_structure(self) -> Dict[str, Any]:
        """Validate flat asset structure (single-level components)."""
        results = {"status": "success", "issues": []}
        asset = self.config_agent.asset

        if not asset or self.asset_structure not in ["flat", "mixed"]:
            return results

        # Build target registry for flat structure
        valid_targets = set()

        for component_name in ["shader", "tone", "haptic"]:
            comp_data = getattr(asset, component_name, None)
            if comp_data:
                targets = self._get_component_targets(comp_data, component_name)
                valid_targets.update(targets)

        # Check modulations
        if asset.modulations:
            modulations = (
                asset.modulations
                if hasattr(asset, "modulations")
                else asset.get("modulations", [])
            )

            for mod in modulations:
                mod_target = mod.target if hasattr(mod, "target") else mod.get("target")
                mod_id = mod.id if hasattr(mod, "id") else mod.get("id")

                if mod_target and mod_target not in valid_targets:
                    self.add_issue(
                        "modulation",
                        "error",
                        f"Modulation target '{mod_target}' does not exist",
                        f"modulations[{mod_id}]",
                        {
                            "target": mod_target,
                            "available_targets": sorted(list(valid_targets)),
                        },
                    )
                    results["issues"].append("invalid_flat_target")
                    results["status"] = "error"

        return results

    async def validate_shader_consistency(self) -> Dict[str, Any]:
        """Validate shader parameter consistency across all assets."""
        results = {"status": "success", "issues_found": []}
        asset = self.config_agent.asset

        if not asset:
            return results

        # Check root level shader
        if asset.shader:
            shader_results = await self._validate_single_shader(asset.shader, "root")
            results["issues_found"].extend(shader_results.get("issues_found", []))
            if shader_results["status"] != "success":
                results["status"] = "error"

        # Check nested asset shaders
        if self.asset_structure in ["nested", "mixed"] and hasattr(asset, "assets"):
            for i, nested_asset in enumerate(asset.assets):
                asset_name = (
                    nested_asset.name if hasattr(nested_asset, "name") else f"asset_{i}"
                )

                if hasattr(nested_asset, "shader") and nested_asset.shader:
                    shader_results = await self._validate_single_shader(
                        nested_asset.shader, f"assets[{i}]({asset_name})"
                    )
                    results["issues_found"].extend(
                        shader_results.get("issues_found", [])
                    )
                    if shader_results["status"] != "success":
                        results["status"] = "error"

        return results

    async def _validate_single_shader(
        self, shader: Any, location: str
    ) -> Dict[str, Any]:
        """Validate a single shader component."""
        results = {"status": "success", "issues_found": []}

        # Handle both dict and Pydantic model access
        if hasattr(shader, "uniforms"):
            uniforms_list = shader.uniforms or []
            input_params_list = shader.input_parameters or []
        else:
            uniforms_list = shader.get("uniforms", [])
            input_params_list = shader.get("input_parameters", [])

        # Convert to dict format for processing
        uniforms = {}
        for u in uniforms_list:
            name = u.name if hasattr(u, "name") else u.get("name")
            uniforms[name] = u

        # Check for parameter/uniform mismatches
        for param in input_params_list:
            param_name = (
                param.parameter
                if hasattr(param, "parameter")
                else param.get("parameter")
            )
            param_display_name = (
                param.name if hasattr(param, "name") else param.get("name")
            )

            if param_name and param_name not in uniforms:
                self.add_issue(
                    "shader",
                    "error",
                    f"Input parameter '{param_name}' has no corresponding uniform",
                    f"{location}.shader.input_parameters[{param_display_name}]",
                    {"parameter": param_name, "location": location},
                )
                results["issues_found"].append("missing_uniform")
                results["status"] = "error"

        return results

    async def run_full_diagnostic(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic tests on the asset."""
        logger.debug("=== %s Agent Diagnostic Starting ===", self.example_filename)

        # Clear previous results
        self.validation_issues.clear()

        diagnostics = {
            "example_filename": self.example_filename,
            "asset_loaded": self.config_agent.asset is not None,
            "asset_structure": self.asset_structure,
            "shader_validation": await self.validate_shader_consistency(),
            "total_issues": 0,
            "issues_by_severity": {},
            "all_issues": [],
        }

        # Structure-specific validations
        if self.asset_structure == "flat":
            diagnostics["flat_validation"] = await self.validate_flat_structure()
        elif self.asset_structure == "nested":
            diagnostics["nested_validation"] = await self.validate_nested_structure()
            diagnostics["cross_asset_modulation_validation"] = (
                await self.validate_cross_asset_modulations()
            )
        elif self.asset_structure == "mixed":
            diagnostics["flat_validation"] = await self.validate_flat_structure()
            diagnostics["nested_validation"] = await self.validate_nested_structure()
            diagnostics["cross_asset_modulation_validation"] = (
                await self.validate_cross_asset_modulations()
            )

        # Update totals
        diagnostics["total_issues"] = len(self.validation_issues)

        # Categorize issues by severity
        for issue in self.validation_issues:
            severity = issue.severity
            if severity not in diagnostics["issues_by_severity"]:
                diagnostics["issues_by_severity"][severity] = 0
            diagnostics["issues_by_severity"][severity] += 1

            diagnostics["all_issues"].append(
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "message": issue.message,
                    "location": issue.location,
                    "details": issue.details,
                }
            )

        # Overall status
        error_count = diagnostics["issues_by_severity"].get("error", 0)
        warning_count = diagnostics["issues_by_severity"].get("warning", 0)

        if error_count > 0:
            diagnostics["overall_status"] = "error"
        elif warning_count > 0:
            diagnostics["overall_status"] = "warning"
        else:
            diagnostics["overall_status"] = "success"

        logger.debug(
            "=== Diagnostic Complete: %s ===",
            diagnostics["overall_status"].upper(),
        )
        logger.debug(
            "Structure: %s, Issues: %d errors, %d warnings",
            self.asset_structure,
            error_count,
            warning_count,
        )

        return diagnostics
