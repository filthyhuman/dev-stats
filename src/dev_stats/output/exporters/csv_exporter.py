"""CSV exporter producing one CSV file per entity type."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

from dev_stats.output.exporters.abstract_exporter import AbstractExporter

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.config.analysis_config import AnalysisConfig
    from dev_stats.core.models import RepoReport


class CsvExporter(AbstractExporter):
    """Exports analysis reports as CSV files.

    Generates separate CSV files for each entity type:

    * ``files.csv`` — per-file line counts and structure counts.
    * ``classes.csv`` — per-class details.
    * ``methods.csv`` — per-method/function details.
    * ``languages.csv`` — per-language breakdown.
    """

    def __init__(
        self,
        report: RepoReport,
        config: AnalysisConfig,
    ) -> None:
        """Initialise the CSV exporter.

        Args:
            report: The analysis report to export.
            config: Analysis configuration.
        """
        super().__init__(report, config)

    def export(self, output_dir: Path) -> list[Path]:
        """Write CSV files to *output_dir*.

        Args:
            output_dir: Directory to write CSV files into.

        Returns:
            List of paths to the generated CSV files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []

        created.append(self._write_files_csv(output_dir))
        created.append(self._write_classes_csv(output_dir))
        created.append(self._write_methods_csv(output_dir))
        created.append(self._write_languages_csv(output_dir))

        return created

    def _write_files_csv(self, output_dir: Path) -> Path:
        """Write files.csv.

        Args:
            output_dir: Output directory.

        Returns:
            Path to the generated file.
        """
        headers = [
            "path",
            "language",
            "total_lines",
            "code_lines",
            "blank_lines",
            "comment_lines",
            "comment_ratio",
            "classes",
            "functions",
        ]

        rows: list[list[str]] = []
        for f in self._report.files:
            rows.append(
                [
                    str(f.path),
                    f.language,
                    str(f.total_lines),
                    str(f.code_lines),
                    str(f.blank_lines),
                    str(f.comment_lines),
                    f"{f.comment_ratio:.4f}",
                    str(f.num_classes),
                    str(f.num_functions),
                ]
            )

        return self._write_csv(output_dir / "files.csv", headers, rows)

    def _write_classes_csv(self, output_dir: Path) -> Path:
        """Write classes.csv.

        Args:
            output_dir: Output directory.

        Returns:
            Path to the generated file.
        """
        headers = [
            "file",
            "name",
            "line",
            "end_line",
            "lines",
            "methods",
            "attributes",
            "base_classes",
        ]

        rows: list[list[str]] = []
        for f in self._report.files:
            for cls in f.classes:
                rows.append(
                    [
                        str(f.path),
                        cls.name,
                        str(cls.line),
                        str(cls.end_line),
                        str(cls.lines),
                        str(cls.num_methods),
                        str(cls.num_attributes),
                        "; ".join(cls.base_classes),
                    ]
                )

        return self._write_csv(output_dir / "classes.csv", headers, rows)

    def _write_methods_csv(self, output_dir: Path) -> Path:
        """Write methods.csv.

        Args:
            output_dir: Output directory.

        Returns:
            Path to the generated file.
        """
        headers = [
            "file",
            "class",
            "name",
            "line",
            "end_line",
            "lines",
            "parameters",
            "cyclomatic_complexity",
            "cognitive_complexity",
            "nesting_depth",
            "is_constructor",
        ]

        rows: list[list[str]] = []
        for f in self._report.files:
            for cls in f.classes:
                for m in cls.methods:
                    rows.append(
                        [
                            str(f.path),
                            cls.name,
                            m.name,
                            str(m.line),
                            str(m.end_line),
                            str(m.lines),
                            str(m.num_parameters),
                            str(m.cyclomatic_complexity),
                            str(m.cognitive_complexity),
                            str(m.nesting_depth),
                            str(m.is_constructor),
                        ]
                    )
            for func in f.functions:
                rows.append(
                    [
                        str(f.path),
                        "",
                        func.name,
                        str(func.line),
                        str(func.end_line),
                        str(func.lines),
                        str(func.num_parameters),
                        str(func.cyclomatic_complexity),
                        str(func.cognitive_complexity),
                        str(func.nesting_depth),
                        str(func.is_constructor),
                    ]
                )

        return self._write_csv(output_dir / "methods.csv", headers, rows)

    def _write_languages_csv(self, output_dir: Path) -> Path:
        """Write languages.csv.

        Args:
            output_dir: Output directory.

        Returns:
            Path to the generated file.
        """
        headers = [
            "language",
            "file_count",
            "total_lines",
            "code_lines",
            "blank_lines",
            "comment_lines",
        ]

        rows: list[list[str]] = []
        for lang in self._report.languages:
            rows.append(
                [
                    lang.language,
                    str(lang.file_count),
                    str(lang.total_lines),
                    str(lang.code_lines),
                    str(lang.blank_lines),
                    str(lang.comment_lines),
                ]
            )

        return self._write_csv(output_dir / "languages.csv", headers, rows)

    @staticmethod
    def _write_csv(
        path: Path,
        headers: list[str],
        rows: list[list[str]],
    ) -> Path:
        """Write a single CSV file.

        Args:
            path: Output file path.
            headers: Column headers.
            rows: Data rows.

        Returns:
            The path written to.
        """
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        writer.writerows(rows)
        path.write_text(buf.getvalue())
        return path
