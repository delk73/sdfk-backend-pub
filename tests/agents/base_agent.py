"""Base class for agent simulations."""

from __future__ import annotations

from typing import Any


class BaseAgent:
    """Simple lifecycle for agents."""

    def __init__(self) -> None:
        self.running = False

    async def start(self, *args: Any, **kwargs: Any) -> None:
        """Start the agent."""
        self.running = True

    async def stop(self) -> None:
        """Stop the agent."""
        self.running = False

    async def step(
        self, *args: Any, **kwargs: Any
    ) -> None:  # pragma: no cover - override in subclasses
        """Advance the agent one step."""
