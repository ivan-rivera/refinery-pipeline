"""FinnhubClient unit tests."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta

import pytest
from src.config import get_settings
from src.integrations.finnhub import FinnhubClient, make_finnhub_client


def test_make_finnhub_client_raises_on_missing_key(mocker):
    settings = mocker.MagicMock(finnhub_api_key="")
    with pytest.raises(ValueError, match="FINNHUB_API_KEY"):
        make_finnhub_client(settings)


def test_get_company_profile_returns_none_on_empty_response(mocker):
    sdk = mocker.MagicMock()
    sdk.company_profile2.return_value = {}
    assert FinnhubClient(sdk).get_company_profile("FAKE") is None


def test_get_company_news_converts_unix_timestamp(mocker):
    sdk = mocker.MagicMock()
    sdk.company_news.return_value = [
        {
            "datetime": 1700000000,
            "headline": "Gold surges",
            "summary": "Gold hit a new high.",
            "source": "Reuters",
            "url": "https://example.com",
        }
    ]
    articles = FinnhubClient(sdk).get_company_news("GDX", date(2023, 11, 1), date(2023, 11, 30))
    assert len(articles) == 1
    assert articles[0].published_at == datetime.fromtimestamp(1700000000, tz=UTC)


def test_get_basic_financials_handles_missing_metrics(mocker):
    sdk = mocker.MagicMock()
    sdk.company_basic_financials.return_value = {"metric": {"52WeekHigh": 35.0}}
    result = FinnhubClient(sdk).get_basic_financials("GDX")
    assert result is not None
    assert result.week_52_high == 35.0
    assert result.beta is None
    assert result.avg_vol_10d is None


def test_get_company_profile_maps_fields(mocker):
    sdk = mocker.MagicMock()
    sdk.company_profile2.return_value = {
        "ticker": "GDX",
        "name": "VanEck Gold Miners ETF",
        "exchange": "NYSE ARCA",
        "gicsSector": "Materials",
        "finnhubIndustry": "Gold",
        "country": "US",
        "marketCapitalization": 0.0,
    }
    profile = FinnhubClient(sdk).get_company_profile("GDX")
    assert profile is not None
    assert profile.symbol == "GDX"
    assert profile.market_cap == 0.0


def test_get_basic_financials_preserves_zero_values(mocker):
    sdk = mocker.MagicMock()
    sdk.company_basic_financials.return_value = {"metric": {"52WeekHigh": 0.0, "beta": 0, "52WeekLow": None}}
    result = FinnhubClient(sdk).get_basic_financials("GDX")
    assert result is not None
    assert result.week_52_high == 0.0
    assert result.beta == 0
    assert result.week_52_low is None


# ---------------------------------------------------------------------------
# Integration tests — skipped unless FINNHUB_API_KEY is set in the environment
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="FINNHUB_API_KEY not set")
def test_integration_get_company_profile():
    # Use GOLD (Barrick Gold Corp) — a regular equity with reliable Finnhub coverage.
    # GDX is an ETF and returns an empty profile on the free tier.
    result = make_finnhub_client(get_settings()).get_company_profile("GOLD")
    assert result is not None
    assert result.symbol != ""


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="FINNHUB_API_KEY not set")
def test_integration_get_company_news():
    today = datetime.now(tz=UTC).date()
    result = make_finnhub_client(get_settings()).get_company_news("GDX", today - timedelta(days=7), today)
    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="FINNHUB_API_KEY not set")
def test_integration_get_basic_financials():
    result = make_finnhub_client(get_settings()).get_basic_financials("GDX")
    assert result is not None


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="FINNHUB_API_KEY not set")
def test_integration_search_symbols():
    results = make_finnhub_client(get_settings()).search_symbols("gold")
    assert len(results) > 0
