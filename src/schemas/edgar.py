"""Typed schemas for SEC EDGAR data."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class InsiderTransaction(BaseModel):
    filed_at: date
    insider_name: str
    position: str
    is_buy: bool
    shares: float
    price_per_share: float | None


class InsiderSummary(BaseModel):
    ticker: str
    period_days: int
    net_shares: float
    buy_count: int
    sell_count: int
    transactions: list[InsiderTransaction]


class InstitutionalHolder(BaseModel):
    fund_name: str
    cik: int
    shares: float
    value_usd: float
    report_period: str
    prior_shares: float | None
    change: float | None


class InstitutionalSnapshot(BaseModel):
    ticker: str
    report_period: str
    holders: list[InstitutionalHolder]
    total_institutional_shares: float
    net_change_shares: float


class MaterialEvent(BaseModel):
    filed_at: date
    item_codes: list[str]
    description: str
    url: str
