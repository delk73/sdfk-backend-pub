"""Environment variable initialization for the application."""

from __future__ import annotations

from functools import lru_cache
from dotenv import load_dotenv


@lru_cache(maxsize=1)
def load_env() -> None:
    """Load environment variables from the ``.env`` file."""
    load_dotenv()
