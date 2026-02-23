"""TeamCity CI adapter producing service messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dev_stats.ci.abstract_ci_adapter import AbstractCIAdapter
from dev_stats.ci.violation import ViolationSeverity

if TYPE_CHECKING:
    from pathlib import Path


def _escape_tc(value: str) -> str:
    """Escape a string for TeamCity service message values.

    Args:
        value: Raw string value.

    Returns:
        Escaped string safe for TeamCity messages.
    """
    return (
        value.replace("|", "||")
        .replace("'", "|'")
        .replace("\n", "|n")
        .replace("\r", "|r")
        .replace("[", "|[")
        .replace("]", "|]")
    )


class TeamCityAdapter(AbstractCIAdapter):
    """Produces TeamCity service messages for build statistics and inspections.

    Emits:
    - ``##teamcity[buildStatisticValue ...]`` for numeric metrics
    - ``##teamcity[inspectionType ...]`` for violation type definitions
    - ``##teamcity[inspection ...]`` for individual violations
    - ``##teamcity[buildProblem ...]`` for ERROR-severity violations
    """

    def emit(self) -> str:
        """Emit violations as TeamCity service messages.

        Returns:
            Multi-line string of ``##teamcity[...]`` messages.
        """
        lines: list[str] = []

        # Emit build statistics
        report = self._report
        lines.append(
            f"##teamcity[buildStatisticValue key='LOC' "
            f"value='{sum(f.total_lines for f in report.files)}']"
        )
        lines.append(f"##teamcity[buildStatisticValue key='files' value='{len(report.files)}']")
        lines.append(
            f"##teamcity[buildStatisticValue key='violations' value='{len(self._violations)}']"
        )

        # Emit inspection types (unique rules)
        seen_rules: set[str] = set()
        for v in self._violations:
            if v.rule not in seen_rules:
                seen_rules.add(v.rule)
                lines.append(
                    f"##teamcity[inspectionType "
                    f"id='{_escape_tc(v.rule)}' "
                    f"name='{_escape_tc(v.rule)}' "
                    f"category='dev-stats' "
                    f"description='{_escape_tc(v.rule)}']"
                )

        # Emit individual inspections
        for v in self._violations:
            severity = "WARNING" if v.severity == ViolationSeverity.WARNING else "ERROR"
            lines.append(
                f"##teamcity[inspection "
                f"typeId='{_escape_tc(v.rule)}' "
                f"message='{_escape_tc(v.message)}' "
                f"file='{_escape_tc(v.file_path)}' "
                f"line='{v.line}' "
                f"SEVERITY='{severity}']"
            )

        # Emit build problems for ERROR violations
        for v in self._violations:
            if v.severity == ViolationSeverity.ERROR:
                lines.append(
                    f"##teamcity[buildProblem "
                    f"description='{_escape_tc(v.message)}' "
                    f"identity='{_escape_tc(v.rule + ':' + v.file_path)}']"
                )

        return "\n".join(lines)

    def write_report(self, output_dir: Path) -> list[Path]:
        """Write TeamCity service messages to a file.

        Args:
            output_dir: Directory to write into.

        Returns:
            Single-element list with the path to the text file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "dev-stats-teamcity.txt"
        out_path.write_text(self.emit(), encoding="utf-8")
        return [out_path]
