"""Typed client over the project's Google Sheet.

Wraps gspread so the rest of the codebase never sees raw cell values.
The `_Tab` helper handles CRUD for a single worksheet; `SheetsClient`
exposes four generic methods that derive the tab from the row model class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import gspread
from gspread.utils import ValueInputOption

from src.schemas.sheets import HoldingsRow, UniverseRow

if TYPE_CHECKING:
    from src.config import Settings

_HEADER_ROWS = 1
_VALUE_INPUT = ValueInputOption.user_entered


class _Tab[T: (UniverseRow, HoldingsRow)]:
    """CRUD adapter over a single worksheet keyed by one column."""

    def __init__(self, worksheet: gspread.Worksheet, model: type[T]) -> None:
        self._ws = worksheet
        self._model: type[T] = model
        self._key_col = model.HEADER.index(model.KEY)

    def read_all(self) -> list[T]:
        rows = self._ws.get_all_values()[_HEADER_ROWS:]
        return [self._model.from_row(row) for row in rows if any(cell.strip() for cell in row)]

    def append(self, item: T) -> None:
        self._ws.append_row(item.to_row(), value_input_option=_VALUE_INPUT)

    def update(self, key: str, item: T) -> None:
        self._ws.update(
            range_name=f"A{self._row_index(key)}",
            values=[item.to_row()],
            value_input_option=_VALUE_INPUT,
        )

    def delete(self, key: str) -> None:
        self._ws.delete_rows(self._row_index(key))

    def _row_index(self, key: str) -> int:
        rows = self._ws.get_all_values()[_HEADER_ROWS:]
        for offset, row in enumerate(rows):
            cell = row[self._key_col] if self._key_col < len(row) else ""
            if cell == key:
                return offset + _HEADER_ROWS + 1
        raise KeyError(f"{self._model.__name__}: no row with {self._model.KEY}={key!r}")


class SheetsClient:
    """Typed access to the project's Google Sheet."""

    def __init__(self, gc: gspread.Client, sheet_id: str) -> None:
        self._spreadsheet = gc.open_by_key(sheet_id)
        self._cache: dict[str, _Tab] = {}

    def _tab[T: (UniverseRow, HoldingsRow)](self, model: type[T]) -> _Tab[T]:
        if model.SHEET not in self._cache:
            ws = self._spreadsheet.worksheet(model.SHEET)
            self._cache[model.SHEET] = _Tab(ws, model)
        return self._cache[model.SHEET]

    def get_table[T: (UniverseRow, HoldingsRow)](self, model: type[T]) -> list[T]:
        """Return every row from the sheet that corresponds to `model`."""
        return self._tab(model).read_all()

    def append_row[T: (UniverseRow, HoldingsRow)](self, row: T) -> None:
        """Append a row to the sheet that corresponds to `row`'s model."""
        self._tab(type(row)).append(row)

    def update_row[T: (UniverseRow, HoldingsRow)](self, key: str, row: T) -> None:
        """Replace the row identified by `key` in `row`'s sheet."""
        self._tab(type(row)).update(key, row)

    def delete_row[T: (UniverseRow, HoldingsRow)](self, model: type[T], key: str) -> None:
        """Delete the row identified by `key` from `model`'s sheet."""
        self._tab(model).delete(key)


def make_sheets_client(settings: Settings, *, debug: bool) -> SheetsClient:
    """Build a `SheetsClient` for the test or prod sheet."""
    if not settings.google_creds_path:
        raise ValueError("GOOGLE_CREDS_PATH is not set")
    gc = gspread.service_account(filename=str(settings.google_creds_path))
    return SheetsClient(gc, settings.sheet_id(debug=debug))
