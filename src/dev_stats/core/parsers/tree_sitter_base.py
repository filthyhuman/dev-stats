"""Base class for tree-sitter-backed language parsers."""

from __future__ import annotations

import logging
from typing import Any

from dev_stats.core.models import MethodReport, ParameterReport
from dev_stats.core.parsers.abstract_parser import AbstractParser

logger = logging.getLogger(__name__)

# Node types that increase cyclomatic complexity across most languages.
_CC_NODE_TYPES: frozenset[str] = frozenset(
    {
        "if_statement",
        "if_expression",
        "else_clause",
        "elif_clause",
        "for_statement",
        "for_in_statement",
        "enhanced_for_statement",
        "while_statement",
        "do_statement",
        "case_statement",
        "switch_expression",
        "catch_clause",
        "ternary_expression",
        "conditional_expression",
        "&&",
        "||",
    }
)

# Node types that contribute to cognitive complexity nesting.
_NESTING_TYPES: frozenset[str] = frozenset(
    {
        "if_statement",
        "for_statement",
        "for_in_statement",
        "enhanced_for_statement",
        "while_statement",
        "do_statement",
        "try_statement",
        "catch_clause",
        "switch_expression",
        "lambda_expression",
        "arrow_function",
    }
)


def _tree_sitter_available() -> bool:
    """Check whether tree-sitter-languages is importable.

    Returns:
        ``True`` if the package is available.
    """
    try:
        import tree_sitter_languages as _tsl  # noqa: F401

        return True
    except ImportError:
        return False


def _get_parser(language: str) -> Any:
    """Obtain a tree-sitter parser for *language*.

    Args:
        language: Grammar name (e.g. ``'java'``, ``'javascript'``).

    Returns:
        A ``tree_sitter.Parser`` configured for the language.

    Raises:
        ImportError: If tree-sitter-languages is not installed.
    """
    import warnings

    from tree_sitter_languages import get_parser

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        return get_parser(language)


class TreeSitterBase(AbstractParser):
    """Base class for parsers that use tree-sitter for structural extraction.

    Subclasses must define :attr:`language_name`, :attr:`supported_extensions`,
    :attr:`_ts_language`, and the node-type classification methods.  The base
    class provides common tree-walking, complexity scoring, and parameter
    extraction utilities.
    """

    @property
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return ``('//',)`` — correct for C-family languages."""
        return ("//",)

    # ── Subclass hooks ────────────────────────────────────────────────

    @property
    def _ts_language(self) -> str:
        """Return the tree-sitter grammar name (e.g. ``'java'``)."""
        return self.language_name

    # ── Tree helpers ──────────────────────────────────────────────────

    def _parse_tree(self, source: str) -> Any | None:
        """Parse *source* into a tree-sitter syntax tree.

        Args:
            source: Source code text.

        Returns:
            The root ``Node``, or ``None`` if tree-sitter is unavailable.
        """
        try:
            parser = _get_parser(self._ts_language)
        except ImportError:
            logger.debug("tree-sitter not available for %s", self._ts_language)
            return None
        tree = parser.parse(source.encode())
        return tree.root_node

    @staticmethod
    def _find_nodes(node: Any, *type_names: str) -> list[Any]:
        """Find all direct children matching one of *type_names*.

        Args:
            node: Parent tree-sitter node.
            *type_names: Node type strings to match.

        Returns:
            List of matching child nodes.
        """
        return [c for c in node.children if c.type in type_names]

    @staticmethod
    def _find_nodes_recursive(node: Any, *type_names: str) -> list[Any]:
        """Find all descendants matching one of *type_names*.

        Args:
            node: Root tree-sitter node.
            *type_names: Node type strings to match.

        Returns:
            List of matching descendant nodes.
        """
        results: list[Any] = []
        stack = list(node.children)
        while stack:
            n = stack.pop()
            if n.type in type_names:
                results.append(n)
            stack.extend(n.children)
        return results

    @staticmethod
    def _node_text(node: Any) -> str:
        """Return the text content of *node* as a string.

        Args:
            node: A tree-sitter node.

        Returns:
            The UTF-8 decoded text.
        """
        result: str = node.text.decode("utf-8", errors="replace")
        return result

    @staticmethod
    def _child_by_type(node: Any, type_name: str) -> Any | None:
        """Return the first child of *node* with the given type.

        Args:
            node: Parent node.
            type_name: Child type to find.

        Returns:
            The child node, or ``None``.
        """
        for c in node.children:
            if c.type == type_name:
                return c
        return None

    # ── Complexity ────────────────────────────────────────────────────

    @staticmethod
    def _cyclomatic_complexity(node: Any) -> int:
        """Compute approximate cyclomatic complexity for a method node.

        Args:
            node: The method/function tree-sitter node.

        Returns:
            Cyclomatic complexity (minimum 1).
        """
        cc = 1
        stack = list(node.children)
        while stack:
            n = stack.pop()
            if n.type in _CC_NODE_TYPES:
                cc += 1
            elif n.type == "binary_expression":
                op = TreeSitterBase._child_by_type(n, "&&") or TreeSitterBase._child_by_type(
                    n, "||"
                )
                if op:
                    cc += 1
            stack.extend(n.children)
        return cc

    @staticmethod
    def _cognitive_complexity(node: Any) -> int:
        """Compute cognitive complexity for a method node.

        Args:
            node: The method/function tree-sitter node.

        Returns:
            Cognitive complexity score.
        """
        score = 0

        def _walk(n: Any, nesting: int) -> None:
            nonlocal score
            for child in n.children:
                inc = 0
                nest_delta = 0

                if child.type in (
                    "if_statement",
                    "for_statement",
                    "for_in_statement",
                    "enhanced_for_statement",
                    "while_statement",
                    "do_statement",
                    "catch_clause",
                ):
                    inc = 1 + nesting
                    nest_delta = 1
                elif child.type in ("else_clause", "else"):
                    # else/finally: +1 flat
                    inc = 1
                elif child.type == "finally_clause":
                    inc = 1
                elif child.type == "binary_expression":
                    op = TreeSitterBase._child_by_type(
                        child, "&&"
                    ) or TreeSitterBase._child_by_type(child, "||")
                    if op:
                        score += 1
                    _walk(child, nesting)
                    continue
                elif child.type in (
                    "try_statement",
                    "lambda_expression",
                    "arrow_function",
                ):
                    nest_delta = 1
                elif child.type in ("ternary_expression", "conditional_expression"):
                    inc = 1 + nesting
                    nest_delta = 1

                score += inc
                _walk(child, nesting + nest_delta)

        _walk(node, 0)
        return score

    # ── Parameter extraction ──────────────────────────────────────────

    @staticmethod
    def _extract_params_from_node(params_node: Any) -> tuple[ParameterReport, ...]:
        """Extract parameters from a formal_parameters / parameter_list node.

        Args:
            params_node: The parameters tree-sitter node.

        Returns:
            Tuple of ``ParameterReport`` objects.
        """
        if params_node is None:
            return ()
        results: list[ParameterReport] = []
        for child in params_node.children:
            if child.type in (
                "formal_parameter",
                "spread_parameter",
                "required_parameter",
                "optional_parameter",
                "rest_parameter",
            ):
                name = ""
                annotation = ""
                has_default = False
                for gc in child.children:
                    if gc.type == "identifier":
                        name = TreeSitterBase._node_text(gc)
                    elif gc.type in ("type_identifier", "generic_type", "array_type"):
                        annotation = TreeSitterBase._node_text(gc)
                    elif gc.type == "=":
                        has_default = True
                if child.type in ("spread_parameter", "rest_parameter"):
                    name = f"...{name}"
                if name:
                    results.append(
                        ParameterReport(
                            name=name,
                            type_annotation=annotation,
                            has_default=has_default,
                        )
                    )
            elif child.type == "identifier":
                # Simple parameter (e.g. JS arrow function)
                results.append(
                    ParameterReport(
                        name=TreeSitterBase._node_text(child),
                        type_annotation="",
                        has_default=False,
                    )
                )
        return tuple(results)

    # ── Method report builder ─────────────────────────────────────────

    def _build_method_report(
        self,
        node: Any,
        *,
        name: str | None = None,
        is_constructor: bool = False,
    ) -> MethodReport:
        """Build a ``MethodReport`` from a tree-sitter method/function node.

        Args:
            node: The method/function tree-sitter node.
            name: Override name (if not extractable from node).
            is_constructor: Whether this is a constructor.

        Returns:
            A frozen ``MethodReport``.
        """
        if name is None:
            name_node = self._child_by_type(node, "identifier")
            name = self._node_text(name_node) if name_node else "<anonymous>"

        params_node = self._child_by_type(node, "formal_parameters")
        params = self._extract_params_from_node(params_node)

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        lines = end_line - start_line + 1

        return MethodReport(
            name=name,
            line=start_line,
            end_line=end_line,
            lines=lines,
            parameters=params,
            cyclomatic_complexity=self._cyclomatic_complexity(node),
            cognitive_complexity=self._cognitive_complexity(node),
            nesting_depth=0,
            is_constructor=is_constructor,
        )
