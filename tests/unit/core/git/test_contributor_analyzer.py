"""Unit tests for ContributorAnalyzer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from dev_stats.core.git.contributor_analyzer import ContributorAnalyzer
from dev_stats.core.models import ChangeType, CommitRecord, FileChange


def _make_commit(
    *,
    sha: str = "abc123",
    author_name: str = "Alice",
    author_email: str = "alice@example.com",
    days_ago: int = 0,
    insertions: int = 10,
    deletions: int = 5,
    files: tuple[FileChange, ...] = (),
    hour: int = 12,
    weekday_offset: int = 0,
) -> CommitRecord:
    """Create a test CommitRecord."""
    # weekday_offset: 0=current weekday, etc
    base = datetime(2024, 6, 10, hour, 0, 0, tzinfo=UTC)  # Monday
    date = base - timedelta(days=days_ago) + timedelta(days=weekday_offset)
    if not files:
        files = (
            FileChange(
                path="main.py",
                change_type=ChangeType.MODIFIED,
                insertions=insertions,
                deletions=deletions,
            ),
        )
    return CommitRecord(
        sha=sha,
        author_name=author_name,
        author_email=author_email,
        authored_date=date,
        committer_name=author_name,
        committer_email=author_email,
        committed_date=date,
        message=f"commit {sha}",
        files=files,
        insertions=insertions,
        deletions=deletions,
    )


class TestContributorAnalyzerProfiles:
    """Tests for profile building."""

    def test_single_author(self) -> None:
        """Single author returns one profile."""
        analyzer = ContributorAnalyzer()
        commits = [_make_commit(sha="a1"), _make_commit(sha="a2")]
        profiles = analyzer.analyse(commits)

        assert len(profiles) == 1
        assert profiles[0].name == "Alice"
        assert profiles[0].commit_count == 2

    def test_multiple_authors(self) -> None:
        """Multiple authors return sorted profiles."""
        analyzer = ContributorAnalyzer()
        commits = [
            _make_commit(sha="a1", author_name="Alice", author_email="alice@example.com"),
            _make_commit(sha="a2", author_name="Alice", author_email="alice@example.com"),
            _make_commit(sha="b1", author_name="Bob", author_email="bob@example.com"),
        ]
        profiles = analyzer.analyse(commits)

        assert len(profiles) == 2
        assert profiles[0].name == "Alice"
        assert profiles[0].commit_count == 2
        assert profiles[1].name == "Bob"
        assert profiles[1].commit_count == 1

    def test_insertions_deletions(self) -> None:
        """Insertions and deletions are summed."""
        analyzer = ContributorAnalyzer()
        commits = [
            _make_commit(sha="a1", insertions=10, deletions=5),
            _make_commit(sha="a2", insertions=20, deletions=3),
        ]
        profiles = analyzer.analyse(commits)

        assert profiles[0].insertions == 30
        assert profiles[0].deletions == 8

    def test_files_touched(self) -> None:
        """Files touched counts unique files."""
        analyzer = ContributorAnalyzer()
        commits = [
            _make_commit(
                sha="a1",
                files=(
                    FileChange(path="a.py", change_type=ChangeType.MODIFIED),
                    FileChange(path="b.py", change_type=ChangeType.MODIFIED),
                ),
            ),
            _make_commit(
                sha="a2",
                files=(
                    FileChange(path="a.py", change_type=ChangeType.MODIFIED),
                    FileChange(path="c.py", change_type=ChangeType.MODIFIED),
                ),
            ),
        ]
        profiles = analyzer.analyse(commits)

        assert profiles[0].files_touched == 3

    def test_empty_commits(self) -> None:
        """Empty commit list returns empty profiles."""
        analyzer = ContributorAnalyzer()
        assert analyzer.analyse([]) == []

    def test_active_days(self) -> None:
        """Active days counts distinct commit dates."""
        analyzer = ContributorAnalyzer()
        commits = [
            _make_commit(sha="a1", days_ago=0),
            _make_commit(sha="a2", days_ago=0),
            _make_commit(sha="a3", days_ago=1),
        ]
        profiles = analyzer.analyse(commits)

        assert profiles[0].active_days == 2


class TestContributorAnalyzerAliases:
    """Tests for alias merging."""

    def test_auto_detect_aliases(self) -> None:
        """Same name, different emails are merged."""
        analyzer = ContributorAnalyzer()
        commits = [
            _make_commit(sha="a1", author_name="Alice", author_email="alice@work.com"),
            _make_commit(sha="a2", author_name="Alice", author_email="alice@work.com"),
            _make_commit(sha="a3", author_name="Alice", author_email="alice@home.com"),
        ]
        profiles = analyzer.analyse(commits)

        # Should be merged into one profile
        assert len(profiles) == 1
        assert profiles[0].commit_count == 3
        assert profiles[0].email == "alice@work.com"  # most commits
        assert "alice@home.com" in profiles[0].aliases

    def test_explicit_alias_map(self) -> None:
        """Explicit alias map overrides auto-detection."""
        analyzer = ContributorAnalyzer()
        commits = [
            _make_commit(sha="a1", author_name="Alice", author_email="alice@old.com"),
            _make_commit(sha="a2", author_name="Alice Smith", author_email="asmith@new.com"),
        ]
        alias_map = {"alice@old.com": "asmith@new.com"}
        profiles = analyzer.analyse(commits, alias_map=alias_map)

        assert len(profiles) == 1
        assert profiles[0].commit_count == 2
        assert profiles[0].email == "asmith@new.com"

    def test_different_names_not_merged(self) -> None:
        """Different names with different emails are not merged."""
        analyzer = ContributorAnalyzer()
        commits = [
            _make_commit(sha="a1", author_name="Alice", author_email="alice@example.com"),
            _make_commit(sha="b1", author_name="Bob", author_email="bob@example.com"),
        ]
        profiles = analyzer.analyse(commits)

        assert len(profiles) == 2


class TestContributorAnalyzerWorkPatterns:
    """Tests for work pattern computation."""

    def test_hour_distribution(self) -> None:
        """Hour distribution counts commits per hour."""
        analyzer = ContributorAnalyzer()
        commits = [
            _make_commit(sha="a1", hour=9),
            _make_commit(sha="a2", hour=9),
            _make_commit(sha="a3", hour=14),
        ]
        patterns = analyzer.work_patterns(commits)

        assert len(patterns) == 1
        assert patterns[0].hour_distribution[9] == 2
        assert patterns[0].hour_distribution[14] == 1

    def test_weekday_distribution(self) -> None:
        """Weekday distribution counts commits per day."""
        analyzer = ContributorAnalyzer()
        # June 10, 2024 is a Monday (weekday=0)
        commits = [
            _make_commit(sha="a1", weekday_offset=0),  # Monday
            _make_commit(sha="a2", weekday_offset=1),  # Tuesday
            _make_commit(sha="a3", weekday_offset=1),  # Tuesday
        ]
        patterns = analyzer.work_patterns(commits)

        assert len(patterns) == 1
        assert patterns[0].weekday_distribution[0] == 1  # Monday
        assert patterns[0].weekday_distribution[1] == 2  # Tuesday

    def test_empty_commits(self) -> None:
        """Empty commits return empty patterns."""
        analyzer = ContributorAnalyzer()
        assert analyzer.work_patterns([]) == []

    def test_multiple_authors(self) -> None:
        """Patterns are computed per author."""
        analyzer = ContributorAnalyzer()
        commits = [
            _make_commit(sha="a1", author_email="alice@example.com"),
            _make_commit(sha="b1", author_email="bob@example.com"),
        ]
        patterns = analyzer.work_patterns(commits)

        assert len(patterns) == 2
        emails = {p.author_email for p in patterns}
        assert "alice@example.com" in emails
        assert "bob@example.com" in emails
