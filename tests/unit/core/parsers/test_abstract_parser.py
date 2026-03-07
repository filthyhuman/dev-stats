"""Unit tests for AbstractParser and its utility functions."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

from dev_stats.core.parsers.abstract_parser import (
    AbstractParser,
    count_loc,
    count_todos,
    detect_encoding,
)

if TYPE_CHECKING:
    from dev_stats.core.models import ClassReport, MethodReport


class TestCountLoc:
    """Tests for the count_loc utility."""

    def test_simple_python(self) -> None:
        """Counts code, comments, and blanks correctly."""
        source = "# comment\nx = 1\n\ny = 2\n"
        result = count_loc(source, ("#",))
        assert result.total == 4
        assert result.comment == 1
        assert result.blank == 1
        assert result.code == 2

    def test_empty_source(self) -> None:
        """Empty string has zero counts."""
        result = count_loc("", ("#",))
        assert result.total == 0
        assert result.code == 0

    def test_c_style_comments(self) -> None:
        """C-style // comments are counted with appropriate prefix."""
        source = "// comment\nint x = 1;\n"
        result = count_loc(source, ("//",))
        assert result.comment == 1
        assert result.code == 1


class TestCountTodos:
    """Tests for the count_todos utility."""

    def test_finds_todo(self) -> None:
        """Finds TODO markers."""
        assert count_todos("# TODO: fix this") == 1

    def test_finds_multiple(self) -> None:
        """Finds multiple marker types."""
        assert count_todos("# TODO fix\n# FIXME later\n# HACK around") == 3

    def test_no_todos(self) -> None:
        """Returns 0 when no markers present."""
        assert count_todos("clean code\nno issues\n") == 0


class TestDetectEncoding:
    """Tests for detect_encoding."""

    def test_utf8_file(self, tmp_path: Path) -> None:
        """UTF-8 file returns 'utf-8'."""
        f = tmp_path / "test.py"
        f.write_text("hello = 'world'\n", encoding="utf-8")
        assert detect_encoding(f) == "utf-8"

    def test_latin1_fallback(self, tmp_path: Path) -> None:
        """Non-UTF-8 file falls back to 'latin-1'."""
        f = tmp_path / "test.py"
        f.write_bytes(b"\xff\xfe latin-1 content\n")
        assert detect_encoding(f) == "latin-1"

    def test_missing_file_returns_utf8(self, tmp_path: Path) -> None:
        """Missing file falls back to 'utf-8'."""
        f = tmp_path / "nonexistent.py"
        assert detect_encoding(f) == "utf-8"


class ConcreteParser(AbstractParser):
    """Minimal concrete parser for testing AbstractParser."""

    @property
    def language_name(self) -> str:
        """Return test language name."""
        return "test"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return test extensions."""
        return (".test",)

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Return empty list."""
        return []

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Return empty list."""
        return []

    def _detect_imports(self, source: str) -> list[str]:
        """Return empty list."""
        return []


class TestAbstractParser:
    """Tests for AbstractParser base class methods."""

    def test_can_parse_matching_extension(self, tmp_path: Path) -> None:
        """can_parse returns True for matching extensions."""
        parser = ConcreteParser()
        assert parser.can_parse(tmp_path / "file.test") is True

    def test_can_parse_non_matching(self, tmp_path: Path) -> None:
        """can_parse returns False for non-matching extensions."""
        parser = ConcreteParser()
        assert parser.can_parse(tmp_path / "file.py") is False

    def test_language_alias(self) -> None:
        """Language property is an alias for language_name."""
        parser = ConcreteParser()
        assert parser.language == "test"

    def test_extensions_alias(self) -> None:
        """Extensions property is an alias for supported_extensions."""
        parser = ConcreteParser()
        assert parser.extensions == (".test",)

    def test_default_comment_prefixes(self) -> None:
        """Default comment_prefixes is ('#',)."""
        parser = ConcreteParser()
        assert parser.comment_prefixes == ("#",)

    def test_parse_unreadable_file(self, tmp_path: Path) -> None:
        """Parsing a file that raises OSError returns an empty report."""
        parser = ConcreteParser()
        f = tmp_path / "bad.test"
        f.write_text("content")
        with patch.object(Path, "read_text", side_effect=OSError("denied")):
            report = parser.parse(f, tmp_path)
        assert report.total_lines == 0
        assert report.language == "test"

    def test_parse_valid_file(self, tmp_path: Path) -> None:
        """Parsing a valid file returns correct LOC counts."""
        parser = ConcreteParser()
        f = tmp_path / "hello.test"
        f.write_text("# comment\ncode\n\n")
        report = parser.parse(f, tmp_path)
        assert report.total_lines == 3
        assert report.comment_lines == 1
        assert report.blank_lines == 1
        assert report.code_lines == 1
