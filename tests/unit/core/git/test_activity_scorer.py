"""Unit tests for ActivityScorer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from dev_stats.core.git.activity_scorer import ActivityScorer
from dev_stats.core.models import (
    BranchStatus,
    DeletabilityCategory,
    MergeStatus,
)


class TestActivityScorerClassify:
    """Tests for classify_status."""

    def test_active_branch(self) -> None:
        """Recent branch is active."""
        scorer = ActivityScorer()
        now = datetime(2024, 6, 15, tzinfo=UTC)
        last = now - timedelta(days=5)
        assert scorer.classify_status(last, now, 30, 90) == BranchStatus.ACTIVE

    def test_stale_branch(self) -> None:
        """Branch inactive for stale_days is stale."""
        scorer = ActivityScorer()
        now = datetime(2024, 6, 15, tzinfo=UTC)
        last = now - timedelta(days=45)
        assert scorer.classify_status(last, now, 30, 90) == BranchStatus.STALE

    def test_abandoned_branch(self) -> None:
        """Branch inactive for abandoned_days is abandoned."""
        scorer = ActivityScorer()
        now = datetime(2024, 6, 15, tzinfo=UTC)
        last = now - timedelta(days=100)
        assert scorer.classify_status(last, now, 30, 90) == BranchStatus.ABANDONED


class TestActivityScorerScore:
    """Tests for score computation."""

    def test_merged_old_branch_high_score(self) -> None:
        """Merged + old branch gets high score (>= 80)."""
        scorer = ActivityScorer()
        now = datetime(2024, 6, 15, tzinfo=UTC)
        last = now - timedelta(days=100)
        merge_status = MergeStatus(merged_into_default=True)
        status = BranchStatus.ABANDONED

        score = scorer.score(
            merge_status=merge_status,
            status=status,
            last_commit_date=last,
            now=now,
            commits_ahead=0,
            is_protected=False,
        )
        assert score >= 80.0

    def test_protected_branch_zero_score(self) -> None:
        """Protected branch always gets 0."""
        scorer = ActivityScorer()
        now = datetime(2024, 6, 15, tzinfo=UTC)
        last = now - timedelta(days=100)
        merge_status = MergeStatus(merged_into_default=True)

        score = scorer.score(
            merge_status=merge_status,
            status=BranchStatus.ABANDONED,
            last_commit_date=last,
            now=now,
            commits_ahead=0,
            is_protected=True,
        )
        assert score == 0.0

    def test_active_unmerged_low_score(self) -> None:
        """Active unmerged branch gets low score."""
        scorer = ActivityScorer()
        now = datetime(2024, 6, 15, tzinfo=UTC)
        last = now - timedelta(days=2)
        merge_status = MergeStatus()

        score = scorer.score(
            merge_status=merge_status,
            status=BranchStatus.ACTIVE,
            last_commit_date=last,
            now=now,
            commits_ahead=5,
            is_protected=False,
        )
        assert score < 40.0

    def test_score_clamped_at_100(self) -> None:
        """Score never exceeds 100."""
        scorer = ActivityScorer()
        now = datetime(2024, 6, 15, tzinfo=UTC)
        last = now - timedelta(days=365)
        merge_status = MergeStatus(merged_into_default=True)

        score = scorer.score(
            merge_status=merge_status,
            status=BranchStatus.ABANDONED,
            last_commit_date=last,
            now=now,
            commits_ahead=0,
            is_protected=False,
        )
        assert score <= 100.0

    def test_no_unique_commits_bonus(self) -> None:
        """Zero commits ahead gives bonus."""
        scorer = ActivityScorer()
        now = datetime(2024, 6, 15, tzinfo=UTC)
        last = now - timedelta(days=50)
        merge_status = MergeStatus(merged_into_default=True)

        score_zero = scorer.score(
            merge_status=merge_status,
            status=BranchStatus.STALE,
            last_commit_date=last,
            now=now,
            commits_ahead=0,
            is_protected=False,
        )
        score_many = scorer.score(
            merge_status=merge_status,
            status=BranchStatus.STALE,
            last_commit_date=last,
            now=now,
            commits_ahead=10,
            is_protected=False,
        )
        assert score_zero > score_many


class TestActivityScorerCategorise:
    """Tests for categorise."""

    def test_safe_category(self) -> None:
        """High score -> SAFE."""
        scorer = ActivityScorer()
        assert scorer.categorise(85.0, False) == DeletabilityCategory.SAFE

    def test_caution_category(self) -> None:
        """Medium score -> CAUTION."""
        scorer = ActivityScorer()
        assert scorer.categorise(55.0, False) == DeletabilityCategory.CAUTION

    def test_keep_category(self) -> None:
        """Low score -> KEEP."""
        scorer = ActivityScorer()
        assert scorer.categorise(20.0, False) == DeletabilityCategory.KEEP

    def test_protected_always_keep(self) -> None:
        """Protected branch -> KEEP regardless of score."""
        scorer = ActivityScorer()
        assert scorer.categorise(100.0, True) == DeletabilityCategory.KEEP


class TestActivityScorerProtected:
    """Tests for is_protected static method."""

    def test_exact_match(self) -> None:
        """Exact name matches."""
        assert ActivityScorer.is_protected("main", ("main", "develop")) is True

    def test_glob_match(self) -> None:
        """Glob pattern matches."""
        assert ActivityScorer.is_protected("release/v1.0", ("release/*",)) is True

    def test_no_match(self) -> None:
        """Non-matching name."""
        assert ActivityScorer.is_protected("feature/x", ("main", "develop")) is False
