"""Tests for TeamCityAdapter."""

from __future__ import annotations

from pathlib import Path

from dev_stats.ci.teamcity_adapter import TeamCityAdapter, _escape_tc
from dev_stats.ci.violation import Violation, ViolationSeverity
from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.models import FileReport, RepoReport


def _make_adapter(
    violations: tuple[Violation, ...] = (),
    files: tuple[FileReport, ...] = (),
) -> TeamCityAdapter:
    """Create a TeamCityAdapter pre-loaded with violations."""
    config = AnalysisConfig()
    report = RepoReport(root=Path("."), files=files)
    adapter = TeamCityAdapter(report=report, config=config)
    adapter._violations = violations
    return adapter


class TestEscaping:
    """TeamCity string escaping tests."""

    def test_pipe_escape(self) -> None:
        """Pipes are doubled."""
        assert _escape_tc("a|b") == "a||b"

    def test_quote_escape(self) -> None:
        """Single quotes are escaped."""
        assert _escape_tc("it's") == "it|'s"

    def test_newline_escape(self) -> None:
        """Newlines become |n."""
        assert _escape_tc("a\nb") == "a|nb"

    def test_carriage_return_escape(self) -> None:
        """Carriage returns become |r."""
        assert _escape_tc("a\rb") == "a|rb"

    def test_bracket_escape(self) -> None:
        """Square brackets are escaped."""
        assert _escape_tc("[x]") == "|[x|]"

    def test_combined_escape(self) -> None:
        """Multiple special characters are all escaped."""
        assert _escape_tc("a|b\n[c]") == "a||b|n|[c|]"


class TestEmit:
    """TeamCity service message tests."""

    def test_build_statistic_values(self) -> None:
        """Emit includes buildStatisticValue for LOC, files, violations."""
        f = FileReport(
            path=Path("a.py"),
            language="python",
            total_lines=100,
            code_lines=80,
            blank_lines=10,
            comment_lines=10,
        )
        adapter = _make_adapter(files=(f,))
        output = adapter.emit()

        assert "##teamcity[buildStatisticValue key='LOC' value='100']" in output
        assert "##teamcity[buildStatisticValue key='files' value='1']" in output
        assert "##teamcity[buildStatisticValue key='violations' value='0']" in output

    def test_inspection_type(self) -> None:
        """Each unique rule gets an inspectionType message."""
        v = Violation(rule="max_file_lines", message="too long")
        adapter = _make_adapter((v,))
        output = adapter.emit()

        assert "##teamcity[inspectionType id='max_file_lines'" in output

    def test_inspection_message(self) -> None:
        """Each violation gets an inspection message with severity."""
        v = Violation(
            rule="max_file_lines",
            message="too long",
            file_path="foo.py",
            line=1,
            severity=ViolationSeverity.WARNING,
        )
        adapter = _make_adapter((v,))
        output = adapter.emit()

        assert "##teamcity[inspection " in output
        assert "SEVERITY='WARNING'" in output
        assert "message='too long'" in output

    def test_error_severity_in_inspection(self) -> None:
        """ERROR violations produce SEVERITY='ERROR' inspections."""
        v = Violation(
            rule="max_cc",
            message="complex",
            file_path="bar.py",
            severity=ViolationSeverity.ERROR,
        )
        adapter = _make_adapter((v,))
        output = adapter.emit()

        assert "SEVERITY='ERROR'" in output

    def test_build_problem_for_errors(self) -> None:
        """ERROR violations also produce buildProblem messages."""
        v = Violation(
            rule="max_cc",
            message="complex",
            file_path="bar.py",
            severity=ViolationSeverity.ERROR,
        )
        adapter = _make_adapter((v,))
        output = adapter.emit()

        assert "##teamcity[buildProblem " in output

    def test_no_build_problem_for_warnings(self) -> None:
        """WARNING violations do not produce buildProblem messages."""
        v = Violation(
            rule="max_cc",
            message="complex",
            severity=ViolationSeverity.WARNING,
        )
        adapter = _make_adapter((v,))
        output = adapter.emit()

        assert "buildProblem" not in output

    def test_unique_inspection_types(self) -> None:
        """Duplicate rules produce only one inspectionType message."""
        v1 = Violation(rule="rule_a", message="m1")
        v2 = Violation(rule="rule_a", message="m2")
        adapter = _make_adapter((v1, v2))
        output = adapter.emit()

        assert output.count("inspectionType id='rule_a'") == 1

    def test_empty_violations(self) -> None:
        """With no violations, only buildStatisticValue messages appear."""
        adapter = _make_adapter()
        output = adapter.emit()

        assert "buildStatisticValue" in output
        assert "inspection " not in output
        assert "buildProblem" not in output


class TestWriteReport:
    """File output tests."""

    def test_write_creates_file(self, tmp_path: Path) -> None:
        """write_report creates dev-stats-teamcity.txt."""
        adapter = _make_adapter()

        paths = adapter.write_report(tmp_path)

        assert len(paths) == 1
        assert paths[0].name == "dev-stats-teamcity.txt"
        assert paths[0].exists()
