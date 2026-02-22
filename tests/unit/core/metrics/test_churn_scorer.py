"""Unit tests for ChurnScorer."""

from __future__ import annotations

from datetime import UTC, datetime

from dev_stats.core.metrics.churn_scorer import ChurnScorer
from dev_stats.core.models import ChangeType, CommitRecord, FileChange


def _make_commit(
    files: tuple[FileChange, ...],
    sha: str = "abc123",
) -> CommitRecord:
    """Create a CommitRecord for testing.

    Args:
        files: File changes.
        sha: Commit SHA.

    Returns:
        A ``CommitRecord``.
    """
    now = datetime.now(tz=UTC)
    return CommitRecord(
        sha=sha,
        author_name="Test",
        author_email="test@example.com",
        authored_date=now,
        committer_name="Test",
        committer_email="test@example.com",
        committed_date=now,
        message="test commit",
        files=files,
    )


class TestChurnScorer:
    """Tests for churn scoring."""

    def test_empty_commits(self) -> None:
        """No commits produces empty results."""
        scorer = ChurnScorer()
        result = scorer.score([])
        assert len(result) == 0

    def test_single_file_churn(self) -> None:
        """Single file churn is computed correctly."""
        scorer = ChurnScorer()
        fc = FileChange(path="a.py", change_type=ChangeType.MODIFIED, insertions=10, deletions=5)
        commit = _make_commit(files=(fc,))
        result = scorer.score([commit])
        assert len(result) == 1
        assert result[0].path == "a.py"
        assert result[0].churn_score == 15
        assert result[0].commit_count == 1

    def test_multiple_commits_accumulated(self) -> None:
        """Churn accumulates across multiple commits."""
        scorer = ChurnScorer()
        fc1 = FileChange(path="a.py", change_type=ChangeType.MODIFIED, insertions=10, deletions=0)
        fc2 = FileChange(path="a.py", change_type=ChangeType.MODIFIED, insertions=5, deletions=3)
        c1 = _make_commit(files=(fc1,), sha="aaa")
        c2 = _make_commit(files=(fc2,), sha="bbb")
        result = scorer.score([c1, c2])
        assert result[0].commit_count == 2
        assert result[0].churn_score == 18

    def test_sorted_by_churn_descending(self) -> None:
        """Results are sorted by churn score descending."""
        scorer = ChurnScorer()
        fc_low = FileChange(
            path="low.py",
            change_type=ChangeType.MODIFIED,
            insertions=1,
            deletions=0,
        )
        fc_high = FileChange(
            path="high.py",
            change_type=ChangeType.MODIFIED,
            insertions=100,
            deletions=50,
        )
        commit = _make_commit(files=(fc_low, fc_high))
        result = scorer.score([commit])
        assert result[0].path == "high.py"
        assert result[1].path == "low.py"
