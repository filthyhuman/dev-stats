"""End-to-end integration tests for the ``analyse`` sub-command."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from typer.testing import CliRunner

if TYPE_CHECKING:
    from pathlib import Path

from dev_stats.cli.app import app

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from *text*.

    Args:
        text: Raw string possibly containing ANSI codes.

    Returns:
        The cleaned string with all ANSI escapes removed.
    """
    return _ANSI_RE.sub("", text)


class TestAnalyseBasic:
    """E2E tests for the analyse sub-command."""

    def test_analyse_exits_zero(self, rich_fake_repo: Path) -> None:
        """Analyse <repo> exits 0."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo)])
        assert result.exit_code == 0

    def test_analyse_shows_file_count(self, rich_fake_repo: Path) -> None:
        """Output mentions the number of files found."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo)])
        plain = _strip_ansi(result.output)
        assert "3 file(s)" in plain

    def test_analyse_shows_languages(self, rich_fake_repo: Path) -> None:
        """Output mentions detected languages."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo)])
        plain = _strip_ansi(result.output)
        assert "python" in plain.lower() or "Python" in plain

    def test_analyse_shows_git_history(self, rich_fake_repo: Path) -> None:
        """Output mentions git history analysis."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo)])
        plain = _strip_ansi(result.output)
        assert "git" in plain.lower()

    def test_analyse_shows_parsed_count(self, rich_fake_repo: Path) -> None:
        """Output shows parsed file count."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo)])
        plain = _strip_ansi(result.output)
        assert "Parsed" in plain
