"""Abstract base class for CI adapters."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

from dev_stats.ci.violation import Violation, ViolationSeverity

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.config.analysis_config import AnalysisConfig
    from dev_stats.core.models import RepoReport


class AbstractCIAdapter(abc.ABC):
    """Base class for CI system adapters.

    Subclasses translate :class:`Violation` objects into the output format
    expected by a specific CI system (JUnit XML, TeamCity service messages,
    GitHub Actions annotations, etc.).
    """

    def __init__(self, report: RepoReport, config: AnalysisConfig) -> None:
        """Initialise the adapter.

        Args:
            report: The analysis report to check.
            config: Analysis configuration with thresholds.
        """
        self._report = report
        self._config = config
        self._violations: tuple[Violation, ...] = ()

    @property
    def violations(self) -> tuple[Violation, ...]:
        """Return detected violations."""
        return self._violations

    def check_violations(self) -> tuple[Violation, ...]:
        """Check the report against configured thresholds.

        Returns:
            Tuple of detected violations.
        """
        results: list[Violation] = []
        thresholds = self._config.thresholds

        # File-level checks
        for f in self._report.files:
            if f.total_lines > thresholds.max_file_lines:
                results.append(
                    Violation(
                        rule="max_file_lines",
                        message=(
                            f"{f.path}: {f.total_lines} lines "
                            f"exceeds limit of {thresholds.max_file_lines}"
                        ),
                        file_path=str(f.path),
                        severity=ViolationSeverity.WARNING,
                        value=float(f.total_lines),
                        threshold=float(thresholds.max_file_lines),
                    )
                )

            if len(f.imports) > thresholds.max_imports:
                results.append(
                    Violation(
                        rule="max_imports",
                        message=(
                            f"{f.path}: {len(f.imports)} imports "
                            f"exceeds limit of {thresholds.max_imports}"
                        ),
                        file_path=str(f.path),
                        severity=ViolationSeverity.WARNING,
                        value=float(len(f.imports)),
                        threshold=float(thresholds.max_imports),
                    )
                )

            # Function-level checks
            for func in f.functions:
                results.extend(self._check_function(func, str(f.path), thresholds))

            # Class-level checks
            for cls in f.classes:
                if cls.lines > thresholds.max_class_lines:
                    results.append(
                        Violation(
                            rule="max_class_lines",
                            message=(
                                f"{f.path}:{cls.line} class {cls.name}: "
                                f"{cls.lines} lines exceeds limit of "
                                f"{thresholds.max_class_lines}"
                            ),
                            file_path=str(f.path),
                            line=cls.line,
                            severity=ViolationSeverity.WARNING,
                            value=float(cls.lines),
                            threshold=float(thresholds.max_class_lines),
                        )
                    )

                if cls.num_methods > thresholds.max_class_methods:
                    results.append(
                        Violation(
                            rule="max_class_methods",
                            message=(
                                f"{f.path}:{cls.line} class {cls.name}: "
                                f"{cls.num_methods} methods exceeds limit of "
                                f"{thresholds.max_class_methods}"
                            ),
                            file_path=str(f.path),
                            line=cls.line,
                            severity=ViolationSeverity.WARNING,
                            value=float(cls.num_methods),
                            threshold=float(thresholds.max_class_methods),
                        )
                    )

                # Method-level checks
                for method in cls.methods:
                    results.extend(self._check_function(method, str(f.path), thresholds))

        # Duplication check
        if self._report.duplication is not None:
            dup_pct = self._report.duplication.duplication_ratio * 100
            if dup_pct > thresholds.max_duplication_pct:
                results.append(
                    Violation(
                        rule="max_duplication_pct",
                        message=(
                            f"Duplication ratio {dup_pct:.1f}% "
                            f"exceeds limit of {thresholds.max_duplication_pct}%"
                        ),
                        severity=ViolationSeverity.ERROR,
                        value=dup_pct,
                        threshold=thresholds.max_duplication_pct,
                    )
                )

        # Coverage check
        if self._report.coverage is not None:
            cov_pct = self._report.coverage.overall_ratio * 100
            if cov_pct < thresholds.min_test_coverage:
                results.append(
                    Violation(
                        rule="min_test_coverage",
                        message=(
                            f"Test coverage {cov_pct:.1f}% "
                            f"below minimum of {thresholds.min_test_coverage}%"
                        ),
                        severity=ViolationSeverity.ERROR,
                        value=cov_pct,
                        threshold=thresholds.min_test_coverage,
                    )
                )

        self._violations = tuple(results)
        return self._violations

    @staticmethod
    def _check_function(
        func: object,
        file_path: str,
        thresholds: object,
    ) -> list[Violation]:
        """Check a function/method against thresholds.

        Args:
            func: A MethodReport instance.
            file_path: Repository-relative file path.
            thresholds: ThresholdConfig instance.

        Returns:
            List of violations for this function.
        """
        from dev_stats.config.threshold_config import ThresholdConfig
        from dev_stats.core.models import MethodReport

        assert isinstance(func, MethodReport)
        assert isinstance(thresholds, ThresholdConfig)

        results: list[Violation] = []

        if func.lines > thresholds.max_function_lines:
            results.append(
                Violation(
                    rule="max_function_lines",
                    message=(
                        f"{file_path}:{func.line} {func.name}: "
                        f"{func.lines} lines exceeds limit of "
                        f"{thresholds.max_function_lines}"
                    ),
                    file_path=file_path,
                    line=func.line,
                    severity=ViolationSeverity.WARNING,
                    value=float(func.lines),
                    threshold=float(thresholds.max_function_lines),
                )
            )

        if func.cyclomatic_complexity > thresholds.max_cyclomatic_complexity:
            results.append(
                Violation(
                    rule="max_cyclomatic_complexity",
                    message=(
                        f"{file_path}:{func.line} {func.name}: "
                        f"CC={func.cyclomatic_complexity} exceeds limit of "
                        f"{thresholds.max_cyclomatic_complexity}"
                    ),
                    file_path=file_path,
                    line=func.line,
                    severity=ViolationSeverity.ERROR,
                    value=float(func.cyclomatic_complexity),
                    threshold=float(thresholds.max_cyclomatic_complexity),
                )
            )

        if func.cognitive_complexity > thresholds.max_cognitive_complexity:
            results.append(
                Violation(
                    rule="max_cognitive_complexity",
                    message=(
                        f"{file_path}:{func.line} {func.name}: "
                        f"cognitive={func.cognitive_complexity} exceeds "
                        f"limit of {thresholds.max_cognitive_complexity}"
                    ),
                    file_path=file_path,
                    line=func.line,
                    severity=ViolationSeverity.WARNING,
                    value=float(func.cognitive_complexity),
                    threshold=float(thresholds.max_cognitive_complexity),
                )
            )

        if func.num_parameters > thresholds.max_parameters:
            results.append(
                Violation(
                    rule="max_parameters",
                    message=(
                        f"{file_path}:{func.line} {func.name}: "
                        f"{func.num_parameters} parameters exceeds "
                        f"limit of {thresholds.max_parameters}"
                    ),
                    file_path=file_path,
                    line=func.line,
                    severity=ViolationSeverity.WARNING,
                    value=float(func.num_parameters),
                    threshold=float(thresholds.max_parameters),
                )
            )

        if func.nesting_depth > thresholds.max_nesting_depth:
            results.append(
                Violation(
                    rule="max_nesting_depth",
                    message=(
                        f"{file_path}:{func.line} {func.name}: "
                        f"nesting depth {func.nesting_depth} exceeds "
                        f"limit of {thresholds.max_nesting_depth}"
                    ),
                    file_path=file_path,
                    line=func.line,
                    severity=ViolationSeverity.WARNING,
                    value=float(func.nesting_depth),
                    threshold=float(thresholds.max_nesting_depth),
                )
            )

        return results

    @abc.abstractmethod
    def emit(self) -> str:
        """Emit violations in the CI system's native format.

        Returns:
            Formatted string output (e.g. TeamCity messages, annotations).
        """

    @abc.abstractmethod
    def write_report(self, output_dir: Path) -> list[Path]:
        """Write a report file to *output_dir*.

        Args:
            output_dir: Directory to write the report into.

        Returns:
            List of paths to generated report files.
        """
