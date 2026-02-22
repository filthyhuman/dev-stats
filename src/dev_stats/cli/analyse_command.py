"""The ``analyse`` sub-command."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.aggregator import Aggregator
from dev_stats.core.dispatcher import Dispatcher
from dev_stats.core.models import RepoReport
from dev_stats.core.parser_registry import create_default_registry
from dev_stats.core.scanner import Scanner
from dev_stats.output.exporters.badge_generator import BadgeGenerator
from dev_stats.output.exporters.csv_exporter import CsvExporter
from dev_stats.output.exporters.json_exporter import JsonExporter
from dev_stats.output.exporters.terminal_reporter import TerminalReporter
from dev_stats.output.exporters.xml_exporter import XmlExporter

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
                help="Output format: json | csv | xml | badges | all.",
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
            fmt: Output format (json, csv, xml, badges, all).
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

        try:
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
            scanner = Scanner(repo_path=repo_path, config=analysis_config)
            paths = list(scanner.scan())

            # Parse
            registry = create_default_registry()
            dispatcher = Dispatcher(registry=registry, repo_root=repo_path)
            file_reports = dispatcher.parse_many(paths)

            # Aggregate
            aggregator = Aggregator()
            report = aggregator.aggregate(files=file_reports, repo_root=repo_path)

            # Terminal output (always shown unless format-only)
            if fmt is None:
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

        except FileNotFoundError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=1) from exc
        except Exception:
            logger.exception("Analysis failed")
            console.print("[red]Analysis failed. See log for details.[/red]")
            raise typer.Exit(code=1) from None

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
            fmt: Format string (json, csv, xml, badges, all).
            report: The RepoReport.
            config: The AnalysisConfig.
            output_dir: Directory to write exports into.
            console: Rich console for status messages.

        Returns:
            List of paths to generated files.
        """
        formats = {fmt} if fmt != "all" else {"json", "csv", "xml", "badges"}
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

        return created
