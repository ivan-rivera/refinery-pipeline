"""Unit tests for the FRED integration."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from src.integrations.fred.client import FredClient, make_fred_client
from src.schemas.fred import MacroSnapshot, SeriesSnapshot

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _daily_series(values: list[float]) -> pd.Series:
    """Build a daily pandas Series with the last value dated today."""
    end = date.today()
    start = end - timedelta(days=len(values) - 1)
    idx = pd.date_range(start=str(start), end=str(end), freq="D")
    return pd.Series(values[-len(idx) :], index=idx)


@pytest.fixture
def mock_fred() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(mock_fred: MagicMock) -> FredClient:
    return FredClient(mock_fred)


# ---------------------------------------------------------------------------
# get_macro_snapshot — return type
# ---------------------------------------------------------------------------


def test_get_macro_snapshot_returns_macro_snapshot(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.5] * 50)
    assert isinstance(client.get_macro_snapshot(), MacroSnapshot)


def test_get_macro_snapshot_all_series_fields_are_series_snapshots(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([2.0] * 50)
    result = client.get_macro_snapshot()
    for field in (
        "real_yield_10y",
        "breakeven_inflation_10y",
        "usd_broad_index",
        "vix",
        "fed_funds_rate",
        "industrial_production",
        "cpi",
        "metals_ppi",
    ):
        assert isinstance(getattr(result, field), SeriesSnapshot), f"Field {field!r} is not a SeriesSnapshot"


def test_get_macro_snapshot_fetches_all_eight_series(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0] * 50)
    client.get_macro_snapshot()
    assert mock_fred.get_series.call_count == 8


# ---------------------------------------------------------------------------
# SeriesSnapshot values
# ---------------------------------------------------------------------------


def test_series_snapshot_latest_value_is_last_non_nan(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0, 2.0, 3.0])
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.latest_value == pytest.approx(3.0)


def test_series_snapshot_latest_date_is_today(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0] * 50)
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.latest_date == date.today()


def test_series_snapshot_delta_14d_computed_correctly(client: FredClient, mock_fred: MagicMock) -> None:
    """delta_14d = latest_value − value of the last observation ≥14 days ago."""
    # Transition at day 26 from start (= 13 days ago), so the observation ≥14d ago is still 1.0.
    values = [1.0] * 26 + [2.0] * 14
    mock_fred.get_series.return_value = _daily_series(values)
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.delta_14d == pytest.approx(1.0, abs=0.01)


def test_series_snapshot_delta_14d_is_none_when_insufficient_history(client: FredClient, mock_fred: MagicMock) -> None:
    """delta_14d is None when the series has fewer than 15 data points."""
    mock_fred.get_series.return_value = _daily_series([1.0, 1.5, 2.0])
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.delta_14d is None


def test_series_snapshot_delta_30d_computed_correctly(client: FredClient, mock_fred: MagicMock) -> None:
    values = [1.0] * 35 + [3.0] * 10
    mock_fred.get_series.return_value = _daily_series(values)
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.delta_30d == pytest.approx(2.0, abs=0.01)


def test_series_snapshot_delta_30d_is_none_when_insufficient_history(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0, 2.0])
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.delta_30d is None


def test_series_snapshot_nan_values_are_dropped(client: FredClient, mock_fred: MagicMock) -> None:
    s = _daily_series([1.0] * 48 + [np.nan, 3.0])  # type: ignore[arg-type]
    mock_fred.get_series.return_value = s
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.latest_value == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# make_fred_client
# ---------------------------------------------------------------------------


def test_make_fred_client_returns_fred_client(mocker: MockerFixture) -> None:
    mocker.patch("src.integrations.fred.client.Fred")
    settings = mocker.MagicMock()
    settings.fred_api_key = "test-key"
    assert isinstance(make_fred_client(settings), FredClient)


def test_make_fred_client_raises_when_key_is_empty(mocker: MockerFixture) -> None:
    settings = mocker.MagicMock()
    settings.fred_api_key = ""
    with pytest.raises(ValueError, match="FRED_API_KEY"):
        make_fred_client(settings)


# ---------------------------------------------------------------------------
# MacroSnapshot.to_text()
# ---------------------------------------------------------------------------


def test_to_text_contains_all_section_headers(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.5] * 50)
    text = client.get_macro_snapshot().to_text()
    for header in ("Rates & Inflation", "Currency", "Risk Regime", "Activity & Prices"):
        assert header in text, f"Missing section header: {header!r}"


def test_to_text_shows_na_when_delta_is_none(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0, 2.0])
    text = client.get_macro_snapshot().to_text()
    assert "N/A" in text


def test_to_text_includes_series_values(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([2.5] * 50)
    text = client.get_macro_snapshot().to_text()
    assert "2.50" in text
