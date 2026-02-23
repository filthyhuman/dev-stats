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

# Size thresholds in bytes.
_WARN_SIZE_BYTES = 30 * 1024 * 1024  # 30 MB
_ERROR_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class DashboardSizeError(Exception):
    """Raised when the generated dashboard exceeds the maximum allowed size.

    Attributes:
        size_bytes: Actual size in bytes.
        limit_bytes: Maximum allowed size in bytes.
    """

    def __init__(self, size_bytes: int, limit_bytes: int) -> None:
        """Initialise the error.

        Args:
            size_bytes: Actual size of the generated HTML.
            limit_bytes: Maximum allowed size.
        """
        self.size_bytes = size_bytes
        self.limit_bytes = limit_bytes
        size_mb = size_bytes / (1024 * 1024)
        limit_mb = limit_bytes / (1024 * 1024)
        super().__init__(
            f"Dashboard HTML is {size_mb:.1f} MB, exceeding the "
            f"{limit_mb:.0f} MB limit. Reduce the data by filtering "
            f"commits (--max-commits), files (--exclude), or disabling "
            f"optional analyses (--no-blame, --no-churn)."
        )


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

        Raises:
            DashboardSizeError: If the generated HTML exceeds 50 MB.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        context = self._build_context()
        html = self._render_template(context)

        self._check_size(html)

        out_path = output_dir / "dashboard.html"
        out_path.write_text(html, encoding="utf-8")
        logger.info("Dashboard written to %s", out_path)
        return [out_path]

    @staticmethod
    def _check_size(html: str) -> None:
        """Check the generated HTML size against thresholds.

        Args:
            html: The rendered HTML string.

        Raises:
            DashboardSizeError: If size exceeds the error threshold.
        """
        size_bytes = len(html.encode("utf-8"))

        if size_bytes > _ERROR_SIZE_BYTES:
            raise DashboardSizeError(size_bytes, _ERROR_SIZE_BYTES)

        if size_bytes > _WARN_SIZE_BYTES:
            size_mb = size_bytes / (1024 * 1024)
            logger.warning(
                "Dashboard HTML is %.1f MB (threshold: %.0f MB). "
                "Consider reducing data with --max-commits, --exclude, "
                "or --no-blame.",
                size_mb,
                _WARN_SIZE_BYTES / (1024 * 1024),
            )

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
