"""Shortlist pipeline.

This pipeline is intended to shortlist tickers that will be considered for trading.
It performs initial screening and filtering to create a candidate pool from the
larger universe of available securities.
"""

from __future__ import annotations

import click

from src.console import console


@click.group()
def cli() -> None:
    """refinery-pipeline shortlist pipeline."""


@cli.command()
@click.option("--input", "input_path", default=None, help="Input file path or URL.")
@click.option("--output", "output_path", default=None, help="Output file path.")
@click.option("--dry-run", is_flag=True, default=False, help="Log without applying side effects.")
def run(input_path: str | None, output_path: str | None, dry_run: bool) -> None:
    """Execute the shortlist pipeline."""
    console.rule("[bold blue]refinery-pipeline shortlist[/bold blue]")
    console.print(f"  [dim]input  :[/dim] {input_path or '—'}")
    console.print(f"  [dim]output :[/dim] {output_path or '—'}")
    console.print(f"  [dim]dry-run:[/dim] {dry_run}")
    console.print()

    # Stub implementation - just print that shortlisting was triggered
    console.print("[yellow]Shortlisting triggered[/yellow]")
    console.print("[dim]This is a stub implementation. Actual shortlisting logic will be added later.[/dim]")

    if dry_run:
        console.print("[yellow]Dry run — no side effects applied.[/yellow]")
    elif output_path:
        console.print(f"[green]Output destination:[/green] {output_path}")

    console.rule("[bold blue]Done[/bold blue]")


if __name__ == "__main__":
    cli()
