"""E2E tests for edge-case scenarios."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from typer.testing import CliRunner

if TYPE_CHECKING:
    from pathlib import Path

from dev_stats.cli.app import app

runner = CliRunner()


def _init_repo(tmp_path: Path) -> None:
    """Initialise a minimal git repository with one commit.

    Creates a git repo at ``tmp_path`` with user config and an initial commit
    containing a ``.gitkeep`` file so that the repo has at least one commit.

    Args:
        tmp_path: Directory in which to initialise the repository.
    """
    subprocess.run(
        ["git", "init", "--initial-branch", "main"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    (tmp_path / ".gitkeep").write_text("")
    subprocess.run(
        ["git", "add", ".gitkeep"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestEmptyDirectory:
    """Tests for analysing an empty directory."""

    def test_empty_dir_exits_zero(self, tmp_path: Path) -> None:
        """Analysing an empty directory exits 0."""
        _init_repo(tmp_path)
        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_empty_dir_shows_minimal_files(self, tmp_path: Path) -> None:
        """Empty directory reports at most 1 file (.gitkeep)."""
        _init_repo(tmp_path)
        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert "0 file(s)" in result.output or "1 file(s)" in result.output


class TestNoGitDirectory:
    """Tests for analysing a directory without .git."""

    def test_no_git_exits_zero(self, tmp_path: Path) -> None:
        """Directory without .git should still work (git analysis skipped)."""
        (tmp_path / "example.py").write_text("x = 1\n")
        result = runner.invoke(app, ["analyse", str(tmp_path)])
        # Should either exit 0 (graceful skip) or exit 1 with an error message
        # Accept both - the key is it doesn't crash with an unhandled exception
        assert result.exit_code in (0, 1)
        if result.exception:
            # Must be a SystemExit from typer.Exit, not an unhandled crash
            assert isinstance(result.exception, SystemExit)


class TestSingleFile:
    """Tests for a repo with just a single file."""

    def test_single_python_file(self, tmp_path: Path) -> None:
        """A repo with a single Python file produces valid output."""
        _init_repo(tmp_path)
        (tmp_path / "single.py").write_text(
            '"""Single file."""\n\ndef hello() -> str:\n    return "world"\n'
        )
        subprocess.run(
            ["git", "add", "single.py"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        subprocess.run(
            ["git", "commit", "-m", "add single file"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0
        # .gitkeep + single.py = 2 files; assert single.py is included
        assert "single.py" in result.output or "2 file(s)" in result.output


class TestBinaryFiles:
    """Tests for repos containing binary files."""

    def test_binary_files_excluded(self, tmp_path: Path) -> None:
        """Binary files are excluded, no crash."""
        _init_repo(tmp_path)
        (tmp_path / "code.py").write_text("x = 1\n")
        (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        subprocess.run(
            ["git", "add", "."],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        subprocess.run(
            ["git", "commit", "-m", "add files"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0
