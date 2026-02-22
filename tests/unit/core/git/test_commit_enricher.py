"""Unit tests for CommitEnricher."""

from __future__ import annotations

from datetime import UTC, datetime

from dev_stats.core.git.commit_enricher import CommitEnricher
from dev_stats.core.models import CommitRecord, CommitSizeCategory


def _make_commit(
    sha: str = "abc123",
    message: str = "fix: typo",
    insertions: int = 5,
    deletions: int = 2,
    author_email: str = "alice@example.com",
    authored_date: datetime | None = None,
) -> CommitRecord:
    """Build a minimal CommitRecord for testing."""
    if authored_date is None:
        authored_date = datetime(2024, 6, 15, 10, 0, tzinfo=UTC)
    return CommitRecord(
        sha=sha,
        author_name="Alice",
        author_email=author_email,
        authored_date=authored_date,
        committer_name="Alice",
        committer_email=author_email,
        committed_date=authored_date,
        message=message,
        insertions=insertions,
        deletions=deletions,
    )


class TestCommitEnricherClassification:
    """Tests for single-commit classification."""

    def test_conventional_type_detected(self) -> None:
        """Conventional commit type is extracted."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(message="feat: add login")])[0]
        assert result.conventional_type == "feat"

    def test_conventional_type_with_scope(self) -> None:
        """Conventional commit with scope is extracted."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(message="fix(auth): token refresh")])[0]
        assert result.conventional_type == "fix"

    def test_no_conventional_type(self) -> None:
        """Non-conventional message returns None."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(message="update readme")])[0]
        assert result.conventional_type is None

    def test_merge_detected(self) -> None:
        """Merge commits are detected from message."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(message="Merge branch 'feature' into main")])[0]
        assert result.is_merge is True

    def test_non_merge(self) -> None:
        """Regular commits are not merges."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(message="fix: typo")])[0]
        assert result.is_merge is False

    def test_revert_detected(self) -> None:
        """Revert commits are detected."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(message='Revert "feat: add login"')])[0]
        assert result.is_revert is True

    def test_non_revert(self) -> None:
        """Regular commits are not reverts."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(message="fix: typo")])[0]
        assert result.is_revert is False

    def test_fixup_detected(self) -> None:
        """Fixup commits are detected."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(message="fixup! fix: typo")])[0]
        assert result.is_fixup is True

    def test_squash_detected(self) -> None:
        """Squash commits are detected."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(message="squash! fix: typo")])[0]
        assert result.is_fixup is True


class TestCommitEnricherSizeCategory:
    """Tests for commit size classification."""

    def test_small_commit(self) -> None:
        """Small churn is SMALL."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(insertions=5, deletions=2)])[0]
        assert result.size_category == CommitSizeCategory.SMALL

    def test_medium_commit(self) -> None:
        """Medium churn is MEDIUM."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(insertions=80, deletions=30)])[0]
        assert result.size_category == CommitSizeCategory.MEDIUM

    def test_large_commit(self) -> None:
        """Large churn is LARGE."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(insertions=200, deletions=100)])[0]
        assert result.size_category == CommitSizeCategory.LARGE

    def test_enormous_commit(self) -> None:
        """Very large churn is ENORMOUS."""
        enricher = CommitEnricher()
        result = enricher.enrich([_make_commit(insertions=400, deletions=200)])[0]
        assert result.size_category == CommitSizeCategory.ENORMOUS


class TestCommitEnricherStreaks:
    """Tests for per-author streak computation."""

    def test_consecutive_days_streak(self) -> None:
        """Consecutive-day commits produce a streak."""
        enricher = CommitEnricher()
        commits = [
            _make_commit(
                sha=f"c{i}",
                authored_date=datetime(2024, 6, 10 + i, 12, 0, tzinfo=UTC),
            )
            for i in range(5)
        ]
        enriched = enricher.enrich(commits)
        streaks = enricher.compute_streaks(enriched)
        assert streaks["alice@example.com"] == 5

    def test_gap_breaks_streak(self) -> None:
        """A gap in dates breaks the streak."""
        enricher = CommitEnricher()
        commits = [
            _make_commit(
                sha="c1",
                authored_date=datetime(2024, 6, 10, 12, 0, tzinfo=UTC),
            ),
            _make_commit(
                sha="c2",
                authored_date=datetime(2024, 6, 11, 12, 0, tzinfo=UTC),
            ),
            _make_commit(
                sha="c3",
                authored_date=datetime(2024, 6, 15, 12, 0, tzinfo=UTC),
            ),
        ]
        enriched = enricher.enrich(commits)
        streaks = enricher.compute_streaks(enriched)
        assert streaks["alice@example.com"] == 2

    def test_single_commit_streak(self) -> None:
        """Single commit has a streak of 1."""
        enricher = CommitEnricher()
        enriched = enricher.enrich([_make_commit()])
        streaks = enricher.compute_streaks(enriched)
        assert streaks["alice@example.com"] == 1


class TestCommitEnricherPercentiles:
    """Tests for churn percentile ranking."""

    def test_percentiles(self) -> None:
        """Commits are ranked by churn score."""
        enricher = CommitEnricher()
        commits = [
            _make_commit(sha="small", insertions=1, deletions=0),
            _make_commit(sha="medium", insertions=50, deletions=30),
            _make_commit(sha="large", insertions=200, deletions=100),
        ]
        enriched = enricher.enrich(commits)
        percentiles = enricher.churn_percentiles(enriched)

        assert percentiles["small"] < percentiles["medium"]
        assert percentiles["medium"] < percentiles["large"]

    def test_empty_percentiles(self) -> None:
        """Empty list returns empty dict."""
        enricher = CommitEnricher()
        assert enricher.churn_percentiles([]) == {}
