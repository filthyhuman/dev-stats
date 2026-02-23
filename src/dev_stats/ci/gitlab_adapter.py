"""GitLab CI adapter producing Code Quality JSON reports."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from dev_stats.ci.abstract_ci_adapter import AbstractCIAdapter
from dev_stats.ci.violation import ViolationSeverity

if TYPE_CHECKING:
    from pathlib import Path

# Map our severity levels to GitLab Code Quality severity strings.
_SEVERITY_MAP: dict[ViolationSeverity, str] = {
    ViolationSeverity.INFO: "info",
    ViolationSeverity.WARNING: "minor",
    ViolationSeverity.ERROR: "major",
}


class GitlabAdapter(AbstractCIAdapter):
    """Produces GitLab Code Quality JSON (``gl-code-quality-report.json``).

    Each violation becomes a Code Quality issue object with a deterministic
    fingerprint derived from rule + file + line.
    """

    def emit(self) -> str:
        """Emit violations as GitLab Code Quality JSON string.

        Returns:
            JSON array of Code Quality issue objects.
        """
        issues: list[dict[str, object]] = []

        for v in self._violations:
            fingerprint = hashlib.md5(f"{v.rule}:{v.file_path}:{v.line}".encode()).hexdigest()

            issue: dict[str, object] = {
                "type": "issue",
                "check_name": v.rule,
                "description": v.message,
                "categories": ["Complexity"],
                "severity": _SEVERITY_MAP.get(v.severity, "minor"),
                "fingerprint": fingerprint,
                "location": {
                    "path": v.file_path or ".",
                    "lines": {"begin": max(v.line, 1)},
                },
            }
            issues.append(issue)

        return json.dumps(issues, indent=2, ensure_ascii=False)

    def write_report(self, output_dir: Path) -> list[Path]:
        """Write GitLab Code Quality JSON to *output_dir*.

        Args:
            output_dir: Directory to write into.

        Returns:
            Single-element list with the path to the JSON file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "gl-code-quality-report.json"
        out_path.write_text(self.emit(), encoding="utf-8")
        return [out_path]
