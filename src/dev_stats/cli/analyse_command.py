"""The ``analyse`` sub-command."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.aggregator import Aggregator
from dev_stats.core.dispatcher import Dispatcher
from dev_stats.core.parser_registry import create_default_registry
from dev_stats.core.scanner import Scanner
from dev_stats.output.dashboard.dashboard_builder import DashboardBuilder
from dev_stats.output.exporters.badge_generator import BadgeGenerator
from dev_stats.output.exporters.csv_exporter import CsvExporter
from dev_stats.output.exporters.json_exporter import JsonExporter
from dev_stats.output.exporters.terminal_reporter import TerminalReporter
from dev_stats.output.exporters.xml_exporter import XmlExporter

if TYPE_CHECKING:
    from dev_stats.ci.abstract_ci_adapter import AbstractCIAdapter
    from dev_stats.core.models import FileReport, RepoReport

logger = logging.getLogger(__name__)


class AnalyseCommand:
    """Typer command that analyses a repository and reports code metrics.

    Runs the full pipeline: Scanner -> Dispatcher -> Aggregator -> Reporter.
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
            typer.Option("--output", "-o", help="Output directory for exports."),
        ] = None,
        fmt: Annotated[
            str | None,
            typer.Option(
                "--format",
                "-f",
                help="Output format: json | csv | xml | badges | dashboard | all.",
            ),
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
            output: Optional output directory for exports.
            fmt: Output format (json, csv, xml, badges, dashboard, all).
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
        repo_path = repo.resolve()
        _fail_exit = False

        try:
            console.print("[bold]Loading configuration...[/bold]")
            analysis_config = AnalysisConfig.load(
                config_path=config,
                repo_path=repo_path,
                exclude_patterns=tuple(exclude) if exclude else None,
                languages=tuple(lang) if lang else None,
            )
            if top != 20:
                analysis_config = analysis_config.model_copy(
                    update={"output": analysis_config.output.model_copy(update={"top_n": top})}
                )

            # Scan
            console.print("[bold]Scanning files...[/bold]")
            scanner = Scanner(repo_path=repo_path, config=analysis_config)
            paths = list(scanner.scan())
            console.print(f"  Found {len(paths)} file(s)")

            # Parse
            registry = create_default_registry()
            dispatcher = Dispatcher(registry=registry, repo_root=repo_path)
            file_reports: list[FileReport] = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold]Parsing files...[/bold]"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("[dim]{task.completed}/{task.total}[/dim]"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Parsing", total=len(paths))
                for path in paths:
                    try:
                        file_reports.append(dispatcher.parse(path))
                    except Exception:
                        logger.exception("Failed to parse %s", path)
                    progress.advance(task)
            console.print(f"  Parsed {len(file_reports)} file(s)")

            # Aggregate
            console.print("[bold]Aggregating results...[/bold]")
            aggregator = Aggregator()
            report = aggregator.aggregate(files=file_reports, repo_root=repo_path)

            # Terminal output (always shown unless format-only)
            if fmt is None:
                console.print("[bold]Generating terminal report...[/bold]")
                reporter = TerminalReporter(
                    report=report,
                    config=analysis_config,
                    console=console,
                )
                reporter.export(output_dir=repo_path)

            # Format exports
            if fmt is not None:
                output_dir = output if output is not None else repo_path / "dev-stats-output"
                created = self._run_exporters(
                    fmt=fmt,
                    report=report,
                    config=analysis_config,
                    output_dir=output_dir,
                    console=console,
                )
                for p in created:
                    console.print(f"  [green]wrote[/green] {p}")

            # CI adapter
            if ci is not None or fail_on_violations:
                console.print("[bold]Checking quality gates...[/bold]")
                adapter = self._create_ci_adapter(
                    name=ci or "github",
                    report=report,
                    config=analysis_config,
                )
                adapter.check_violations()

                # Delta mode: filter to changed files only
                if diff is not None:
                    diff_files = self._get_diff_files(repo_path, diff)
                    adapter._violations = tuple(
                        v
                        for v in adapter.violations
                        if not v.file_path or v.file_path in diff_files
                    )

                if ci is not None:
                    console.print(adapter.emit(), markup=False, highlight=False)
                    ci_output_dir = output if output is not None else repo_path / "dev-stats-output"
                    created_ci = adapter.write_report(ci_output_dir)
                    for p in created_ci:
                        console.print(f"  [green]wrote[/green] {p}")

                if fail_on_violations and adapter.violations:
                    from dev_stats.ci.violation import ViolationSeverity

                    error_count = sum(
                        1 for v in adapter.violations if v.severity == ViolationSeverity.ERROR
                    )
                    warn_count = sum(
                        1 for v in adapter.violations if v.severity == ViolationSeverity.WARNING
                    )
                    console.print(
                        f"[red]Quality gate failed:[/red] "
                        f"{error_count} error(s), {warn_count} warning(s)"
                    )
                    _fail_exit = True

        except FileNotFoundError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=1) from exc
        except Exception:
            logger.exception("Analysis failed")
            console.print("[red]Analysis failed. See log for details.[/red]")
            raise typer.Exit(code=1) from None

        if _fail_exit:
            raise typer.Exit(code=1)

    @staticmethod
    def _run_exporters(
        fmt: str,
        report: RepoReport,
        config: AnalysisConfig,
        output_dir: Path,
        console: Console,
    ) -> list[Path]:
        """Dispatch to the requested exporter(s).

        Args:
            fmt: Format string (json, csv, xml, badges, dashboard, all).
            report: The RepoReport.
            config: The AnalysisConfig.
            output_dir: Directory to write exports into.
            console: Rich console for status messages.

        Returns:
            List of paths to generated files.
        """
        formats = {fmt} if fmt != "all" else {"json", "csv", "xml", "badges", "dashboard"}
        created: list[Path] = []

        if "json" in formats:
            console.print("[bold]Exporting JSON...[/bold]")
            exporter = JsonExporter(report=report, config=config)
            created.extend(exporter.export(output_dir))
            summary_exp = JsonExporter(report=report, config=config, summary=True)
            created.extend(summary_exp.export(output_dir))

        if "csv" in formats:
            console.print("[bold]Exporting CSV...[/bold]")
            exporter_csv = CsvExporter(report=report, config=config)
            created.extend(exporter_csv.export(output_dir))

        if "xml" in formats:
            console.print("[bold]Exporting XML...[/bold]")
            exporter_xml = XmlExporter(report=report, config=config)
            created.extend(exporter_xml.export(output_dir))

        if "badges" in formats:
            console.print("[bold]Generating badges...[/bold]")
            badge_gen = BadgeGenerator(report=report, config=config)
            created.extend(badge_gen.export(output_dir))

        if "dashboard" in formats:
            console.print("[bold]Building dashboard...[/bold]")
            dashboard = DashboardBuilder(report=report, config=config)
            created.extend(dashboard.export(output_dir))

        return created

    @staticmethod
    def _create_ci_adapter(
        name: str,
        report: RepoReport,
        config: AnalysisConfig,
    ) -> AbstractCIAdapter:
        """Create a CI adapter by name.

        Args:
            name: Adapter name (jenkins, gitlab, teamcity, github).
            report: The analysis report.
            config: Analysis configuration.

        Returns:
            Concrete CI adapter instance.

        Raises:
            ValueError: If *name* is not a recognised adapter.
        """
        from dev_stats.ci.github_actions_adapter import GithubActionsAdapter
        from dev_stats.ci.gitlab_adapter import GitlabAdapter
        from dev_stats.ci.jenkins_adapter import JenkinsAdapter
        from dev_stats.ci.teamcity_adapter import TeamCityAdapter

        adapters: dict[str, type[AbstractCIAdapter]] = {
            "jenkins": JenkinsAdapter,
            "gitlab": GitlabAdapter,
            "teamcity": TeamCityAdapter,
            "github": GithubActionsAdapter,
        }

        adapter_cls = adapters.get(name)
        if adapter_cls is None:
            msg = f"Unknown CI adapter: {name!r}. Choose from: {', '.join(sorted(adapters))}"
            raise ValueError(msg)

        return adapter_cls(report=report, config=config)

    @staticmethod
    def _get_diff_files(repo_path: Path, base_ref: str) -> set[str]:
        """Get files changed between *base_ref* and HEAD.

        Args:
            repo_path: Path to the Git repository.
            base_ref: Base branch or commit reference.

        Returns:
            Set of changed file paths (relative to repo root).
        """
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(repo_path),
        )
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
