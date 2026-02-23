"""Unit tests for the ``branches`` CLI command."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dev_stats.cli.app import app
from dev_stats.core.models import (
    BranchesReport,
    BranchReport,
    BranchStatus,
    DeletabilityCategory,
    MergeStatus,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

runner = CliRunner()

_MODULE = "dev_stats.cli.branches_command"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2025, 6, 1, tzinfo=UTC)


def _make_branch(
    name: str = "feature/x",
    *,
    status: BranchStatus = BranchStatus.ACTIVE,
    is_merged: bool = False,
    deletability: DeletabilityCategory = DeletabilityCategory.KEEP,
) -> BranchReport:
    """Build a minimal ``BranchReport``."""
    return BranchReport(
        name=name,
        is_remote=False,
        last_commit_date=_NOW,
        last_commit_sha="abc1234",
        commits_ahead=1,
        commits_behind=0,
        author_name="Test",
        author_email="test@example.com",
        status=status,
        merge_status=MergeStatus(merged_into_default=is_merged),
        deletability_score=80.0 if deletability == DeletabilityCategory.SAFE else 10.0,
        deletability_category=deletability,
    )


def _make_branches_report(
    branches: tuple[BranchReport, ...] | None = None,
) -> BranchesReport:
    """Build a minimal ``BranchesReport``."""
    if branches is None:
        branches = (_make_branch(),)
    stale = sum(1 for b in branches if b.status == BranchStatus.STALE)
    abandoned = sum(1 for b in branches if b.status == BranchStatus.ABANDONED)
    deletable = sum(1 for b in branches if b.deletability_category == DeletabilityCategory.SAFE)
    return BranchesReport(
        branches=branches,
        default_branch="main",
        target_branch="main",
        total_branches=len(branches),
        stale_count=stale,
        abandoned_count=abandoned,
        deletable_count=deletable,
    )


@pytest.fixture
def mock_branches(tmp_path: Path) -> Generator[MagicMock, None, None]:
    """Patch branch-analysis pipeline returning a fixture report."""
    report = _make_branches_report()

    with (
        patch(f"{_MODULE}.AnalysisConfig") as mock_config_cls,
        patch(f"{_MODULE}.BranchAnalyzer") as mock_analyzer_cls,
    ):
        cfg = MagicMock()
        cfg.branches = MagicMock()
        cfg.branches.model_copy.return_value = cfg.branches
        mock_config_cls.load.return_value = cfg

        mock_analyzer_cls.return_value.analyse.return_value = report

        carrier = MagicMock()
        carrier.config_cls = mock_config_cls
        carrier.analyzer_cls = mock_analyzer_cls
        carrier.cfg = cfg
        carrier.report = report

        yield carrier


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBranchesCommand:
    """Tests for the ``branches`` CLI command."""

    def test_branches_default(self, mock_branches: MagicMock, tmp_path: Path) -> None:
        """Basic invocation exits 0 and prints summary."""
        result = runner.invoke(app, ["branches", str(tmp_path)])
        assert result.exit_code == 0
        assert "branches" in result.output.lower()

    def test_branches_show_merged(self, tmp_path: Path) -> None:
        """``--show merged`` filters to merged branches only."""
        branches = (
            _make_branch("merged-one", is_merged=True),
            _make_branch("not-merged"),
        )
        report = _make_branches_report(branches)

        with (
            patch(f"{_MODULE}.AnalysisConfig") as mock_cfg,
            patch(f"{_MODULE}.BranchAnalyzer") as mock_ba,
        ):
            cfg = MagicMock()
            cfg.branches = MagicMock()
            cfg.branches.model_copy.return_value = cfg.branches
            mock_cfg.load.return_value = cfg
            mock_ba.return_value.analyse.return_value = report

            result = runner.invoke(app, ["branches", str(tmp_path), "--show", "merged"])

        assert result.exit_code == 0
        assert "merged-one" in result.output
        # not-merged should not appear in the table (though it counts in summary)
        lines_with_not_merged = [
            ln for ln in result.output.splitlines() if "not-merged" in ln and "Branch" not in ln
        ]
        assert not lines_with_not_merged

    def test_branches_show_stale(self, tmp_path: Path) -> None:
        """``--show stale`` filters to stale branches."""
        branches = (
            _make_branch("stale-one", status=BranchStatus.STALE),
            _make_branch("active-one"),
        )
        report = _make_branches_report(branches)

        with (
            patch(f"{_MODULE}.AnalysisConfig") as mock_cfg,
            patch(f"{_MODULE}.BranchAnalyzer") as mock_ba,
        ):
            cfg = MagicMock()
            cfg.branches = MagicMock()
            cfg.branches.model_copy.return_value = cfg.branches
            mock_cfg.load.return_value = cfg
            mock_ba.return_value.analyse.return_value = report

            result = runner.invoke(app, ["branches", str(tmp_path), "--show", "stale"])

        assert result.exit_code == 0
        assert "stale-one" in result.output

    def test_branches_show_abandoned(self, tmp_path: Path) -> None:
        """``--show abandoned`` filters to abandoned branches."""
        branches = (
            _make_branch("dead-branch", status=BranchStatus.ABANDONED),
            _make_branch("alive"),
        )
        report = _make_branches_report(branches)

        with (
            patch(f"{_MODULE}.AnalysisConfig") as mock_cfg,
            patch(f"{_MODULE}.BranchAnalyzer") as mock_ba,
        ):
            cfg = MagicMock()
            cfg.branches = MagicMock()
            cfg.branches.model_copy.return_value = cfg.branches
            mock_cfg.load.return_value = cfg
            mock_ba.return_value.analyse.return_value = report

            result = runner.invoke(app, ["branches", str(tmp_path), "--show", "abandoned"])

        assert result.exit_code == 0
        assert "dead-branch" in result.output

    def test_branches_generate_script(self, mock_branches: MagicMock, tmp_path: Path) -> None:
        """``--generate-script`` writes cleanup_branches.sh."""
        # Override the report to include a deletable branch
        deletable = _make_branch(
            "old-feature",
            status=BranchStatus.STALE,
            is_merged=True,
            deletability=DeletabilityCategory.SAFE,
        )
        report = _make_branches_report((deletable,))
        mock_branches.analyzer_cls.return_value.analyse.return_value = report

        result = runner.invoke(app, ["branches", str(tmp_path), "--generate-script"])
        assert result.exit_code == 0

        script = tmp_path / "cleanup_branches.sh"
        assert script.exists()
        content = script.read_text()
        assert "old-feature" in content
        assert "git branch -d" in content

    def test_branches_no_deletable_script(self, mock_branches: MagicMock, tmp_path: Path) -> None:
        """Script says 'no branches' when none are deletable."""
        report = _make_branches_report(
            (_make_branch("keep-me", deletability=DeletabilityCategory.KEEP),)
        )
        mock_branches.analyzer_cls.return_value.analyse.return_value = report

        result = runner.invoke(app, ["branches", str(tmp_path), "--generate-script"])
        assert result.exit_code == 0

        script = tmp_path / "cleanup_branches.sh"
        assert script.exists()
        assert "No branches" in script.read_text()

    def test_branches_file_not_found(self, tmp_path: Path) -> None:
        """Bad path results in exit code 1."""
        bad = tmp_path / "no_such_repo"
        with patch(f"{_MODULE}.AnalysisConfig") as mock_cfg:
            mock_cfg.load.side_effect = FileNotFoundError(str(bad))
            result = runner.invoke(app, ["branches", str(bad)])
        assert result.exit_code == 1

    def test_branches_exception(self, tmp_path: Path) -> None:
        """Generic exception results in exit code 1."""
        with patch(f"{_MODULE}.AnalysisConfig") as mock_cfg:
            mock_cfg.load.side_effect = RuntimeError("boom")
            result = runner.invoke(app, ["branches", str(tmp_path)])
        assert result.exit_code == 1
