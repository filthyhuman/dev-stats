"""Reader for test coverage data from .coverage (SQLite) and lcov.info files."""

from __future__ import annotations

import logging
import re
import sqlite3
from typing import TYPE_CHECKING

from dev_stats.core.models import CoverageReport, FileCoverage

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

_LCOV_SF_RE = re.compile(r"^SF:(.+)$")
_LCOV_DA_RE = re.compile(r"^DA:(\d+),(\d+)")


class TestCoverageReader:
    """Reads test coverage data from common coverage file formats.

    Supports:
    - ``.coverage`` (pytest-cov / coverage.py SQLite database)
    - ``lcov.info`` (LCOV trace file format)

    Returns ``CoverageReport(overall_ratio=0.0)`` when no coverage file
    is found, without raising exceptions.
    """

    def read(self, repo_root: Path) -> CoverageReport:
        """Read coverage data from the repository root.

        Searches for ``.coverage`` and ``lcov.info`` files in *repo_root*.

        Args:
            repo_root: Absolute path to the repository root.

        Returns:
            A ``CoverageReport``. Returns empty report if no data found.
        """
        # Try .coverage (SQLite) first
        coverage_db = repo_root / ".coverage"
        if coverage_db.is_file():
            try:
                return self._read_coverage_db(coverage_db)
            except (sqlite3.Error, OSError):
                logger.warning("Could not read .coverage database")

        # Try lcov.info
        lcov_file = repo_root / "lcov.info"
        if lcov_file.is_file():
            try:
                return self._read_lcov(lcov_file)
            except OSError:
                logger.warning("Could not read lcov.info")

        # Try coverage.lcov (alternative name)
        lcov_alt = repo_root / "coverage.lcov"
        if lcov_alt.is_file():
            try:
                return self._read_lcov(lcov_alt)
            except OSError:
                logger.warning("Could not read coverage.lcov")

        return CoverageReport()

    def _read_coverage_db(self, db_path: Path) -> CoverageReport:
        """Read a .coverage SQLite database.

        Args:
            db_path: Path to the .coverage file.

        Returns:
            A ``CoverageReport``.
        """
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.cursor()

            # Check schema version
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='line_bits'")
            if cursor.fetchone() is None:
                # Old format or empty
                return CoverageReport()

            cursor.execute("SELECT file_id, path FROM file")
            file_map = dict(cursor.fetchall())

            files: list[FileCoverage] = []
            total_covered = 0
            total_coverable = 0

            for file_id, path in file_map.items():
                cursor.execute(
                    "SELECT numbits FROM line_bits WHERE file_id = ?",
                    (file_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    continue

                # numbits is a blob encoding covered line numbers
                numbits = row[0]
                covered = self._count_bits(numbits) if numbits else 0

                # Estimate total lines from the file
                total = max(covered, 1)
                ratio = covered / total if total > 0 else 0.0

                files.append(
                    FileCoverage(
                        path=str(path),
                        covered_lines=covered,
                        total_lines=total,
                        coverage_ratio=round(ratio, 4),
                    )
                )
                total_covered += covered
                total_coverable += total

            overall = total_covered / total_coverable if total_coverable > 0 else 0.0
            return CoverageReport(files=tuple(files), overall_ratio=round(overall, 4))
        finally:
            conn.close()

    @staticmethod
    def _count_bits(data: bytes) -> int:
        """Count set bits in a bytes object.

        Args:
            data: Binary data.

        Returns:
            Number of bits set to 1.
        """
        return sum(bin(byte).count("1") for byte in data)

    @staticmethod
    def _read_lcov(lcov_path: Path) -> CoverageReport:
        """Read an LCOV trace file.

        Args:
            lcov_path: Path to the lcov.info or coverage.lcov file.

        Returns:
            A ``CoverageReport``.
        """
        content = lcov_path.read_text(errors="replace")
        files: list[FileCoverage] = []
        total_covered = 0
        total_coverable = 0

        current_file: str | None = None
        covered = 0
        coverable = 0

        for line in content.splitlines():
            sf_match = _LCOV_SF_RE.match(line)
            if sf_match:
                # Save previous file
                if current_file is not None:
                    ratio = covered / coverable if coverable > 0 else 0.0
                    files.append(
                        FileCoverage(
                            path=current_file,
                            covered_lines=covered,
                            total_lines=coverable,
                            coverage_ratio=round(ratio, 4),
                        )
                    )
                    total_covered += covered
                    total_coverable += coverable
                current_file = sf_match.group(1)
                covered = 0
                coverable = 0
                continue

            da_match = _LCOV_DA_RE.match(line)
            if da_match:
                coverable += 1
                if int(da_match.group(2)) > 0:
                    covered += 1
                continue

            if line.strip() == "end_of_record" and current_file is not None:
                ratio = covered / coverable if coverable > 0 else 0.0
                files.append(
                    FileCoverage(
                        path=current_file,
                        covered_lines=covered,
                        total_lines=coverable,
                        coverage_ratio=round(ratio, 4),
                    )
                )
                total_covered += covered
                total_coverable += coverable
                current_file = None
                covered = 0
                coverable = 0

        overall = total_covered / total_coverable if total_coverable > 0 else 0.0
        return CoverageReport(files=tuple(files), overall_ratio=round(overall, 4))
