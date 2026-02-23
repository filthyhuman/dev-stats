"""Violation frozen dataclass for CI adapter output."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ViolationSeverity(enum.Enum):
    """Severity level for a quality-gate violation."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Violation:
    """A single quality-gate violation detected during analysis.

    Attributes:
        rule: Machine-readable rule identifier (e.g. ``"max_file_lines"``).
        message: Human-readable description of the violation.
        file_path: Repository-relative file path, or empty for repo-wide.
        line: Line number (0 when not applicable).
        severity: Severity level.
        value: The measured value that triggered the violation.
        threshold: The threshold that was exceeded.
    """

    rule: str
    message: str
    file_path: str = ""
    line: int = 0
    severity: ViolationSeverity = ViolationSeverity.WARNING
    value: float = 0.0
    threshold: float = 0.0
