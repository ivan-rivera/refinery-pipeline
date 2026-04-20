"""Schema round-trip and validation tests."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError
from src.schemas.sheets import ClosedPosition, Holding, Learning, UniverseEntry


def test_universe_entry_round_trip() -> None:
    row = UniverseEntry(ticker="GDX", description="VanEck Gold Miners ETF")
    assert UniverseEntry.from_row(row.to_row()) == row


def test_holding_round_trip() -> None:
    row = Holding(
        date=date(2026, 4, 19),
        ticker="NEM",
        entry_price=Decimal("52.10"),
        stop_loss=Decimal("48.00"),
        take_profit=Decimal("60.00"),
        expiry_days=14,
        thesis="Gold breakout above 2400.",
    )
    assert Holding.from_row(row.to_row()) == row


def test_holding_rejects_negative_expiry() -> None:
    with pytest.raises(ValidationError):
        Holding(
            date=date(2026, 4, 19),
            ticker="NEM",
            entry_price=Decimal("52.10"),
            stop_loss=Decimal("48.00"),
            take_profit=Decimal("60.00"),
            expiry_days=-1,
            thesis="bad",
        )


def test_from_row_pads_short_rows() -> None:
    row = UniverseEntry.from_row(["GDX"])
    assert row == UniverseEntry(ticker="GDX", description="")


def test_closed_position_round_trip() -> None:
    row = ClosedPosition(
        date=date(2026, 4, 19),
        ticker="NEM",
        entry_price=Decimal("52.10"),
        exit_price=Decimal("58.75"),
        stop_loss=Decimal("48.00"),
        take_profit=Decimal("60.00"),
        expiry_days=14,
        thesis="Gold breakout above 2400.",
        learnings="Exit too early; let winners run.",
    )
    assert ClosedPosition.from_row(row.to_row()) == row


def test_learning_round_trip() -> None:
    row = Learning(date=date(2026, 4, 19), learning="Always check macro regime before entry.")
    assert Learning.from_row(row.to_row()) == row
