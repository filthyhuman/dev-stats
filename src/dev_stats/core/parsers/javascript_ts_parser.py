"""JavaScript parser using tree-sitter for structural extraction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from dev_stats.core.models import ClassReport, MethodReport
from dev_stats.core.parsers.tree_sitter_base import TreeSitterBase

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class JavaScriptTreeSitterParser(TreeSitterBase):
    """Parser for JavaScript source files using tree-sitter.

    Extracts classes, methods, functions (including arrow functions),
    parameters, imports/requires, cyclomatic complexity, and cognitive
    complexity.
    """

    @property
    def language_name(self) -> str:
        """Return ``'javascript'``."""
        return "javascript"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return ``('.js', '.jsx', '.mjs', '.cjs')``."""
        return (".js", ".jsx", ".mjs", ".cjs")

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract ES6 class definitions using tree-sitter.

        Args:
            source: JavaScript source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        classes: list[ClassReport] = []
        for node in self._find_nodes_recursive(root, "class_declaration"):
            report = self._build_class_report(node)
            if report is not None:
                classes.append(report)
        return classes

    def _build_class_report(self, node: Any) -> ClassReport | None:
        """Build a ``ClassReport`` from a class_declaration node.

        Args:
            node: A ``class_declaration`` tree-sitter node.

        Returns:
            A ``ClassReport``, or ``None`` if the name cannot be determined.
        """
        name_node = self._child_by_type(node, "identifier")
        if name_node is None:
            return None
        name = self._node_text(name_node)

        # Base class
        base_classes: list[str] = []
        heritage = self._child_by_type(node, "class_heritage")
        if heritage is not None:
            for child in heritage.children:
                if child.type == "identifier":
                    base_classes.append(self._node_text(child))

        # Methods
        body = self._child_by_type(node, "class_body")
        methods: list[MethodReport] = []
        if body is not None:
            for child in body.children:
                if child.type == "method_definition":
                    mname_node = self._child_by_type(child, "property_identifier")
                    mname = self._node_text(mname_node) if mname_node else "<anonymous>"
                    is_ctor = mname == "constructor"
                    methods.append(
                        self._build_method_report(child, name=mname, is_constructor=is_ctor)
                    )

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        return ClassReport(
            name=name,
            line=start_line,
            end_line=end_line,
            lines=end_line - start_line + 1,
            methods=tuple(methods),
            base_classes=tuple(base_classes),
        )

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level functions and arrow function assignments.

        Args:
            source: JavaScript source code.
            path: File path for error messages.

        Returns:
            List of ``MethodReport`` objects.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        functions: list[MethodReport] = []
        class_ranges = self._class_ranges(root)

        # Function declarations
        for node in root.children:
            if node.type == "function_declaration":
                functions.append(self._build_method_report(node))
            elif node.type in ("lexical_declaration", "variable_declaration"):
                # Look for arrow functions: const foo = (...) => { ... }
                for decl in node.children:
                    if decl.type == "variable_declarator":
                        arrow = self._extract_arrow_function(decl, class_ranges)
                        if arrow is not None:
                            functions.append(arrow)
            elif node.type == "export_statement":
                for child in node.children:
                    if child.type == "function_declaration":
                        functions.append(self._build_method_report(child))

        return functions

    def _extract_arrow_function(
        self, decl_node: Any, class_ranges: list[tuple[int, int]]
    ) -> MethodReport | None:
        """Extract an arrow function from a variable_declarator.

        Args:
            decl_node: A ``variable_declarator`` tree-sitter node.
            class_ranges: Line ranges of class declarations to exclude.

        Returns:
            A ``MethodReport``, or ``None`` if not an arrow function.
        """
        name_node = self._child_by_type(decl_node, "identifier")
        arrow_node = self._child_by_type(decl_node, "arrow_function")
        if name_node is None or arrow_node is None:
            return None

        # Exclude arrow functions inside class bodies
        start_line = arrow_node.start_point[0] + 1
        for cstart, cend in class_ranges:
            if cstart <= start_line <= cend:
                return None

        name = self._node_text(name_node)
        params_node = self._child_by_type(arrow_node, "formal_parameters")
        params = self._extract_params_from_node(params_node)

        end_line = arrow_node.end_point[0] + 1
        lines = end_line - start_line + 1

        return MethodReport(
            name=name,
            line=start_line,
            end_line=end_line,
            lines=lines,
            parameters=params,
            cyclomatic_complexity=self._cyclomatic_complexity(arrow_node),
            cognitive_complexity=self._cognitive_complexity(arrow_node),
        )

    def _class_ranges(self, root: Any) -> list[tuple[int, int]]:
        """Collect line ranges of class declarations.

        Args:
            root: The root tree-sitter node.

        Returns:
            List of ``(start_line, end_line)`` tuples.
        """
        ranges: list[tuple[int, int]] = []
        for node in self._find_nodes_recursive(root, "class_declaration"):
            ranges.append((node.start_point[0] + 1, node.end_point[0] + 1))
        return ranges

    def _detect_imports(self, source: str) -> list[str]:
        """Detect imported module names using tree-sitter.

        Args:
            source: JavaScript source code.

        Returns:
            Sorted, deduplicated list of module names.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        modules: set[str] = set()
        for node in root.children:
            if node.type == "import_statement":
                string_node = self._child_by_type(node, "string")
                if string_node is not None:
                    mod = self._node_text(string_node).strip("'\"")
                    modules.add(mod.split("/")[0])

        # Also find require() calls
        for node in self._find_nodes_recursive(root, "call_expression"):
            func_node = self._child_by_type(node, "identifier")
            if func_node is not None and self._node_text(func_node) == "require":
                args = self._child_by_type(node, "arguments")
                if args is not None:
                    for arg in args.children:
                        if arg.type == "string":
                            mod = self._node_text(arg).strip("'\"")
                            modules.add(mod.split("/")[0])

        return sorted(modules)
