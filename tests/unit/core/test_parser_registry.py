"""Unit tests for ParserRegistry."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from dev_stats.core.parser_registry import ParserRegistry
from dev_stats.core.parsers.abstract_parser import AbstractParser
from dev_stats.core.parsers.generic_parser import GenericParser


def _make_mock_parser(language: str, extensions: tuple[str, ...]) -> AbstractParser:
    """Create a mock parser with the given language and extensions.

    Args:
        language: Language name.
        extensions: File extensions.

    Returns:
        A mock ``AbstractParser``.
    """
    mock = MagicMock(spec=AbstractParser)
    type(mock).language = property(lambda self: language)
    type(mock).extensions = property(lambda self: extensions)
    return mock


class TestRegisterAndGet:
    """Tests for registering and retrieving parsers."""

    def test_register_and_get(self) -> None:
        """A registered parser is retrievable by extension."""
        registry = ParserRegistry()
        parser = _make_mock_parser("python", (".py", ".pyi"))
        registry.register(parser)

        assert registry.get(".py") is parser
        assert registry.get(".pyi") is parser

    def test_get_unknown_raises(self) -> None:
        """Getting an unregistered extension raises KeyError."""
        registry = ParserRegistry()
        try:
            registry.get(".xyz")
        except KeyError:
            pass
        else:
            msg = "Expected KeyError"
            raise AssertionError(msg)


class TestGetOrDefault:
    """Tests for get_or_default fallback behaviour."""

    def test_known_extension(self) -> None:
        """get_or_default returns the registered parser for known extensions."""
        registry = ParserRegistry()
        parser = _make_mock_parser("python", (".py",))
        registry.register(parser)

        result = registry.get_or_default(Path("foo.py"))
        assert result is parser

    def test_unknown_extension_returns_generic(self) -> None:
        """get_or_default returns GenericParser for unknown extensions."""
        registry = ParserRegistry()
        result = registry.get_or_default(Path("foo.xyz"))
        assert isinstance(result, GenericParser)

    def test_no_extension_returns_generic(self) -> None:
        """get_or_default returns GenericParser for files without extensions."""
        registry = ParserRegistry()
        result = registry.get_or_default(Path("Makefile"))
        assert isinstance(result, GenericParser)


class TestSupportedLanguages:
    """Tests for supported_languages reporting."""

    def test_format(self) -> None:
        """supported_languages returns {language: [extensions]}."""
        registry = ParserRegistry()
        parser = _make_mock_parser("python", (".py", ".pyi"))
        registry.register(parser)

        langs = registry.supported_languages()
        assert "python" in langs
        assert ".py" in langs["python"]
        assert ".pyi" in langs["python"]

    def test_empty_registry(self) -> None:
        """Empty registry returns empty dict."""
        registry = ParserRegistry()
        assert registry.supported_languages() == {}


class TestCreateDefaultRegistry:
    """Tests for the create_default_registry factory."""

    def test_default_includes_all_languages(self) -> None:
        """Default registry includes all supported languages."""
        from dev_stats.core.parser_registry import create_default_registry

        registry = create_default_registry()
        langs = registry.supported_languages()
        assert "python" in langs
        assert "java" in langs
        assert "javascript" in langs
        assert "typescript" in langs
        assert "cpp" in langs
        assert "csharp" in langs
        assert "go" in langs

    def test_no_tree_sitter_flag(self) -> None:
        """Passing use_tree_sitter=False forces regex parsers."""
        from dev_stats.core.parser_registry import create_default_registry
        from dev_stats.core.parsers.java_parser import JavaParser
        from dev_stats.core.parsers.javascript_parser import JavaScriptParser

        registry = create_default_registry(use_tree_sitter=False)
        java_parser = registry.get(".java")
        js_parser = registry.get(".js")
        assert isinstance(java_parser, JavaParser)
        assert isinstance(js_parser, JavaScriptParser)

    def test_tree_sitter_preferred_when_available(self) -> None:
        """Tree-sitter parsers are used when available."""
        from dev_stats.core.parser_registry import create_default_registry
        from dev_stats.core.parsers.tree_sitter_base import _tree_sitter_available

        if not _tree_sitter_available():
            return

        from dev_stats.core.parsers.java_ts_parser import JavaTreeSitterParser
        from dev_stats.core.parsers.javascript_ts_parser import JavaScriptTreeSitterParser

        registry = create_default_registry(use_tree_sitter=True)
        assert isinstance(registry.get(".java"), JavaTreeSitterParser)
        assert isinstance(registry.get(".js"), JavaScriptTreeSitterParser)
