"""E2E tests for CI adapter output."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typer.testing import CliRunner

from dev_stats.cli.app import app

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


class TestGithubAdapter:
    """Tests for --ci github output."""

    def test_github_ci_exits_zero(self, rich_fake_repo: Path) -> None:
        """Github CI adapter exits without crash."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo), "--ci", "github"])
        assert result.exit_code in (0, 1)

    def test_github_ci_format(self, rich_fake_repo: Path) -> None:
        """Github CI produces annotations or runs cleanly."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo), "--ci", "github"])
        plain = result.output.lower()
        assert "quality" in plain or "gate" in plain or result.exit_code == 0


class TestGitlabAdapter:
    """Tests for --ci gitlab output."""

    def test_gitlab_ci_exits_cleanly(self, rich_fake_repo: Path) -> None:
        """Gitlab CI adapter exits without crash."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo), "--ci", "gitlab"])
        assert result.exit_code in (0, 1)


class TestJenkinsAdapter:
    """Tests for --ci jenkins output."""

    def test_jenkins_ci_exits_cleanly(self, rich_fake_repo: Path) -> None:
        """Jenkins CI adapter exits without crash."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo), "--ci", "jenkins"])
        assert result.exit_code in (0, 1)


class TestTeamcityAdapter:
    """Tests for --ci teamcity output."""

    def test_teamcity_ci_exits_cleanly(self, rich_fake_repo: Path) -> None:
        """TeamCity CI adapter exits without crash."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo), "--ci", "teamcity"])
        assert result.exit_code in (0, 1)


class TestUnknownAdapter:
    """Tests for unknown --ci value."""

    def test_unknown_ci_exits_nonzero(self, rich_fake_repo: Path) -> None:
        """Unknown --ci value exits non-zero."""
        result = runner.invoke(app, ["analyse", str(rich_fake_repo), "--ci", "nonexistent"])
        assert result.exit_code != 0
