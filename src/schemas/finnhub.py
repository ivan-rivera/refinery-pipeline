"""Typed response models for Finnhub API data."""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel


class CompanyProfile(BaseModel):
    symbol: str
    name: str = ""
    exchange: str = ""
    sector: str = ""
    industry: str = ""
    country: str = ""
    market_cap: float | None = None


class NewsArticle(BaseModel):
    published_at: AwareDatetime
    headline: str = ""
    summary: str = ""
    source: str = ""
    url: str = ""


class BasicFinancials(BaseModel):
    symbol: str
    week_52_high: float | None = None
    week_52_low: float | None = None
    beta: float | None = None
    avg_vol_10d: float | None = None


class SymbolMatch(BaseModel):
    symbol: str
    description: str = ""
    security_type: str = ""
