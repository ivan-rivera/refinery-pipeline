"""Schema round-trip and validation tests."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError
from src.schemas.sheets import HoldingsRow, UniverseRow


def test_universe_row_round_trip() -> None:
    row = UniverseRow(ticker="GDX", description="VanEck Gold Miners ETF")
    assert UniverseRow.from_row(row.to_row()) == row


def test_holdings_row_round_trip() -> None:
    row = HoldingsRow(
        date=date(2026, 4, 19),
        ticker="NEM",
        entry_price=Decimal("52.10"),
        stop_loss=Decimal("48.00"),
        take_profit=Decimal("60.00"),
        expiry_days=14,
        thesis="Gold breakout above 2400.",
    )
    assert HoldingsRow.from_row(row.to_row()) == row


def test_holdings_row_rejects_negative_expiry() -> None:
    with pytest.raises(ValidationError):
        HoldingsRow(
            date=date(2026, 4, 19),
            ticker="NEM",
            entry_price=Decimal("52.10"),
            stop_loss=Decimal("48.00"),
            take_profit=Decimal("60.00"),
            expiry_days=-1,
            thesis="bad",
        )


def test_from_row_pads_short_rows() -> None:
    row = UniverseRow.from_row(["GDX"])
    assert row == UniverseRow(ticker="GDX", description="")
