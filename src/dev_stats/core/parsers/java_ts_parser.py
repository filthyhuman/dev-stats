"""Java parser using tree-sitter for structural extraction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from dev_stats.core.models import ClassReport, MethodReport
from dev_stats.core.parsers.tree_sitter_base import TreeSitterBase

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class JavaTreeSitterParser(TreeSitterBase):
    """Parser for Java source files using tree-sitter.

    Extracts classes, interfaces, enums, methods, constructors,
    parameters, imports, cyclomatic complexity, and cognitive complexity.
    """

    @property
    def language_name(self) -> str:
        """Return ``'java'``."""
        return "java"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return ``('.java',)``."""
        return (".java",)

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract class, interface, and enum definitions using tree-sitter.

        Args:
            source: Java source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        classes: list[ClassReport] = []
        self._collect_classes(root, classes)
        return classes

    def _collect_classes(self, node: Any, classes: list[ClassReport]) -> None:
        """Recursively collect class/interface/enum declarations.

        Args:
            node: Current tree-sitter node.
            classes: Accumulator list for found classes.
        """
        for child in node.children:
            if child.type in ("class_declaration", "interface_declaration", "enum_declaration"):
                report = self._build_class_report(child)
                if report is not None:
                    classes.append(report)
                # Also look for nested classes inside the class body
                body = self._child_by_type(child, "class_body") or self._child_by_type(
                    child, "interface_body"
                )
                if body is not None:
                    self._collect_classes(body, classes)
            else:
                self._collect_classes(child, classes)

    def _build_class_report(self, node: Any) -> ClassReport | None:
        """Build a ``ClassReport`` from a class/interface/enum node.

        Args:
            node: A ``class_declaration``, ``interface_declaration``, or
                ``enum_declaration`` tree-sitter node.

        Returns:
            A ``ClassReport``, or ``None`` if the name cannot be determined.
        """
        name_node = self._child_by_type(node, "identifier")
        if name_node is None:
            return None
        name = self._node_text(name_node)

        # Extract base classes / interfaces
        base_classes: list[str] = []
        superclass = self._child_by_type(node, "superclass")
        if superclass is not None:
            type_node = self._child_by_type(superclass, "type_identifier")
            if type_node is not None:
                base_classes.append(self._node_text(type_node))

        interfaces = self._child_by_type(node, "super_interfaces")
        if interfaces is not None:
            type_list = self._child_by_type(interfaces, "type_list")
            if type_list is not None:
                for tc in type_list.children:
                    if tc.type in ("type_identifier", "generic_type"):
                        base_classes.append(self._node_text(tc))

        # Extract methods
        body = self._child_by_type(node, "class_body") or self._child_by_type(
            node, "interface_body"
        )
        methods: list[MethodReport] = []
        if body is not None:
            for child in body.children:
                if child.type == "method_declaration":
                    methods.append(self._build_method_report(child))
                elif child.type == "constructor_declaration":
                    methods.append(self._build_method_report(child, name=name, is_constructor=True))

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
        """Return empty list (Java has no top-level functions).

        Args:
            source: Java source code.
            path: File path.

        Returns:
            Empty list.
        """
        return []

    def _detect_imports(self, source: str) -> list[str]:
        """Detect imported package names using tree-sitter.

        Args:
            source: Java source code.

        Returns:
            Sorted, deduplicated list of top-level package names.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        modules: set[str] = set()
        for child in root.children:
            if child.type == "import_declaration":
                # Extract the first identifier in the scoped_identifier chain
                scoped = self._child_by_type(child, "scoped_identifier")
                if scoped is not None:
                    first = self._find_first_identifier(scoped)
                    if first:
                        modules.add(first)
        return sorted(modules)

    def _find_first_identifier(self, node: Any) -> str:
        """Find the leftmost identifier in a scoped_identifier chain.

        Args:
            node: A ``scoped_identifier`` node.

        Returns:
            The text of the first (leftmost) identifier.
        """
        for child in node.children:
            if child.type == "scoped_identifier":
                return self._find_first_identifier(child)
            if child.type == "identifier":
                return self._node_text(child)
        return ""
