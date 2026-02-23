"""Unit tests for MergeDetector."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from dev_stats.core.git.merge_detector import MergeDetector


class TestMergeDetectorAncestor:
    """Tests for ancestor-based merge detection."""

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_is_ancestor_true(self, mock_run: MagicMock) -> None:
        """Branch is ancestor of target returns merged_into_default=True."""
        mock_run.return_value = MagicMock(stdout="")
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        status = detector.detect("feature", "main", "main")
        assert status.merged_into_default is True

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_is_not_ancestor(self, mock_run: MagicMock) -> None:
        """Branch not ancestor returns merged_into_default=False."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        status = detector.detect("feature", "main", "main")
        assert status.merged_into_default is False

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_different_target(self, mock_run: MagicMock) -> None:
        """Different target branch checks both default and target."""
        # First call (branch vs default) succeeds, second (branch vs target) fails
        mock_run.side_effect = [
            MagicMock(stdout=""),  # is_ancestor(branch, default)
            subprocess.CalledProcessError(1, "git"),  # is_ancestor(branch, target)
        ]
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        status = detector.detect("feature", "main", "develop")
        assert status.merged_into_default is True
        assert status.merged_into_target is False


class TestMergeDetectorMergeStatus:
    """Tests for MergeStatus properties."""

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_is_merged_true(self, mock_run: MagicMock) -> None:
        """is_merged returns True when merged into default."""
        mock_run.return_value = MagicMock(stdout="")
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        status = detector.detect("feature", "main", "main")
        assert status.is_merged is True

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_is_merged_false(self, mock_run: MagicMock) -> None:
        """is_merged returns False when not merged."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        status = detector.detect("feature", "main", "main")
        assert status.is_merged is False

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_merge_type_merged(self, mock_run: MagicMock) -> None:
        """Merged branch has MERGE_COMMIT type."""
        mock_run.return_value = MagicMock(stdout="")
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        status = detector.detect("feature", "main", "main")
        assert status.merge_type.value == "merge_commit"

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_merge_type_not_merged(self, mock_run: MagicMock) -> None:
        """Unmerged branch has NOT_MERGED type."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        status = detector.detect("feature", "main", "main")
        assert status.merge_type.value == "not_merged"


class TestMergeDetectorSquash:
    """Tests for squash-merge detection."""

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_squash_merge_error_returns_false(self, mock_run: MagicMock) -> None:
        """CalledProcessError in squash detection returns False."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        assert detector.is_squash_merged("feature", "main") is False

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_squash_merge_matched(self, mock_run: MagicMock) -> None:
        """Squash merge detected when tree matches target commit."""
        merge_base_sha = "abc123"
        branch_tree = "tree_sha_123"
        mock_run.side_effect = [
            MagicMock(stdout=f"{merge_base_sha}\n"),  # merge-base
            MagicMock(stdout=f"{branch_tree}\n"),  # merge-tree
            MagicMock(stdout=f"other_tree\n{branch_tree}\n"),  # log --format=%T
        ]
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        assert detector.is_squash_merged("feature", "main") is True

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_squash_merge_no_match(self, mock_run: MagicMock) -> None:
        """Not squash merged when tree does not match any target commit."""
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),  # merge-base
            MagicMock(stdout="branch_tree\n"),  # merge-tree
            MagicMock(stdout="other1\nother2\n"),  # log --format=%T
        ]
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        assert detector.is_squash_merged("feature", "main") is False

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_squash_merge_empty_tree(self, mock_run: MagicMock) -> None:
        """Returns False when merge-tree output is empty."""
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),  # merge-base
            MagicMock(stdout="\n"),  # merge-tree (empty)
        ]
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        assert detector.is_squash_merged("feature", "main") is False

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_squash_merge_tree_error(self, mock_run: MagicMock) -> None:
        """Returns False when merge-tree command fails."""
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),  # merge-base
            subprocess.CalledProcessError(1, "git"),  # merge-tree
        ]
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        assert detector.is_squash_merged("feature", "main") is False

    @patch("dev_stats.core.git.merge_detector.subprocess.run")
    def test_squash_merge_log_error(self, mock_run: MagicMock) -> None:
        """Returns False when log command fails."""
        mock_run.side_effect = [
            MagicMock(stdout="abc123\n"),  # merge-base
            MagicMock(stdout="branch_tree\n"),  # merge-tree
            subprocess.CalledProcessError(1, "git"),  # log
        ]
        detector = MergeDetector(repo_path=Path("/tmp/fake"))

        assert detector.is_squash_merged("feature", "main") is False
