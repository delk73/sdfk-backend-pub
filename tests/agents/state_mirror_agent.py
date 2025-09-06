"""Agent that mirrors and broadcasts state changes."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .base_agent import BaseAgent


class StateMirrorAgent(BaseAgent):
    """Maintain a mutable state dictionary and broadcast updates."""

    def __init__(self) -> None:
        super().__init__()
        self.state: Dict[str, Any] = {}
        self.subscribers: List[Callable[[Dict[str, Any]], None]] = []
        self.broadcast_log: List[Dict[str, Any]] = []

    async def start(self, initial_state: Optional[Dict[str, Any]] = None) -> None:
        await super().start()
        if initial_state:
            self.state.update(initial_state)

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a subscriber for state updates."""
        self.subscribers.append(callback)

    def update(self, key: str, value: Any) -> None:
        """Update a state value and broadcast the change."""
        self.state[key] = value
        self.broadcast()

    def broadcast(self) -> None:
        """Notify subscribers of the current state."""
        for callback in self.subscribers:
            callback(self.state)
        self.broadcast_log.append(self.state.copy())
