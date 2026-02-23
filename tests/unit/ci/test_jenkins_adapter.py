"""Tests for JenkinsAdapter."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from dev_stats.ci.jenkins_adapter import JenkinsAdapter
from dev_stats.ci.violation import Violation, ViolationSeverity
from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.models import RepoReport


def _make_adapter(
    violations: tuple[Violation, ...] = (),
) -> JenkinsAdapter:
    """Create a JenkinsAdapter pre-loaded with violations."""
    config = AnalysisConfig()
    report = RepoReport(root=Path("."))
    adapter = JenkinsAdapter(report=report, config=config)
    adapter._violations = violations
    return adapter


class TestEmit:
    """JUnit XML output tests."""

    def test_valid_xml(self) -> None:
        """Emit produces parseable XML."""
        v = Violation(
            rule="max_file_lines",
            message="too long",
            file_path="foo.py",
            line=1,
            severity=ViolationSeverity.ERROR,
        )
        adapter = _make_adapter((v,))
        xml_str = adapter.emit()

        root = ET.fromstring(xml_str)
        assert root.tag == "testsuites"

    def test_testsuite_structure(self) -> None:
        """The testsuite element has correct attributes."""
        v = Violation(
            rule="max_file_lines",
            message="too long",
            file_path="foo.py",
            severity=ViolationSeverity.WARNING,
        )
        adapter = _make_adapter((v,))
        root = ET.fromstring(adapter.emit())

        suite = root.find("testsuite")
        assert suite is not None
        assert suite.get("name") == "dev-stats"
        assert suite.get("tests") == "1"

    def test_failure_counts(self) -> None:
        """Failure/warning counts are correct."""
        violations = (
            Violation(rule="r1", message="m", severity=ViolationSeverity.ERROR),
            Violation(rule="r2", message="m", severity=ViolationSeverity.WARNING),
            Violation(rule="r3", message="m", severity=ViolationSeverity.ERROR),
        )
        adapter = _make_adapter(violations)
        root = ET.fromstring(adapter.emit())

        suite = root.find("testsuite")
        assert suite is not None
        assert suite.get("failures") == "2"
        assert suite.get("warnings") == "1"

    def test_failure_element(self) -> None:
        """An ERROR violation produces a <failure> element with details."""
        v = Violation(
            rule="max_file_lines",
            message="too long",
            file_path="foo.py",
            line=42,
            severity=ViolationSeverity.ERROR,
            value=600.0,
            threshold=500.0,
        )
        adapter = _make_adapter((v,))
        root = ET.fromstring(adapter.emit())

        tc = root.find(".//testcase")
        assert tc is not None
        assert tc.get("classname") == "foo.py"
        assert tc.get("name") == "max_file_lines"

        fail = tc.find("failure")
        assert fail is not None
        assert fail.get("message") == "too long"
        assert "Rule: max_file_lines" in (fail.text or "")
        assert "Value: 600.0" in (fail.text or "")
        assert "Threshold: 500.0" in (fail.text or "")

    def test_no_failure_for_info(self) -> None:
        """An INFO violation produces no <failure> element."""
        v = Violation(
            rule="info_rule",
            message="fyi",
            severity=ViolationSeverity.INFO,
        )
        adapter = _make_adapter((v,))
        root = ET.fromstring(adapter.emit())

        tc = root.find(".//testcase")
        assert tc is not None
        assert tc.find("failure") is None

    def test_empty_file_path_uses_repo(self) -> None:
        """When file_path is empty, classname falls back to 'repo'."""
        v = Violation(rule="r", message="m", file_path="")
        adapter = _make_adapter((v,))
        root = ET.fromstring(adapter.emit())

        tc = root.find(".//testcase")
        assert tc is not None
        assert tc.get("classname") == "repo"


class TestWriteReport:
    """File output tests."""

    def test_write_creates_file(self, tmp_path: Path) -> None:
        """write_report creates dev-stats-junit.xml."""
        v = Violation(rule="r", message="m", severity=ViolationSeverity.WARNING)
        adapter = _make_adapter((v,))

        paths = adapter.write_report(tmp_path)

        assert len(paths) == 1
        assert paths[0].name == "dev-stats-junit.xml"
        assert paths[0].exists()
        assert paths[0].read_text(encoding="utf-8").startswith("<?xml")
