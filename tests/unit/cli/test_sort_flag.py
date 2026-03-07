"""Tests for the --sort CLI flag."""

from __future__ import annotations

from typer.testing import CliRunner

from dev_stats.cli.app import app

runner = CliRunner()


class TestSortFlag:
    """Tests for the --sort CLI option."""

    def test_sort_lines_accepted(self) -> None:
        """--sort lines is accepted."""
        result = runner.invoke(app, ["analyse", ".", "--sort", "lines"])
        assert result.exit_code == 0

    def test_sort_code_accepted(self) -> None:
        """--sort code is accepted."""
        result = runner.invoke(app, ["analyse", ".", "--sort", "code"])
        assert result.exit_code == 0

    def test_sort_complexity_accepted(self) -> None:
        """--sort complexity is accepted."""
        result = runner.invoke(app, ["analyse", ".", "--sort", "complexity"])
        assert result.exit_code == 0

    def test_sort_name_accepted(self) -> None:
        """--sort name is accepted."""
        result = runner.invoke(app, ["analyse", ".", "--sort", "name"])
        assert result.exit_code == 0

    def test_default_no_sort(self) -> None:
        """No --sort flag defaults to lines sort."""
        result = runner.invoke(app, ["analyse", "."])
        assert result.exit_code == 0
