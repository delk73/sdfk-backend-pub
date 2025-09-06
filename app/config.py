from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.env import load_env

load_env()


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    REDIS_URL: str = Field("redis://localhost:6379")
    CACHE_ENABLED: bool = Field(True)

    RLHF_DATASET_PATH: str = Field("/data/patch_feedback.jsonl")

    TESTING: bool = Field(False)

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
