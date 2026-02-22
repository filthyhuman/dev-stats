"""Unit tests for BadgeGenerator."""

from __future__ import annotations

from pathlib import Path

from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.models import (
    CoverageReport,
    FileReport,
    LanguageSummary,
    MethodReport,
    RepoReport,
)
from dev_stats.output.exporters.badge_generator import BadgeGenerator


def _make_report(
    tmp_path: Path,
    *,
    with_coverage: bool = False,
) -> RepoReport:
    """Build a minimal RepoReport for badge testing."""
    func = MethodReport(
        name="compute",
        line=1,
        end_line=10,
        lines=10,
        cyclomatic_complexity=3,
    )
    file_rpt = FileReport(
        path=Path("src/main.py"),
        language="python",
        total_lines=100,
        code_lines=80,
        blank_lines=10,
        comment_lines=10,
        functions=(func,),
    )
    coverage = CoverageReport(overall_ratio=0.85) if with_coverage else None
    return RepoReport(
        root=tmp_path,
        files=(file_rpt,),
        languages=(
            LanguageSummary(
                language="python",
                file_count=1,
                total_lines=100,
                code_lines=80,
                blank_lines=10,
                comment_lines=10,
            ),
        ),
        coverage=coverage,
    )


class TestBadgeGenerator:
    """Tests for BadgeGenerator."""

    def test_export_creates_at_least_four_badges(self, tmp_path: Path) -> None:
        """Without coverage, at least 4 badges are generated."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        gen = BadgeGenerator(report=report, config=config)

        out_dir = tmp_path / "badges"
        created = gen.export(out_dir)

        assert len(created) >= 4
        names = {p.name for p in created}
        assert "badge-lines.svg" in names
        assert "badge-files.svg" in names
        assert "badge-languages.svg" in names
        assert "badge-complexity.svg" in names

    def test_export_with_coverage_creates_five_badges(self, tmp_path: Path) -> None:
        """With coverage data, 5 badges are generated."""
        report = _make_report(tmp_path, with_coverage=True)
        config = AnalysisConfig.load(repo_path=tmp_path)
        gen = BadgeGenerator(report=report, config=config)

        out_dir = tmp_path / "badges"
        created = gen.export(out_dir)

        assert len(created) == 5
        names = {p.name for p in created}
        assert "badge-coverage.svg" in names

    def test_badges_are_valid_svg(self, tmp_path: Path) -> None:
        """Generated badges contain valid SVG markup."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        gen = BadgeGenerator(report=report, config=config)

        out_dir = tmp_path / "badges"
        created = gen.export(out_dir)

        for path in created:
            content = path.read_text()
            assert content.strip().startswith("<svg")
            assert "</svg>" in content

    def test_lines_badge_contains_count(self, tmp_path: Path) -> None:
        """Lines badge displays the line count."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        gen = BadgeGenerator(report=report, config=config)

        out_dir = tmp_path / "badges"
        gen.export(out_dir)

        content = (out_dir / "badge-lines.svg").read_text()
        assert "80" in content  # 80 code lines

    def test_files_badge_contains_count(self, tmp_path: Path) -> None:
        """Files badge displays the file count."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        gen = BadgeGenerator(report=report, config=config)

        out_dir = tmp_path / "badges"
        gen.export(out_dir)

        content = (out_dir / "badge-files.svg").read_text()
        assert "1" in content

    def test_complexity_badge_colour_green(self, tmp_path: Path) -> None:
        """Low complexity gets green colour."""
        report = _make_report(tmp_path)
        config = AnalysisConfig.load(repo_path=tmp_path)
        gen = BadgeGenerator(report=report, config=config)

        out_dir = tmp_path / "badges"
        gen.export(out_dir)

        content = (out_dir / "badge-complexity.svg").read_text()
        # CC=3 -> green (#4c1)
        assert "#4c1" in content


class TestBadgeFormatNumber:
    """Tests for _format_number static method."""

    def test_small_number(self) -> None:
        """Numbers below 1000 are returned as-is."""
        assert BadgeGenerator._format_number(42) == "42"

    def test_thousands(self) -> None:
        """Numbers in thousands get K suffix."""
        assert BadgeGenerator._format_number(1500) == "1.5K"

    def test_millions(self) -> None:
        """Numbers in millions get M suffix."""
        assert BadgeGenerator._format_number(2_500_000) == "2.5M"


class TestBadgeCcColour:
    """Tests for _cc_colour static method."""

    def test_low(self) -> None:
        """Low complexity is green."""
        assert BadgeGenerator._cc_colour(3.0) == "#4c1"

    def test_medium(self) -> None:
        """Medium complexity is yellow-green."""
        assert BadgeGenerator._cc_colour(7.0) == "#a4a61d"

    def test_high(self) -> None:
        """High complexity is orange."""
        assert BadgeGenerator._cc_colour(15.0) == "#dfb317"

    def test_very_high(self) -> None:
        """Very high complexity is red."""
        assert BadgeGenerator._cc_colour(25.0) == "#e05d44"


class TestBadgeCoverageColour:
    """Tests for _coverage_colour static method."""

    def test_excellent(self) -> None:
        """90%+ coverage is green."""
        assert BadgeGenerator._coverage_colour(95.0) == "#4c1"

    def test_good(self) -> None:
        """75-90% coverage is yellow-green."""
        assert BadgeGenerator._coverage_colour(80.0) == "#a4a61d"

    def test_fair(self) -> None:
        """50-75% coverage is orange."""
        assert BadgeGenerator._coverage_colour(60.0) == "#dfb317"

    def test_poor(self) -> None:
        """Below 50% coverage is red."""
        assert BadgeGenerator._coverage_colour(30.0) == "#e05d44"
