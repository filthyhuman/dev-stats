"""Unit tests for the Aggregator."""

from __future__ import annotations

from pathlib import Path

from dev_stats.core.aggregator import Aggregator
from dev_stats.core.models import ClassReport, FileReport, MethodReport


def _make_file(
    name: str,
    language: str = "python",
    total: int = 100,
    code: int = 80,
    blank: int = 10,
    comment: int = 10,
) -> FileReport:
    """Create a FileReport for testing.

    Args:
        name: File name.
        language: Language string.
        total: Total lines.
        code: Code lines.
        blank: Blank lines.
        comment: Comment lines.

    Returns:
        A ``FileReport``.
    """
    return FileReport(
        path=Path(name),
        language=language,
        total_lines=total,
        code_lines=code,
        blank_lines=blank,
        comment_lines=comment,
    )


class TestAggregatorTotals:
    """Tests for aggregate totals."""

    def test_file_count(self) -> None:
        """RepoReport contains all files."""
        files = [_make_file("a.py"), _make_file("b.py")]
        agg = Aggregator()
        report = agg.aggregate(files, Path("/repo"))
        assert len(report.files) == 2

    def test_total_lines_sum(self) -> None:
        """Total lines are summed correctly."""
        files = [_make_file("a.py", total=100), _make_file("b.py", total=200)]
        agg = Aggregator()
        report = agg.aggregate(files, Path("/repo"))
        total = sum(f.total_lines for f in report.files)
        assert total == 300


class TestAggregatorLanguageSummaries:
    """Tests for per-language summaries."""

    def test_language_grouping(self) -> None:
        """Files are grouped by language."""
        files = [
            _make_file("a.py", language="python"),
            _make_file("b.py", language="python"),
            _make_file("c.js", language="javascript"),
        ]
        agg = Aggregator()
        report = agg.aggregate(files, Path("/repo"))
        langs = {s.language: s for s in report.languages}
        assert langs["python"].file_count == 2
        assert langs["javascript"].file_count == 1

    def test_language_lines_summed(self) -> None:
        """Per-language line counts are correct."""
        files = [
            _make_file("a.py", language="python", total=50, code=40, blank=5, comment=5),
            _make_file("b.py", language="python", total=30, code=25, blank=3, comment=2),
        ]
        agg = Aggregator()
        report = agg.aggregate(files, Path("/repo"))
        py = next(s for s in report.languages if s.language == "python")
        assert py.total_lines == 80
        assert py.code_lines == 65


class TestAggregatorModuleReports:
    """Tests for module grouping."""

    def test_files_grouped_by_directory(self) -> None:
        """Files in different directories produce different modules."""
        files = [
            _make_file("src/a.py"),
            _make_file("src/b.py"),
            _make_file("tests/c.py"),
        ]
        agg = Aggregator()
        report = agg.aggregate(files, Path("/repo"))
        module_names = {m.name for m in report.modules}
        assert "src" in module_names
        assert "tests" in module_names

    def test_root_files(self) -> None:
        """Files at the root are grouped into '(root)' module."""
        files = [_make_file("setup.py")]
        agg = Aggregator()
        report = agg.aggregate(files, Path("/repo"))
        assert report.modules[0].name == "(root)"


class TestAggregatorWithStructure:
    """Tests with classes and methods."""

    def test_classes_preserved(self) -> None:
        """Classes from file reports are accessible in the aggregate."""
        cls = ClassReport(name="Foo", line=1, end_line=10, lines=10)
        method = MethodReport(name="bar", line=1, end_line=5, lines=5)
        fr = FileReport(
            path=Path("a.py"),
            language="python",
            total_lines=20,
            code_lines=18,
            blank_lines=1,
            comment_lines=1,
            classes=(cls,),
            functions=(method,),
        )
        agg = Aggregator()
        report = agg.aggregate([fr], Path("/repo"))
        assert report.files[0].num_classes == 1
        assert report.files[0].num_functions == 1
