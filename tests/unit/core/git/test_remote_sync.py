"""Tests for RemoteSync."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from dev_stats.core.git.remote_sync import RemoteSync

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def sync(tmp_path: Path) -> RemoteSync:
    """Create a RemoteSync for a temp directory."""
    return RemoteSync(repo_path=tmp_path)


class TestAheadBehind:
    """ahead_behind tests."""

    def test_parses_counts(self, sync: RemoteSync, mocker: MagicMock) -> None:
        """Parses the ahead/behind counts from git output."""
        mock_run = mocker.patch("dev_stats.core.git.remote_sync.subprocess.run")
        mock_run.return_value = MagicMock(stdout="3\t5\n")

        ahead, behind = sync.ahead_behind("feature", "main")

        assert ahead == 3
        assert behind == 5

    def test_returns_zero_on_error(self, sync: RemoteSync, mocker: MagicMock) -> None:
        """Returns (0, 0) when git command fails."""
        mock_run = mocker.patch("dev_stats.core.git.remote_sync.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        ahead, behind = sync.ahead_behind("feature", "main")

        assert ahead == 0
        assert behind == 0

    def test_returns_zero_on_bad_output(self, sync: RemoteSync, mocker: MagicMock) -> None:
        """Returns (0, 0) when output cannot be parsed."""
        mock_run = mocker.patch("dev_stats.core.git.remote_sync.subprocess.run")
        mock_run.return_value = MagicMock(stdout="unparseable\n")

        ahead, behind = sync.ahead_behind("feature", "main")

        assert ahead == 0
        assert behind == 0


class TestHasRemote:
    """has_remote tests."""

    def test_true_when_remote_configured(self, sync: RemoteSync, mocker: MagicMock) -> None:
        """Returns True when branch has a remote configured."""
        mock_run = mocker.patch("dev_stats.core.git.remote_sync.subprocess.run")
        mock_run.return_value = MagicMock(stdout="origin\n")

        assert sync.has_remote("main") is True

    def test_false_when_no_remote(self, sync: RemoteSync, mocker: MagicMock) -> None:
        """Returns False when git config fails."""
        mock_run = mocker.patch("dev_stats.core.git.remote_sync.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        assert sync.has_remote("local-only") is False


class TestTrackingBranch:
    """tracking_branch tests."""

    def test_returns_upstream(self, sync: RemoteSync, mocker: MagicMock) -> None:
        """Returns the upstream branch name."""
        mock_run = mocker.patch("dev_stats.core.git.remote_sync.subprocess.run")
        mock_run.return_value = MagicMock(stdout="origin/main\n")

        result = sync.tracking_branch("main")

        assert result == "origin/main"

    def test_returns_none_on_error(self, sync: RemoteSync, mocker: MagicMock) -> None:
        """Returns None when no upstream is configured."""
        mock_run = mocker.patch("dev_stats.core.git.remote_sync.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = sync.tracking_branch("local-only")

        assert result is None

    def test_returns_none_on_empty(self, sync: RemoteSync, mocker: MagicMock) -> None:
        """Returns None when upstream is empty."""
        mock_run = mocker.patch("dev_stats.core.git.remote_sync.subprocess.run")
        mock_run.return_value = MagicMock(stdout="\n")

        result = sync.tracking_branch("main")

        assert result is None
