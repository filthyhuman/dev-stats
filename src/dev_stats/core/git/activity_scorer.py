"""Activity scorer computing 0-100 deletability scores for branches."""

from __future__ import annotations

import fnmatch
from typing import TYPE_CHECKING

from dev_stats.core.models import BranchStatus, DeletabilityCategory

if TYPE_CHECKING:
    from datetime import datetime

    from dev_stats.core.models import MergeStatus


class ActivityScorer:
    """Scores branch deletability on a 0-100 scale.

    The score combines merge status, age, and activity into a single
    deletability recommendation. Higher scores indicate stronger
    deletion candidates.
    """

    def classify_status(
        self,
        last_commit_date: datetime,
        now: datetime,
        stale_days: int,
        abandoned_days: int,
    ) -> BranchStatus:
        """Classify a branch's activity status.

        Args:
            last_commit_date: Timestamp of the latest commit on the branch.
            now: Current timestamp.
            stale_days: Days threshold for stale status.
            abandoned_days: Days threshold for abandoned status.

        Returns:
            A ``BranchStatus`` enum value.
        """
        age_days = (now - last_commit_date).days
        if age_days >= abandoned_days:
            return BranchStatus.ABANDONED
        if age_days >= stale_days:
            return BranchStatus.STALE
        return BranchStatus.ACTIVE

    def score(
        self,
        *,
        merge_status: MergeStatus,
        status: BranchStatus,
        last_commit_date: datetime,
        now: datetime,
        commits_ahead: int,
        is_protected: bool,
    ) -> float:
        """Compute a deletability score for a branch.

        Args:
            merge_status: Whether the branch is merged.
            status: Activity status.
            last_commit_date: Latest commit timestamp.
            now: Current timestamp.
            commits_ahead: Commits ahead of target.
            is_protected: Whether the branch matches a protected pattern.

        Returns:
            Score from 0.0 (keep) to 100.0 (safe to delete).
        """
        if is_protected:
            return 0.0

        score = 0.0

        # Merge status is the strongest signal.
        if merge_status.is_merged:
            score += 50.0

        # Age contributes up to 30 points.
        age_days = (now - last_commit_date).days
        age_score = min(age_days / 90.0, 1.0) * 30.0
        score += age_score

        # Activity status.
        if status == BranchStatus.ABANDONED:
            score += 15.0
        elif status == BranchStatus.STALE:
            score += 10.0

        # No unique commits means nothing to lose.
        if commits_ahead == 0:
            score += 5.0

        return min(score, 100.0)

    def categorise(
        self,
        score: float,
        is_protected: bool,
    ) -> DeletabilityCategory:
        """Categorise a deletability score.

        Args:
            score: Deletability score (0-100).
            is_protected: Whether the branch is protected.

        Returns:
            A ``DeletabilityCategory``.
        """
        if is_protected:
            return DeletabilityCategory.KEEP
        if score >= 70.0:
            return DeletabilityCategory.SAFE
        if score >= 40.0:
            return DeletabilityCategory.CAUTION
        return DeletabilityCategory.KEEP

    @staticmethod
    def is_protected(branch_name: str, patterns: tuple[str, ...]) -> bool:
        """Check if a branch name matches any protected pattern.

        Args:
            branch_name: Branch name to check.
            patterns: Glob patterns for protected branches.

        Returns:
            ``True`` if the branch is protected.
        """
        return any(fnmatch.fnmatch(branch_name, pattern) for pattern in patterns)
