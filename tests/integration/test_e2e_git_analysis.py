"""E2E tests for git analysis in the analyse command."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from dev_stats.cli.app import app

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


def _analyse_json(rich_fake_repo: Path, tmp_path: Path, extra: list[str] | None = None) -> str:
    """Run analyse with --format json and return concatenated JSON text.

    Args:
        rich_fake_repo: Path to the fake repository.
        tmp_path: Temporary directory for output.
        extra: Additional CLI arguments.

    Returns:
        Concatenated text of all generated JSON files.
    """
    out = tmp_path / "out"
    args = ["analyse", str(rich_fake_repo), "--format", "json", "--output", str(out)]
    if extra:
        args.extend(extra)
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    all_text = ""
    for jf in out.glob("*.json"):
        all_text += jf.read_text()
    return all_text


class TestGitAnalysisInJson:
    """Tests that git analysis data appears in JSON export."""

    def test_json_contains_git_data(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """JSON export includes commit or contributor data."""
        all_text = _analyse_json(rich_fake_repo, tmp_path)
        assert (
            "commit" in all_text.lower()
            or "contributor" in all_text.lower()
            or "author" in all_text.lower()
        )

    def test_json_has_contributor_names(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """JSON export includes contributor names from the fake repo."""
        all_text = _analyse_json(rich_fake_repo, tmp_path)
        assert "Alice" in all_text or "Bob" in all_text

    def test_json_export_is_parseable(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """All JSON exports are valid JSON."""
        out = tmp_path / "out"
        runner.invoke(
            app,
            ["analyse", str(rich_fake_repo), "--format", "json", "--output", str(out)],
        )
        json_files = list(out.glob("*.json"))
        assert json_files
        for jf in json_files:
            data = json.loads(jf.read_text())
            assert isinstance(data, (dict, list))

    def test_since_flag_accepted(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """The --since flag is accepted without error."""
        _analyse_json(rich_fake_repo, tmp_path, extra=["--since", "2099-01-01"])


class TestGitAnalysisTerminal:
    """Tests that terminal output includes git info."""

    def test_terminal_mentions_git(self, rich_fake_repo: Path) -> None:
        """Terminal output mentions git analysis."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo)])
        assert result.exit_code == 0
        assert "git" in result.output.lower()
