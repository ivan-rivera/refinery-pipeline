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


def test_alpaca_credentials_returns_test_keys_in_debug() -> None:
    settings = Settings(_env_file=None, TEST_ALPACA_API_KEY="tkey", TEST_ALPACA_SECRET_KEY="tsecret")
    assert settings.alpaca_credentials(debug=True) == ("tkey", "tsecret")


def test_alpaca_credentials_returns_prod_keys_when_not_debug() -> None:
    settings = Settings(_env_file=None, PROD_ALPACA_API_KEY="pkey", PROD_ALPACA_SECRET_KEY="psecret")
    assert settings.alpaca_credentials(debug=False) == ("pkey", "psecret")
