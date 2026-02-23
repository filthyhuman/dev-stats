"""Unit tests for the ``analyse`` CLI command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dev_stats.cli.app import app

if TYPE_CHECKING:
    from collections.abc import Generator

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MODULE = "dev_stats.cli.analyse_command"


def _make_file_report() -> MagicMock:
    """Return a minimal mock FileReport."""
    fr = MagicMock()
    fr.path = Path("example.py")
    fr.language = "python"
    fr.total_lines = 100
    fr.code_lines = 80
    fr.blank_lines = 10
    fr.comment_lines = 10
    fr.classes = ()
    fr.functions = ()
    fr.imports = ()
    return fr


def _make_repo_report() -> MagicMock:
    """Return a minimal mock RepoReport."""
    report = MagicMock()
    report.root = Path("/tmp/repo")
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


@pytest.fixture
def mock_pipeline(tmp_path: Path) -> Generator[MagicMock, None, None]:
    """Patch the full analyse pipeline returning a mock report."""
    report = _make_repo_report()
    report.root = tmp_path

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
        patch(f"{_MODULE}.JsonExporter") as mock_json_cls,
        patch(f"{_MODULE}.CsvExporter") as mock_csv_cls,
        patch(f"{_MODULE}.XmlExporter") as mock_xml_cls,
        patch(f"{_MODULE}.BadgeGenerator") as mock_badge_cls,
        patch(f"{_MODULE}.DashboardBuilder") as mock_dashboard_cls,
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
        mock_json_cls.return_value.export.return_value = [Path("report.json")]
        mock_csv_cls.return_value.export.return_value = [Path("report.csv")]
        mock_xml_cls.return_value.export.return_value = [Path("report.xml")]
        mock_badge_cls.return_value.export.return_value = [Path("badge.svg")]
        mock_dashboard_cls.return_value.export.return_value = [Path("dashboard.html")]

        # Expose mocks on a carrier object
        carrier = MagicMock()
        carrier.config_cls = mock_config_cls
        carrier.scanner_cls = mock_scanner_cls
        carrier.dispatcher_cls = mock_dispatcher_cls
        carrier.aggregator_cls = mock_aggregator_cls
        carrier.harvester_cls = mock_harvester_cls
        carrier.enricher_cls = mock_enricher_cls
        carrier.branch_cls = mock_branch_cls
        carrier.contrib_cls = mock_contrib_cls
        carrier.pattern_cls = mock_pattern_cls
        carrier.timeline_cls = mock_timeline_cls
        carrier.reporter_cls = mock_reporter_cls
        carrier.json_cls = mock_json_cls
        carrier.csv_cls = mock_csv_cls
        carrier.xml_cls = mock_xml_cls
        carrier.badge_cls = mock_badge_cls
        carrier.dashboard_cls = mock_dashboard_cls
        carrier.report = report
        carrier.cfg = cfg

        yield carrier


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnalyseCommand:
    """Tests for the ``analyse`` CLI command."""

    def test_analyse_default_terminal_output(
        self, mock_pipeline: MagicMock, tmp_path: Path
    ) -> None:
        """Default invocation (no --format) shows terminal output."""
        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0
        mock_pipeline.reporter_cls.assert_called_once()

    def test_analyse_format_json(self, mock_pipeline: MagicMock, tmp_path: Path) -> None:
        """``--format json`` invokes the JSON exporter (regular + summary)."""
        result = runner.invoke(app, ["analyse", str(tmp_path), "--format", "json"])
        assert result.exit_code == 0
        # Called twice: once for full report, once for summary
        assert mock_pipeline.json_cls.return_value.export.call_count == 2
        mock_pipeline.reporter_cls.assert_not_called()

    def test_analyse_format_all(self, mock_pipeline: MagicMock, tmp_path: Path) -> None:
        """``--format all`` invokes every exporter."""
        result = runner.invoke(app, ["analyse", str(tmp_path), "--format", "all"])
        assert result.exit_code == 0
        mock_pipeline.json_cls.return_value.export.assert_called()
        mock_pipeline.csv_cls.return_value.export.assert_called_once()
        mock_pipeline.xml_cls.return_value.export.assert_called_once()
        mock_pipeline.badge_cls.return_value.export.assert_called_once()
        mock_pipeline.dashboard_cls.return_value.export.assert_called_once()

    def test_analyse_format_dashboard(self, mock_pipeline: MagicMock, tmp_path: Path) -> None:
        """``--format dashboard`` builds the HTML dashboard."""
        result = runner.invoke(app, ["analyse", str(tmp_path), "--format", "dashboard"])
        assert result.exit_code == 0
        mock_pipeline.dashboard_cls.return_value.export.assert_called_once()

    def test_analyse_custom_top(self, mock_pipeline: MagicMock, tmp_path: Path) -> None:
        """``--top 5`` triggers config model_copy."""
        result = runner.invoke(app, ["analyse", str(tmp_path), "--top", "5"])
        assert result.exit_code == 0
        mock_pipeline.cfg.model_copy.assert_called_once()

    def test_analyse_ci_github(self, mock_pipeline: MagicMock, tmp_path: Path) -> None:
        """``--ci github`` invokes the GitHub Actions adapter."""
        with patch(f"{_MODULE}.AnalyseCommand._create_ci_adapter") as mock_ci:
            adapter = MagicMock()
            adapter.violations = ()
            mock_ci.return_value = adapter
            result = runner.invoke(app, ["analyse", str(tmp_path), "--ci", "github"])
        assert result.exit_code == 0
        mock_ci.assert_called_once()

    def test_analyse_fail_on_violations(self, mock_pipeline: MagicMock, tmp_path: Path) -> None:
        """``--fail-on-violations`` exits 1 when violations present."""
        with patch(f"{_MODULE}.AnalyseCommand._create_ci_adapter") as mock_ci:
            from dev_stats.ci.violation import Violation, ViolationSeverity

            adapter = MagicMock()
            adapter.violations = (
                Violation(
                    rule="test-rule",
                    message="fail",
                    severity=ViolationSeverity.ERROR,
                ),
            )
            mock_ci.return_value = adapter
            result = runner.invoke(
                app,
                ["analyse", str(tmp_path), "--fail-on-violations"],
            )
        assert result.exit_code == 1

    def test_analyse_file_not_found(self, tmp_path: Path) -> None:
        """Non-existent path raises exit code 1."""
        bad_path = tmp_path / "does_not_exist"
        with patch(f"{_MODULE}.AnalysisConfig") as mock_cfg:
            mock_cfg.load.side_effect = FileNotFoundError(str(bad_path))
            result = runner.invoke(app, ["analyse", str(bad_path)])
        assert result.exit_code == 1

    def test_analyse_parse_exception_logged(self, mock_pipeline: MagicMock, tmp_path: Path) -> None:
        """One file failing to parse doesn't abort the run."""
        scanner = mock_pipeline.scanner_cls.return_value
        scanner.scan.return_value = [tmp_path / "a.py", tmp_path / "b.py"]
        dispatcher = mock_pipeline.dispatcher_cls.return_value
        dispatcher.parse.side_effect = [RuntimeError("bad parse"), _make_file_report()]

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0
        assert dispatcher.parse.call_count == 2


class TestCreateCIAdapter:
    """Tests for ``AnalyseCommand._create_ci_adapter``."""

    def test_ci_unknown_raises(self) -> None:
        """Unknown adapter name raises ``ValueError``."""
        from dev_stats.cli.analyse_command import AnalyseCommand

        with pytest.raises(ValueError, match="Unknown CI adapter"):
            AnalyseCommand._create_ci_adapter(
                name="bogus",
                report=MagicMock(),
                config=MagicMock(),
            )


class TestGetDiffFiles:
    """Tests for ``AnalyseCommand._get_diff_files``."""

    def test_get_diff_files(self, tmp_path: Path) -> None:
        """Returns set of changed file paths from ``git diff``."""
        from dev_stats.cli.analyse_command import AnalyseCommand

        mock_result = MagicMock()
        mock_result.stdout = "src/foo.py\nsrc/bar.py\n"
        with patch(f"{_MODULE}.subprocess.run", return_value=mock_result) as mock_run:
            files = AnalyseCommand._get_diff_files(tmp_path, "main")
        assert files == {"src/foo.py", "src/bar.py"}
        mock_run.assert_called_once()
