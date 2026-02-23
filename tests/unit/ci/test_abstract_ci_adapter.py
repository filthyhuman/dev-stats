"""Tests for AbstractCIAdapter.check_violations()."""

from __future__ import annotations

from pathlib import Path

from dev_stats.ci.abstract_ci_adapter import AbstractCIAdapter
from dev_stats.ci.violation import ViolationSeverity
from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.config.threshold_config import ThresholdConfig
from dev_stats.core.models import (
    ClassReport,
    CoverageReport,
    DuplicationReport,
    FileReport,
    MethodReport,
    ParameterReport,
    RepoReport,
)


class _ConcreteAdapter(AbstractCIAdapter):
    """Minimal concrete adapter for testing check_violations."""

    def emit(self) -> str:
        """Return empty string."""
        return ""

    def write_report(self, output_dir: Path) -> list[Path]:
        """Return empty list."""
        return []


def _make_config(**threshold_overrides: object) -> AnalysisConfig:
    """Create an AnalysisConfig with custom threshold overrides."""
    thresholds = ThresholdConfig(**threshold_overrides)  # type: ignore[arg-type]
    return AnalysisConfig(thresholds=thresholds)


def _make_method(**kwargs: object) -> MethodReport:
    """Create a MethodReport with sensible defaults."""
    defaults: dict[str, object] = {
        "name": "func",
        "line": 1,
        "end_line": 10,
        "lines": 10,
    }
    defaults.update(kwargs)
    return MethodReport(**defaults)  # type: ignore[arg-type]


def _make_file(path: str = "example.py", **kwargs: object) -> FileReport:
    """Create a FileReport with sensible defaults."""
    defaults: dict[str, object] = {
        "path": Path(path),
        "language": "python",
        "total_lines": 100,
        "code_lines": 80,
        "blank_lines": 10,
        "comment_lines": 10,
    }
    defaults.update(kwargs)
    return FileReport(**defaults)  # type: ignore[arg-type]


class TestCheckViolationsClean:
    """No violations for a report within thresholds."""

    def test_no_violations_on_clean_report(self) -> None:
        """A clean report produces zero violations."""
        config = _make_config()
        report = RepoReport(root=Path("."), files=(_make_file(),))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert violations == ()


class TestFileViolations:
    """File-level threshold checks."""

    def test_max_file_lines(self) -> None:
        """A file exceeding max_file_lines triggers a violation."""
        config = _make_config(max_file_lines=100)
        f = _make_file(total_lines=200)
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert len(violations) == 1
        assert violations[0].rule == "max_file_lines"
        assert violations[0].severity == ViolationSeverity.WARNING
        assert violations[0].value == 200.0
        assert violations[0].threshold == 100.0

    def test_max_imports(self) -> None:
        """A file exceeding max_imports triggers a violation."""
        config = _make_config(max_imports=2)
        f = _make_file(imports=("os", "sys", "math"))
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert len(violations) == 1
        assert violations[0].rule == "max_imports"


class TestFunctionViolations:
    """Function-level threshold checks."""

    def test_max_function_lines(self) -> None:
        """A function exceeding max_function_lines triggers a violation."""
        config = _make_config(max_function_lines=10)
        func = _make_method(lines=20)
        f = _make_file(functions=(func,))
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert any(v.rule == "max_function_lines" for v in violations)

    def test_max_cyclomatic_complexity(self) -> None:
        """A function exceeding max_cyclomatic_complexity triggers an ERROR."""
        config = _make_config(max_cyclomatic_complexity=5)
        func = _make_method(cyclomatic_complexity=15)
        f = _make_file(functions=(func,))
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        cc_violations = [v for v in violations if v.rule == "max_cyclomatic_complexity"]
        assert len(cc_violations) == 1
        assert cc_violations[0].severity == ViolationSeverity.ERROR

    def test_max_cognitive_complexity(self) -> None:
        """A function exceeding max_cognitive_complexity triggers a violation."""
        config = _make_config(max_cognitive_complexity=5)
        func = _make_method(cognitive_complexity=10)
        f = _make_file(functions=(func,))
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert any(v.rule == "max_cognitive_complexity" for v in violations)

    def test_max_parameters(self) -> None:
        """A function exceeding max_parameters triggers a violation."""
        config = _make_config(max_parameters=2)
        params = tuple(ParameterReport(name=f"p{i}") for i in range(5))
        func = _make_method(parameters=params)
        f = _make_file(functions=(func,))
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert any(v.rule == "max_parameters" for v in violations)

    def test_max_nesting_depth(self) -> None:
        """A function exceeding max_nesting_depth triggers a violation."""
        config = _make_config(max_nesting_depth=2)
        func = _make_method(nesting_depth=5)
        f = _make_file(functions=(func,))
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert any(v.rule == "max_nesting_depth" for v in violations)


class TestClassViolations:
    """Class-level threshold checks."""

    def test_max_class_lines(self) -> None:
        """A class exceeding max_class_lines triggers a violation."""
        config = _make_config(max_class_lines=100)
        cls = ClassReport(name="Big", line=1, end_line=200, lines=200)
        f = _make_file(classes=(cls,))
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert any(v.rule == "max_class_lines" for v in violations)

    def test_max_class_methods(self) -> None:
        """A class exceeding max_class_methods triggers a violation."""
        config = _make_config(max_class_methods=2)
        methods = tuple(_make_method(name=f"m{i}", line=i * 10) for i in range(5))
        cls = ClassReport(name="Many", line=1, end_line=50, lines=50, methods=methods)
        f = _make_file(classes=(cls,))
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert any(v.rule == "max_class_methods" for v in violations)

    def test_class_method_violations(self) -> None:
        """Methods inside a class are also checked."""
        config = _make_config(max_function_lines=5)
        method = _make_method(name="big_method", lines=20)
        cls = ClassReport(name="Cls", line=1, end_line=30, lines=30, methods=(method,))
        f = _make_file(classes=(cls,))
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert any(v.rule == "max_function_lines" for v in violations)


class TestRepoViolations:
    """Repo-wide threshold checks."""

    def test_max_duplication_pct(self) -> None:
        """Duplication ratio above max_duplication_pct triggers an ERROR."""
        config = _make_config(max_duplication_pct=5.0)
        dup = DuplicationReport(duplication_ratio=0.1)  # 10%
        report = RepoReport(root=Path("."), duplication=dup)
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        dup_violations = [v for v in violations if v.rule == "max_duplication_pct"]
        assert len(dup_violations) == 1
        assert dup_violations[0].severity == ViolationSeverity.ERROR

    def test_min_test_coverage(self) -> None:
        """Coverage below min_test_coverage triggers an ERROR."""
        config = _make_config(min_test_coverage=80.0)
        cov = CoverageReport(overall_ratio=0.5)  # 50%
        report = RepoReport(root=Path("."), coverage=cov)
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        cov_violations = [v for v in violations if v.rule == "min_test_coverage"]
        assert len(cov_violations) == 1
        assert cov_violations[0].severity == ViolationSeverity.ERROR

    def test_no_duplication_report_skips_check(self) -> None:
        """When duplication is None the check is skipped."""
        config = _make_config(max_duplication_pct=0.0)
        report = RepoReport(root=Path("."))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert not any(v.rule == "max_duplication_pct" for v in violations)

    def test_no_coverage_report_skips_check(self) -> None:
        """When coverage is None the check is skipped."""
        config = _make_config(min_test_coverage=100.0)
        report = RepoReport(root=Path("."))
        adapter = _ConcreteAdapter(report=report, config=config)

        violations = adapter.check_violations()

        assert not any(v.rule == "min_test_coverage" for v in violations)


class TestViolationsProperty:
    """The violations property reflects check results."""

    def test_violations_empty_before_check(self) -> None:
        """Before check_violations is called, violations is empty."""
        config = _make_config()
        report = RepoReport(root=Path("."))
        adapter = _ConcreteAdapter(report=report, config=config)

        assert adapter.violations == ()

    def test_violations_populated_after_check(self) -> None:
        """After check_violations, violations is populated."""
        config = _make_config(max_file_lines=10)
        f = _make_file(total_lines=100)
        report = RepoReport(root=Path("."), files=(f,))
        adapter = _ConcreteAdapter(report=report, config=config)

        adapter.check_violations()

        assert len(adapter.violations) > 0
