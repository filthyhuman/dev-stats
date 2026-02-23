"""Unit tests for GenericParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.core.parsers.generic_parser import GenericParser

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


def _parse_source(source: str, filename: str = "test.sh") -> FileReport:
    """Write source to a temp file and parse it.

    Args:
        source: File contents.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    tmp = Path("/tmp/_dev_stats_test_generic")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = GenericParser()
    return parser.parse(test_file, tmp)


class TestGenericParserLOC:
    """Tests for line counting."""

    def test_total_lines(self) -> None:
        """GenericParser counts total lines."""
        report = _parse_source("line1\nline2\nline3\n")
        assert report.total_lines == 3

    def test_blank_lines(self) -> None:
        """GenericParser counts blank lines."""
        report = _parse_source("line1\n\n\nline2\n")
        assert report.blank_lines == 2

    def test_comment_lines_hash(self) -> None:
        """GenericParser counts # comment lines for shell scripts."""
        report = _parse_source("#!/bin/bash\n# comment\necho hello\n")
        assert report.comment_lines == 2

    def test_code_lines(self) -> None:
        """GenericParser computes code = total - blank - comment."""
        report = _parse_source("# comment\n\ncode\n")
        assert report.code_lines == 1


class TestGenericParserLanguageDetection:
    """Tests for language detection from extension."""

    def test_shell_detected(self) -> None:
        """Shell scripts are detected from .sh extension."""
        report = _parse_source("echo hi\n", "test.sh")
        assert report.language == "shell"

    def test_sql_detected(self) -> None:
        """SQL files are detected from .sql extension."""
        report = _parse_source("SELECT 1;\n", "test.sql")
        assert report.language == "sql"

    def test_unknown_extension_is_generic(self) -> None:
        """Unknown extensions fall back to generic."""
        report = _parse_source("data\n", "test.xyz")
        assert report.language == "generic"

    def test_makefile_detected(self) -> None:
        """Makefiles are detected by name."""
        report = _parse_source("all:\n\techo build\n", "Makefile")
        assert report.language == "makefile"

    def test_dockerfile_detected(self) -> None:
        """Dockerfiles are detected by name."""
        report = _parse_source("FROM python:3.12\n", "Dockerfile")
        assert report.language == "dockerfile"


class TestGenericParserProperties:
    """Tests for parser properties."""

    def test_language_name(self) -> None:
        """Language name is 'generic'."""
        parser = GenericParser()
        assert parser.language_name == "generic"

    def test_supported_extensions(self) -> None:
        """Supported extensions is empty (fallback parser)."""
        parser = GenericParser()
        assert parser.supported_extensions == ()


class TestGenericParserPrivateMethods:
    """Tests for private extract methods (no-op implementations)."""

    def test_extract_classes_empty(self) -> None:
        """Returns empty list (no structural analysis)."""
        parser = GenericParser()
        assert parser._extract_classes("", Path("x")) == []

    def test_extract_functions_empty(self) -> None:
        """Returns empty list (no structural analysis)."""
        parser = GenericParser()
        assert parser._extract_functions("", Path("x")) == []

    def test_detect_imports_empty(self) -> None:
        """Returns empty list (no import detection)."""
        parser = GenericParser()
        assert parser._detect_imports("") == []


class TestGenericParserCanParse:
    """Tests for can_parse behaviour."""

    def test_can_parse_always_true(self) -> None:
        """GenericParser.can_parse returns True for any path."""
        parser = GenericParser()
        assert parser.can_parse(Path("anything.xyz")) is True
        assert parser.can_parse(Path("no_extension")) is True
