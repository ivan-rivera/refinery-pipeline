"""Pipeline CLI smoke tests."""
from click.testing import CliRunner

from src.pipeline import cli


def test_run_exits_cleanly(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["run"])
    assert result.exit_code == 0


def test_run_dry_run_flag(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["run", "--dry-run"])
    assert result.exit_code == 0


def test_run_with_input_and_output(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["run", "--input", "data/in.json", "--output", "data/out.json"])
    assert result.exit_code == 0


def test_run_help(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "--input" in result.output
    assert "--output" in result.output
    assert "--dry-run" in result.output
