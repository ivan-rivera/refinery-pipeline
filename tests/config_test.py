"""Tests for settings."""
from src.config import Settings, get_settings


def test_settings_has_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "refinery-pipeline"
    assert settings.log_level == "INFO"


def test_get_settings_returns_cached_instance() -> None:
    assert get_settings() is get_settings()
