"""The ``branches`` sub-command."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console


class BranchesCommand:
    """Typer command that analyses branches in a Git repository.

    Skeleton implementation -- body is a no-op until the git subsystem is wired.
    """

    def __call__(
        self,
        repo: Annotated[
            Path,
            typer.Argument(help="Path to the Git repository."),
        ] = Path("."),
        *,
        target: Annotated[
            str,
            typer.Option("--target", "-t", help="Default merge-target branch."),
        ] = "main",
        stale_days: Annotated[
            int,
            typer.Option("--stale-days", help="Days before a branch is stale."),
        ] = 30,
        output: Annotated[
            Path | None,
            typer.Option("--output", "-o", help="Write report to this file."),
        ] = None,
        config: Annotated[
            Path | None,
            typer.Option("--config", "-c", help="Path to TOML config file."),
        ] = None,
    ) -> None:
        """Analyse branches and report stale/abandoned status.

        Args:
            repo: Path to the repository.
            target: Default merge-target branch name.
            stale_days: Inactivity threshold in days.
            output: Optional output file path.
            config: Optional TOML config file path.
        """
        console = Console()
        console.print(f"[bold]dev-stats branches[/bold] -- target: {repo}")
        console.print("[dim]Branch analysis not yet implemented.[/dim]")
