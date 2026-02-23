"""Unit tests for dashboard performance and size enforcement."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dev_stats.core.models import (
    ChangeType,
    CommitRecord,
    FileChange,
    FileReport,
    LanguageSummary,
    RepoReport,
)
from dev_stats.output.dashboard.dashboard_builder import (
    DashboardBuilder,
    DashboardSizeError,
)


def _make_config() -> MagicMock:
    """Create a mock AnalysisConfig."""
    return MagicMock()


def _make_large_report(
    num_files: int = 500,
    num_commits: int = 5000,
) -> RepoReport:
    """Create a large RepoReport for performance testing.

    Args:
        num_files: Number of file reports to generate.
        num_commits: Number of commit records to generate.

    Returns:
        A RepoReport with the specified number of files and commits.
    """
    files = tuple(
        FileReport(
            path=Path(f"src/module_{i // 50}/file_{i}.py"),
            language="python",
            total_lines=100 + (i % 200),
            code_lines=80 + (i % 150),
            blank_lines=10 + (i % 20),
            comment_lines=10 + (i % 30),
        )
        for i in range(num_files)
    )

    languages = (
        LanguageSummary(
            language="python",
            file_count=num_files,
            total_lines=sum(f.total_lines for f in files),
            code_lines=sum(f.code_lines for f in files),
            blank_lines=sum(f.blank_lines for f in files),
            comment_lines=sum(f.comment_lines for f in files),
        ),
    )

    commits = tuple(
        CommitRecord(
            sha=f"{i:040x}",
            author_name=f"dev{i % 10}",
            author_email=f"dev{i % 10}@example.com",
            authored_date=datetime(2024, 1 + (i % 12), 1 + (i % 28), tzinfo=UTC),
            committer_name=f"dev{i % 10}",
            committer_email=f"dev{i % 10}@example.com",
            committed_date=datetime(2024, 1 + (i % 12), 1 + (i % 28), tzinfo=UTC),
            message=f"feat: implement feature {i} for module {i % 50}",
            files=(
                FileChange(
                    path=f"src/module_{i % 50}/file_{i % num_files}.py",
                    change_type=ChangeType.MODIFIED,
                    insertions=10 + (i % 30),
                    deletions=5 + (i % 15),
                ),
            ),
            insertions=10 + (i % 30),
            deletions=5 + (i % 15),
        )
        for i in range(num_commits)
    )

    return RepoReport(
        root=Path("/tmp/large-repo"),
        files=files,
        languages=languages,
        commits=commits,
    )


class TestDashboardSizeEnforcement:
    """Tests for size threshold enforcement."""

    def test_small_dashboard_no_error(self, tmp_path: Path) -> None:
        """A small dashboard should not raise any errors."""
        report = RepoReport(
            root=Path("/tmp/repo"),
            files=(
                FileReport(
                    path=Path("main.py"),
                    language="python",
                    total_lines=100,
                    code_lines=80,
                    blank_lines=10,
                    comment_lines=10,
                ),
            ),
            languages=(
                LanguageSummary(
                    language="python",
                    file_count=1,
                    total_lines=100,
                    code_lines=80,
                    blank_lines=10,
                    comment_lines=10,
                ),
            ),
        )
        config = _make_config()
        builder = DashboardBuilder(report, config)

        # Should not raise
        result = builder.export(tmp_path)
        assert len(result) == 1

    def test_check_size_warns_above_threshold(self, caplog: pytest.LogCaptureFixture) -> None:
        """_check_size logs a warning for sizes between 30 and 50 MB."""
        # Create a string that is ~35 MB
        html = "x" * (35 * 1024 * 1024)

        with caplog.at_level(logging.WARNING):
            DashboardBuilder._check_size(html)

        assert "35.0 MB" in caplog.text
        assert "threshold" in caplog.text.lower()

    def test_check_size_raises_above_error_threshold(self) -> None:
        """_check_size raises DashboardSizeError for sizes above 50 MB."""
        # Create a string that is ~55 MB
        html = "x" * (55 * 1024 * 1024)

        with pytest.raises(DashboardSizeError) as exc_info:
            DashboardBuilder._check_size(html)

        assert exc_info.value.size_bytes > 50 * 1024 * 1024
        assert exc_info.value.limit_bytes == 50 * 1024 * 1024
        assert "55.0 MB" in str(exc_info.value)
        assert "--max-commits" in str(exc_info.value)

    def test_check_size_no_warning_under_threshold(self, caplog: pytest.LogCaptureFixture) -> None:
        """_check_size is silent for sizes under 30 MB."""
        html = "x" * (10 * 1024 * 1024)

        with caplog.at_level(logging.WARNING):
            DashboardBuilder._check_size(html)

        assert caplog.text == ""

    def test_dashboard_size_error_attributes(self) -> None:
        """DashboardSizeError stores size and limit."""
        err = DashboardSizeError(
            size_bytes=55 * 1024 * 1024,
            limit_bytes=50 * 1024 * 1024,
        )

        assert err.size_bytes == 55 * 1024 * 1024
        assert err.limit_bytes == 50 * 1024 * 1024
        assert "55.0 MB" in str(err)
        assert "50 MB" in str(err)


class TestDashboardPerformance:
    """Performance tests for large report generation."""

    def test_large_report_generates_under_budget(self, tmp_path: Path) -> None:
        """5000 commits + 500 files generates < 45 MB."""
        report = _make_large_report(num_files=500, num_commits=5000)
        config = _make_config()
        builder = DashboardBuilder(report, config)

        result = builder.export(tmp_path)
        html_path = result[0]

        size_bytes = html_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        assert size_mb < 45, f"Dashboard is {size_mb:.1f} MB, exceeds 45 MB budget"

    def test_large_report_generates_under_time_limit(self, tmp_path: Path) -> None:
        """5000 commits + 500 files generates in < 30 seconds."""
        report = _make_large_report(num_files=500, num_commits=5000)
        config = _make_config()
        builder = DashboardBuilder(report, config)

        start = time.monotonic()
        builder.export(tmp_path)
        elapsed = time.monotonic() - start

        assert elapsed < 30, f"Generation took {elapsed:.1f}s, exceeds 30s budget"

    def test_medium_report_under_warn_threshold(self, tmp_path: Path) -> None:
        """100 commits + 50 files stays well under warn threshold."""
        report = _make_large_report(num_files=50, num_commits=100)
        config = _make_config()
        builder = DashboardBuilder(report, config)

        result = builder.export(tmp_path)
        html_path = result[0]

        size_bytes = html_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        assert size_mb < 30, f"Dashboard is {size_mb:.1f} MB, exceeds warn threshold"
