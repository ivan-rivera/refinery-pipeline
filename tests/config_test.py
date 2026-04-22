"""Tests for settings."""

from src.config import Settings, get_settings


def test_settings_has_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "refinery-pipeline"
    assert settings.log_level == "INFO"


def test_get_settings_returns_cached_instance() -> None:
    assert get_settings() is get_settings()


def test_sheet_id_selects_test_when_debug() -> None:
    settings = Settings(_env_file=None, GOOGLE_SHEET_ID_TEST="t-id", GOOGLE_SHEET_ID_PROD="p-id")
    assert settings.sheet_id(debug=True) == "t-id"
    assert settings.sheet_id(debug=False) == "p-id"


def test_twelvedata_api_key_loaded_from_env() -> None:
    settings = Settings(_env_file=None, TWELVEDATA_API_KEY="td-test-key")
    assert settings.twelvedata_api_key == "td-test-key"


def test_twelvedata_api_key_defaults_to_empty() -> None:
    settings = Settings(_env_file=None)
    assert settings.twelvedata_api_key == ""
