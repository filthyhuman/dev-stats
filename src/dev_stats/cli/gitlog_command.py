"""The ``gitlog`` sub-command."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console


class GitlogCommand:
    """Typer command that analyses the Git log of a repository.

    Skeleton implementation -- body is a no-op until the git subsystem is wired.
    """

    def __call__(
        self,
        repo: Annotated[
            Path,
            typer.Argument(help="Path to the Git repository."),
        ] = Path("."),
        *,
        max_commits: Annotated[
            int,
            typer.Option("--max-commits", help="Max commits to process (0 = all)."),
        ] = 0,
        since: Annotated[
            str | None,
            typer.Option("--since", help="Analyse commits since this date."),
        ] = None,
        output: Annotated[
            Path | None,
            typer.Option("--output", "-o", help="Write report to this file."),
        ] = None,
        config: Annotated[
            Path | None,
            typer.Option("--config", "-c", help="Path to TOML config file."),
        ] = None,
    ) -> None:
        """Analyse the Git log and display commit statistics.

        Args:
            repo: Path to the repository.
            max_commits: Maximum number of commits to process.
            since: Date filter for commits.
            output: Optional output file path.
            config: Optional TOML config file path.
        """
        console = Console()
        console.print(f"[bold]dev-stats gitlog[/bold] -- target: {repo}")
        console.print("[dim]Git-log analysis not yet implemented.[/dim]")
