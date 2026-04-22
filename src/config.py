"""Settings management.

Reads variables from .env and environment. All fields have defaults so
the pipeline runs without a .env file during development and testing.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "refinery-pipeline"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    google_creds_path: Path | None = Field(default=None, alias="GOOGLE_CREDS_PATH")
    google_sheet_id_test: str = Field(default="", alias="GOOGLE_SHEET_ID_TEST")
    google_sheet_id_prod: str = Field(default="", alias="GOOGLE_SHEET_ID_PROD")
    twelvedata_api_key: str = Field(default="", alias="TWELVEDATA_API_KEY")

    def sheet_id(self, *, debug: bool) -> str:
        """Return the Google Sheet id for the current environment."""
        return self.google_sheet_id_test if debug else self.google_sheet_id_prod


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance."""
    return Settings()
