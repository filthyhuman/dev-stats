"""Tests for GithubActionsAdapter."""

from __future__ import annotations

from pathlib import Path

from dev_stats.ci.github_actions_adapter import GithubActionsAdapter
from dev_stats.ci.violation import Violation, ViolationSeverity
from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.models import FileReport, RepoReport


def _make_adapter(
    violations: tuple[Violation, ...] = (),
    files: tuple[FileReport, ...] = (),
) -> GithubActionsAdapter:
    """Create a GithubActionsAdapter pre-loaded with violations."""
    config = AnalysisConfig()
    report = RepoReport(root=Path("."), files=files)
    adapter = GithubActionsAdapter(report=report, config=config)
    adapter._violations = violations
    return adapter


class TestEmit:
    """GitHub Actions annotation tests."""

    def test_error_annotation(self) -> None:
        """An ERROR violation produces an ::error annotation."""
        v = Violation(
            rule="max_cc",
            message="too complex",
            file_path="foo.py",
            line=42,
            severity=ViolationSeverity.ERROR,
        )
        adapter = _make_adapter((v,))
        output = adapter.emit()

        assert output.startswith("::error ")
        assert "file=foo.py" in output
        assert "line=42" in output
        assert "title=max_cc" in output
        assert "::too complex" in output

    def test_warning_annotation(self) -> None:
        """A WARNING violation produces a ::warning annotation."""
        v = Violation(
            rule="max_lines",
            message="long file",
            severity=ViolationSeverity.WARNING,
        )
        adapter = _make_adapter((v,))
        output = adapter.emit()

        assert output.startswith("::warning ")

    def test_info_treated_as_warning(self) -> None:
        """An INFO violation is emitted as a ::warning annotation."""
        v = Violation(
            rule="info_rule",
            message="fyi",
            severity=ViolationSeverity.INFO,
        )
        adapter = _make_adapter((v,))
        output = adapter.emit()

        assert output.startswith("::warning ")

    def test_no_file_params_when_empty(self) -> None:
        """When file_path is empty and line is 0, those params are omitted."""
        v = Violation(rule="r", message="m", file_path="", line=0)
        adapter = _make_adapter((v,))
        output = adapter.emit()

        assert "file=" not in output
        assert "line=" not in output

    def test_multiple_violations(self) -> None:
        """Multiple violations produce one line each."""
        v1 = Violation(rule="a", message="m1", severity=ViolationSeverity.ERROR)
        v2 = Violation(rule="b", message="m2", severity=ViolationSeverity.WARNING)
        adapter = _make_adapter((v1, v2))

        lines = adapter.emit().splitlines()

        assert len(lines) == 2

    def test_empty_violations(self) -> None:
        """No violations produces an empty string."""
        adapter = _make_adapter()

        assert adapter.emit() == ""


class TestStepSummary:
    """Step summary markdown tests."""

    def test_header(self) -> None:
        """Step summary starts with the report header."""
        adapter = _make_adapter()
        summary = adapter.step_summary()

        assert "## dev-stats Quality Report" in summary

    def test_stats(self) -> None:
        """Step summary includes file count and total lines."""
        f = FileReport(
            path=Path("a.py"),
            language="python",
            total_lines=100,
            code_lines=80,
            blank_lines=10,
            comment_lines=10,
        )
        adapter = _make_adapter(files=(f,))
        summary = adapter.step_summary()

        assert "**Files:** 1" in summary
        assert "**Total Lines:** 100" in summary

    def test_violation_count(self) -> None:
        """Step summary includes violation count."""
        v = Violation(rule="r", message="m")
        adapter = _make_adapter((v,))
        summary = adapter.step_summary()

        assert "**Violations:** 1" in summary

    def test_violation_table(self) -> None:
        """Step summary includes a markdown table when violations exist."""
        v = Violation(
            rule="max_cc",
            message="complex",
            file_path="foo.py",
            severity=ViolationSeverity.ERROR,
        )
        adapter = _make_adapter((v,))
        summary = adapter.step_summary()

        assert "| Severity | Rule |" in summary
        assert "max_cc" in summary
        assert "complex" in summary

    def test_all_passed_message(self) -> None:
        """When no violations exist, show an all-passed message."""
        adapter = _make_adapter()
        summary = adapter.step_summary()

        assert "All quality gates passed." in summary


class TestWriteReport:
    """File output tests."""

    def test_write_creates_two_files(self, tmp_path: Path) -> None:
        """write_report creates annotations and step summary files."""
        v = Violation(rule="r", message="m", severity=ViolationSeverity.WARNING)
        adapter = _make_adapter((v,))

        paths = adapter.write_report(tmp_path)

        assert len(paths) == 2
        names = {p.name for p in paths}
        assert "dev-stats-annotations.txt" in names
        assert "dev-stats-step-summary.md" in names
        for p in paths:
            assert p.exists()

    def test_write_creates_output_dir(self, tmp_path: Path) -> None:
        """write_report creates the output directory if needed."""
        adapter = _make_adapter()
        out_dir = tmp_path / "sub" / "dir"

        paths = adapter.write_report(out_dir)

        assert out_dir.exists()
        assert len(paths) == 2
