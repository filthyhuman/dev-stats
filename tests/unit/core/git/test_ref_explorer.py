"""Unit tests for RefExplorer."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from dev_stats.core.git.ref_explorer import RefExplorer
from dev_stats.core.models import TagRecord


class TestRefExplorerTags:
    """Tests for tag listing."""

    @patch("dev_stats.core.git.ref_explorer.subprocess.run")
    def test_annotated_tag(self, mock_run: MagicMock) -> None:
        """Annotated tag is parsed with is_annotated=True."""
        mock_run.return_value = MagicMock(
            stdout=(
                "v1.0.0\x00tag\x00abc123def456abc123def456abc123def456abc1"
                "\x002024-06-15T10:00:00+00:00\x00Release 1.0\n"
            )
        )
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        tags = explorer.list_tags()

        assert len(tags) == 1
        assert tags[0].name == "v1.0.0"
        assert tags[0].is_annotated is True
        assert tags[0].message == "Release 1.0"

    @patch("dev_stats.core.git.ref_explorer.subprocess.run")
    def test_lightweight_tag(self, mock_run: MagicMock) -> None:
        """Lightweight tag is parsed with is_annotated=False."""
        mock_run.return_value = MagicMock(
            stdout="v0.1.0\x00commit\x00abc123def456abc123def456abc123def456abc1\x002024-06-15T10:00:00+00:00\x00\n"
        )
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        tags = explorer.list_tags()

        assert len(tags) == 1
        assert tags[0].name == "v0.1.0"
        assert tags[0].is_annotated is False

    @patch("dev_stats.core.git.ref_explorer.subprocess.run")
    def test_multiple_tags_sorted(self, mock_run: MagicMock) -> None:
        """Tags are sorted by date descending."""
        mock_run.return_value = MagicMock(
            stdout=(
                "v1.0.0\x00tag\x00abc1\x002024-01-01T00:00:00+00:00\x00First\n"
                "v2.0.0\x00tag\x00abc2\x002024-06-01T00:00:00+00:00\x00Second\n"
            )
        )
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        tags = explorer.list_tags()

        assert len(tags) == 2
        assert tags[0].name == "v2.0.0"
        assert tags[1].name == "v1.0.0"


class TestRefExplorerSemver:
    """Tests for semver parsing."""

    def test_simple_semver(self) -> None:
        """Simple v1.2.3 is parsed correctly."""
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        tag = TagRecord(
            name="v1.2.3",
            sha="abc123",
            date=datetime(2024, 6, 15, tzinfo=UTC),
        )
        result = explorer.parse_semver_tags([tag])

        assert len(result) == 1
        assert result[0].major == 1
        assert result[0].minor == 2
        assert result[0].patch == 3
        assert result[0].prerelease == ""

    def test_semver_with_prerelease(self) -> None:
        """v1.2.3-rc.1 is parsed with prerelease label."""
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        tag = TagRecord(
            name="v1.2.3-rc.1",
            sha="abc123",
            date=datetime(2024, 6, 15, tzinfo=UTC),
        )
        result = explorer.parse_semver_tags([tag])

        assert len(result) == 1
        assert result[0].major == 1
        assert result[0].minor == 2
        assert result[0].patch == 3
        assert result[0].prerelease == "rc.1"

    def test_semver_without_v_prefix(self) -> None:
        """1.0.0 without v prefix is parsed."""
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        tag = TagRecord(
            name="1.0.0",
            sha="abc123",
            date=datetime(2024, 6, 15, tzinfo=UTC),
        )
        result = explorer.parse_semver_tags([tag])

        assert len(result) == 1
        assert result[0].major == 1

    def test_non_semver_tag_excluded(self) -> None:
        """Non-semver tags are excluded."""
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        tag = TagRecord(
            name="release-candidate",
            sha="abc123",
            date=datetime(2024, 6, 15, tzinfo=UTC),
        )
        result = explorer.parse_semver_tags([tag])

        assert len(result) == 0

    def test_sorted_by_version(self) -> None:
        """Semver tags are sorted by version descending."""
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        tags = [
            TagRecord(name="v1.0.0", sha="a", date=datetime(2024, 1, 1, tzinfo=UTC)),
            TagRecord(name="v2.1.0", sha="b", date=datetime(2024, 2, 1, tzinfo=UTC)),
            TagRecord(name="v1.5.0", sha="c", date=datetime(2024, 3, 1, tzinfo=UTC)),
        ]
        result = explorer.parse_semver_tags(tags)

        assert result[0].major == 2
        assert result[1].minor == 5
        assert result[2].minor == 0


class TestRefExplorerStash:
    """Tests for stash listing."""

    @patch("dev_stats.core.git.ref_explorer.subprocess.run")
    def test_stash_list(self, mock_run: MagicMock) -> None:
        """Stash entries are parsed."""
        mock_run.return_value = MagicMock(
            stdout="stash@{0}\x00WIP on main: abc123 fix bug\x002024-06-15 10:00:00 +0000\n"
        )
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        stashes = explorer.list_stashes()

        assert len(stashes) == 1
        assert stashes[0].index == 0
        assert "WIP" in stashes[0].message

    @patch("dev_stats.core.git.ref_explorer.subprocess.run")
    def test_empty_stash(self, mock_run: MagicMock) -> None:
        """No stashes returns empty list."""
        mock_run.return_value = MagicMock(stdout="")
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))

        assert explorer.list_stashes() == []


class TestRefExplorerWorktree:
    """Tests for worktree listing."""

    @patch("dev_stats.core.git.ref_explorer.subprocess.run")
    def test_worktree_list(self, mock_run: MagicMock) -> None:
        """Worktrees are parsed from porcelain output."""
        mock_run.return_value = MagicMock(
            stdout="worktree /home/user/repo\nHEAD abc123def456\nbranch refs/heads/main\n\n"
        )
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        worktrees = explorer.list_worktrees()

        assert len(worktrees) == 1
        assert worktrees[0].path == "/home/user/repo"
        assert worktrees[0].branch == "main"

    @patch("dev_stats.core.git.ref_explorer.subprocess.run")
    def test_detached_worktree(self, mock_run: MagicMock) -> None:
        """Detached worktree has no branch."""
        mock_run.return_value = MagicMock(
            stdout="worktree /home/user/wt\nHEAD abc123\ndetached\n\n"
        )
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        worktrees = explorer.list_worktrees()

        assert len(worktrees) == 1
        assert worktrees[0].branch is None


class TestRefExplorerNotes:
    """Tests for notes listing."""

    @patch("dev_stats.core.git.ref_explorer.subprocess.run")
    def test_notes_list(self, mock_run: MagicMock) -> None:
        """Notes are listed with their commit SHAs."""
        mock_run.side_effect = [
            MagicMock(stdout="note_sha abc123\n"),
            MagicMock(stdout="This is a note"),
        ]
        explorer = RefExplorer(repo_path=Path("/tmp/fake"))
        notes = explorer.list_notes()

        assert len(notes) == 1
        assert notes[0].commit_sha == "abc123"
        assert notes[0].message == "This is a note"
