"""SVG badge generator producing shields-style status badges."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dev_stats.output.exporters.abstract_exporter import AbstractExporter

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.config.analysis_config import AnalysisConfig
    from dev_stats.core.models import RepoReport


# Shield badge SVG template.  Follows the shields.io flat-square style.
_BADGE_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{colour}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle"\
 font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_x}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_x}" y="14">{label}</text>
    <text x="{value_x}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{value_x}" y="14">{value}</text>
  </g>
</svg>
"""


class BadgeGenerator(AbstractExporter):
    """Generates SVG shield-style badges for key metrics.

    Produces one SVG file per metric:

    * ``badge-lines.svg`` — Total lines of code.
    * ``badge-files.svg`` — Total files analysed.
    * ``badge-languages.svg`` — Number of languages detected.
    * ``badge-complexity.svg`` — Average cyclomatic complexity.
    * ``badge-coverage.svg`` — Test coverage percentage (if available).
    """

    def __init__(
        self,
        report: RepoReport,
        config: AnalysisConfig,
    ) -> None:
        """Initialise the badge generator.

        Args:
            report: The analysis report to export.
            config: Analysis configuration.
        """
        super().__init__(report, config)

    def export(self, output_dir: Path) -> list[Path]:
        """Write SVG badge files to *output_dir*.

        Args:
            output_dir: Directory to write badges into.

        Returns:
            List of paths to the generated SVG files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []

        rpt = self._report

        # Lines badge
        total_lines = sum(f.code_lines for f in rpt.files)
        created.append(
            self._write_badge(
                output_dir / "badge-lines.svg",
                "lines of code",
                self._format_number(total_lines),
                "#007ec6",
            )
        )

        # Files badge
        total_files = len(rpt.files)
        created.append(
            self._write_badge(
                output_dir / "badge-files.svg",
                "files",
                str(total_files),
                "#97ca00",
            )
        )

        # Languages badge
        num_languages = len(rpt.languages)
        created.append(
            self._write_badge(
                output_dir / "badge-languages.svg",
                "languages",
                str(num_languages),
                "#4c1",
            )
        )

        # Average complexity badge
        avg_cc = self._compute_average_cc()
        cc_colour = self._cc_colour(avg_cc)
        created.append(
            self._write_badge(
                output_dir / "badge-complexity.svg",
                "avg complexity",
                f"{avg_cc:.1f}",
                cc_colour,
            )
        )

        # Coverage badge (if available)
        if rpt.coverage is not None:
            pct = rpt.coverage.overall_ratio * 100
            cov_colour = self._coverage_colour(pct)
            created.append(
                self._write_badge(
                    output_dir / "badge-coverage.svg",
                    "coverage",
                    f"{pct:.0f}%",
                    cov_colour,
                )
            )

        return created

    def _compute_average_cc(self) -> float:
        """Compute the average cyclomatic complexity across all methods.

        Returns:
            Average CC, or 0.0 if no methods found.
        """
        total_cc = 0
        count = 0
        for f in self._report.files:
            for func in f.functions:
                total_cc += func.cyclomatic_complexity
                count += 1
            for cls in f.classes:
                for m in cls.methods:
                    total_cc += m.cyclomatic_complexity
                    count += 1
        return total_cc / count if count > 0 else 0.0

    @staticmethod
    def _write_badge(
        path: Path,
        label: str,
        value: str,
        colour: str,
    ) -> Path:
        """Render and write a single SVG badge.

        Args:
            path: Output file path.
            label: Left-side label text.
            value: Right-side value text.
            colour: Hex colour for the value background.

        Returns:
            The path written to.
        """
        # Approximate character widths (Verdana 11px ≈ 6.5px per char)
        char_width = 6.5
        padding = 10
        label_width = int(len(label) * char_width + padding * 2)
        value_width = int(len(value) * char_width + padding * 2)
        total_width = label_width + value_width

        svg = _BADGE_TEMPLATE.format(
            total_width=total_width,
            label_width=label_width,
            value_width=value_width,
            label_x=label_width / 2,
            value_x=label_width + value_width / 2,
            label=label,
            value=value,
            colour=colour,
        )
        path.write_text(svg)
        return path

    @staticmethod
    def _format_number(n: int) -> str:
        """Format a large number with K/M suffix.

        Args:
            n: The number to format.

        Returns:
            Human-readable string (e.g. ``"12.3K"``).
        """
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)

    @staticmethod
    def _cc_colour(avg_cc: float) -> str:
        """Choose badge colour based on average cyclomatic complexity.

        Args:
            avg_cc: Average cyclomatic complexity.

        Returns:
            Hex colour string.
        """
        if avg_cc <= 5:
            return "#4c1"
        if avg_cc <= 10:
            return "#a4a61d"
        if avg_cc <= 20:
            return "#dfb317"
        return "#e05d44"

    @staticmethod
    def _coverage_colour(pct: float) -> str:
        """Choose badge colour based on coverage percentage.

        Args:
            pct: Coverage percentage (0-100).

        Returns:
            Hex colour string.
        """
        if pct >= 90:
            return "#4c1"
        if pct >= 75:
            return "#a4a61d"
        if pct >= 50:
            return "#dfb317"
        return "#e05d44"
