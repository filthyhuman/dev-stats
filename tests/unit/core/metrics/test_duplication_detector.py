"""Unit tests for DuplicationDetector."""

from __future__ import annotations

from dev_stats.core.metrics.duplication_detector import DuplicationDetector


class TestDuplicationDetector:
    """Tests for duplicate code detection."""

    def test_no_duplicates_in_unique_code(self) -> None:
        """Unique code produces no duplicates."""
        detector = DuplicationDetector(min_lines=3)
        sources = {
            "a.py": "line1\nline2\nline3\nline4\n",
            "b.py": "other1\nother2\nother3\nother4\n",
        }
        report = detector.detect_from_sources(sources)
        assert len(report.duplicates) == 0

    def test_exact_duplicate_detected(self) -> None:
        """Exact duplicate block of min_lines is detected."""
        detector = DuplicationDetector(min_lines=3)
        block = "alpha\nbeta\ngamma\ndelta\n"
        sources = {
            "a.py": f"unique_a\n{block}unique_end_a\n",
            "b.py": f"unique_b\n{block}unique_end_b\n",
        }
        report = detector.detect_from_sources(sources)
        assert len(report.duplicates) >= 1
        assert report.total_duplicated_lines >= 3

    def test_within_file_duplicate(self) -> None:
        """Duplicate block within the same file is detected."""
        detector = DuplicationDetector(min_lines=3)
        block = "same1\nsame2\nsame3\nsame4\n"
        sources = {
            "a.py": f"header\n{block}middle\nmiddle2\n{block}footer\n",
        }
        report = detector.detect_from_sources(sources)
        assert len(report.duplicates) >= 1

    def test_short_blocks_ignored(self) -> None:
        """Blocks shorter than min_lines are not flagged."""
        detector = DuplicationDetector(min_lines=6)
        block = "x\ny\nz\n"
        sources = {
            "a.py": f"a\n{block}b\n",
            "b.py": f"c\n{block}d\n",
        }
        report = detector.detect_from_sources(sources)
        assert len(report.duplicates) == 0

    def test_duplication_ratio_computed(self) -> None:
        """Duplication ratio is computed correctly."""
        detector = DuplicationDetector(min_lines=3)
        block = "dup1\ndup2\ndup3\n"
        sources = {
            "a.py": f"{block}unique\n",
            "b.py": f"{block}other\n",
        }
        report = detector.detect_from_sources(sources)
        assert report.duplication_ratio > 0.0
        assert report.duplication_ratio <= 1.0

    def test_large_min_lines(self) -> None:
        """A 10-line block is found when min_lines=10."""
        detector = DuplicationDetector(min_lines=10)
        block = "\n".join(f"line_{i}" for i in range(12))
        sources = {
            "a.py": f"header\n{block}\nfooter\n",
            "b.py": f"preamble\n{block}\npostamble\n",
        }
        report = detector.detect_from_sources(sources)
        assert len(report.duplicates) >= 1
