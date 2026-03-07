"""Tests for dashboard template rendering edge cases."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from dev_stats.core.models import FileReport, LanguageSummary, RepoReport
from dev_stats.output.dashboard.dashboard_builder import DashboardBuilder


def _make_config() -> MagicMock:
    """Create a mock AnalysisConfig."""
    return MagicMock()


class TestDashboardRendering:
    """Tests for dashboard HTML rendering edge cases."""

    @staticmethod
    def _make_report(
        files: tuple[FileReport, ...] = (),
        languages: tuple[LanguageSummary, ...] = (),
    ) -> RepoReport:
        """Build a minimal RepoReport.

        Args:
            files: File reports to include.
            languages: Language summaries to include.

        Returns:
            A frozen ``RepoReport`` instance.
        """
        return RepoReport(
            root=Path("/tmp/test-repo"),
            files=files,
            languages=languages,
        )

    def test_empty_report_renders(self, tmp_path: Path) -> None:
        """Dashboard renders for empty report without error."""
        report = self._make_report()
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        assert paths
        html = paths[0].read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html

    def test_minimal_report_renders(self, tmp_path: Path) -> None:
        """Dashboard renders for report with one file."""
        fr = FileReport(
            path=Path("test.py"),
            language="python",
            total_lines=10,
            code_lines=8,
            blank_lines=1,
            comment_lines=1,
        )
        lang = LanguageSummary(
            language="python",
            file_count=1,
            total_lines=10,
            code_lines=8,
            blank_lines=1,
            comment_lines=1,
        )
        report = self._make_report(files=(fr,), languages=(lang,))
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        assert paths
        html = paths[0].read_text(encoding="utf-8")
        assert "python" in html.lower()

    def test_dashboard_contains_doctype(self, tmp_path: Path) -> None:
        """Dashboard HTML starts with DOCTYPE."""
        report = self._make_report()
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        html = paths[0].read_text(encoding="utf-8")
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_noscript_warning_present(self, tmp_path: Path) -> None:
        """Dashboard contains a noscript warning for non-JS browsers."""
        report = self._make_report()
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        html = paths[0].read_text(encoding="utf-8")
        assert "noscript-warning" in html
        assert "JavaScript is required" in html

    def test_aria_tablist_present(self, tmp_path: Path) -> None:
        """Sidebar nav has role=tablist for accessibility."""
        report = self._make_report()
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        html = paths[0].read_text(encoding="utf-8")
        assert 'role="tablist"' in html

    def test_aria_tab_roles_present(self, tmp_path: Path) -> None:
        """Sidebar links have role=tab attributes."""
        report = self._make_report()
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        html = paths[0].read_text(encoding="utf-8")
        assert 'role="tab"' in html
        assert 'aria-selected="true"' in html
        assert 'aria-selected="false"' in html

    def test_tabpanel_roles_present(self, tmp_path: Path) -> None:
        """Tab panel sections have role=tabpanel."""
        report = self._make_report()
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        html = paths[0].read_text(encoding="utf-8")
        assert 'role="tabpanel"' in html

    def test_focus_visible_styles_embedded(self, tmp_path: Path) -> None:
        """Focus-visible CSS rules are embedded in the dashboard."""
        report = self._make_report()
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        html = paths[0].read_text(encoding="utf-8")
        assert "focus-visible" in html

    def test_table_scroll_class_in_css(self, tmp_path: Path) -> None:
        """Table scroll wrapper CSS class is embedded."""
        report = self._make_report()
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        html = paths[0].read_text(encoding="utf-8")
        assert ".table-scroll" in html

    def test_375_breakpoint_in_css(self, tmp_path: Path) -> None:
        """375px responsive breakpoint is embedded."""
        report = self._make_report()
        config = _make_config()
        builder = DashboardBuilder(report=report, config=config)
        paths = builder.export(tmp_path)
        html = paths[0].read_text(encoding="utf-8")
        assert "max-width: 375px" in html
