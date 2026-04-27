"""Trade pipeline CLI tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from click.testing import CliRunner
from src.pipelines.trade import cli
from src.schemas.fred import MacroSnapshot, SeriesSnapshot

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def _fake_macro_snapshot() -> MacroSnapshot:
    def _snap(series_id: str) -> SeriesSnapshot:
        return SeriesSnapshot(
            series_id=series_id,
            latest_value=1.0,
            latest_date=datetime.now(UTC).date(),
            delta_14d=None,
            delta_30d=None,
        )

    return MacroSnapshot(
        fetched_at=datetime.now(UTC),
        real_yield_10y=_snap("DFII10"),
        breakeven_inflation_10y=_snap("T10YIE"),
        usd_broad_index=_snap("DTWEXBGS"),
        vix=_snap("VIXCLS"),
        fed_funds_rate=_snap("FEDFUNDS"),
        industrial_production=_snap("INDPRO"),
        cpi=_snap("CPIAUCSL"),
        metals_ppi=_snap("WPU10"),
    )


def _patch_fred(mocker: MockerFixture) -> MagicMock:
    mock_client = MagicMock()
    mock_client.get_macro_snapshot.return_value = _fake_macro_snapshot()
    return mocker.patch("src.pipelines.trade.make_fred_client", return_value=mock_client)


def test_run_exits_cleanly(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.make_sheets_client")
    _patch_fred(mocker)
    result = runner.invoke(cli, ["run"])
    assert result.exit_code == 0


def test_run_dry_run_flag(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.make_sheets_client")
    _patch_fred(mocker)
    result = runner.invoke(cli, ["run", "--dry-run"])
    assert result.exit_code == 0


def test_run_with_input_and_output(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.make_sheets_client")
    _patch_fred(mocker)
    result = runner.invoke(cli, ["run", "--input", "data/in.json", "--output", "data/out.json"])
    assert result.exit_code == 0


def test_run_help(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "--input" in result.output
    assert "--output" in result.output
    assert "--dry-run" in result.output


def test_run_prints_fred_snapshot_date(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.make_sheets_client")
    _patch_fred(mocker)
    result = runner.invoke(cli, ["run"])
    assert result.exit_code == 0
    assert "FRED snapshot fetched" in result.output


def test_dry_run_uses_test_sheet(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.get_settings")
    factory = mocker.patch("src.pipelines.trade.make_sheets_client")
    _patch_fred(mocker)

    result = runner.invoke(cli, ["run", "--dry-run"])

    assert result.exit_code == 0
    factory.assert_called_once()
    assert factory.call_args.kwargs["debug"] is True


def test_no_dry_run_uses_prod_sheet(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.get_settings")
    factory = mocker.patch("src.pipelines.trade.make_sheets_client")
    _patch_fred(mocker)

    result = runner.invoke(cli, ["run"])

    assert result.exit_code == 0
    factory.assert_called_once()
    assert factory.call_args.kwargs["debug"] is False
