"""Log harvester extracting structured commit records from git log."""

from __future__ import annotations

import logging
import re
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from dev_stats.core.models import ChangeType, CommitRecord, FileChange

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# Null-byte delimited format for reliable parsing.
# Fields: sha, author name, author email, author date (ISO), committer name,
# committer email, committer date (ISO), parent hashes, subject, body.
_LOG_FORMAT = "%x00".join(
    [
        "%H",  # sha
        "%an",  # author name
        "%ae",  # author email
        "%aI",  # author date ISO
        "%cn",  # committer name
        "%ce",  # committer email
        "%cI",  # committer date ISO
        "%P",  # parent hashes (space-separated)
        "%s",  # subject
        "%b",  # body
    ]
)

# Record separator between commits.
_RECORD_SEP = "\x01"
_FIELD_SEP = "\x00"

# --numstat line: added<TAB>deleted<TAB>path
_NUMSTAT_RE = re.compile(r"^(\d+|-)\t(\d+|-)\t(.+)$")

# Rename: {old => new} or old => new
_RENAME_RE = re.compile(r"^(.*)\{(.+) => (.+)\}(.*)$")


class LogHarvester:
    """Harvests structured commit records from a Git repository.

    Uses ``git log`` with a null-byte-delimited format and ``--numstat``
    to extract full commit metadata and per-file change statistics.
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialise the harvester.

        Args:
            repo_path: Absolute path to the repository root.
        """
        self._repo_path = repo_path

    def harvest(
        self,
        *,
        max_commits: int = 0,
        since: str | None = None,
    ) -> list[CommitRecord]:
        """Harvest commit records from the repository.

        Args:
            max_commits: Maximum number of commits (0 = unlimited).
            since: Date string for ``--since`` filter.

        Returns:
            List of ``CommitRecord`` in reverse chronological order.
        """
        cmd = [
            "git",
            "log",
            f"--format={_RECORD_SEP}{_LOG_FORMAT}",
            "--numstat",
        ]
        if max_commits > 0:
            cmd.append(f"-n{max_commits}")
        if since:
            cmd.append(f"--since={since}")

        raw = self._run_git(*cmd)
        return self._parse_log(raw)

    def head_info(self) -> CommitRecord | None:
        """Return the HEAD commit record, or ``None`` if the repo is empty.

        Returns:
            The HEAD ``CommitRecord``, or ``None``.
        """
        commits = self.harvest(max_commits=1)
        return commits[0] if commits else None

    def current_branch(self) -> str:
        """Return the name of the currently checked-out branch.

        Returns:
            Branch name, or ``"HEAD"`` if detached.
        """
        result = self._run_git("git", "rev-parse", "--abbrev-ref", "HEAD")
        return result.strip() or "HEAD"

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

    def _parse_log(self, raw: str) -> list[CommitRecord]:
        """Parse raw git log output into commit records.

        Args:
            raw: Raw output from ``git log``.

        Returns:
            List of ``CommitRecord`` instances.
        """
        records: list[CommitRecord] = []
        # Split by record separator, skip the first empty element.
        chunks = raw.split(_RECORD_SEP)
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            record = self._parse_chunk(chunk)
            if record is not None:
                records.append(record)
        return records

    def _parse_chunk(self, chunk: str) -> CommitRecord | None:
        """Parse a single commit chunk.

        Args:
            chunk: A single commit's raw text.

        Returns:
            A ``CommitRecord``, or ``None`` if parsing fails.
        """
        # Split fields from numstat section.
        # The format fields come first, then blank line + numstat lines.
        lines = chunk.split("\n")

        # Find the field line (contains null bytes).
        field_line = ""
        numstat_lines: list[str] = []
        in_numstat = False

        for line in lines:
            if _FIELD_SEP in line and not field_line:
                field_line = line
            elif _NUMSTAT_RE.match(line):
                in_numstat = True
                numstat_lines.append(line)
            elif in_numstat and line.strip() and _NUMSTAT_RE.match(line):
                numstat_lines.append(line)

        if not field_line:
            return None

        parts = field_line.split(_FIELD_SEP)
        if len(parts) < 10:
            logger.warning("Incomplete commit record: %s fields", len(parts))
            return None

        sha = parts[0].strip()
        author_name = parts[1]
        author_email = parts[2]
        author_date_str = parts[3]
        committer_name = parts[4]
        committer_email = parts[5]
        committer_date_str = parts[6]
        parent_hashes = parts[7]
        subject = parts[8]
        body = parts[9] if len(parts) > 9 else ""

        authored_date = self._parse_iso_date(author_date_str)
        committed_date = self._parse_iso_date(committer_date_str)

        message = subject
        if body.strip():
            message = f"{subject}\n\n{body.strip()}"

        # Parse numstat for file changes.
        files: list[FileChange] = []
        total_ins = 0
        total_del = 0

        for ns_line in numstat_lines:
            fc = self._parse_numstat_line(ns_line)
            if fc is not None:
                files.append(fc)
                total_ins += fc.insertions
                total_del += fc.deletions

        # Detect merge commits.
        is_merge = len(parent_hashes.split()) > 1

        _ = is_merge  # stored in EnrichedCommit, not CommitRecord

        return CommitRecord(
            sha=sha,
            author_name=author_name,
            author_email=author_email,
            authored_date=authored_date,
            committer_name=committer_name,
            committer_email=committer_email,
            committed_date=committed_date,
            message=message,
            files=tuple(files),
            insertions=total_ins,
            deletions=total_del,
        )

    @staticmethod
    def _parse_numstat_line(line: str) -> FileChange | None:
        """Parse a --numstat line into a FileChange.

        Args:
            line: A numstat line (``added<TAB>deleted<TAB>path``).

        Returns:
            A ``FileChange``, or ``None`` if unparseable.
        """
        m = _NUMSTAT_RE.match(line)
        if not m:
            return None

        added_str, deleted_str, raw_path = m.group(1), m.group(2), m.group(3)

        # Binary files show "-" for both counts.
        added = int(added_str) if added_str != "-" else 0
        deleted = int(deleted_str) if deleted_str != "-" else 0

        # Handle renames: path like "src/{old.py => new.py}"
        old_path: str | None = None
        rename_m = _RENAME_RE.match(raw_path)
        if rename_m:
            prefix, old_part, new_part, suffix = rename_m.groups()
            path = f"{prefix}{new_part}{suffix}"
            old_path = f"{prefix}{old_part}{suffix}"
            change_type = ChangeType.RENAMED
        else:
            path = raw_path
            if added > 0 and deleted == 0:
                change_type = ChangeType.ADDED
            elif added == 0 and deleted > 0:
                change_type = ChangeType.DELETED
            else:
                change_type = ChangeType.MODIFIED

        return FileChange(
            path=path,
            change_type=change_type,
            insertions=added,
            deletions=deleted,
            old_path=old_path,
        )

    @staticmethod
    def _parse_iso_date(date_str: str) -> datetime:
        """Parse an ISO 8601 date string from git.

        Args:
            date_str: ISO date string.

        Returns:
            A timezone-aware ``datetime``.
        """
        date_str = date_str.strip()
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            logger.warning("Could not parse date '%s', using epoch", date_str)
            return datetime(1970, 1, 1, tzinfo=UTC)
