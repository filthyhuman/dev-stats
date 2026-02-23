"""Dashboard builder assembling a self-contained HTML report."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import jinja2

from dev_stats.output.dashboard.asset_embedder import AssetEmbedder
from dev_stats.output.dashboard.data_compressor import DataCompressor
from dev_stats.output.exporters.abstract_exporter import AbstractExporter

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.config.analysis_config import AnalysisConfig
    from dev_stats.core.models import RepoReport

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = __file__.replace("dashboard_builder.py", "templates")


class DashboardBuilder(AbstractExporter):
    """Builds a fully self-contained single-file HTML dashboard.

    Uses Jinja2 to render the dashboard template with embedded CSS, JS,
    Chart.js, and compressed data chunks. The output HTML file opens in
    any browser with no server or internet required.
    """

    def __init__(self, report: RepoReport, config: AnalysisConfig) -> None:
        """Initialise the dashboard builder.

        Args:
            report: The analysis report to render.
            config: Analysis configuration.
        """
        super().__init__(report, config)
        self._embedder = AssetEmbedder()
        self._compressor = DataCompressor()

    def export(self, output_dir: Path) -> list[Path]:
        """Build the dashboard HTML and write to *output_dir*.

        Args:
            output_dir: Directory to write the HTML file into.

        Returns:
            Single-element list with the path to the generated HTML.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        context = self._build_context()
        html = self._render_template(context)

        out_path = output_dir / "dashboard.html"
        out_path.write_text(html, encoding="utf-8")
        logger.info("Dashboard written to %s", out_path)
        return [out_path]

    def _build_context(self) -> dict[str, object]:
        """Build the full Jinja2 template context.

        Returns:
            Dictionary with all template variables.
        """
        report = self._report
        assets = self._embedder.embed_all()
        data_chunks = self._compressor.compress_report(report)

        # Summary statistics for hero cards
        total_files = len(report.files)
        total_lines = sum(f.total_lines for f in report.files)
        code_lines = sum(f.code_lines for f in report.files)
        total_classes = sum(f.num_classes for f in report.files)
        total_functions = sum(f.num_functions for f in report.files)
        total_methods = sum(len(c.methods) for f in report.files for c in f.classes)

        # Language breakdown
        languages = [
            {
                "name": lang.language,
                "file_count": lang.file_count,
                "total_lines": lang.total_lines,
                "code_lines": lang.code_lines,
            }
            for lang in report.languages
        ]

        # Commit stats
        commit_count = len(report.commits) if report.commits else 0
        branch_count = report.branches_report.total_branches if report.branches_report else 0
        contributor_count = len(report.contributors) if report.contributors else 0
        pattern_count = len(report.patterns) if report.patterns else 0

        return {
            "repo_name": report.root.name,
            "repo_path": str(report.root),
            # Assets
            "chart_js": assets.get("chart_js_uri", ""),
            "css": assets.get("css_uri", ""),
            "app_js": assets.get("app_js_uri", ""),
            # Inline assets (for direct embedding)
            "inline_css": self._embedder.inline_css(self._embedder._assets_dir / "styles.css"),
            "inline_app_js": self._embedder.inline_js(self._embedder._assets_dir / "app.js"),
            "inline_chart_js": self._embedder.inline_js(
                self._embedder._assets_dir / "chart.min.js"
            ),
            # Data chunks
            "data_chunks": data_chunks,
            # Summary stats
            "total_files": total_files,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "total_methods": total_methods,
            "commit_count": commit_count,
            "branch_count": branch_count,
            "contributor_count": contributor_count,
            "pattern_count": pattern_count,
            "language_count": len(report.languages),
            "languages": languages,
            # Flags for conditional sections
            "has_commits": report.commits is not None,
            "has_branches": report.branches_report is not None,
            "has_contributors": report.contributors is not None,
            "has_patterns": report.patterns is not None,
            "has_coverage": report.coverage is not None,
            "has_duplication": report.duplication is not None,
            "has_coupling": report.coupling is not None,
            "has_churn": report.file_churn is not None,
        }

    @staticmethod
    def _render_template(context: dict[str, object]) -> str:
        """Render the Jinja2 dashboard template.

        Args:
            context: Template variables.

        Returns:
            Rendered HTML string.
        """
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(_TEMPLATES_DIR),
            autoescape=jinja2.select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template("dashboard.html.jinja2")
        return template.render(**context)
