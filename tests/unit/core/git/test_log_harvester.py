"""Unit tests for LogHarvester."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from dev_stats.core.git.log_harvester import LogHarvester
from dev_stats.core.models import ChangeType

# Simulated git log output with null-byte field separators.
_RECORD_SEP = "\x01"
_FIELD_SEP = "\x00"


def _make_log_output(
    sha: str = "abc123def456abc123def456abc123def456abc1",
    author_name: str = "Alice",
    author_email: str = "alice@example.com",
    author_date: str = "2024-06-15T10:30:00+00:00",
    committer_name: str = "Alice",
    committer_email: str = "alice@example.com",
    committer_date: str = "2024-06-15T10:30:00+00:00",
    parents: str = "abc000",
    subject: str = "feat: add login",
    body: str = "",
    numstat_lines: str = "",
) -> str:
    """Build a simulated git log chunk."""
    field_line = _FIELD_SEP.join(
        [
            sha,
            author_name,
            author_email,
            author_date,
            committer_name,
            committer_email,
            committer_date,
            parents,
            subject,
            body,
        ]
    )
    result = _RECORD_SEP + field_line
    if numstat_lines:
        result += "\n\n" + numstat_lines
    return result


class TestLogHarvesterParsing:
    """Tests for parsing git log output."""

    def test_parse_single_commit(self) -> None:
        """Single commit is parsed correctly."""
        raw = _make_log_output()
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        records = harvester._parse_log(raw)

        assert len(records) == 1
        assert records[0].sha == "abc123def456abc123def456abc123def456abc1"
        assert records[0].author_name == "Alice"
        assert records[0].author_email == "alice@example.com"

    def test_parse_commit_dates(self) -> None:
        """Dates are parsed as timezone-aware datetimes."""
        raw = _make_log_output(
            author_date="2024-06-15T10:30:00+00:00",
            committer_date="2024-06-15T11:00:00+02:00",
        )
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        records = harvester._parse_log(raw)

        assert records[0].authored_date.tzinfo is not None
        assert records[0].committed_date.tzinfo is not None

    def test_parse_message_with_body(self) -> None:
        """Subject + body are combined into message."""
        raw = _make_log_output(subject="feat: login", body="Added OAuth support")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        records = harvester._parse_log(raw)

        assert "feat: login" in records[0].message
        assert "Added OAuth support" in records[0].message

    def test_parse_message_subject_only(self) -> None:
        """Subject-only commit has no body in message."""
        raw = _make_log_output(subject="fix typo", body="")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        records = harvester._parse_log(raw)

        assert records[0].message == "fix typo"

    def test_parse_numstat(self) -> None:
        """--numstat lines are parsed into FileChange objects."""
        raw = _make_log_output(numstat_lines="10\t2\tsrc/main.py\n3\t0\tREADME.md")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        records = harvester._parse_log(raw)

        assert records[0].insertions == 13
        assert records[0].deletions == 2
        assert len(records[0].files) == 2
        assert records[0].files[0].path == "src/main.py"
        assert records[0].files[0].insertions == 10

    def test_parse_numstat_binary(self) -> None:
        """Binary files with - show 0 insertions/deletions."""
        raw = _make_log_output(numstat_lines="-\t-\timage.png")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        records = harvester._parse_log(raw)

        assert len(records[0].files) == 1
        assert records[0].files[0].insertions == 0
        assert records[0].files[0].deletions == 0

    def test_parse_rename(self) -> None:
        """Rename paths are parsed correctly."""
        raw = _make_log_output(numstat_lines="5\t3\tsrc/{old.py => new.py}")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        records = harvester._parse_log(raw)

        fc = records[0].files[0]
        assert fc.path == "src/new.py"
        assert fc.old_path == "src/old.py"
        assert fc.change_type == ChangeType.RENAMED

    def test_parse_multiple_commits(self) -> None:
        """Multiple commits are parsed."""
        raw = _make_log_output(sha="aaa" + "0" * 37, subject="first")
        raw += _make_log_output(sha="bbb" + "0" * 37, subject="second")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        records = harvester._parse_log(raw)

        assert len(records) == 2
        assert records[0].sha.startswith("aaa")
        assert records[1].sha.startswith("bbb")

    def test_empty_log(self) -> None:
        """Empty log returns empty list."""
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        records = harvester._parse_log("")
        assert records == []

    def test_parse_iso_date_fallback(self) -> None:
        """Invalid date falls back to epoch."""
        dt = LogHarvester._parse_iso_date("not-a-date")
        assert dt == datetime(1970, 1, 1, tzinfo=UTC)


class TestLogHarvesterCommands:
    """Tests for harvest/head_info/current_branch commands."""

    @patch("dev_stats.core.git.log_harvester.subprocess.run")
    def test_harvest_calls_git_log(self, mock_run: MagicMock) -> None:
        """harvest() calls git log with correct args."""
        mock_run.return_value = MagicMock(stdout="")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        harvester.harvest()

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "git" in cmd
        assert "log" in cmd

    @patch("dev_stats.core.git.log_harvester.subprocess.run")
    def test_harvest_with_max_commits(self, mock_run: MagicMock) -> None:
        """harvest(max_commits=5) passes -n5."""
        mock_run.return_value = MagicMock(stdout="")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        harvester.harvest(max_commits=5)

        cmd = mock_run.call_args[0][0]
        assert "-n5" in cmd

    @patch("dev_stats.core.git.log_harvester.subprocess.run")
    def test_harvest_with_since(self, mock_run: MagicMock) -> None:
        """harvest(since='2024-01-01') passes --since."""
        mock_run.return_value = MagicMock(stdout="")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        harvester.harvest(since="2024-01-01")

        cmd = mock_run.call_args[0][0]
        assert "--since=2024-01-01" in cmd

    @patch("dev_stats.core.git.log_harvester.subprocess.run")
    def test_current_branch(self, mock_run: MagicMock) -> None:
        """current_branch() returns branch name."""
        mock_run.return_value = MagicMock(stdout="main\n")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        assert harvester.current_branch() == "main"

    @patch("dev_stats.core.git.log_harvester.subprocess.run")
    def test_head_info_empty_repo(self, mock_run: MagicMock) -> None:
        """head_info() returns None on empty repo."""
        mock_run.return_value = MagicMock(stdout="")
        harvester = LogHarvester(repo_path=Path("/tmp/fake"))
        assert harvester.head_info() is None


class TestNumstatParsing:
    """Tests for _parse_numstat_line static method."""

    def test_added_file(self) -> None:
        """File with only additions is ADDED."""
        fc = LogHarvester._parse_numstat_line("10\t0\tnew_file.py")
        assert fc is not None
        assert fc.change_type == ChangeType.ADDED
        assert fc.insertions == 10
        assert fc.deletions == 0

    def test_deleted_file(self) -> None:
        """File with only deletions is DELETED."""
        fc = LogHarvester._parse_numstat_line("0\t15\told_file.py")
        assert fc is not None
        assert fc.change_type == ChangeType.DELETED

    def test_modified_file(self) -> None:
        """File with both additions and deletions is MODIFIED."""
        fc = LogHarvester._parse_numstat_line("5\t3\tmodified.py")
        assert fc is not None
        assert fc.change_type == ChangeType.MODIFIED

    def test_invalid_line(self) -> None:
        """Invalid line returns None."""
        assert LogHarvester._parse_numstat_line("not a numstat line") is None
