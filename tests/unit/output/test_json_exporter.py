"""Unit tests for JsonExporter."""

from __future__ import annotations

import json
from pathlib import Path

from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.models import (
    ClassReport,
    FileReport,
    LanguageSummary,
    MethodReport,
    ModuleReport,
    RepoReport,
)
from dev_stats.output.exporters.json_exporter import JsonExporter


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
    file_rpt = FileReport(
        path=Path("src/hello.py"),
        language="python",
        total_lines=20,
        code_lines=15,
        blank_lines=3,
        comment_lines=2,
        classes=(cls,),
        functions=(),
    )
    return RepoReport(
        root=tmp_path,
        files=(file_rpt,),
        modules=(ModuleReport(name="src", path=Path("src"), files=(file_rpt,)),),
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


class TestJsonExporterFull:
    """Tests for full-mode JSON export."""

    def test_export_creates_file(self, tmp_path: Path) -> None:
        """export() creates dev-stats.json."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        created = exporter.export(out_dir)

        assert len(created) == 1
        assert created[0].name == "dev-stats.json"
        assert created[0].exists()

    def test_output_is_valid_json(self, tmp_path: Path) -> None:
        """The generated file is valid JSON."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats.json").read_text())
        assert isinstance(data, dict)

    def test_full_contains_files(self, tmp_path: Path) -> None:
        """Full export contains file-level data."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats.json").read_text())
        assert "files" in data
        assert len(data["files"]) == 1
        assert data["files"][0]["language"] == "python"

    def test_full_contains_classes_and_methods(self, tmp_path: Path) -> None:
        """Full export includes nested class and method data."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats.json").read_text())
        file_data = data["files"][0]
        assert len(file_data["classes"]) == 1
        assert file_data["classes"][0]["name"] == "Hello"
        assert len(file_data["classes"][0]["methods"]) == 1

    def test_paths_serialised_as_strings(self, tmp_path: Path) -> None:
        """Path objects are serialised as strings."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats.json").read_text())
        assert isinstance(data["root"], str)
        assert isinstance(data["files"][0]["path"], str)


class TestJsonExporterSummary:
    """Tests for summary-mode JSON export."""

    def test_summary_creates_file(self, tmp_path: Path) -> None:
        """Summary mode creates dev-stats-summary.json."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config, summary=True)

        out_dir = tmp_path / "output"
        created = exporter.export(out_dir)

        assert len(created) == 1
        assert created[0].name == "dev-stats-summary.json"

    def test_summary_contains_counts(self, tmp_path: Path) -> None:
        """Summary mode includes aggregate counts."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config, summary=True)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats-summary.json").read_text())
        assert data["files"] == 1
        assert data["total_lines"] == 20
        assert data["code_lines"] == 15
        assert data["classes"] == 1
        assert data["methods"] == 1
        assert data["functions"] == 0

    def test_summary_contains_languages(self, tmp_path: Path) -> None:
        """Summary mode includes language breakdown."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config, summary=True)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats-summary.json").read_text())
        assert len(data["languages"]) == 1
        assert data["languages"][0]["language"] == "python"
