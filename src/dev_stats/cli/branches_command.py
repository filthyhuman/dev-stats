"""The ``branches`` sub-command."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.git.branch_analyzer import BranchAnalyzer

logger = logging.getLogger(__name__)


class BranchesCommand:
    """Typer command that analyses branches in a Git repository.

    Lists branches with their merge status, activity, and deletability
    scores. Can filter by status (merged, stale, abandoned).
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
        show: Annotated[
            str | None,
            typer.Option("--show", help="Filter: merged | stale | abandoned | all."),
        ] = None,
        generate_script: Annotated[
            bool,
            typer.Option("--generate-script", help="Write cleanup_branches.sh."),
        ] = False,
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
            show: Optional status filter.
            generate_script: Write a cleanup script.
            output: Optional output file path.
            config: Optional TOML config file path.
        """
        console = Console()
        repo_path = repo.resolve()

        try:
            analysis_config = AnalysisConfig.load(
                config_path=config,
                repo_path=repo_path,
            )
            branch_config = analysis_config.branches.model_copy(
                update={
                    "default_target": target,
                    "stale_days": stale_days,
                }
            )

            analyzer = BranchAnalyzer(
                repo_path=repo_path,
                config=branch_config,
            )
            report = analyzer.analyse()

            # Filter branches
            branches = list(report.branches)
            if show == "merged":
                branches = [b for b in branches if b.merge_status.is_merged]
            elif show == "stale":
                branches = [b for b in branches if b.status.value == "stale"]
            elif show == "abandoned":
                branches = [b for b in branches if b.status.value == "abandoned"]

            # Summary
            console.print(f"[bold]dev-stats branches[/bold] -- {report.total_branches} branches")
            console.print(
                f"[dim]Stale: {report.stale_count} | "
                f"Abandoned: {report.abandoned_count} | "
                f"Deletable: {report.deletable_count}[/dim]"
            )

            # Table
            if branches:
                table = Table(title="Branch Analysis")
                table.add_column("Branch", style="cyan")
                table.add_column("Status")
                table.add_column("Merged")
                table.add_column("Ahead", justify="right")
                table.add_column("Behind", justify="right")
                table.add_column("Score", justify="right")
                table.add_column("Action")
                table.add_column("Author")

                for b in branches:
                    merged = "[green]Yes[/green]" if b.merge_status.is_merged else "No"
                    status_style = {
                        "active": "[green]Active[/green]",
                        "stale": "[yellow]Stale[/yellow]",
                        "abandoned": "[red]Abandoned[/red]",
                    }.get(b.status.value, b.status.value)
                    action_style = {
                        "safe": "[green]Delete[/green]",
                        "caution": "[yellow]Review[/yellow]",
                        "keep": "[dim]Keep[/dim]",
                    }.get(b.deletability_category.value, "")

                    table.add_row(
                        b.name,
                        status_style,
                        merged,
                        str(b.commits_ahead),
                        str(b.commits_behind),
                        f"{b.deletability_score:.0f}",
                        action_style,
                        b.author_name,
                    )

                console.print(table)

            # Generate cleanup script
            if generate_script:
                self._write_cleanup_script(report, repo_path, console)

        except FileNotFoundError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=1) from exc
        except Exception:
            logger.exception("Branch analysis failed")
            console.print("[red]Branch analysis failed. See log for details.[/red]")
            raise typer.Exit(code=1) from None

    @staticmethod
    def _write_cleanup_script(
        report: object,
        repo_path: Path,
        console: Console,
    ) -> None:
        """Write a cleanup_branches.sh script.

        Args:
            report: The BranchesReport.
            repo_path: Repository root.
            console: Rich console for output.
        """
        from dev_stats.core.models import BranchesReport

        assert isinstance(report, BranchesReport)

        script_path = repo_path / "cleanup_branches.sh"
        lines = ["#!/bin/bash", "# Auto-generated by dev-stats", ""]
        deletable = [b for b in report.branches if b.deletability_category.value == "safe"]

        if not deletable:
            lines.append("echo 'No branches recommended for deletion.'")
        else:
            for b in deletable:
                lines.append(f'echo "Deleting branch: {b.name}"')
                lines.append(f"git branch -d {b.name}")

        lines.append("")
        script_path.write_text("\n".join(lines))
        script_path.chmod(0o755)
        console.print(f"  [green]wrote[/green] {script_path}")
