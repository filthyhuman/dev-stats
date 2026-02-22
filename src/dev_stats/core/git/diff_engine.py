"""Unified diff parser extracting hunks and lines."""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

from dev_stats.core.models import DiffHunk, DiffLine

if TYPE_CHECKING:
    from pathlib import Path

# @@ -old_start,old_count +new_start,new_count @@ optional header
_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


class DiffEngine:
    """Parses unified diffs from ``git diff`` output.

    Extracts ``DiffHunk`` and ``DiffLine`` models from the raw diff text.
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialise the diff engine.

        Args:
            repo_path: Absolute path to the repository root.
        """
        self._repo_path = repo_path

    def diff_commit(self, sha: str) -> list[DiffHunk]:
        """Get diff hunks for a single commit.

        Args:
            sha: Commit SHA to diff.

        Returns:
            List of ``DiffHunk`` objects.
        """
        raw = self._run_git("git", "diff", f"{sha}~1..{sha}", "--unified=3")
        return self.parse_diff(raw)

    def diff_range(self, base: str, head: str) -> list[DiffHunk]:
        """Get diff hunks between two refs.

        Args:
            base: Base ref.
            head: Head ref.

        Returns:
            List of ``DiffHunk`` objects.
        """
        raw = self._run_git("git", "diff", f"{base}..{head}", "--unified=3")
        return self.parse_diff(raw)

    def parse_diff(self, raw: str) -> list[DiffHunk]:
        """Parse raw unified diff text into hunks.

        Args:
            raw: Raw unified diff output.

        Returns:
            List of ``DiffHunk`` objects.
        """
        hunks: list[DiffHunk] = []
        current_hunk: _HunkBuilder | None = None

        for line in raw.splitlines():
            hunk_match = _HUNK_RE.match(line)
            if hunk_match:
                # Finish previous hunk.
                if current_hunk is not None:
                    hunks.append(current_hunk.build())

                old_start = int(hunk_match.group(1))
                old_count = int(hunk_match.group(2) or "1")
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4) or "1")
                header_text = hunk_match.group(5).strip()

                current_hunk = _HunkBuilder(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    header=line,
                    function_context=header_text,
                )
                continue

            if current_hunk is not None:
                # Skip diff meta lines (---, +++, diff, index).
                if line.startswith(("---", "+++", "diff ", "index ")):
                    continue
                current_hunk.add_line(line)

        # Don't forget the last hunk.
        if current_hunk is not None:
            hunks.append(current_hunk.build())

        return hunks

    def _run_git(self, *args: str) -> str:
        """Execute a git command and return stdout.

        Args:
            *args: Full command arguments.

        Returns:
            Standard output as a string.
        """
        result = subprocess.run(
            list(args),
            cwd=self._repo_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout


class _HunkBuilder:
    """Accumulates diff lines and builds a ``DiffHunk``."""

    def __init__(
        self,
        *,
        old_start: int,
        old_count: int,
        new_start: int,
        new_count: int,
        header: str,
        function_context: str,
    ) -> None:
        """Initialise the hunk builder.

        Args:
            old_start: Start line in old file.
            old_count: Line count in old file.
            new_start: Start line in new file.
            new_count: Line count in new file.
            header: Full ``@@`` header line.
            function_context: Function context after ``@@``.
        """
        self._old_start = old_start
        self._old_count = old_count
        self._new_start = new_start
        self._new_count = new_count
        self._header = header
        self._function_context = function_context
        self._lines: list[DiffLine] = []
        self._old_lineno = old_start
        self._new_lineno = new_start

    def add_line(self, raw: str) -> None:
        """Add a raw diff line.

        Args:
            raw: A line from the diff output.
        """
        if raw.startswith("+"):
            self._lines.append(
                DiffLine(
                    content=raw[1:],
                    line_type="add",
                    old_lineno=None,
                    new_lineno=self._new_lineno,
                )
            )
            self._new_lineno += 1
        elif raw.startswith("-"):
            self._lines.append(
                DiffLine(
                    content=raw[1:],
                    line_type="delete",
                    old_lineno=self._old_lineno,
                    new_lineno=None,
                )
            )
            self._old_lineno += 1
        elif raw.startswith(" "):
            self._lines.append(
                DiffLine(
                    content=raw[1:],
                    line_type="context",
                    old_lineno=self._old_lineno,
                    new_lineno=self._new_lineno,
                )
            )
            self._old_lineno += 1
            self._new_lineno += 1
        # Ignore "\ No newline at end of file" and other meta lines.

    def build(self) -> DiffHunk:
        """Build the final ``DiffHunk``.

        Returns:
            A frozen ``DiffHunk`` instance.
        """
        return DiffHunk(
            old_start=self._old_start,
            old_count=self._old_count,
            new_start=self._new_start,
            new_count=self._new_count,
            header=self._header,
            lines=tuple(self._lines),
        )
