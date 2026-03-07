"""End-to-end integration tests for all export formats.

Exercises the full CLI pipeline via ``typer.testing.CliRunner``, verifying
that each ``--format`` option produces the expected output files on disk.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from typer.testing import CliRunner

if TYPE_CHECKING:
    from pathlib import Path

from dev_stats.cli.app import app

runner = CliRunner()


class TestJsonExport:
    """Verify that ``--format json`` produces valid JSON output."""

    def test_json_export_creates_file(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """--format json creates a JSON file."""
        out = tmp_path / "out"
        result = runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "json",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        json_files = list(out.glob("*.json"))
        assert len(json_files) >= 1

    def test_json_export_is_valid(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """JSON export is parseable."""
        out = tmp_path / "out"
        runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "json",
                "--output",
                str(out),
            ],
        )
        json_files = list(out.glob("*.json"))
        for jf in json_files:
            data = json.loads(jf.read_text())
            assert isinstance(data, (dict, list))


class TestCsvExport:
    """Verify that ``--format csv`` produces valid CSV output."""

    def test_csv_export_creates_file(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """--format csv creates a CSV file."""
        out = tmp_path / "out"
        result = runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "csv",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        csv_files = list(out.glob("*.csv"))
        assert len(csv_files) >= 1

    def test_csv_has_header(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """CSV file has a header row."""
        out = tmp_path / "out"
        runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "csv",
                "--output",
                str(out),
            ],
        )
        csv_files = list(out.glob("*.csv"))
        content = csv_files[0].read_text()
        assert len(content.strip().splitlines()) >= 2  # header + at least 1 data row


class TestXmlExport:
    """Verify that ``--format xml`` produces well-formed XML output."""

    def test_xml_export_creates_file(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """--format xml creates an XML file."""
        out = tmp_path / "out"
        result = runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "xml",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        xml_files = list(out.glob("*.xml"))
        assert len(xml_files) >= 1

    def test_xml_is_well_formed(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """XML export is well-formed."""
        out = tmp_path / "out"
        runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "xml",
                "--output",
                str(out),
            ],
        )
        xml_files = list(out.glob("*.xml"))
        for xf in xml_files:
            ET.parse(xf)  # raises if malformed


class TestBadgeExport:
    """Verify that ``--format badges`` produces SVG badge files."""

    def test_badges_creates_svg(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """--format badges creates SVG files."""
        out = tmp_path / "out"
        result = runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "badges",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        svg_files = list(out.rglob("*.svg"))
        assert len(svg_files) >= 1

    def test_badges_contain_svg_tag(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """SVG files contain <svg> tag."""
        out = tmp_path / "out"
        runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "badges",
                "--output",
                str(out),
            ],
        )
        for svg in out.rglob("*.svg"):
            assert "<svg" in svg.read_text()


class TestDashboardExport:
    """Verify that ``--format dashboard`` produces a self-contained HTML file."""

    def test_dashboard_creates_html(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """--format dashboard creates an HTML file."""
        out = tmp_path / "out"
        result = runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "dashboard",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        html_files = list(out.rglob("*.html"))
        assert len(html_files) >= 1

    def test_dashboard_is_self_contained(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """Dashboard HTML contains DOCTYPE."""
        out = tmp_path / "out"
        runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "dashboard",
                "--output",
                str(out),
            ],
        )
        html_files = list(out.rglob("*.html"))
        content = html_files[0].read_text()
        assert "<!DOCTYPE html>" in content or "<!doctype html>" in content


class TestAllExport:
    """Verify that ``--format all`` produces every export type at once."""

    def test_format_all_creates_everything(self, rich_fake_repo: Path, tmp_path: Path) -> None:
        """--format all creates JSON, CSV, XML, SVG, and HTML."""
        out = tmp_path / "out"
        result = runner.invoke(
            app,
            [
                "analyse",
                str(rich_fake_repo),
                "--format",
                "all",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0
        assert list(out.rglob("*.json"))
        assert list(out.rglob("*.csv"))
        assert list(out.rglob("*.xml"))
        assert list(out.rglob("*.svg"))
        assert list(out.rglob("*.html"))
