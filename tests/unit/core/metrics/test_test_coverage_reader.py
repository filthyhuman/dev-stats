"""Unit tests for TestCoverageReader."""

from __future__ import annotations

from pathlib import Path

from dev_stats.core.metrics.test_coverage_reader import TestCoverageReader


class TestCoverageReaderNoFile:
    """Tests for missing coverage files."""

    def test_no_coverage_returns_zero(self) -> None:
        """Missing coverage files return 0.0 overall ratio."""
        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_empty")
        tmp.mkdir(parents=True, exist_ok=True)
        # Ensure no coverage files exist
        for f in (tmp / ".coverage", tmp / "lcov.info", tmp / "coverage.lcov"):
            if f.exists():
                f.unlink()
        report = reader.read(tmp)
        assert report.overall_ratio == 0.0
        assert len(report.files) == 0


class TestCoverageReaderLcov:
    """Tests for LCOV file reading."""

    def test_lcov_basic(self) -> None:
        """Basic LCOV file is parsed correctly."""
        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_lcov")
        tmp.mkdir(parents=True, exist_ok=True)
        lcov = tmp / "lcov.info"
        lcov.write_text("SF:src/main.py\nDA:1,1\nDA:2,1\nDA:3,0\nDA:4,1\nend_of_record\n")
        report = reader.read(tmp)
        assert len(report.files) == 1
        assert report.files[0].path == "src/main.py"
        assert report.files[0].covered_lines == 3
        assert report.files[0].total_lines == 4
        assert report.overall_ratio == 0.75

    def test_lcov_multiple_files(self) -> None:
        """LCOV with multiple files is parsed."""
        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_lcov_multi")
        tmp.mkdir(parents=True, exist_ok=True)
        lcov = tmp / "lcov.info"
        lcov.write_text(
            "SF:a.py\nDA:1,1\nDA:2,1\nend_of_record\nSF:b.py\nDA:1,0\nDA:2,0\nend_of_record\n"
        )
        report = reader.read(tmp)
        assert len(report.files) == 2
        assert report.overall_ratio == 0.5

    def test_lcov_empty_file(self) -> None:
        """Empty LCOV file returns empty report."""
        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_lcov_empty")
        tmp.mkdir(parents=True, exist_ok=True)
        lcov = tmp / "lcov.info"
        lcov.write_text("")
        report = reader.read(tmp)
        assert report.overall_ratio == 0.0


class TestCoverageReaderCoverageLcov:
    """Tests for coverage.lcov alternative name."""

    def test_coverage_lcov_read(self) -> None:
        """coverage.lcov is read as fallback."""
        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_lcov_alt")
        tmp.mkdir(parents=True, exist_ok=True)
        # Remove .coverage and lcov.info
        for f in (tmp / ".coverage", tmp / "lcov.info"):
            if f.exists():
                f.unlink()
        lcov = tmp / "coverage.lcov"
        lcov.write_text("SF:x.py\nDA:1,1\nend_of_record\n")
        report = reader.read(tmp)
        assert len(report.files) == 1
        assert report.overall_ratio == 1.0
