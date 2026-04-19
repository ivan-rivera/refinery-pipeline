"""Trade pipeline CLI entrypoint."""

from __future__ import annotations

import click

from src.components.filter import filter as apply_filter
from src.components.transform import transform as apply_transform
from src.console import console


@click.group()
def cli() -> None:
    """refinery-pipeline trade pipeline."""


@cli.command()
@click.option("--input", "input_path", default=None, help="Input file path or URL.")
@click.option("--output", "output_path", default=None, help="Output file path.")
@click.option("--dry-run", is_flag=True, default=False, help="Log without applying side effects.")
def run(input_path: str | None, output_path: str | None, dry_run: bool) -> None:
    """Execute the trade pipeline."""
    console.rule("[bold green]refinery-pipeline[/bold green]")
    console.print(f"  [dim]input  :[/dim] {input_path or '—'}")
    console.print(f"  [dim]output :[/dim] {output_path or '—'}")
    console.print(f"  [dim]dry-run:[/dim] {dry_run}")
    console.print()

    filtered_data = apply_filter(None)
    apply_transform(filtered_data)

    if dry_run:
        console.print("[yellow]Dry run — no side effects applied.[/yellow]")
    elif output_path:
        console.print(f"[green]Output destination:[/green] {output_path}")

    console.rule("[bold green]Done[/bold green]")


if __name__ == "__main__":
    cli()
