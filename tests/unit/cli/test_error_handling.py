"""Unit tests for Sprint 19 error handling improvements."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dev_stats.cli.app import app
from dev_stats.core.dispatcher import Dispatcher

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MODULE = "dev_stats.cli.analyse_command"


def _make_file_report() -> MagicMock:
    """Return a minimal mock FileReport."""
    from pathlib import Path as _Path

    fr = MagicMock()
    fr.path = _Path("example.py")
    fr.language = "python"
    fr.total_lines = 100
    fr.code_lines = 80
    fr.blank_lines = 10
    fr.comment_lines = 10
    fr.classes = ()
    fr.functions = ()
    fr.imports = ()
    return fr


def _make_repo_report(root: Path) -> MagicMock:
    """Return a minimal mock RepoReport.

    Args:
        root: Repository root path to set on the report.
    """
    report = MagicMock()
    report.root = root
    report.files = (_make_file_report(),)
    report.modules = ()
    report.languages = ()
    report.commits = None
    report.enriched_commits = None
    report.branches_report = None
    report.contributors = None
    report.patterns = None
    report.timeline = None
    return report


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

import pytest  # noqa: E402


@pytest.fixture
def mock_pipeline(tmp_path: Path) -> Generator[MagicMock, None, None]:
    """Patch the full analyse pipeline returning a mock report."""
    report = _make_repo_report(tmp_path)

    with (
        patch(f"{_MODULE}.AnalysisConfig") as mock_config_cls,
        patch(f"{_MODULE}.Scanner") as mock_scanner_cls,
        patch(f"{_MODULE}.create_default_registry") as mock_registry,
        patch(f"{_MODULE}.Dispatcher") as mock_dispatcher_cls,
        patch(f"{_MODULE}.Aggregator") as mock_aggregator_cls,
        patch(f"{_MODULE}.LogHarvester") as mock_harvester_cls,
        patch(f"{_MODULE}.CommitEnricher") as mock_enricher_cls,
        patch(f"{_MODULE}.BranchAnalyzer") as mock_branch_cls,
        patch(f"{_MODULE}.ContributorAnalyzer") as mock_contrib_cls,
        patch(f"{_MODULE}.PatternDetector") as mock_pattern_cls,
        patch(f"{_MODULE}.TimelineBuilder") as mock_timeline_cls,
        patch(f"{_MODULE}.TerminalReporter") as mock_reporter_cls,
    ):
        # Config
        cfg = MagicMock()
        cfg.output.top_n = 20
        cfg.branches = MagicMock()
        mock_config_cls.load.return_value = cfg
        cfg.model_copy.return_value = cfg

        # Scanner
        mock_scanner_cls.return_value.scan.return_value = [tmp_path / "example.py"]

        # Registry + Dispatcher
        mock_registry.return_value = MagicMock()
        mock_dispatcher_cls.return_value.parse.return_value = _make_file_report()

        # Git modules
        mock_harvester_cls.return_value.harvest.return_value = []
        mock_enricher_cls.return_value.enrich.return_value = []
        mock_branch_cls.return_value.analyse.return_value = MagicMock()
        mock_contrib_cls.return_value.analyse.return_value = []
        mock_pattern_cls.return_value.detect_all.return_value = []
        mock_timeline_cls.return_value.loc_timeline.return_value = []

        # Aggregator
        mock_aggregator_cls.return_value.aggregate.return_value = report

        # Exporters
        mock_reporter_cls.return_value.export.return_value = []

        # Expose mocks on a carrier object
        carrier = MagicMock()
        carrier.config_cls = mock_config_cls
        carrier.scanner_cls = mock_scanner_cls
        carrier.dispatcher_cls = mock_dispatcher_cls
        carrier.aggregator_cls = mock_aggregator_cls
        carrier.harvester_cls = mock_harvester_cls
        carrier.reporter_cls = mock_reporter_cls
        carrier.report = report
        carrier.cfg = cfg

        yield carrier


# ---------------------------------------------------------------------------
# Tests — Verbose / Quiet flags
# ---------------------------------------------------------------------------


class TestVerboseQuietFlags:
    """Tests for --verbose and --quiet CLI flags."""

    def test_verbose_flag_accepted(self, mock_pipeline: MagicMock, tmp_path: Path) -> None:
        """--verbose flag is accepted and the command succeeds."""
        result = runner.invoke(app, ["--verbose", "analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_quiet_flag_accepted(self, mock_pipeline: MagicMock, tmp_path: Path) -> None:
        """--quiet flag is accepted and the command succeeds."""
        result = runner.invoke(app, ["--quiet", "analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_verbose_and_quiet_conflict(self) -> None:
        """--verbose and --quiet together raise an error."""
        result = runner.invoke(app, ["--verbose", "--quiet", "analyse", "."])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Tests — Dispatcher error resilience
# ---------------------------------------------------------------------------


class TestDispatcherErrorResilience:
    """Tests for Dispatcher.parse_many error handling."""

    def test_parse_many_skips_failures(self) -> None:
        """parse_many continues after individual file errors."""
        from pathlib import Path as _Path

        registry = MagicMock()
        repo_root = _Path("/fake/repo")

        dispatcher = Dispatcher(registry=registry, repo_root=repo_root)

        good_report = _make_file_report()
        parser = MagicMock()
        parser.parse.side_effect = [OSError("permission denied"), good_report]
        registry.get_or_default.return_value = parser

        paths = [_Path("bad.py"), _Path("good.py")]
        results = dispatcher.parse_many(paths)

        assert len(results) == 1
        assert results[0] is good_report

    def test_parse_many_handles_syntax_error(self) -> None:
        """parse_many logs and skips SyntaxError from a parser."""
        from pathlib import Path as _Path

        registry = MagicMock()
        repo_root = _Path("/fake/repo")
        dispatcher = Dispatcher(registry=registry, repo_root=repo_root)

        good_report = _make_file_report()
        parser = MagicMock()
        parser.parse.side_effect = [SyntaxError("invalid syntax"), good_report]
        registry.get_or_default.return_value = parser

        paths = [_Path("broken.py"), _Path("valid.py")]
        results = dispatcher.parse_many(paths)

        assert len(results) == 1

    def test_parse_many_handles_unicode_error(self) -> None:
        """parse_many logs and skips UnicodeDecodeError from a parser."""
        from pathlib import Path as _Path

        registry = MagicMock()
        repo_root = _Path("/fake/repo")
        dispatcher = Dispatcher(registry=registry, repo_root=repo_root)

        good_report = _make_file_report()
        parser = MagicMock()
        parser.parse.side_effect = [
            UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
            good_report,
        ]
        registry.get_or_default.return_value = parser

        paths = [_Path("binary.dat"), _Path("valid.py")]
        results = dispatcher.parse_many(paths)

        assert len(results) == 1

    def test_parse_many_all_fail_returns_empty(self) -> None:
        """parse_many returns an empty list when every file fails."""
        from pathlib import Path as _Path

        registry = MagicMock()
        repo_root = _Path("/fake/repo")
        dispatcher = Dispatcher(registry=registry, repo_root=repo_root)

        parser = MagicMock()
        parser.parse.side_effect = [OSError("fail1"), ValueError("fail2")]
        registry.get_or_default.return_value = parser

        paths = [_Path("a.py"), _Path("b.py")]
        results = dispatcher.parse_many(paths)

        assert results == []


# ---------------------------------------------------------------------------
# Tests — Git analysis warning
# ---------------------------------------------------------------------------


class TestGitAnalysisWarning:
    """Tests for graceful degradation when git is unavailable."""

    def test_no_git_shows_warning(self, tmp_path: Path) -> None:
        """Non-git directory shows warning about git unavailability."""
        import subprocess

        (tmp_path / "test.py").write_text("x = 1\n")

        with (
            patch(f"{_MODULE}.AnalysisConfig") as mock_config_cls,
            patch(f"{_MODULE}.Scanner") as mock_scanner_cls,
            patch(f"{_MODULE}.create_default_registry") as mock_registry,
            patch(f"{_MODULE}.Dispatcher") as mock_dispatcher_cls,
            patch(f"{_MODULE}.Aggregator") as mock_aggregator_cls,
            patch(f"{_MODULE}.LogHarvester") as mock_harvester_cls,
            patch(f"{_MODULE}.CommitEnricher"),
            patch(f"{_MODULE}.BranchAnalyzer"),
            patch(f"{_MODULE}.ContributorAnalyzer"),
            patch(f"{_MODULE}.PatternDetector"),
            patch(f"{_MODULE}.TimelineBuilder"),
            patch(f"{_MODULE}.TerminalReporter") as mock_reporter_cls,
        ):
            cfg = MagicMock()
            cfg.output.top_n = 20
            cfg.branches = MagicMock()
            mock_config_cls.load.return_value = cfg
            cfg.model_copy.return_value = cfg

            mock_scanner_cls.return_value.scan.return_value = [tmp_path / "test.py"]
            mock_registry.return_value = MagicMock()
            mock_dispatcher_cls.return_value.parse.return_value = _make_file_report()

            # Simulate git failure
            mock_harvester_cls.return_value.harvest.side_effect = subprocess.CalledProcessError(
                128, "git"
            )

            report = _make_repo_report(tmp_path)
            mock_aggregator_cls.return_value.aggregate.return_value = report
            mock_reporter_cls.return_value.export.return_value = []

            result = runner.invoke(app, ["analyse", str(tmp_path)])

        # Should succeed despite git failure
        assert result.exit_code == 0
        assert "Git analysis unavailable" in result.output

    def test_git_oserror_shows_warning(self, tmp_path: Path) -> None:
        """OSError during git analysis shows warning and continues."""
        (tmp_path / "test.py").write_text("x = 1\n")

        with (
            patch(f"{_MODULE}.AnalysisConfig") as mock_config_cls,
            patch(f"{_MODULE}.Scanner") as mock_scanner_cls,
            patch(f"{_MODULE}.create_default_registry") as mock_registry,
            patch(f"{_MODULE}.Dispatcher") as mock_dispatcher_cls,
            patch(f"{_MODULE}.Aggregator") as mock_aggregator_cls,
            patch(f"{_MODULE}.LogHarvester") as mock_harvester_cls,
            patch(f"{_MODULE}.CommitEnricher"),
            patch(f"{_MODULE}.BranchAnalyzer"),
            patch(f"{_MODULE}.ContributorAnalyzer"),
            patch(f"{_MODULE}.PatternDetector"),
            patch(f"{_MODULE}.TimelineBuilder"),
            patch(f"{_MODULE}.TerminalReporter") as mock_reporter_cls,
        ):
            cfg = MagicMock()
            cfg.output.top_n = 20
            cfg.branches = MagicMock()
            mock_config_cls.load.return_value = cfg
            cfg.model_copy.return_value = cfg

            mock_scanner_cls.return_value.scan.return_value = [tmp_path / "test.py"]
            mock_registry.return_value = MagicMock()
            mock_dispatcher_cls.return_value.parse.return_value = _make_file_report()

            # Simulate git binary not found
            mock_harvester_cls.return_value.harvest.side_effect = OSError("git not found")

            report = _make_repo_report(tmp_path)
            mock_aggregator_cls.return_value.aggregate.return_value = report
            mock_reporter_cls.return_value.export.return_value = []

            result = runner.invoke(app, ["analyse", str(tmp_path)])

        assert result.exit_code == 0
        assert "Git analysis unavailable" in result.output
