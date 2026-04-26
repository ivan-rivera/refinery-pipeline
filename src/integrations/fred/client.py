"""Typed FRED (Federal Reserve Economic Data) client."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pandas as pd
from fredapi import Fred

from src.constants import (
    FRED_OBSERVATION_WINDOW_DAYS,
    FRED_SERIES_CPIAUCSL,
    FRED_SERIES_DFII10,
    FRED_SERIES_DTWEXBGS,
    FRED_SERIES_FEDFUNDS,
    FRED_SERIES_INDPRO,
    FRED_SERIES_T10YIE,
    FRED_SERIES_VIXCLS,
    FRED_SERIES_WPU10,
)
from src.schemas.fred import MacroSnapshot, SeriesSnapshot

if TYPE_CHECKING:
    from src.config import Settings


def _delta(series: pd.Series, days: int) -> float | None:
    """Return (latest - value at or before `days` calendar days ago), or None."""
    cutoff = series.index[-1] - pd.Timedelta(days=days)
    past = series[series.index <= cutoff]
    if past.empty:
        return None
    return float(series.iloc[-1]) - float(past.iloc[-1])


class FredClient:
    """Typed access to FRED macro series."""

    def __init__(self, fred: Fred) -> None:
        self._fred = fred

    def _fetch_series(self, series_id: str) -> SeriesSnapshot:
        end = datetime.now(tz=UTC).date()
        start = end - timedelta(days=FRED_OBSERVATION_WINDOW_DAYS)
        raw: pd.Series = self._fred.get_series(series_id, observation_start=start, observation_end=end)
        raw = raw.dropna()
        if raw.empty:
            raise ValueError(f"No observations returned for FRED series {series_id!r}")
        return SeriesSnapshot(
            series_id=series_id,
            latest_value=float(raw.iloc[-1]),
            latest_date=raw.index[-1].date(),
            delta_14d=_delta(raw, 14),
            delta_30d=_delta(raw, 30),
        )

    def get_macro_snapshot(self) -> MacroSnapshot:
        """Fetch all 8 tracked FRED series and return a typed MacroSnapshot."""
        return MacroSnapshot(
            fetched_at=datetime.now(UTC),
            real_yield_10y=self._fetch_series(FRED_SERIES_DFII10),
            breakeven_inflation_10y=self._fetch_series(FRED_SERIES_T10YIE),
            usd_broad_index=self._fetch_series(FRED_SERIES_DTWEXBGS),
            vix=self._fetch_series(FRED_SERIES_VIXCLS),
            fed_funds_rate=self._fetch_series(FRED_SERIES_FEDFUNDS),
            industrial_production=self._fetch_series(FRED_SERIES_INDPRO),
            cpi=self._fetch_series(FRED_SERIES_CPIAUCSL),
            metals_ppi=self._fetch_series(FRED_SERIES_WPU10),
        )


def make_fred_client(settings: Settings) -> FredClient:
    """Build a FredClient from application settings."""
    if not settings.fred_api_key:
        raise ValueError("FRED_API_KEY is not set")
    return FredClient(Fred(api_key=settings.fred_api_key))
