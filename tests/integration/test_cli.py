"""Integration tests for the dev-stats CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from dev_stats import __version__
from dev_stats.cli.app import app

runner = CliRunner()


class TestVersion:
    """Tests for the --version flag."""

    def test_version_exits_zero(self) -> None:
        """``--version`` should exit 0."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_version_prints_version(self) -> None:
        """``--version`` should print the current version string."""
        result = runner.invoke(app, ["--version"])
        assert __version__ in result.output


class TestHelp:
    """Tests for --help on the root and sub-commands."""

    def test_root_help_exits_zero(self) -> None:
        """``--help`` should exit 0."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_analyse_help_exits_zero(self) -> None:
        """``analyse --help`` should exit 0 and show flags."""
        result = runner.invoke(app, ["analyse", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--ci" in result.output


class TestAnalyse:
    """Tests for the ``analyse`` sub-command."""

    def test_analyse_dot_exits_zero(self) -> None:
        """``analyse .`` should exit 0."""
        result = runner.invoke(app, ["analyse", "."])
        assert result.exit_code == 0

    def test_analyse_prints_something(self) -> None:
        """``analyse .`` should produce output."""
        result = runner.invoke(app, ["analyse", "."])
        assert len(result.output.strip()) > 0


class TestBranches:
    """Tests for the ``branches`` sub-command."""

    def test_branches_exits_zero(self) -> None:
        """``branches .`` should exit 0."""
        result = runner.invoke(app, ["branches", "."])
        assert result.exit_code == 0


class TestGitlog:
    """Tests for the ``gitlog`` sub-command."""

    def test_gitlog_exits_zero(self) -> None:
        """``gitlog .`` should exit 0."""
        result = runner.invoke(app, ["gitlog", "."])
        assert result.exit_code == 0
