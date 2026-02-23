"""Remote sync checking ahead/behind counts and tracking status."""

from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class RemoteSync:
    """Checks branch tracking status and ahead/behind counts.

    Uses ``git rev-list --left-right --count`` to determine divergence
    between a local branch and its upstream or a target branch.
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialise the remote sync checker.

        Args:
            repo_path: Absolute path to the repository root.
        """
        self._repo_path = repo_path

    def ahead_behind(self, branch: str, target: str) -> tuple[int, int]:
        """Compute commits ahead and behind between branch and target.

        Args:
            branch: Local branch name.
            target: Target branch to compare against.

        Returns:
            Tuple of ``(ahead, behind)`` commit counts.
        """
        try:
            raw = self._run_git(
                "git",
                "rev-list",
                "--left-right",
                "--count",
                f"{branch}...{target}",
            )
            parts = raw.strip().split()
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
        except (subprocess.CalledProcessError, ValueError):
            logger.debug("Could not compute ahead/behind for %s vs %s", branch, target)
        return 0, 0

    def has_remote(self, branch: str) -> bool:
        """Check if a branch has a remote-tracking branch.

        Args:
            branch: Local branch name.

        Returns:
            ``True`` if the branch tracks a remote.
        """
        try:
            result = self._run_git(
                "git",
                "config",
                f"branch.{branch}.remote",
            )
            return bool(result.strip())
        except subprocess.CalledProcessError:
            return False

    def tracking_branch(self, branch: str) -> str | None:
        """Get the upstream tracking branch name.

        Args:
            branch: Local branch name.

        Returns:
            The upstream ref (e.g. ``origin/main``), or ``None``.
        """
        try:
            result = self._run_git(
                "git",
                "rev-parse",
                "--abbrev-ref",
                f"{branch}@{{upstream}}",
            )
            name = result.strip()
            return name if name else None
        except subprocess.CalledProcessError:
            return None

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
            timeout=30,
        )
        return result.stdout
