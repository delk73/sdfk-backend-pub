"""Agent for loading example configuration files."""

from __future__ import annotations

import json
from typing import Optional

from app.schemas.synesthetic_asset import NestedSynestheticAssetCreate
from tests.fixtures.factories import load_example_file

from .base_agent import BaseAgent


class ConfigAgent(BaseAgent):
    """Load and parse synesthetic asset configuration files."""

    def __init__(self, filename: str) -> None:
        super().__init__()
        self.filename = filename
        self.asset: Optional[NestedSynestheticAssetCreate] = None

    async def start(self) -> None:
        await super().start()
        data = load_example_file(self.filename)
        if isinstance(data, str):
            data = json.loads(data)
        self.asset = NestedSynestheticAssetCreate(**data)

    async def stop(self) -> None:
        self.asset = None
        await super().stop()
