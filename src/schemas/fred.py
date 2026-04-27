"""FRED macro data schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


def _fmt(delta: float | None) -> str:
    return "N/A" if delta is None else f"{delta:+.2f}"


class SeriesSnapshot(BaseModel):
    """Latest value and short-term deltas for a single FRED series."""

    series_id: str
    latest_value: float
    latest_date: date
    delta_14d: float | None  # latest - value ≥14 calendar days ago; None if insufficient history
    delta_30d: float | None  # latest - value ≥30 calendar days ago; None if insufficient history


class MacroSnapshot(BaseModel):
    """Point-in-time snapshot of all tracked FRED macro series."""

    fetched_at: datetime
    real_yield_10y: SeriesSnapshot  # DFII10
    breakeven_inflation_10y: SeriesSnapshot  # T10YIE
    usd_broad_index: SeriesSnapshot  # DTWEXBGS
    vix: SeriesSnapshot  # VIXCLS
    fed_funds_rate: SeriesSnapshot  # FEDFUNDS
    industrial_production: SeriesSnapshot  # INDPRO
    cpi: SeriesSnapshot  # CPIAUCSL
    metals_ppi: SeriesSnapshot  # WPU10

    def to_text(self) -> str:
        """Serialise to plain text for injection into LLM agent context."""
        return "\n".join(
            [
                f"Macro snapshot ({self.fetched_at.strftime('%Y-%m-%d')})",
                "",
                "--- Rates & Inflation ---",
                f"  Real 10Y yield (DFII10):        {self.real_yield_10y.latest_value:+.2f}%  Δ14d {_fmt(self.real_yield_10y.delta_14d)}pp",
                f"  10Y breakeven inflation:         {self.breakeven_inflation_10y.latest_value:.2f}%   Δ14d {_fmt(self.breakeven_inflation_10y.delta_14d)}pp",
                f"  Fed funds rate:                  {self.fed_funds_rate.latest_value:.2f}%   Δ30d {_fmt(self.fed_funds_rate.delta_30d)}pp",
                "",
                "--- Currency ---",
                f"  USD broad index (DTWEXBGS):      {self.usd_broad_index.latest_value:.2f}   Δ14d {_fmt(self.usd_broad_index.delta_14d)}",
                "",
                "--- Risk Regime ---",
                f"  VIX:                             {self.vix.latest_value:.2f}   Δ14d {_fmt(self.vix.delta_14d)}",
                "",
                "--- Activity & Prices ---",
                f"  Industrial production (INDPRO):  {self.industrial_production.latest_value:.2f}   Δ30d {_fmt(self.industrial_production.delta_30d)}",
                f"  CPI (CPIAUCSL):                  {self.cpi.latest_value:.2f}   Δ30d {_fmt(self.cpi.delta_30d)}",
                f"  Metals PPI (WPU10):              {self.metals_ppi.latest_value:.2f}   Δ30d {_fmt(self.metals_ppi.delta_30d)}",
            ]
        )
