"""Blame engine extracting per-file authorship data from git blame."""

from __future__ import annotations

import logging
import re
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from dev_stats.core.models import AuthorBlameStat, BlameLine, FileBlameReport

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# Porcelain blame field patterns.
_SHA_RE = re.compile(r"^([0-9a-f]{40})\s+(\d+)\s+(\d+)")
_AUTHOR_RE = re.compile(r"^author (.+)$")
_AUTHOR_MAIL_RE = re.compile(r"^author-mail <(.+)>$")
_AUTHOR_TIME_RE = re.compile(r"^author-time (\d+)$")


class BlameEngine:
    """Extracts per-file authorship data using ``git blame --line-porcelain``.

    Produces ``FileBlameReport`` objects with per-line blame data,
    per-author statistics, and bus-factor computation.
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialise the blame engine.

        Args:
            repo_path: Absolute path to the repository root.
        """
        self._repo_path = repo_path

    def blame_file(self, file_path: str) -> FileBlameReport:
        """Run git blame on a single file.

        Args:
            file_path: Repository-relative file path.

        Returns:
            A ``FileBlameReport`` with per-line and per-author data.
        """
        try:
            raw = self._run_git("git", "blame", "--line-porcelain", file_path)
        except subprocess.CalledProcessError:
            logger.debug("Could not blame %s", file_path)
            return FileBlameReport(path=file_path, total_lines=0)

        lines = self._parse_porcelain(raw)
        authors = self._aggregate_authors(lines)

        return FileBlameReport(
            path=file_path,
            total_lines=len(lines),
            authors=tuple(authors),
            lines=tuple(lines),
        )

    def blame_files(self, file_paths: list[str]) -> list[FileBlameReport]:
        """Run git blame on multiple files.

        Args:
            file_paths: Repository-relative file paths.

        Returns:
            List of ``FileBlameReport`` objects.
        """
        return [self.blame_file(fp) for fp in file_paths]

    def bus_factor(self, report: FileBlameReport) -> int:
        """Compute the bus factor for a file.

        The bus factor is the minimum number of authors whose combined
        ownership exceeds 50% of the file.

        Args:
            report: A file blame report.

        Returns:
            Bus factor (minimum 1 if the file has any lines).
        """
        if not report.authors:
            return 0

        sorted_authors = sorted(report.authors, key=lambda a: a.percentage, reverse=True)
        cumulative = 0.0
        count = 0
        for author in sorted_authors:
            cumulative += author.percentage
            count += 1
            if cumulative > 50.0:
                break
        return count

    def _parse_porcelain(self, raw: str) -> list[BlameLine]:
        """Parse ``git blame --line-porcelain`` output.

        Args:
            raw: Raw porcelain blame output.

        Returns:
            List of ``BlameLine`` objects.
        """
        lines: list[BlameLine] = []
        current_sha = ""
        current_lineno = 0
        current_author = ""
        current_email = ""
        current_time = 0

        for line in raw.splitlines():
            sha_match = _SHA_RE.match(line)
            if sha_match:
                current_sha = sha_match.group(1)
                current_lineno = int(sha_match.group(3))
                continue

            author_match = _AUTHOR_RE.match(line)
            if author_match:
                current_author = author_match.group(1)
                continue

            mail_match = _AUTHOR_MAIL_RE.match(line)
            if mail_match:
                current_email = mail_match.group(1)
                continue

            time_match = _AUTHOR_TIME_RE.match(line)
            if time_match:
                current_time = int(time_match.group(1))
                continue

            # The actual content line starts with \t
            if line.startswith("\t"):
                lines.append(
                    BlameLine(
                        line_number=current_lineno,
                        author_name=current_author,
                        author_email=current_email,
                        date=datetime.fromtimestamp(current_time, tz=UTC),
                        commit_sha=current_sha,
                    )
                )

        return lines

    @staticmethod
    def _aggregate_authors(lines: list[BlameLine]) -> list[AuthorBlameStat]:
        """Aggregate per-author blame statistics.

        Args:
            lines: Parsed blame lines.

        Returns:
            List of ``AuthorBlameStat`` sorted by line count descending.
        """
        if not lines:
            return []

        counts: dict[str, int] = defaultdict(int)
        names: dict[str, str] = {}
        total = len(lines)

        for bl in lines:
            counts[bl.author_email] += 1
            names[bl.author_email] = bl.author_name

        stats = [
            AuthorBlameStat(
                author_name=names[email],
                author_email=email,
                line_count=count,
                percentage=round(count / total * 100, 2),
            )
            for email, count in counts.items()
        ]
        return sorted(stats, key=lambda s: s.line_count, reverse=True)

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
            timeout=120,
        )
        return result.stdout
