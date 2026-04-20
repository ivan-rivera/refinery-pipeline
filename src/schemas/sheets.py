"""Row schemas for the Google Sheets tabs.

Each model owns its column order via `HEADER` and serialises to/from the
flat `list[str]` rows that `gspread` returns.

`SheetRow` is the base class — adding a new sheet model only requires
subclassing it; no changes to `SheetsClient` are needed.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar, Self

from pydantic import BaseModel, Field

_DATE_FORMAT = "%Y-%m-%d"


class SheetRow(BaseModel):
    """Base for all Google Sheets row models."""

    SHEET: ClassVar[str]
    KEY: ClassVar[str]
    HEADER: ClassVar[tuple[str, ...]]

    @classmethod
    def from_row(cls, row: list[str]) -> Self:
        """Build the model from a raw cell-value row."""
        raise NotImplementedError

    def to_row(self) -> list[str]:
        """Serialise the model into the sheet's column order."""
        raise NotImplementedError


class UniverseEntry(SheetRow):
    """A row in the `universe` sheet."""

    SHEET: ClassVar[str] = "universe"
    KEY: ClassVar[str] = "ticker"
    HEADER: ClassVar[tuple[str, ...]] = ("ticker", "description")

    ticker: str
    description: str

    @classmethod
    def from_row(cls, row: list[str]) -> Self:
        ticker, description = _padded(row, len(cls.HEADER))
        return cls(ticker=ticker, description=description)

    def to_row(self) -> list[str]:
        return [self.ticker, self.description]


class Holding(SheetRow):
    """A row in the `holdings` sheet (one open position per ticker)."""

    SHEET: ClassVar[str] = "holdings"
    KEY: ClassVar[str] = "ticker"
    HEADER: ClassVar[tuple[str, ...]] = (
        "date",
        "ticker",
        "entry_price",
        "stop_loss",
        "take_profit",
        "expiry_days",
        "thesis",
    )

    date: date
    ticker: str
    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    expiry_days: int = Field(ge=0)
    thesis: str

    @classmethod
    def from_row(cls, row: list[str]) -> Self:
        d, ticker, entry, stop, take, expiry, thesis = _padded(row, len(cls.HEADER))
        return cls(
            date=datetime.strptime(d, _DATE_FORMAT).date(),  # noqa: DTZ007
            ticker=ticker,
            entry_price=Decimal(entry),
            stop_loss=Decimal(stop),
            take_profit=Decimal(take),
            expiry_days=int(expiry),
            thesis=thesis,
        )

    def to_row(self) -> list[str]:
        return [
            self.date.strftime(_DATE_FORMAT),
            self.ticker,
            str(self.entry_price),
            str(self.stop_loss),
            str(self.take_profit),
            str(self.expiry_days),
            self.thesis,
        ]


def _padded(row: list[str], width: int) -> list[str]:
    """Right-pad with empty strings so unpacking never raises on short rows."""
    if len(row) >= width:
        return row[:width]
    return [*row, *([""] * (width - len(row)))]
