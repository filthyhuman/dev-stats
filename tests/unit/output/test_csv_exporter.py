"""Unit tests for CsvExporter."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.models import (
    ClassReport,
    FileReport,
    LanguageSummary,
    MethodReport,
    RepoReport,
)
from dev_stats.output.exporters.csv_exporter import CsvExporter


def _make_report(tmp_path: Path) -> RepoReport:
    """Build a minimal RepoReport for testing."""
    method = MethodReport(
        name="greet",
        line=3,
        end_line=5,
        lines=3,
        cyclomatic_complexity=2,
    )
    cls = ClassReport(
        name="Hello",
        line=1,
        end_line=10,
        lines=10,
        methods=(method,),
        base_classes=("Base",),
    )
    func = MethodReport(
        name="helper",
        line=12,
        end_line=14,
        lines=3,
        cyclomatic_complexity=1,
    )
    file_rpt = FileReport(
        path=Path("src/hello.py"),
        language="python",
        total_lines=20,
        code_lines=15,
        blank_lines=3,
        comment_lines=2,
        classes=(cls,),
        functions=(func,),
    )
    return RepoReport(
        root=tmp_path,
        files=(file_rpt,),
        languages=(
            LanguageSummary(
                language="python",
                file_count=1,
                total_lines=20,
                code_lines=15,
                blank_lines=3,
                comment_lines=2,
            ),
        ),
    )


def _parse_csv(path: Path) -> list[dict[str, str]]:
    """Parse a CSV file into a list of dicts."""
    content = path.read_text()
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


class TestCsvExporter:
    """Tests for CsvExporter."""

    def test_export_creates_four_files(self, tmp_path: Path) -> None:
        """export() creates files.csv, classes.csv, methods.csv, languages.csv."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = CsvExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        created = exporter.export(out_dir)

        names = sorted(p.name for p in created)
        assert names == ["classes.csv", "files.csv", "languages.csv", "methods.csv"]

    def test_files_csv_headers(self, tmp_path: Path) -> None:
        """files.csv has correct column headers."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = CsvExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        rows = _parse_csv(out_dir / "files.csv")
        assert len(rows) == 1
        assert "path" in rows[0]
        assert "language" in rows[0]
        assert "total_lines" in rows[0]
        assert "code_lines" in rows[0]

    def test_files_csv_data(self, tmp_path: Path) -> None:
        """files.csv contains correct file data."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = CsvExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        rows = _parse_csv(out_dir / "files.csv")
        assert rows[0]["path"] == "src/hello.py"
        assert rows[0]["language"] == "python"
        assert rows[0]["total_lines"] == "20"

    def test_classes_csv(self, tmp_path: Path) -> None:
        """classes.csv includes class data."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = CsvExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        rows = _parse_csv(out_dir / "classes.csv")
        assert len(rows) == 1
        assert rows[0]["name"] == "Hello"
        assert rows[0]["base_classes"] == "Base"

    def test_methods_csv(self, tmp_path: Path) -> None:
        """methods.csv includes both class methods and top-level functions."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = CsvExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        rows = _parse_csv(out_dir / "methods.csv")
        assert len(rows) == 2
        names = {r["name"] for r in rows}
        assert "greet" in names
        assert "helper" in names

    def test_methods_csv_class_column(self, tmp_path: Path) -> None:
        """methods.csv shows parent class for class methods, empty for functions."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = CsvExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        rows = _parse_csv(out_dir / "methods.csv")
        by_name = {r["name"]: r for r in rows}
        assert by_name["greet"]["class"] == "Hello"
        assert by_name["helper"]["class"] == ""

    def test_languages_csv(self, tmp_path: Path) -> None:
        """languages.csv includes language breakdown."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = CsvExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        rows = _parse_csv(out_dir / "languages.csv")
        assert len(rows) == 1
        assert rows[0]["language"] == "python"
        assert rows[0]["file_count"] == "1"

    def test_empty_report(self, tmp_path: Path) -> None:
        """Empty report produces CSVs with headers only."""
        report = RepoReport(root=tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = CsvExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        created = exporter.export(out_dir)
        assert len(created) == 4

        for p in created:
            rows = _parse_csv(p)
            assert len(rows) == 0
