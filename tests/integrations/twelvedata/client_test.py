"""TwelveDataClient unit tests with a mocked twelvedata SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest
from src.config import Settings
from src.integrations.twelvedata.client import TwelveDataClient, make_twelvedata_client

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def _make_raw_df() -> pd.DataFrame:
    """Return a two-bar OHLCV DataFrame in descending order (newest first), as the SDK delivers."""
    return pd.DataFrame(
        {
            "open": [202.0, 201.0],
            "high": [206.0, 205.0],
            "low": [201.0, 200.0],
            "close": [204.0, 203.0],
            "volume": [1_200_000.0, 1_000_000.0],
        },
        index=pd.to_datetime(["2024-01-02", "2024-01-01"]),
    )


def test_get_ohlcv_returns_dataframe_per_symbol(mocker: MockerFixture) -> None:
    mock_td = mocker.patch("src.integrations.twelvedata.client.TDClient")
    mock_td.return_value.time_series.return_value.as_pandas.return_value = _make_raw_df()

    client = TwelveDataClient("test-key")
    result = client.get_ohlcv(["GDX", "GLD"])

    assert set(result.keys()) == {"GDX", "GLD"}
    for df in result.values():
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.is_monotonic_increasing
        assert all(df[col].dtype == float for col in df.columns)


def test_get_ohlcv_skips_symbol_on_error(mocker: MockerFixture) -> None:
    mock_td = mocker.patch("src.integrations.twelvedata.client.TDClient")

    def _ts_side_effect(symbol: str, **_kwargs: object) -> object:
        mock = mocker.MagicMock()
        if symbol == "INVALID":
            mock.as_pandas.side_effect = RuntimeError("symbol not found")
        else:
            mock.as_pandas.return_value = _make_raw_df()
        return mock

    mock_td.return_value.time_series.side_effect = _ts_side_effect

    client = TwelveDataClient("test-key")
    result = client.get_ohlcv(["GDX", "INVALID"])

    assert "GDX" in result
    assert "INVALID" not in result


def test_make_twelvedata_client_raises_for_missing_key() -> None:
    settings = Settings(_env_file=None)
    with pytest.raises(ValueError, match="TWELVEDATA_API_KEY"):
        make_twelvedata_client(settings)
