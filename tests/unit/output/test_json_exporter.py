"""Unit tests for JsonExporter."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.models import (
    ChangeType,
    ClassReport,
    CommitRecord,
    CouplingReport,
    CoverageReport,
    DuplicationReport,
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

    def test_summary_with_duplication(self, tmp_path: Path) -> None:
        """Summary includes duplication_ratio when duplication data present."""
        report = _make_report(tmp_path)
        report = RepoReport(
            root=report.root,
            files=report.files,
            modules=report.modules,
            languages=report.languages,
            duplication=DuplicationReport(duplication_ratio=0.05),
        )
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config, summary=True)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats-summary.json").read_text())
        assert data["duplication_ratio"] == 0.05

    def test_summary_with_coverage(self, tmp_path: Path) -> None:
        """Summary includes coverage_ratio when coverage data present."""
        report = _make_report(tmp_path)
        report = RepoReport(
            root=report.root,
            files=report.files,
            modules=report.modules,
            languages=report.languages,
            coverage=CoverageReport(overall_ratio=0.93),
        )
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config, summary=True)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats-summary.json").read_text())
        assert data["coverage_ratio"] == 0.93

    def test_summary_with_coupling(self, tmp_path: Path) -> None:
        """Summary includes coupling_modules count when coupling data present."""
        report = _make_report(tmp_path)
        report = RepoReport(
            root=report.root,
            files=report.files,
            modules=report.modules,
            languages=report.languages,
            coupling=CouplingReport(modules=()),
        )
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config, summary=True)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats-summary.json").read_text())
        assert data["coupling_modules"] == 0


class TestJsonExporterConversion:
    """Tests for value conversion edge cases."""

    def test_datetime_serialised_as_iso(self, tmp_path: Path) -> None:
        """Datetime fields are serialised as ISO 8601 strings."""
        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        commit = CommitRecord(
            sha="abc123",
            author_name="Test",
            author_email="test@test.com",
            authored_date=dt,
            committer_name="Test",
            committer_email="test@test.com",
            committed_date=dt,
            message="test",
        )
        report = RepoReport(
            root=tmp_path,
            files=(),
            commits=(commit,),
        )
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats.json").read_text())
        assert data["commits"][0]["authored_date"] == "2024-06-15T12:00:00+00:00"

    def test_enum_serialised_as_value(self, tmp_path: Path) -> None:
        """Enum fields are serialised as their .value string."""
        from dev_stats.core.models import FileChange

        change = FileChange(path="x.py", change_type=ChangeType.ADDED)
        commit = CommitRecord(
            sha="abc123",
            author_name="Test",
            author_email="test@test.com",
            authored_date=datetime(2024, 1, 1, tzinfo=UTC),
            committer_name="Test",
            committer_email="test@test.com",
            committed_date=datetime(2024, 1, 1, tzinfo=UTC),
            message="test",
            files=(change,),
        )
        report = RepoReport(root=tmp_path, files=(), commits=(commit,))
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = JsonExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        data = json.loads((out_dir / "dev-stats.json").read_text())
        assert data["commits"][0]["files"][0]["change_type"] == "added"

    def test_json_default_raises_for_unknown(self) -> None:
        """_json_default raises TypeError for unhandled types."""
        with pytest.raises(TypeError, match="not JSON serializable"):
            JsonExporter._json_default(object())

    def test_dataclass_to_dict_raises_for_non_dataclass(self) -> None:
        """_dataclass_to_dict raises TypeError for non-dataclass input."""
        with pytest.raises(TypeError, match="Expected a dataclass"):
            JsonExporter._dataclass_to_dict("not a dataclass")

    def test_convert_unknown_type_falls_back_to_str(self, tmp_path: Path) -> None:
        """Unknown types in _convert_value fall back to str()."""
        result = JsonExporter._convert_value(frozenset({1, 2}))
        assert isinstance(result, str)
