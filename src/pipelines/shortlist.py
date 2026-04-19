"""Shortlist pipeline.

This pipeline is intended to shortlist tickers that will be considered for trading.
It performs initial screening and filtering to create a candidate pool from the
larger universe of available securities.
"""

from __future__ import annotations

import click

from src.config import get_settings
from src.console import console
from src.integrations.sheets import make_sheets_client


@click.group()
def cli() -> None:
    """refinery-pipeline shortlist pipeline."""


@cli.command()
@click.option("--input", "input_path", default=None, help="Input file path or URL.")
@click.option("--output", "output_path", default=None, help="Output file path.")
@click.option("--dry-run", is_flag=True, default=False, help="Log without applying side effects; uses the test sheet.")
def run(input_path: str | None, output_path: str | None, dry_run: bool) -> None:
    """Execute the shortlist pipeline."""
    console.rule("[bold blue]refinery-pipeline shortlist[/bold blue]")
    console.print(f"  [dim]input  :[/dim] {input_path or '—'}")
    console.print(f"  [dim]output :[/dim] {output_path or '—'}")
    console.print(f"  [dim]dry-run:[/dim] {dry_run}")
    console.print()

    settings = get_settings()
    sheets = make_sheets_client(settings, debug=dry_run)

    console.print("[yellow]Shortlisting triggered[/yellow]")
    console.print("[dim]This is a stub implementation. Actual shortlisting logic will be added later.[/dim]")
    _ = sheets

    console.rule("[bold blue]Done[/bold blue]")


if __name__ == "__main__":
    cli()
