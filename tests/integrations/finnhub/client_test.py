"""FinnhubClient unit tests."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

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
    assert articles[0].published_at == datetime.fromtimestamp(1700000000, tz=timezone.utc)


def test_get_basic_financials_handles_missing_metrics(mocker):
    sdk = mocker.MagicMock()
    sdk.company_basic_financials.return_value = {"metric": {"52WeekHigh": 35.0}}
    result = FinnhubClient(sdk).get_basic_financials("GDX")
    assert result is not None
    assert result.week_52_high == 35.0
    assert result.beta is None
    assert result.avg_vol_10d is None
