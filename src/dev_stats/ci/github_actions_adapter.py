"""GitHub Actions CI adapter producing workflow annotations and step summaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dev_stats.ci.abstract_ci_adapter import AbstractCIAdapter
from dev_stats.ci.violation import ViolationSeverity

if TYPE_CHECKING:
    from pathlib import Path


class GithubActionsAdapter(AbstractCIAdapter):
    """Produces GitHub Actions workflow annotations and a step summary.

    Emits ``::error::`` and ``::warning::`` commands for annotations, and a
    Markdown table for the ``$GITHUB_STEP_SUMMARY`` file.
    """

    def emit(self) -> str:
        """Emit violations as GitHub Actions annotation commands.

        Returns:
            Multi-line string of ``::error::`` and ``::warning::`` commands.
        """
        lines: list[str] = []

        for v in self._violations:
            level = "error" if v.severity == ViolationSeverity.ERROR else "warning"
            params: list[str] = []
            if v.file_path:
                params.append(f"file={v.file_path}")
            if v.line:
                params.append(f"line={v.line}")
            params.append(f"title={v.rule}")

            param_str = ",".join(params)
            lines.append(f"::{level} {param_str}::{v.message}")

        return "\n".join(lines)

    def step_summary(self) -> str:
        """Generate a Markdown step summary table.

        Returns:
            Markdown string suitable for ``$GITHUB_STEP_SUMMARY``.
        """
        lines: list[str] = []
        lines.append("## dev-stats Quality Report")
        lines.append("")

        report = self._report
        lines.append(f"- **Files:** {len(report.files)}")
        lines.append(f"- **Total Lines:** {sum(f.total_lines for f in report.files)}")
        lines.append(f"- **Violations:** {len(self._violations)}")
        lines.append("")

        if self._violations:
            lines.append("| Severity | Rule | File | Line | Message |")
            lines.append("|----------|------|------|------|---------|")
            for v in self._violations:
                sev = v.severity.value
                lines.append(f"| {sev} | {v.rule} | {v.file_path} | {v.line} | {v.message} |")
        else:
            lines.append("All quality gates passed.")

        return "\n".join(lines)

    def write_report(self, output_dir: Path) -> list[Path]:
        """Write annotations and step summary to *output_dir*.

        Args:
            output_dir: Directory to write into.

        Returns:
            List of paths to generated report files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []

        annotations_path = output_dir / "dev-stats-annotations.txt"
        annotations_path.write_text(self.emit(), encoding="utf-8")
        created.append(annotations_path)

        summary_path = output_dir / "dev-stats-step-summary.md"
        summary_path.write_text(self.step_summary(), encoding="utf-8")
        created.append(summary_path)

        return created
