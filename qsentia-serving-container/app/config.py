from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_bundle_path: Path = Field(
        default=Path("/models/model_bundle"),
        validation_alias="MODEL_BUNDLE_PATH",
    )
    service_name: str = Field(default="qsentia-serving-container")


@lru_cache
def get_settings() -> Settings:
    return Settings()

