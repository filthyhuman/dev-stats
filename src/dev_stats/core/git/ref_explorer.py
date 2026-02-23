"""Ref explorer for tags, stashes, worktrees, and notes."""

from __future__ import annotations

import logging
import re
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from dev_stats.core.models import (
    NoteRecord,
    SemverTag,
    StashRecord,
    TagRecord,
    WorktreeRecord,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# Semver regex: v?MAJOR.MINOR.PATCH[-prerelease]
_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-(.+))?$")


class RefExplorer:
    """Explores Git refs: tags, stashes, worktrees, and notes.

    Extracts structured records from ``git tag``, ``git stash list``,
    ``git worktree list``, and ``git notes list``.
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialise the ref explorer.

        Args:
            repo_path: Absolute path to the repository root.
        """
        self._repo_path = repo_path

    def list_tags(self) -> list[TagRecord]:
        """List all tags in the repository.

        Returns:
            List of ``TagRecord`` sorted by date descending.
        """
        try:
            raw = self._run_git(
                "git",
                "tag",
                "-l",
                "--format=%(refname:short)%x00%(objecttype)%x00%(*objectname)%(objectname)%x00%(creatordate:iso-strict)%x00%(contents:subject)",
            )
        except subprocess.CalledProcessError:
            logger.debug("Could not list tags")
            return []

        tags: list[TagRecord] = []
        for line in raw.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("\x00")
            if len(parts) < 4:
                continue

            name = parts[0].strip()
            obj_type = parts[1].strip()
            sha = parts[2].strip()[:40]
            date_str = parts[3].strip()
            message = parts[4].strip() if len(parts) > 4 else None

            is_annotated = obj_type == "tag"
            date = self._parse_date(date_str)

            tags.append(
                TagRecord(
                    name=name,
                    sha=sha,
                    date=date,
                    message=message if message else None,
                    is_annotated=is_annotated,
                )
            )

        return sorted(tags, key=lambda t: t.date, reverse=True)

    def parse_semver_tags(self, tags: list[TagRecord]) -> list[SemverTag]:
        """Parse tags as semantic versions.

        Only tags matching the semver pattern are included.

        Args:
            tags: Tag records to parse.

        Returns:
            List of ``SemverTag`` sorted by version descending.
        """
        semver_tags: list[SemverTag] = []
        for tag in tags:
            m = _SEMVER_RE.match(tag.name)
            if m:
                semver_tags.append(
                    SemverTag(
                        tag=tag,
                        major=int(m.group(1)),
                        minor=int(m.group(2)),
                        patch=int(m.group(3)),
                        prerelease=m.group(4) or "",
                    )
                )
        return sorted(
            semver_tags,
            key=lambda s: (s.major, s.minor, s.patch),
            reverse=True,
        )

    def list_stashes(self) -> list[StashRecord]:
        """List all stash entries.

        Returns:
            List of ``StashRecord`` ordered by index.
        """
        try:
            raw = self._run_git(
                "git",
                "stash",
                "list",
                "--format=%gd%x00%gs%x00%ci",
            )
        except subprocess.CalledProcessError:
            logger.debug("Could not list stashes")
            return []

        stashes: list[StashRecord] = []
        for line in raw.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("\x00")
            if len(parts) < 3:
                continue

            ref = parts[0].strip()
            message = parts[1].strip()
            date_str = parts[2].strip()

            # Extract index from stash@{N}
            idx_match = re.search(r"\{(\d+)\}", ref)
            index = int(idx_match.group(1)) if idx_match else len(stashes)
            date = self._parse_date(date_str)

            stashes.append(
                StashRecord(
                    index=index,
                    message=message,
                    date=date,
                )
            )

        return stashes

    def list_worktrees(self) -> list[WorktreeRecord]:
        """List all worktrees.

        Returns:
            List of ``WorktreeRecord``.
        """
        try:
            raw = self._run_git("git", "worktree", "list", "--porcelain")
        except subprocess.CalledProcessError:
            logger.debug("Could not list worktrees")
            return []

        worktrees: list[WorktreeRecord] = []
        current_path = ""
        current_sha = ""
        current_branch: str | None = None

        for line in raw.splitlines():
            if line.startswith("worktree "):
                if current_path:
                    worktrees.append(
                        WorktreeRecord(
                            path=current_path,
                            head_sha=current_sha,
                            branch=current_branch,
                        )
                    )
                current_path = line[9:].strip()
                current_sha = ""
                current_branch = None
            elif line.startswith("HEAD "):
                current_sha = line[5:].strip()
            elif line.startswith("branch "):
                ref = line[7:].strip()
                # Strip refs/heads/ prefix
                if ref.startswith("refs/heads/"):
                    ref = ref[11:]
                current_branch = ref

        if current_path:
            worktrees.append(
                WorktreeRecord(
                    path=current_path,
                    head_sha=current_sha,
                    branch=current_branch,
                )
            )

        return worktrees

    def list_notes(self) -> list[NoteRecord]:
        """List all Git notes.

        Returns:
            List of ``NoteRecord``.
        """
        try:
            raw = self._run_git("git", "notes", "list")
        except subprocess.CalledProcessError:
            logger.debug("Could not list notes")
            return []

        notes: list[NoteRecord] = []
        for line in raw.strip().splitlines():
            if not line.strip():
                continue
            parts = line.strip().split(None, 1)
            if len(parts) < 2:
                continue

            commit_sha = parts[1]

            try:
                message = self._run_git("git", "notes", "show", commit_sha).strip()
            except subprocess.CalledProcessError:
                message = ""

            notes.append(
                NoteRecord(
                    commit_sha=commit_sha,
                    message=message,
                )
            )

        return notes

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse a date string from git.

        Args:
            date_str: ISO or git-format date string.

        Returns:
            A timezone-aware ``datetime``.
        """
        date_str = date_str.strip()
        if not date_str:
            return datetime(1970, 1, 1, tzinfo=UTC)
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            logger.debug("Could not parse date '%s'", date_str)
            return datetime(1970, 1, 1, tzinfo=UTC)

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
