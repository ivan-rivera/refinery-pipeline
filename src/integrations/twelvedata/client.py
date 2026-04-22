"""Typed client over the TwelveData API.

Wraps the official twelvedata SDK so the rest of the codebase
receives typed pandas DataFrames rather than raw SDK objects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd
from twelvedata import TDClient

if TYPE_CHECKING:
    from src.config import Settings

_logger = logging.getLogger(__name__)


class TwelveDataClient:
    """Fetch OHLCV price/volume history from TwelveData."""

    def __init__(self, api_key: str) -> None:
        self._td = TDClient(apikey=api_key)

    def get_ohlcv(
        self,
        symbols: list[str],
        *,
        outputsize: int = 100,
        interval: str = "1day",
    ) -> dict[str, pd.DataFrame]:
        """Return split-adjusted OHLCV bars per symbol.

        Each DataFrame has columns open/high/low/close/volume (float64),
        indexed by DatetimeIndex sorted ascending. Symbols that produce
        an error are omitted from the result without raising.
        """
        results: dict[str, pd.DataFrame] = {}
        for symbol in symbols:
            try:
                df: pd.DataFrame = (
                    self._td.time_series(
                        symbol=symbol,
                        interval=interval,
                        outputsize=outputsize,
                        adjust="splits",
                    )
                    .as_pandas()
                )
            except Exception:
                _logger.warning("Failed to fetch OHLCV for %s", symbol, exc_info=True)
                continue
            if df is None or df.empty:
                _logger.warning("No data returned for %s", symbol)
                continue
            df = df.rename(columns=str.lower)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index(ascending=True)
            results[symbol] = df[["open", "high", "low", "close", "volume"]].astype(float)
        return results


def make_twelvedata_client(settings: Settings) -> TwelveDataClient:
    """Build a TwelveDataClient from application settings."""
    if not settings.twelvedata_api_key:
        raise ValueError("TWELVEDATA_API_KEY is not set")
    return TwelveDataClient(settings.twelvedata_api_key)
