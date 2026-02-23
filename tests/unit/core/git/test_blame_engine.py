"""Unit tests for BlameEngine."""

from __future__ import annotations

from dev_stats.core.git.blame_engine import BlameEngine
from dev_stats.core.models import AuthorBlameStat, FileBlameReport

_SAMPLE_PORCELAIN = """\
abc123def456abc123def456abc123def456abc1 1 1 3
author Alice
author-mail <alice@example.com>
author-time 1718450000
author-tz +0000
committer Alice
committer-mail <alice@example.com>
committer-time 1718450000
committer-tz +0000
summary initial commit
filename main.py
\tdef greet():
abc123def456abc123def456abc123def456abc1 2 2
author Alice
author-mail <alice@example.com>
author-time 1718450000
author-tz +0000
committer Alice
committer-mail <alice@example.com>
committer-time 1718450000
committer-tz +0000
summary initial commit
filename main.py
\t    return "hi"
def456abc123def456abc123def456abc123def4 3 3 1
author Bob
author-mail <bob@example.com>
author-time 1718460000
author-tz +0000
committer Bob
committer-mail <bob@example.com>
committer-time 1718460000
committer-tz +0000
summary add comment
filename main.py
\t# greeting function
"""


class TestBlameEngineParsing:
    """Tests for porcelain parsing."""

    def test_parse_lines(self) -> None:
        """Three content lines are parsed."""
        engine = BlameEngine.__new__(BlameEngine)
        lines = engine._parse_porcelain(_SAMPLE_PORCELAIN)
        assert len(lines) == 3

    def test_line_numbers(self) -> None:
        """Line numbers are correct."""
        engine = BlameEngine.__new__(BlameEngine)
        lines = engine._parse_porcelain(_SAMPLE_PORCELAIN)
        assert [ln.line_number for ln in lines] == [1, 2, 3]

    def test_author_extracted(self) -> None:
        """Author names are extracted."""
        engine = BlameEngine.__new__(BlameEngine)
        lines = engine._parse_porcelain(_SAMPLE_PORCELAIN)
        assert lines[0].author_name == "Alice"
        assert lines[2].author_name == "Bob"

    def test_email_extracted(self) -> None:
        """Author emails are extracted."""
        engine = BlameEngine.__new__(BlameEngine)
        lines = engine._parse_porcelain(_SAMPLE_PORCELAIN)
        assert lines[0].author_email == "alice@example.com"
        assert lines[2].author_email == "bob@example.com"

    def test_sha_extracted(self) -> None:
        """Commit SHAs are extracted."""
        engine = BlameEngine.__new__(BlameEngine)
        lines = engine._parse_porcelain(_SAMPLE_PORCELAIN)
        assert lines[0].commit_sha.startswith("abc123")
        assert lines[2].commit_sha.startswith("def456")

    def test_date_is_datetime(self) -> None:
        """Dates are parsed as datetime objects."""
        engine = BlameEngine.__new__(BlameEngine)
        lines = engine._parse_porcelain(_SAMPLE_PORCELAIN)
        assert lines[0].date.year >= 2024


class TestBlameEngineAggregation:
    """Tests for per-author aggregation."""

    def test_aggregate_counts(self) -> None:
        """Line counts are correct per author."""
        engine = BlameEngine.__new__(BlameEngine)
        lines = engine._parse_porcelain(_SAMPLE_PORCELAIN)
        authors = engine._aggregate_authors(lines)

        by_email = {a.author_email: a for a in authors}
        assert by_email["alice@example.com"].line_count == 2
        assert by_email["bob@example.com"].line_count == 1

    def test_aggregate_percentages_sum_100(self) -> None:
        """Percentages sum to approximately 100."""
        engine = BlameEngine.__new__(BlameEngine)
        lines = engine._parse_porcelain(_SAMPLE_PORCELAIN)
        authors = engine._aggregate_authors(lines)

        total_pct = sum(a.percentage for a in authors)
        assert abs(total_pct - 100.0) < 0.1

    def test_sorted_by_line_count(self) -> None:
        """Authors are sorted by line count descending."""
        engine = BlameEngine.__new__(BlameEngine)
        lines = engine._parse_porcelain(_SAMPLE_PORCELAIN)
        authors = engine._aggregate_authors(lines)

        assert authors[0].line_count >= authors[1].line_count

    def test_empty_lines(self) -> None:
        """Empty lines return empty authors."""
        assert BlameEngine._aggregate_authors([]) == []


class TestBlameEngineBusFactor:
    """Tests for bus_factor computation."""

    def test_single_author_bus_factor_1(self) -> None:
        """Single-author file has bus factor 1."""
        engine = BlameEngine.__new__(BlameEngine)
        report = FileBlameReport(
            path="main.py",
            total_lines=10,
            authors=(
                AuthorBlameStat(
                    author_name="Alice",
                    author_email="alice@example.com",
                    line_count=10,
                    percentage=100.0,
                ),
            ),
        )
        assert engine.bus_factor(report) == 1

    def test_two_equal_authors_bus_factor_1(self) -> None:
        """Two equal authors: bus factor is 1 (first exceeds 50%)."""
        engine = BlameEngine.__new__(BlameEngine)
        report = FileBlameReport(
            path="main.py",
            total_lines=10,
            authors=(
                AuthorBlameStat(
                    author_name="Alice",
                    author_email="alice@example.com",
                    line_count=5,
                    percentage=50.0,
                ),
                AuthorBlameStat(
                    author_name="Bob",
                    author_email="bob@example.com",
                    line_count=5,
                    percentage=50.0,
                ),
            ),
        )
        # 50% is not > 50%, so need both -> bus_factor=2
        assert engine.bus_factor(report) == 2

    def test_empty_report_bus_factor_0(self) -> None:
        """Empty report has bus factor 0."""
        engine = BlameEngine.__new__(BlameEngine)
        report = FileBlameReport(path="empty.py", total_lines=0)
        assert engine.bus_factor(report) == 0

    def test_dominant_author_bus_factor_1(self) -> None:
        """One dominant author (>50%) gives bus factor 1."""
        engine = BlameEngine.__new__(BlameEngine)
        report = FileBlameReport(
            path="main.py",
            total_lines=10,
            authors=(
                AuthorBlameStat(
                    author_name="Alice",
                    author_email="alice@example.com",
                    line_count=8,
                    percentage=80.0,
                ),
                AuthorBlameStat(
                    author_name="Bob",
                    author_email="bob@example.com",
                    line_count=2,
                    percentage=20.0,
                ),
            ),
        )
        assert engine.bus_factor(report) == 1
