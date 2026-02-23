"""Tests for TimelineBuilder."""

from __future__ import annotations

from datetime import UTC, datetime

from dev_stats.core.git.timeline_builder import TimelineBuilder
from dev_stats.core.models import ChangeType, CommitRecord, FileChange


def _make_commit(
    sha: str = "a" * 40,
    date: datetime | None = None,
    insertions: int = 10,
    deletions: int = 0,
    author_email: str = "dev@example.com",
    files: tuple[FileChange, ...] = (),
) -> CommitRecord:
    """Create a CommitRecord with sensible defaults."""
    if date is None:
        date = datetime(2024, 1, 1, tzinfo=UTC)
    return CommitRecord(
        sha=sha,
        author_name="Dev",
        author_email=author_email,
        authored_date=date,
        committer_name="Dev",
        committer_email=author_email,
        committed_date=date,
        message="commit",
        files=files,
        insertions=insertions,
        deletions=deletions,
    )


class TestLocTimeline:
    """LOC timeline tests."""

    def test_empty_commits(self) -> None:
        """Empty input returns empty list."""
        builder = TimelineBuilder()

        assert builder.loc_timeline([]) == []

    def test_single_commit(self) -> None:
        """One commit produces one data point."""
        builder = TimelineBuilder()
        c = _make_commit(insertions=100, deletions=0)

        points = builder.loc_timeline([c])

        assert len(points) == 1
        assert points[0].value == 100
        assert points[0].label == "loc"

    def test_cumulative_values(self) -> None:
        """Values are cumulative net lines."""
        builder = TimelineBuilder()
        c1 = _make_commit(
            sha="a" * 40,
            date=datetime(2024, 1, 1, tzinfo=UTC),
            insertions=100,
            deletions=0,
        )
        c2 = _make_commit(
            sha="b" * 40,
            date=datetime(2024, 1, 2, tzinfo=UTC),
            insertions=50,
            deletions=20,
        )

        points = builder.loc_timeline([c2, c1])  # unsorted

        assert len(points) == 2
        assert points[0].value == 100  # c1
        assert points[1].value == 130  # c1 + c2 (100 + 30)

    def test_sorted_by_date(self) -> None:
        """Points are sorted by date ascending."""
        builder = TimelineBuilder()
        c1 = _make_commit(sha="a" * 40, date=datetime(2024, 3, 1, tzinfo=UTC))
        c2 = _make_commit(sha="b" * 40, date=datetime(2024, 1, 1, tzinfo=UTC))

        points = builder.loc_timeline([c1, c2])

        assert points[0].date < points[1].date


class TestLanguageTimeline:
    """Language timeline tests."""

    def test_empty_commits(self) -> None:
        """Empty input returns empty dict."""
        builder = TimelineBuilder()

        assert builder.language_timeline([]) == {}

    def test_groups_by_extension(self) -> None:
        """File changes are grouped by extension."""
        builder = TimelineBuilder()
        files = (
            FileChange(path="main.py", change_type=ChangeType.MODIFIED, insertions=10, deletions=2),
            FileChange(path="app.js", change_type=ChangeType.MODIFIED, insertions=5, deletions=1),
        )
        c = _make_commit(files=files)

        result = builder.language_timeline([c])

        assert "py" in result
        assert "js" in result
        assert result["py"][0].value == 8  # 10-2
        assert result["js"][0].value == 4  # 5-1

    def test_cumulative_per_language(self) -> None:
        """Language values are cumulative across commits."""
        builder = TimelineBuilder()
        f1 = (FileChange(path="a.py", change_type=ChangeType.ADDED, insertions=100, deletions=0),)
        f2 = (FileChange(path="b.py", change_type=ChangeType.ADDED, insertions=50, deletions=0),)
        c1 = _make_commit(sha="a" * 40, date=datetime(2024, 1, 1, tzinfo=UTC), files=f1)
        c2 = _make_commit(sha="b" * 40, date=datetime(2024, 1, 2, tzinfo=UTC), files=f2)

        result = builder.language_timeline([c1, c2])

        assert result["py"][-1].value == 150

    def test_no_extension_skipped(self) -> None:
        """Files without extensions are skipped."""
        builder = TimelineBuilder()
        files = (
            FileChange(path="Makefile", change_type=ChangeType.ADDED, insertions=10, deletions=0),
        )
        c = _make_commit(files=files)

        result = builder.language_timeline([c])

        assert result == {}


class TestTeamGrowth:
    """Team growth timeline tests."""

    def test_empty_commits(self) -> None:
        """Empty input returns empty list."""
        builder = TimelineBuilder()

        assert builder.team_growth([]) == []

    def test_unique_contributors(self) -> None:
        """Each new author increments the count."""
        builder = TimelineBuilder()
        c1 = _make_commit(
            sha="a" * 40,
            date=datetime(2024, 1, 1, tzinfo=UTC),
            author_email="alice@dev.com",
        )
        c2 = _make_commit(
            sha="b" * 40,
            date=datetime(2024, 1, 2, tzinfo=UTC),
            author_email="bob@dev.com",
        )
        c3 = _make_commit(
            sha="c" * 40,
            date=datetime(2024, 1, 3, tzinfo=UTC),
            author_email="alice@dev.com",
        )

        points = builder.team_growth([c1, c2, c3])

        assert points[0].value == 1  # alice
        assert points[1].value == 2  # alice + bob
        assert points[2].value == 2  # alice (repeat) + bob

    def test_label_is_contributors(self) -> None:
        """Points use 'contributors' label."""
        builder = TimelineBuilder()
        c = _make_commit()

        points = builder.team_growth([c])

        assert points[0].label == "contributors"


class TestFileExtension:
    """_file_extension helper tests."""

    def test_python_extension(self) -> None:
        """Extracts 'py' from a Python file."""
        assert TimelineBuilder._file_extension("src/main.py") == "py"

    def test_no_extension(self) -> None:
        """Returns empty string for files without extension."""
        assert TimelineBuilder._file_extension("Makefile") == ""

    def test_uppercase_normalized(self) -> None:
        """Extensions are lowercased."""
        assert TimelineBuilder._file_extension("README.MD") == "md"

    def test_nested_dots(self) -> None:
        """Only the last extension is returned."""
        assert TimelineBuilder._file_extension("app.test.js") == "js"
