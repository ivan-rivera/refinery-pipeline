"""SheetsClient CRUD tests with a mocked gspread backend."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from src.integrations.sheets.client import SheetsClient, make_sheets_client
from src.schemas.sheets import Holding, UniverseEntry

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


_UNIVERSE_HEADER = list(UniverseEntry.HEADER)
_HOLDINGS_HEADER = list(Holding.HEADER)


def _make_client(
    mocker: MockerFixture,
    *,
    universe: list[list[str]],
    holdings: list[list[str]],
) -> tuple[SheetsClient, object, object]:
    universe_ws = mocker.MagicMock(name="universe_ws")
    universe_ws.get_all_values.return_value = [_UNIVERSE_HEADER, *universe]
    holdings_ws = mocker.MagicMock(name="holdings_ws")
    holdings_ws.get_all_values.return_value = [_HOLDINGS_HEADER, *holdings]
    spreadsheet = mocker.MagicMock(name="spreadsheet")
    spreadsheet.worksheet.side_effect = lambda name: {
        "universe": universe_ws,
        "holdings": holdings_ws,
    }[name]
    gc = mocker.MagicMock(name="gc")
    gc.open_by_key.return_value = spreadsheet
    return SheetsClient(gc, "sheet-id"), universe_ws, holdings_ws


def test_get_table_universe(mocker: MockerFixture) -> None:
    client, _, _ = _make_client(
        mocker,
        universe=[["GDX", "Gold Miners"], ["NEM", "Newmont"]],
        holdings=[],
    )
    assert client.get_table(UniverseEntry) == [
        UniverseEntry(ticker="GDX", description="Gold Miners"),
        UniverseEntry(ticker="NEM", description="Newmont"),
    ]


def test_append_row_universe(mocker: MockerFixture) -> None:
    client, universe_ws, _ = _make_client(mocker, universe=[], holdings=[])
    client.append_row(UniverseEntry(ticker="GLD", description="Gold ETF"))
    universe_ws.append_row.assert_called_once_with(["GLD", "Gold ETF"], value_input_option="USER_ENTERED")


def test_get_table_holdings(mocker: MockerFixture) -> None:
    client, _, _ = _make_client(
        mocker,
        universe=[],
        holdings=[["2026-04-19", "NEM", "52.10", "48.00", "60.00", "14", "thesis"]],
    )
    assert client.get_table(Holding) == [
        Holding(
            date=date(2026, 4, 19),
            ticker="NEM",
            entry_price=Decimal("52.10"),
            stop_loss=Decimal("48.00"),
            take_profit=Decimal("60.00"),
            expiry_days=14,
            thesis="thesis",
        ),
    ]


def test_append_row_holdings(mocker: MockerFixture) -> None:
    client, _, holdings_ws = _make_client(mocker, universe=[], holdings=[])
    row = Holding(
        date=date(2026, 4, 19),
        ticker="GDX",
        entry_price=Decimal("32.0"),
        stop_loss=Decimal("30.0"),
        take_profit=Decimal("38.0"),
        expiry_days=21,
        thesis="momentum",
    )
    client.append_row(row)
    holdings_ws.append_row.assert_called_once_with(
        ["2026-04-19", "GDX", "32.0", "30.0", "38.0", "21", "momentum"],
        value_input_option="USER_ENTERED",
    )


def test_update_row_targets_correct_row(mocker: MockerFixture) -> None:
    client, _, holdings_ws = _make_client(
        mocker,
        universe=[],
        holdings=[
            ["2026-04-10", "GDX", "30.0", "28.0", "35.0", "14", "old"],
            ["2026-04-11", "NEM", "50.0", "48.0", "60.0", "14", "old"],
        ],
    )
    new_row = Holding(
        date=date(2026, 4, 19),
        ticker="NEM",
        entry_price=Decimal("52.0"),
        stop_loss=Decimal("49.0"),
        take_profit=Decimal("65.0"),
        expiry_days=21,
        thesis="updated",
    )
    client.update_row("NEM", new_row)
    holdings_ws.update.assert_called_once_with(
        range_name="A3",
        values=[["2026-04-19", "NEM", "52.0", "49.0", "65.0", "21", "updated"]],
        value_input_option="USER_ENTERED",
    )


def test_delete_row_removes_correct_row(mocker: MockerFixture) -> None:
    client, _, holdings_ws = _make_client(
        mocker,
        universe=[],
        holdings=[
            ["2026-04-10", "GDX", "30.0", "28.0", "35.0", "14", "t"],
            ["2026-04-11", "NEM", "50.0", "48.0", "60.0", "14", "t"],
        ],
    )
    client.delete_row(Holding, "GDX")
    holdings_ws.delete_rows.assert_called_once_with(2)


def test_update_row_unknown_key_raises(mocker: MockerFixture) -> None:
    client, _, _ = _make_client(mocker, universe=[], holdings=[])
    row = Holding(
        date=date(2026, 4, 19),
        ticker="MISSING",
        entry_price=Decimal(1),
        stop_loss=Decimal(1),
        take_profit=Decimal(1),
        expiry_days=1,
        thesis="t",
    )
    with pytest.raises(KeyError, match="MISSING"):
        client.update_row("MISSING", row)


def test_make_sheets_client_requires_creds_path(mocker: MockerFixture) -> None:
    settings = mocker.MagicMock(google_creds_path=None)
    with pytest.raises(ValueError, match="GOOGLE_CREDS_PATH"):
        make_sheets_client(settings, debug=True)


def test_make_sheets_client_passes_debug_to_settings(mocker: MockerFixture, tmp_path) -> None:
    creds = tmp_path / "sa.json"
    creds.write_text("{}")
    settings = mocker.MagicMock()
    settings.google_creds_path = creds
    settings.sheet_id.return_value = "SID"
    fake_gc = mocker.MagicMock()
    mocker.patch("src.integrations.sheets.client.gspread.service_account", return_value=fake_gc)
    spy_ctor = mocker.patch("src.integrations.sheets.client.SheetsClient")

    make_sheets_client(settings, debug=True)

    settings.sheet_id.assert_called_once_with(debug=True)
    spy_ctor.assert_called_once_with(fake_gc, "SID")
