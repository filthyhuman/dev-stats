"""The ``gitlog`` sub-command."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from dev_stats.core.git.commit_enricher import CommitEnricher
from dev_stats.core.git.log_harvester import LogHarvester

logger = logging.getLogger(__name__)


class GitlogCommand:
    """Typer command that analyses the Git log of a repository.

    Harvests commit records, enriches them with metadata, and displays
    a summary table in the terminal.
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
        repo_path = repo.resolve()

        try:
            harvester = LogHarvester(repo_path=repo_path)
            commits = harvester.harvest(
                max_commits=max_commits,
                since=since,
            )

            if not commits:
                console.print("[yellow]No commits found.[/yellow]")
                return

            enricher = CommitEnricher()
            enriched = enricher.enrich(commits)

            # Summary
            console.print(
                f"[bold]dev-stats gitlog[/bold] -- {len(commits)} commits from {repo_path.name}"
            )

            # Branch info
            branch = harvester.current_branch()
            console.print(f"[dim]Branch:[/dim] {branch}")

            # Commit type breakdown
            merges = sum(1 for e in enriched if e.is_merge)
            reverts = sum(1 for e in enriched if e.is_revert)
            fixups = sum(1 for e in enriched if e.is_fixup)
            console.print(f"[dim]Merges: {merges} | Reverts: {reverts} | Fixups: {fixups}[/dim]")

            # Top commits by churn
            table = Table(title="Recent Commits")
            table.add_column("SHA", style="cyan", max_width=8)
            table.add_column("Author")
            table.add_column("Date")
            table.add_column("+/-", justify="right")
            table.add_column("Size")
            table.add_column("Subject", max_width=50)

            for ec in enriched[:20]:
                c = ec.commit
                table.add_row(
                    c.sha[:8],
                    c.author_name,
                    c.authored_date.strftime("%Y-%m-%d"),
                    f"+{c.insertions}/-{c.deletions}",
                    ec.size_category.value,
                    c.message.split("\n", 1)[0][:50],
                )

            console.print(table)

        except FileNotFoundError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=1) from exc
        except Exception:
            logger.exception("Gitlog analysis failed")
            console.print("[red]Gitlog analysis failed. See log for details.[/red]")
            raise typer.Exit(code=1) from None
