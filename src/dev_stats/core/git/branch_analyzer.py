"""Branch analyzer orchestrating merge detection, scoring, and reporting."""

from __future__ import annotations

import logging
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from dev_stats.core.git.activity_scorer import ActivityScorer
from dev_stats.core.git.merge_detector import MergeDetector
from dev_stats.core.git.remote_sync import RemoteSync
from dev_stats.core.models import BranchesReport, BranchReport

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.config.branch_config import BranchConfig

logger = logging.getLogger(__name__)


class BranchAnalyzer:
    """Orchestrates all branch analysis modules.

    Combines ``MergeDetector``, ``ActivityScorer``, and ``RemoteSync``
    to produce a comprehensive ``BranchesReport``.
    """

    def __init__(self, repo_path: Path, config: BranchConfig) -> None:
        """Initialise the branch analyzer.

        Args:
            repo_path: Absolute path to the repository root.
            config: Branch analysis configuration.
        """
        self._repo_path = repo_path
        self._config = config
        self._merge_detector = MergeDetector(repo_path)
        self._activity_scorer = ActivityScorer()
        self._remote_sync = RemoteSync(repo_path)

    def analyse(self) -> BranchesReport:
        """Analyse all branches in the repository.

        Returns:
            A ``BranchesReport`` with per-branch metrics and summaries.
        """
        default_branch = self._config.default_target
        target_branch = self._config.default_target
        now = datetime.now(tz=UTC)

        branches_raw = self._list_branches()
        reports: list[BranchReport] = []

        for name, is_remote, sha in branches_raw:
            # Skip the default branch itself.
            if name == default_branch:
                continue

            report = self._analyse_branch(
                name=name,
                is_remote=is_remote,
                sha=sha,
                default_branch=default_branch,
                target_branch=target_branch,
                now=now,
            )
            reports.append(report)

        stale = sum(1 for r in reports if r.status.value == "stale")
        abandoned = sum(1 for r in reports if r.status.value == "abandoned")
        deletable = sum(1 for r in reports if r.deletability_category.value == "safe")

        return BranchesReport(
            branches=tuple(sorted(reports, key=lambda r: r.name)),
            default_branch=default_branch,
            target_branch=target_branch,
            total_branches=len(reports),
            stale_count=stale,
            abandoned_count=abandoned,
            deletable_count=deletable,
        )

    def _analyse_branch(
        self,
        *,
        name: str,
        is_remote: bool,
        sha: str,
        default_branch: str,
        target_branch: str,
        now: datetime,
    ) -> BranchReport:
        """Analyse a single branch.

        Args:
            name: Branch name.
            is_remote: Whether this is a remote-tracking branch.
            sha: Commit SHA at the branch tip.
            default_branch: Repository default branch.
            target_branch: Configured target branch.
            now: Current timestamp.

        Returns:
            A ``BranchReport``.
        """
        # Get last commit info
        author_name, author_email, last_date = self._get_commit_info(sha)

        # Merge status
        merge_status = self._merge_detector.detect(
            branch=name,
            default_branch=default_branch,
            target_branch=target_branch,
        )

        # Ahead/behind
        ahead, behind = self._remote_sync.ahead_behind(name, target_branch)

        # Activity status
        status = self._activity_scorer.classify_status(
            last_commit_date=last_date,
            now=now,
            stale_days=self._config.stale_days,
            abandoned_days=self._config.abandoned_days,
        )

        # Deletability
        is_protected = ActivityScorer.is_protected(name, self._config.protected_patterns)
        score = self._activity_scorer.score(
            merge_status=merge_status,
            status=status,
            last_commit_date=last_date,
            now=now,
            commits_ahead=ahead,
            is_protected=is_protected,
        )
        category = self._activity_scorer.categorise(score, is_protected)

        return BranchReport(
            name=name,
            is_remote=is_remote,
            last_commit_date=last_date,
            last_commit_sha=sha,
            commits_ahead=ahead,
            commits_behind=behind,
            author_name=author_name,
            author_email=author_email,
            status=status,
            merge_status=merge_status,
            deletability_score=round(score, 1),
            deletability_category=category,
        )

    def _list_branches(self) -> list[tuple[str, bool, str]]:
        """List all branches with their tip SHAs.

        Returns:
            List of ``(name, is_remote, sha)`` tuples.
        """
        result: list[tuple[str, bool, str]] = []

        try:
            raw = self._run_git(
                "git",
                "for-each-ref",
                "--format=%(refname:short) %(objectname:short)",
                "refs/heads/",
            )
            for line in raw.strip().splitlines():
                if not line.strip():
                    continue
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    result.append((parts[0], False, parts[1]))
        except subprocess.CalledProcessError:
            logger.warning("Could not list local branches")

        return result

    def _get_commit_info(self, sha: str) -> tuple[str, str, datetime]:
        """Get author info and date for a commit.

        Args:
            sha: Commit SHA.

        Returns:
            Tuple of ``(author_name, author_email, authored_date)``.
        """
        try:
            raw = self._run_git("git", "log", "-1", "--format=%an%x00%ae%x00%aI", sha)
            parts = raw.strip().split("\x00")
            if len(parts) >= 3:
                return parts[0], parts[1], datetime.fromisoformat(parts[2])
        except (subprocess.CalledProcessError, ValueError):
            logger.debug("Could not get commit info for %s", sha)
        return "Unknown", "unknown@unknown", datetime.now(tz=UTC)

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
