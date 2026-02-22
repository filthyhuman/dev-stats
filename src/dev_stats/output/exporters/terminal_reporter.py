"""Terminal reporter using Rich for formatted console output."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dev_stats.output.exporters.abstract_exporter import AbstractExporter

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.config.analysis_config import AnalysisConfig
    from dev_stats.core.models import RepoReport


class TerminalReporter(AbstractExporter):
    """Prints analysis results to the terminal using Rich.

    Renders a hero panel with summary stats, a language breakdown table,
    and top-N lists for files, classes, and methods.
    """

    def __init__(
        self,
        report: RepoReport,
        config: AnalysisConfig,
        console: Console | None = None,
    ) -> None:
        """Initialise the terminal reporter.

        Args:
            report: The analysis report to display.
            config: Analysis configuration.
            console: Optional Rich console (defaults to stdout).
        """
        super().__init__(report, config)
        self._console = console or Console()
        self._top_n = config.output.top_n

    def export(self, output_dir: Path) -> list[Path]:
        """Print the report to the terminal.

        Args:
            output_dir: Unused (terminal output only).

        Returns:
            Empty list (no files produced).
        """
        self._print_hero()
        self._print_language_table()
        self._print_top_files()
        self._print_top_methods()
        return []

    def _print_hero(self) -> None:
        """Print summary hero panel."""
        rpt = self._report
        total_files = len(rpt.files)
        total_lines = sum(f.total_lines for f in rpt.files)
        code_lines = sum(f.code_lines for f in rpt.files)
        total_classes = sum(f.num_classes for f in rpt.files)
        total_functions = sum(f.num_functions for f in rpt.files)
        total_methods = sum(len(c.methods) for f in rpt.files for c in f.classes)
        num_languages = len(rpt.languages)

        lines = [
            f"[bold]Files:[/bold] {total_files}",
            f"[bold]Total lines:[/bold] {total_lines:,}",
            f"[bold]Code lines:[/bold] {code_lines:,}",
            f"[bold]Classes:[/bold] {total_classes}",
            f"[bold]Methods:[/bold] {total_methods}",
            f"[bold]Functions:[/bold] {total_functions}",
            f"[bold]Languages:[/bold] {num_languages}",
        ]
        panel = Panel("\n".join(lines), title="dev-stats", border_style="blue")
        self._console.print(panel)

    def _print_language_table(self) -> None:
        """Print per-language breakdown table."""
        if not self._report.languages:
            return

        table = Table(title="Languages", show_lines=False)
        table.add_column("Language", style="cyan")
        table.add_column("Files", justify="right")
        table.add_column("Code", justify="right")
        table.add_column("Comment", justify="right")
        table.add_column("Blank", justify="right")
        table.add_column("Total", justify="right")

        for lang in self._report.languages:
            table.add_row(
                lang.language,
                str(lang.file_count),
                f"{lang.code_lines:,}",
                f"{lang.comment_lines:,}",
                f"{lang.blank_lines:,}",
                f"{lang.total_lines:,}",
            )

        self._console.print(table)

    def _print_top_files(self) -> None:
        """Print top-N files by total lines."""
        files = sorted(self._report.files, key=lambda f: f.total_lines, reverse=True)
        top = files[: self._top_n]
        if not top:
            return

        table = Table(title=f"Top {len(top)} Files by LOC")
        table.add_column("File", style="green")
        table.add_column("Language")
        table.add_column("Lines", justify="right")
        table.add_column("Code", justify="right")
        table.add_column("Classes", justify="right")
        table.add_column("Functions", justify="right")

        for f in top:
            table.add_row(
                str(f.path),
                f.language,
                str(f.total_lines),
                str(f.code_lines),
                str(f.num_classes),
                str(f.num_functions),
            )

        self._console.print(table)

    def _print_top_methods(self) -> None:
        """Print top-N methods by cyclomatic complexity."""
        methods: list[tuple[str, str, int]] = []
        for f in self._report.files:
            for cls in f.classes:
                for m in cls.methods:
                    methods.append((f"{cls.name}.{m.name}", str(f.path), m.cyclomatic_complexity))
            for func in f.functions:
                methods.append((func.name, str(f.path), func.cyclomatic_complexity))

        methods.sort(key=lambda x: x[2], reverse=True)
        top = methods[: self._top_n]
        if not top:
            return

        table = Table(title=f"Top {len(top)} Functions by Complexity")
        table.add_column("Function", style="yellow")
        table.add_column("File")
        table.add_column("CC", justify="right")

        for name, file_path, cc in top:
            table.add_row(name, file_path, str(cc))

        self._console.print(table)
