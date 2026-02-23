"""Merge detector checking if a branch has been merged into a target."""

from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING

from dev_stats.core.models import MergeStatus

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class MergeDetector:
    """Detects whether branches have been merged into a target branch.

    Supports exact merge-commit detection, squash-merge detection (by
    comparing tree objects), and checks whether the branch tip is an
    ancestor of the target.
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialise the merge detector.

        Args:
            repo_path: Absolute path to the repository root.
        """
        self._repo_path = repo_path

    def detect(
        self,
        branch: str,
        default_branch: str,
        target_branch: str,
    ) -> MergeStatus:
        """Detect the merge status of a branch.

        Args:
            branch: Branch name to check.
            default_branch: The default branch (e.g. ``main``).
            target_branch: The configured target branch.

        Returns:
            A ``MergeStatus`` describing how (or if) the branch was merged.
        """
        merged_into_default = self._is_ancestor(branch, default_branch)
        merged_into_target = (
            self._is_ancestor(branch, target_branch) if target_branch != default_branch else False
        )

        return MergeStatus(
            merged_into_default=merged_into_default,
            merged_into_target=merged_into_target,
        )

    def is_squash_merged(self, branch: str, target: str) -> bool:
        """Detect if a branch was squash-merged into target.

        Compares the tree of each commit on ``target`` with the tree
        produced by merging ``branch`` into the merge-base. If any match,
        the branch content was squash-merged.

        Args:
            branch: Branch to check.
            target: Target branch.

        Returns:
            ``True`` if the branch appears to be squash-merged.
        """
        merge_base = self._merge_base(branch, target)
        if not merge_base:
            return False

        # Get tree of branch tip merged onto merge-base
        try:
            branch_tree = self._run_git("git", "merge-tree", merge_base, merge_base, branch).strip()
        except subprocess.CalledProcessError:
            return False

        if not branch_tree:
            return False

        # Check recent commits on target for matching tree
        try:
            target_trees = (
                self._run_git("git", "log", "--format=%T", "-n20", target).strip().splitlines()
            )
        except subprocess.CalledProcessError:
            return False

        return branch_tree in target_trees

    def _is_ancestor(self, branch: str, target: str) -> bool:
        """Check if branch tip is an ancestor of target.

        Args:
            branch: Branch to check.
            target: Target branch.

        Returns:
            ``True`` if ``branch`` is an ancestor of ``target``.
        """
        try:
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", branch, target],
                cwd=self._repo_path,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _merge_base(self, branch: str, target: str) -> str:
        """Find the merge base between two refs.

        Args:
            branch: First ref.
            target: Second ref.

        Returns:
            The merge-base SHA, or empty string if none.
        """
        try:
            result = self._run_git("git", "merge-base", branch, target)
            return result.strip()
        except subprocess.CalledProcessError:
            return ""

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
