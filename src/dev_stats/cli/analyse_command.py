"""The ``analyse`` sub-command."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console


class AnalyseCommand:
    """Typer command that analyses a repository and reports code metrics.

    All CLI flags are declared here. The body is a no-op placeholder until
    the core pipeline is wired in.
    """

    def __call__(
        self,
        repo: Annotated[
            Path,
            typer.Argument(help="Path to the Git repository to analyse."),
        ] = Path("."),
        *,
        output: Annotated[
            Path | None,
            typer.Option("--output", "-o", help="Write report to this file."),
        ] = None,
        ci: Annotated[
            str | None,
            typer.Option(
                "--ci",
                help="CI format: jenkins | gitlab | teamcity | github.",
            ),
        ] = None,
        config: Annotated[
            Path | None,
            typer.Option("--config", "-c", help="Path to TOML config file."),
        ] = None,
        exclude: Annotated[
            list[str] | None,
            typer.Option("--exclude", "-e", help="Glob patterns to exclude."),
        ] = None,
        top: Annotated[
            int,
            typer.Option("--top", "-n", help="Number of top items to show."),
        ] = 20,
        lang: Annotated[
            list[str] | None,
            typer.Option("--lang", "-l", help="Language filter."),
        ] = None,
        diff: Annotated[
            str | None,
            typer.Option("--diff", help="Compare against a branch or commit."),
        ] = None,
        fail_on_violations: Annotated[
            bool,
            typer.Option(
                "--fail-on-violations",
                help="Exit non-zero when violations are found.",
            ),
        ] = False,
        watch: Annotated[
            bool,
            typer.Option("--watch", "-w", help="Re-run on file changes."),
        ] = False,
        since: Annotated[
            str | None,
            typer.Option("--since", help="Analyse commits since this date."),
        ] = None,
    ) -> None:
        """Analyse a Git repository and display code statistics.

        Args:
            repo: Path to the repository.
            output: Optional output file path.
            ci: Optional CI adapter name.
            config: Optional TOML config file path.
            exclude: Glob patterns to exclude.
            top: Number of top items in tables.
            lang: Language filter list.
            diff: Branch or commit to diff against.
            fail_on_violations: Whether to fail on violations.
            watch: Re-run on file changes.
            since: Date filter for commits.
        """
        console = Console()
        console.print(f"[bold]dev-stats analyse[/bold] -- target: {repo}")
        console.print("[dim]Analysis pipeline not yet implemented.[/dim]")
