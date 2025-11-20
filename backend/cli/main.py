from __future__ import annotations

from importlib import metadata

import typer
from rich.console import Console

from app.logging_config import setup_logging

# Configure logging with INFO level
setup_logging(log_level="INFO")

console = Console()

app = typer.Typer(
    help="Job Apply Assistant CLI - Tools for scraping and managing job data",
    rich_markup_mode="rich",
)


def _version_callback(value: bool) -> None:
    if not value:
        return

    try:
        cli_version = metadata.version("job-apply-assistant-backend")
    except metadata.PackageNotFoundError:
        cli_version = "0.0.0"

    console.print(f"[bold cyan]Job Apply Assistant CLI[/] v{cli_version}")
    raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the CLI version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Root callback for shared CLI options."""
    return


# Import command modules so they can register with the Typer app.
from . import register as _register  # noqa: E402,F401
from . import scrape as _scrape  # noqa: E402,F401


if __name__ == "__main__":
    app()
