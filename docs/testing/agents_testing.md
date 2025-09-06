---
version: v0.4
lastReviewed: 2025-07-29
---

# Agent Simulation Tests

This directory contains lightweight agents used to simulate runtime behaviour in tests.

## Components

- **ConfigAgent** – Loads example assets from `app/examples` and parses them into Pydantic models.
- **StateMirrorAgent** – Maintains a mutable state dictionary and broadcasts updates.
- **ModulationAgent** – Applies simple LFO-style updates to values in the mirror state.
- **OrchestrationAgent** – Composes the other agents to demonstrate a complete lifecycle.

## Running

To execute only the agent simulations run:

```bash
./codex.sh --agents
```

Agents can also be tested directly via `pytest tests/agents`.
