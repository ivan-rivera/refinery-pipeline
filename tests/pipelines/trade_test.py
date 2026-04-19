"""Trade pipeline CLI tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner
from src.pipelines.trade import cli

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_run_exits_cleanly(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.make_sheets_client")
    result = runner.invoke(cli, ["run"])
    assert result.exit_code == 0


def test_run_dry_run_flag(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.make_sheets_client")
    result = runner.invoke(cli, ["run", "--dry-run"])
    assert result.exit_code == 0


def test_run_with_input_and_output(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.make_sheets_client")
    result = runner.invoke(cli, ["run", "--input", "data/in.json", "--output", "data/out.json"])
    assert result.exit_code == 0


def test_run_help(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "--input" in result.output
    assert "--output" in result.output
    assert "--dry-run" in result.output


def test_dry_run_uses_test_sheet(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.get_settings")
    factory = mocker.patch("src.pipelines.trade.make_sheets_client")

    result = runner.invoke(cli, ["run", "--dry-run"])

    assert result.exit_code == 0
    factory.assert_called_once()
    assert factory.call_args.kwargs["debug"] is True


def test_no_dry_run_uses_prod_sheet(runner: CliRunner, mocker: MockerFixture) -> None:
    mocker.patch("src.pipelines.trade.get_settings")
    factory = mocker.patch("src.pipelines.trade.make_sheets_client")

    result = runner.invoke(cli, ["run"])

    assert result.exit_code == 0
    factory.assert_called_once()
    assert factory.call_args.kwargs["debug"] is False
