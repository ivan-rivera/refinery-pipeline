"""Typed Finnhub client.

Wraps the finnhub-python SDK so the rest of the codebase never sees raw dicts.
Rate limit: 60 requests/min on the free tier — callers are responsible for pacing.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

import finnhub

from src.schemas.finnhub import BasicFinancials, CompanyProfile, NewsArticle, SymbolMatch

if TYPE_CHECKING:
    from src.config import Settings


class FinnhubClient:
    """Typed access to the Finnhub REST API."""

    def __init__(self, client: finnhub.Client) -> None:
        self._client = client

    def get_company_profile(self, symbol: str) -> CompanyProfile | None:
        """Return company profile for `symbol`, or None if Finnhub has no data."""
        data = self._client.company_profile2(symbol=symbol)
        if not data or not data.get("ticker"):
            return None
        return CompanyProfile(
            symbol=data["ticker"],
            name=data.get("name", ""),
            exchange=data.get("exchange", ""),
            sector=data.get("gicsSector", ""),
            industry=data.get("finnhubIndustry", ""),
            country=data.get("country", ""),
            market_cap=data.get("marketCapitalization"),
        )

    def get_company_news(self, symbol: str, from_date: date, to_date: date) -> list[NewsArticle]:
        """Return news articles for `symbol` between `from_date` and `to_date`."""
        articles = self._client.company_news(
            symbol,
            _from=from_date.strftime("%Y-%m-%d"),
            to=to_date.strftime("%Y-%m-%d"),
        )
        if not articles:
            return []
        return [
            NewsArticle(
                published_at=datetime.fromtimestamp(a["datetime"], tz=UTC),
                headline=a.get("headline", ""),
                summary=a.get("summary", ""),
                source=a.get("source", ""),
                url=a.get("url", ""),
            )
            for a in articles
        ]

    def get_basic_financials(self, symbol: str) -> BasicFinancials | None:
        """Return key financial metrics for `symbol`, or None if unavailable."""
        data = self._client.company_basic_financials(symbol, "all")
        if not data or not data.get("metric"):
            return None
        metric = data["metric"]
        return BasicFinancials(
            symbol=symbol,
            week_52_high=metric.get("52WeekHigh"),
            week_52_low=metric.get("52WeekLow"),
            beta=metric.get("beta"),
            avg_vol_10d=metric.get("10DayAverageTradingVolume"),
        )

    def search_symbols(self, query: str) -> list[SymbolMatch]:
        """Search for symbols matching `query`."""
        data = self._client.symbol_search(query)
        if not data or not data.get("result"):
            return []
        return [
            SymbolMatch(
                symbol=r.get("symbol", ""),
                description=r.get("description", ""),
                security_type=r.get("type", ""),
            )
            for r in data["result"]
        ]


def make_finnhub_client(settings: Settings) -> FinnhubClient:
    """Build a FinnhubClient from application settings."""
    if not settings.finnhub_api_key:
        raise ValueError("FINNHUB_API_KEY is not set")
    return FinnhubClient(finnhub.Client(api_key=settings.finnhub_api_key))
