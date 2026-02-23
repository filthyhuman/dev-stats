"""Tests for GitlabAdapter."""

from __future__ import annotations

import json
from pathlib import Path

from dev_stats.ci.gitlab_adapter import GitlabAdapter
from dev_stats.ci.violation import Violation, ViolationSeverity
from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.models import RepoReport


def _make_adapter(
    violations: tuple[Violation, ...] = (),
) -> GitlabAdapter:
    """Create a GitlabAdapter pre-loaded with violations."""
    config = AnalysisConfig()
    report = RepoReport(root=Path("."))
    adapter = GitlabAdapter(report=report, config=config)
    adapter._violations = violations
    return adapter


class TestEmit:
    """GitLab Code Quality JSON tests."""

    def test_valid_json(self) -> None:
        """Emit produces parseable JSON."""
        v = Violation(
            rule="max_file_lines",
            message="too long",
            file_path="foo.py",
            line=42,
            severity=ViolationSeverity.WARNING,
        )
        adapter = _make_adapter((v,))
        data = json.loads(adapter.emit())

        assert isinstance(data, list)
        assert len(data) == 1

    def test_issue_structure(self) -> None:
        """Each issue has the required Code Quality fields."""
        v = Violation(
            rule="max_file_lines",
            message="too long",
            file_path="foo.py",
            line=42,
            severity=ViolationSeverity.WARNING,
        )
        adapter = _make_adapter((v,))
        issues = json.loads(adapter.emit())
        issue = issues[0]

        assert issue["type"] == "issue"
        assert issue["check_name"] == "max_file_lines"
        assert issue["description"] == "too long"
        assert issue["location"]["path"] == "foo.py"
        assert issue["location"]["lines"]["begin"] == 42
        assert "fingerprint" in issue

    def test_fingerprint_deterministic(self) -> None:
        """The same violation always produces the same fingerprint."""
        v = Violation(rule="r", message="m", file_path="f.py", line=1)
        adapter1 = _make_adapter((v,))
        adapter2 = _make_adapter((v,))

        issues1 = json.loads(adapter1.emit())
        issues2 = json.loads(adapter2.emit())

        assert issues1[0]["fingerprint"] == issues2[0]["fingerprint"]

    def test_fingerprint_unique_per_location(self) -> None:
        """Different locations produce different fingerprints."""
        v1 = Violation(rule="r", message="m", file_path="a.py", line=1)
        v2 = Violation(rule="r", message="m", file_path="b.py", line=1)
        adapter = _make_adapter((v1, v2))

        issues = json.loads(adapter.emit())

        assert issues[0]["fingerprint"] != issues[1]["fingerprint"]

    def test_severity_mapping(self) -> None:
        """Our severity levels map to GitLab Code Quality severities."""
        mappings = [
            (ViolationSeverity.INFO, "info"),
            (ViolationSeverity.WARNING, "minor"),
            (ViolationSeverity.ERROR, "major"),
        ]
        for our_sev, gl_sev in mappings:
            v = Violation(rule="r", message="m", severity=our_sev)
            adapter = _make_adapter((v,))
            issues = json.loads(adapter.emit())

            assert issues[0]["severity"] == gl_sev

    def test_empty_violations(self) -> None:
        """No violations produces an empty JSON array."""
        adapter = _make_adapter()
        data = json.loads(adapter.emit())

        assert data == []

    def test_empty_file_path_defaults(self) -> None:
        """An empty file_path defaults to '.' in the location."""
        v = Violation(rule="r", message="m", file_path="", line=0)
        adapter = _make_adapter((v,))
        issues = json.loads(adapter.emit())

        assert issues[0]["location"]["path"] == "."
        assert issues[0]["location"]["lines"]["begin"] == 1


class TestWriteReport:
    """File output tests."""

    def test_write_creates_file(self, tmp_path: Path) -> None:
        """write_report creates gl-code-quality-report.json."""
        adapter = _make_adapter()

        paths = adapter.write_report(tmp_path)

        assert len(paths) == 1
        assert paths[0].name == "gl-code-quality-report.json"
        assert paths[0].exists()
