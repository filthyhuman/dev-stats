"""Unit tests for XmlExporter."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.models import (
    ClassReport,
    FileReport,
    MethodReport,
    RepoReport,
)
from dev_stats.output.exporters.xml_exporter import XmlExporter


def _make_report(
    tmp_path: Path,
    *,
    cc: int = 2,
    method_lines: int = 10,
    file_lines: int = 50,
) -> RepoReport:
    """Build a minimal RepoReport for testing."""
    method = MethodReport(
        name="process",
        line=3,
        end_line=3 + method_lines - 1,
        lines=method_lines,
        cyclomatic_complexity=cc,
    )
    cls = ClassReport(
        name="Worker",
        line=1,
        end_line=file_lines,
        lines=file_lines,
        methods=(method,),
    )
    file_rpt = FileReport(
        path=Path("src/worker.py"),
        language="python",
        total_lines=file_lines,
        code_lines=file_lines - 5,
        blank_lines=3,
        comment_lines=2,
        classes=(cls,),
    )
    return RepoReport(root=tmp_path, files=(file_rpt,))


class TestXmlExporter:
    """Tests for XmlExporter."""

    def test_export_creates_file(self, tmp_path: Path) -> None:
        """export() creates dev-stats.xml."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = XmlExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        created = exporter.export(out_dir)

        assert len(created) == 1
        assert created[0].name == "dev-stats.xml"
        assert created[0].exists()

    def test_output_is_valid_xml(self, tmp_path: Path) -> None:
        """The generated file is valid XML."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = XmlExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        tree = ET.parse(str(out_dir / "dev-stats.xml"))
        root = tree.getroot()
        assert root.tag == "testsuites"

    def test_junit_structure(self, tmp_path: Path) -> None:
        """Output follows JUnit XML structure with testsuites/testsuite/testcase."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = XmlExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        tree = ET.parse(str(out_dir / "dev-stats.xml"))
        root = tree.getroot()

        suites = root.findall("testsuite")
        assert len(suites) == 1
        assert suites[0].get("name") == "src/worker.py"

        cases = suites[0].findall("testcase")
        assert len(cases) >= 1

    def test_no_failures_under_thresholds(self, tmp_path: Path) -> None:
        """Clean report has no failures."""
        report = _make_report(tmp_path, cc=2, method_lines=10, file_lines=50)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = XmlExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        tree = ET.parse(str(out_dir / "dev-stats.xml"))
        root = tree.getroot()
        assert root.get("failures") == "0"

    def test_complexity_violation(self, tmp_path: Path) -> None:
        """High complexity produces a failure element."""
        report = _make_report(tmp_path, cc=25)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = XmlExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        tree = ET.parse(str(out_dir / "dev-stats.xml"))
        root = tree.getroot()
        failures = root.findall(".//failure[@type='CyclomaticComplexity']")
        assert len(failures) >= 1

    def test_file_size_violation(self, tmp_path: Path) -> None:
        """Large file produces a FileTooLarge failure."""
        report = _make_report(tmp_path, file_lines=600)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = XmlExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        tree = ET.parse(str(out_dir / "dev-stats.xml"))
        root = tree.getroot()
        failures = root.findall(".//failure[@type='FileTooLarge']")
        assert len(failures) == 1

    def test_method_length_violation(self, tmp_path: Path) -> None:
        """Long method produces a MethodTooLong failure."""
        report = _make_report(tmp_path, method_lines=100)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = XmlExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        tree = ET.parse(str(out_dir / "dev-stats.xml"))
        root = tree.getroot()
        failures = root.findall(".//failure[@type='MethodTooLong']")
        assert len(failures) == 1

    def test_empty_report(self, tmp_path: Path) -> None:
        """Empty report produces valid XML with zero tests."""
        report = RepoReport(root=tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        exporter = XmlExporter(report=report, config=config)

        out_dir = tmp_path / "output"
        exporter.export(out_dir)

        tree = ET.parse(str(out_dir / "dev-stats.xml"))
        root = tree.getroot()
        assert root.get("tests") == "0"
        assert root.get("failures") == "0"
