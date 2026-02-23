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


class TestCoverageReaderSQLite:
    """Tests for .coverage SQLite database reading."""

    def test_reads_coverage_db(self) -> None:
        """Valid .coverage SQLite database is parsed."""
        import sqlite3

        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_sqlite")
        tmp.mkdir(parents=True, exist_ok=True)
        db_path = tmp / ".coverage"

        # Create a minimal coverage.py SQLite database
        if db_path.exists():
            db_path.unlink()
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE file (file_id INTEGER PRIMARY KEY, path TEXT)")
        conn.execute("CREATE TABLE line_bits (file_id INTEGER, numbits BLOB)")
        conn.execute("INSERT INTO file VALUES (1, 'src/main.py')")
        # numbits: each byte with bits set = covered lines
        # 0xFF = 8 bits set
        conn.execute("INSERT INTO line_bits VALUES (1, ?)", (b"\xff\x0f",))
        conn.commit()
        conn.close()

        report = reader.read(tmp)
        assert len(report.files) == 1
        assert report.files[0].path == "src/main.py"
        assert report.files[0].covered_lines == 12  # 8 + 4

    def test_empty_db_returns_empty(self) -> None:
        """DB without line_bits table returns empty report."""
        import sqlite3

        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_sqlite_empty")
        tmp.mkdir(parents=True, exist_ok=True)
        db_path = tmp / ".coverage"

        if db_path.exists():
            db_path.unlink()
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.commit()
        conn.close()

        report = reader.read(tmp)
        assert report.overall_ratio == 0.0

    def test_db_with_no_line_bits_row(self) -> None:
        """File with no line_bits row is skipped."""
        import sqlite3

        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_sqlite_norow")
        tmp.mkdir(parents=True, exist_ok=True)
        db_path = tmp / ".coverage"

        if db_path.exists():
            db_path.unlink()
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE file (file_id INTEGER PRIMARY KEY, path TEXT)")
        conn.execute("CREATE TABLE line_bits (file_id INTEGER, numbits BLOB)")
        conn.execute("INSERT INTO file VALUES (1, 'src/main.py')")
        # No line_bits row for file_id=1
        conn.commit()
        conn.close()

        report = reader.read(tmp)
        assert len(report.files) == 0

    def test_db_error_falls_through(self) -> None:
        """Corrupt .coverage falls through to lcov."""
        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_corrupt")
        tmp.mkdir(parents=True, exist_ok=True)
        # Remove alternative files
        for f in (tmp / "lcov.info", tmp / "coverage.lcov"):
            if f.exists():
                f.unlink()
        db_path = tmp / ".coverage"
        db_path.write_text("not a sqlite database")

        report = reader.read(tmp)
        assert report.overall_ratio == 0.0

    def test_multiple_files_in_db(self) -> None:
        """Multiple files in DB produce correct overall ratio."""
        import sqlite3

        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_multi_files")
        tmp.mkdir(parents=True, exist_ok=True)
        db_path = tmp / ".coverage"

        if db_path.exists():
            db_path.unlink()
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE file (file_id INTEGER PRIMARY KEY, path TEXT)")
        conn.execute("CREATE TABLE line_bits (file_id INTEGER, numbits BLOB)")
        conn.execute("INSERT INTO file VALUES (1, 'a.py')")
        conn.execute("INSERT INTO file VALUES (2, 'b.py')")
        conn.execute("INSERT INTO line_bits VALUES (1, ?)", (b"\xff",))  # 8 bits
        conn.execute("INSERT INTO line_bits VALUES (2, ?)", (b"\x0f",))  # 4 bits
        conn.commit()
        conn.close()

        report = reader.read(tmp)
        assert len(report.files) == 2
        assert report.overall_ratio > 0.0


class TestCoverageReaderCountBits:
    """Tests for _count_bits static method."""

    def test_count_bits_all_set(self) -> None:
        """0xFF byte has 8 bits set."""
        assert TestCoverageReader._count_bits(b"\xff") == 8

    def test_count_bits_none_set(self) -> None:
        """0x00 byte has 0 bits set."""
        assert TestCoverageReader._count_bits(b"\x00") == 0

    def test_count_bits_mixed(self) -> None:
        """Mixed bytes count correctly."""
        assert TestCoverageReader._count_bits(b"\x0f\xf0") == 8


class TestCoverageReaderLcovEdgeCases:
    """Edge cases for LCOV parsing."""

    def test_lcov_file_without_end_of_record(self) -> None:
        """LCOV file ending without end_of_record skips last file."""
        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_lcov_noend")
        tmp.mkdir(parents=True, exist_ok=True)
        for f in (tmp / ".coverage", tmp / "coverage.lcov"):
            if f.exists():
                f.unlink()
        lcov = tmp / "lcov.info"
        lcov.write_text("SF:a.py\nDA:1,1\n")
        report = reader.read(tmp)
        # File without end_of_record: not appended
        assert len(report.files) == 0

    def test_lcov_sf_saves_previous_file(self) -> None:
        """Second SF line triggers saving the previous file."""
        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_lcov_sf")
        tmp.mkdir(parents=True, exist_ok=True)
        for f in (tmp / ".coverage", tmp / "coverage.lcov"):
            if f.exists():
                f.unlink()
        lcov = tmp / "lcov.info"
        # Two SF entries without end_of_record between them
        lcov.write_text("SF:a.py\nDA:1,1\nDA:2,0\nSF:b.py\nDA:1,1\nend_of_record\n")
        report = reader.read(tmp)
        assert len(report.files) == 2
        # a.py: 1/2 covered (saved when second SF encountered)
        assert report.files[0].path == "a.py"
        assert report.files[0].covered_lines == 1
        assert report.files[0].total_lines == 2

    def test_lcov_zero_coverable_ratio(self) -> None:
        """File with zero coverable lines gets ratio 0.0."""
        reader = TestCoverageReader()
        tmp = Path("/tmp/_dev_stats_test_coverage_lcov_zero")
        tmp.mkdir(parents=True, exist_ok=True)
        for f in (tmp / ".coverage", tmp / "coverage.lcov"):
            if f.exists():
                f.unlink()
        lcov = tmp / "lcov.info"
        # SF with no DA lines
        lcov.write_text("SF:empty.py\nend_of_record\n")
        report = reader.read(tmp)
        assert len(report.files) == 1
        assert report.files[0].coverage_ratio == 0.0
