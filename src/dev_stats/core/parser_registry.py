"""Registry mapping file extensions to language parsers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dev_stats.core.parsers.cpp_parser import CppParser
from dev_stats.core.parsers.csharp_parser import CSharpParser
from dev_stats.core.parsers.generic_parser import GenericParser
from dev_stats.core.parsers.go_parser import GoParser
from dev_stats.core.parsers.java_parser import JavaParser
from dev_stats.core.parsers.javascript_parser import JavaScriptParser
from dev_stats.core.parsers.objectivec_parser import ObjectiveCParser
from dev_stats.core.parsers.python_parser import PythonParser
from dev_stats.core.parsers.typescript_parser import TypeScriptParser

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.core.parsers.abstract_parser import AbstractParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """Maintains a mapping from file extensions to parser instances.

    Use :meth:`register` to add parsers and :meth:`get` or
    :meth:`get_or_default` to retrieve them.
    """

    def __init__(self) -> None:
        """Initialise a registry with built-in parsers and a generic fallback."""
        self._registry: dict[str, AbstractParser] = {}
        self._generic = GenericParser()

    def register(self, parser: AbstractParser) -> None:
        """Register a parser for all its declared extensions.

        Args:
            parser: Parser instance to register.
        """
        for ext in parser.extensions:
            self._registry[ext] = parser

    def get(self, extension: str) -> AbstractParser:
        """Return the parser registered for *extension*.

        Args:
            extension: File extension including the dot (e.g. ``'.py'``).

        Returns:
            The registered parser.

        Raises:
            KeyError: If no parser is registered for this extension.
        """
        return self._registry[extension]

    def get_or_default(self, path: Path) -> AbstractParser:
        """Return the parser for *path*'s extension, or the generic fallback.

        Args:
            path: File path whose suffix determines the parser.

        Returns:
            The matching parser, or :class:`GenericParser` if none is registered.
        """
        return self._registry.get(path.suffix, self._generic)

    def supported_languages(self) -> dict[str, list[str]]:
        """Return a mapping of language names to their registered extensions.

        Returns:
            ``{language: [ext1, ext2, ...]}`` for all registered parsers.
        """
        languages: dict[str, list[str]] = {}
        for ext, parser in self._registry.items():
            languages.setdefault(parser.language, []).append(ext)
        return languages


def create_default_registry(*, use_tree_sitter: bool = True) -> ParserRegistry:
    """Create a :class:`ParserRegistry` with all built-in parsers registered.

    When *use_tree_sitter* is ``True`` (the default) and ``tree-sitter-languages``
    is installed, tree-sitter-backed parsers are preferred for Java and JavaScript.
    Regex-based parsers are used as a fallback.

    Args:
        use_tree_sitter: Whether to prefer tree-sitter parsers when available.

    Returns:
        A registry with all language parsers.
    """
    registry = ParserRegistry()
    registry.register(PythonParser())

    # Java: prefer tree-sitter, fall back to regex
    if use_tree_sitter:
        try:
            from dev_stats.core.parsers.java_ts_parser import JavaTreeSitterParser
            from dev_stats.core.parsers.tree_sitter_base import _tree_sitter_available

            if _tree_sitter_available():
                registry.register(JavaTreeSitterParser())
                logger.debug("Using tree-sitter Java parser")
            else:
                registry.register(JavaParser())
        except ImportError:
            registry.register(JavaParser())
    else:
        registry.register(JavaParser())

    # JavaScript: prefer tree-sitter, fall back to regex
    if use_tree_sitter:
        try:
            from dev_stats.core.parsers.javascript_ts_parser import JavaScriptTreeSitterParser
            from dev_stats.core.parsers.tree_sitter_base import _tree_sitter_available

            if _tree_sitter_available():
                registry.register(JavaScriptTreeSitterParser())
                logger.debug("Using tree-sitter JavaScript parser")
            else:
                registry.register(JavaScriptParser())
        except ImportError:
            registry.register(JavaScriptParser())
    else:
        registry.register(JavaScriptParser())

    registry.register(TypeScriptParser())
    registry.register(CppParser())
    registry.register(CSharpParser())
    registry.register(GoParser())
    registry.register(ObjectiveCParser())
    return registry
