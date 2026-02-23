"""Unit tests for DashboardBuilder."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from dev_stats.core.models import (
    FileReport,
    LanguageSummary,
    RepoReport,
)
from dev_stats.output.dashboard.dashboard_builder import DashboardBuilder


def _make_report(root: Path | None = None) -> RepoReport:
    """Create a minimal RepoReport for testing."""
    return RepoReport(
        root=root or Path("/tmp/repo"),
        files=(
            FileReport(
                path=Path("main.py"),
                language="python",
                total_lines=100,
                code_lines=80,
                blank_lines=10,
                comment_lines=10,
            ),
            FileReport(
                path=Path("utils.py"),
                language="python",
                total_lines=50,
                code_lines=40,
                blank_lines=5,
                comment_lines=5,
            ),
        ),
        languages=(
            LanguageSummary(
                language="python",
                file_count=2,
                total_lines=150,
                code_lines=120,
                blank_lines=15,
                comment_lines=15,
            ),
        ),
    )


def _make_config() -> MagicMock:
    """Create a mock AnalysisConfig."""
    return MagicMock()


class TestDashboardBuilderExport:
    """Tests for the export method."""

    def test_export_creates_html_file(self, tmp_path: Path) -> None:
        """export() creates a dashboard.html file."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        result = builder.export(tmp_path)

        assert len(result) == 1
        assert result[0] == tmp_path / "dashboard.html"
        assert result[0].exists()

    def test_export_creates_output_dir(self, tmp_path: Path) -> None:
        """export() creates the output directory if it does not exist."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)
        out_dir = tmp_path / "nested" / "output"

        result = builder.export(out_dir)

        assert result[0].exists()
        assert out_dir.is_dir()

    def test_export_html_is_utf8(self, tmp_path: Path) -> None:
        """Generated HTML is valid UTF-8."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert len(html) > 0

    def test_export_html_contains_doctype(self, tmp_path: Path) -> None:
        """Generated HTML starts with DOCTYPE."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert html.strip().startswith("<!DOCTYPE html>")


class TestDashboardBuilderTabs:
    """Tests that all 10 tab IDs are present in the output."""

    _TAB_IDS = (
        "tab-overview",
        "tab-languages",
        "tab-files",
        "tab-classes",
        "tab-methods",
        "tab-hotspots",
        "tab-dependencies",
        "tab-branches",
        "tab-git",
        "tab-quality",
    )

    def test_all_ten_tab_ids_present(self, tmp_path: Path) -> None:
        """All 10 tab panel IDs appear in the generated HTML."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        for tab_id in self._TAB_IDS:
            assert f'id="{tab_id}"' in html, f"Missing tab: {tab_id}"

    def test_sidebar_links_match_tabs(self, tmp_path: Path) -> None:
        """Sidebar links reference all 10 tab IDs."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        for tab_id in self._TAB_IDS:
            assert f'data-tab="{tab_id}"' in html, f"Missing sidebar link: {tab_id}"

    def test_overview_is_default_active(self, tmp_path: Path) -> None:
        """Overview tab panel is active by default."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert 'id="tab-overview" class="tab-panel tab-panel--active"' in html


class TestDashboardBuilderDataChunks:
    """Tests for embedded data chunks."""

    def test_data_chunks_embedded(self, tmp_path: Path) -> None:
        """Compressed data chunks are embedded as script tags."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert 'type="application/x-devstats-data"' in html
        assert 'data-chunk="meta"' in html
        assert 'data-chunk="files"' in html
        assert 'data-chunk="languages"' in html

    def test_optional_chunks_absent_for_minimal(self, tmp_path: Path) -> None:
        """Optional chunks are not present for a minimal report."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert 'data-chunk="commits"' not in html
        assert 'data-chunk="branches"' not in html
        assert 'data-chunk="contributors"' not in html


class TestDashboardBuilderContent:
    """Tests for rendered content correctness."""

    def test_repo_name_in_html(self, tmp_path: Path) -> None:
        """Repository name appears in the HTML."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert "repo" in html

    def test_summary_stats_in_html(self, tmp_path: Path) -> None:
        """Summary statistics appear in the HTML."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        # 2 files, 150 total lines, 120 code lines
        assert ">2<" in html
        assert ">150<" in html
        assert ">120<" in html

    def test_language_table_populated(self, tmp_path: Path) -> None:
        """Language table has rows from the report."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert "python" in html

    def test_inline_css_embedded(self, tmp_path: Path) -> None:
        """Inline CSS is embedded in a style tag."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert "<style>" in html
        assert "--color-bg" in html

    def test_inline_js_embedded(self, tmp_path: Path) -> None:
        """Inline JavaScript is embedded in a script tag."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert "TableSorter" in html
        assert "LazyRenderer" in html

    def test_footer_present(self, tmp_path: Path) -> None:
        """Footer with dev-stats branding is present."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        builder.export(tmp_path)
        html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")

        assert "dev-stats" in html


class TestDashboardBuilderContext:
    """Tests for _build_context internals."""

    def test_context_has_required_keys(self) -> None:
        """Context dict contains all required template keys."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        context = builder._build_context()

        required_keys = {
            "repo_name",
            "repo_path",
            "inline_css",
            "inline_app_js",
            "inline_chart_js",
            "data_chunks",
            "total_files",
            "total_lines",
            "code_lines",
            "total_classes",
            "total_functions",
            "total_methods",
            "commit_count",
            "branch_count",
            "contributor_count",
            "pattern_count",
            "language_count",
            "languages",
            "has_commits",
            "has_branches",
            "has_contributors",
            "has_patterns",
            "has_coverage",
            "has_duplication",
            "has_coupling",
            "has_churn",
        }
        for key in required_keys:
            assert key in context, f"Missing context key: {key}"

    def test_context_summary_stats(self) -> None:
        """Context summary statistics match the report."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        context = builder._build_context()

        assert context["total_files"] == 2
        assert context["total_lines"] == 150
        assert context["code_lines"] == 120
        assert context["language_count"] == 1

    def test_context_flags_false_for_minimal(self) -> None:
        """Boolean flags are False for a minimal report."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        context = builder._build_context()

        assert context["has_commits"] is False
        assert context["has_branches"] is False
        assert context["has_contributors"] is False
        assert context["has_patterns"] is False
        assert context["has_coverage"] is False
        assert context["has_duplication"] is False
        assert context["has_coupling"] is False
        assert context["has_churn"] is False

    def test_context_languages_list(self) -> None:
        """Languages list matches the report."""
        report = _make_report()
        config = _make_config()
        builder = DashboardBuilder(report, config)

        context = builder._build_context()
        langs = context["languages"]

        assert isinstance(langs, list)
        assert len(langs) == 1
        assert langs[0]["name"] == "python"
        assert langs[0]["file_count"] == 2
