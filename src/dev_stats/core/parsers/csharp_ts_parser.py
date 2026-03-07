"""C# parser using tree-sitter for structural extraction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from dev_stats.core.models import ClassReport, MethodReport
from dev_stats.core.parsers.tree_sitter_base import TreeSitterBase

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class CSharpTreeSitterParser(TreeSitterBase):
    """Parser for C# source files using tree-sitter.

    Extracts classes, interfaces, structs, enums, records, methods,
    constructors, properties, parameters, ``using`` directives,
    cyclomatic complexity, and cognitive complexity.
    """

    @property
    def language_name(self) -> str:
        """Return ``'csharp'``."""
        return "csharp"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return ``('.cs',)``."""
        return (".cs",)

    @property
    def _ts_language(self) -> str:
        """Return ``'c_sharp'`` (tree-sitter grammar name)."""
        return "c_sharp"

    # ── Class extraction ─────────────────────────────────────────────

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract class, interface, struct, enum, and record definitions.

        Args:
            source: C# source code.
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
        """Recursively collect class/interface/struct/enum/record declarations.

        Args:
            node: Current tree-sitter node.
            classes: Accumulator list for found classes.
        """
        for child in node.children:
            if child.type in (
                "class_declaration",
                "interface_declaration",
                "struct_declaration",
                "enum_declaration",
                "record_declaration",
            ):
                report = self._build_class_report(child)
                if report is not None:
                    classes.append(report)
                # Look for nested types inside the declaration body
                body = self._find_declaration_body(child)
                if body is not None:
                    self._collect_classes(body, classes)
            elif child.type == "namespace_declaration":
                # Recurse into namespace bodies
                body = self._child_by_type(child, "declaration_list")
                if body is not None:
                    self._collect_classes(body, classes)
            elif child.type == "file_scoped_namespace_declaration":
                self._collect_classes(child, classes)
            else:
                self._collect_classes(child, classes)

    def _find_declaration_body(self, node: Any) -> Any | None:
        """Find the body node for a type declaration.

        Args:
            node: A type declaration tree-sitter node.

        Returns:
            The body node, or ``None``.
        """
        return self._child_by_type(node, "declaration_list") or self._child_by_type(
            node, "enum_member_declaration_list"
        )

    def _build_class_report(self, node: Any) -> ClassReport | None:
        """Build a ``ClassReport`` from a type declaration node.

        Args:
            node: A ``class_declaration``, ``interface_declaration``,
                ``struct_declaration``, ``enum_declaration``, or
                ``record_declaration`` tree-sitter node.

        Returns:
            A ``ClassReport``, or ``None`` if the name cannot be determined.
        """
        name_node = self._child_by_type(node, "identifier")
        if name_node is None:
            return None
        name = self._node_text(name_node)

        # Extract base classes / interfaces
        base_classes = self._extract_base_types(node)

        # Extract methods, constructors, and properties
        body = self._find_declaration_body(node)
        methods: list[MethodReport] = []
        if body is not None:
            for child in body.children:
                if child.type == "method_declaration":
                    methods.append(self._build_method_report(child))
                elif child.type == "constructor_declaration":
                    methods.append(self._build_method_report(child, name=name, is_constructor=True))
                elif child.type == "property_declaration":
                    prop_report = self._build_property_report(child)
                    if prop_report is not None:
                        methods.append(prop_report)

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

    def _extract_base_types(self, node: Any) -> list[str]:
        """Extract base class and interface names from a type declaration.

        Args:
            node: A type declaration tree-sitter node.

        Returns:
            List of base type name strings.
        """
        base_classes: list[str] = []
        base_list = self._child_by_type(node, "base_list")
        if base_list is not None:
            for child in base_list.children:
                if child.type in ("identifier", "generic_name", "qualified_name"):
                    base_classes.append(self._node_text(child))
                else:
                    # Walk into nodes to find type identifiers
                    for gc in child.children:
                        if gc.type in ("identifier", "generic_name", "qualified_name"):
                            base_classes.append(self._node_text(gc))
        return base_classes

    @staticmethod
    def _method_name_node(node: Any) -> Any | None:
        """Find the method/constructor name node in a C# declaration.

        In C# tree-sitter, the return type may also be an ``identifier``
        (e.g. a generic type parameter ``T``).  This method uses the
        ``child_by_field_name`` API first, then falls back to finding
        the ``identifier`` that immediately precedes the ``parameter_list``.

        Args:
            node: A method or constructor tree-sitter node.

        Returns:
            The name ``identifier`` node, or ``None``.
        """
        # Prefer the named field provided by tree-sitter grammars.
        field_node: Any = node.child_by_field_name("name")
        if field_node is not None:
            return field_node

        # Fallback: find the identifier right before parameter_list.
        prev: Any = None
        for child in node.children:
            if child.type == "parameter_list" and prev is not None:
                return prev
            if child.type == "identifier":
                prev = child
        return prev

    def _build_method_report(
        self,
        node: Any,
        *,
        name: str | None = None,
        is_constructor: bool = False,
    ) -> MethodReport:
        """Build a ``MethodReport`` from a method/constructor tree-sitter node.

        Args:
            node: The method/constructor tree-sitter node.
            name: Override name (if not extractable from node).
            is_constructor: Whether this is a constructor.

        Returns:
            A frozen ``MethodReport``.
        """
        if name is None:
            name_node = self._method_name_node(node)
            name = self._node_text(name_node) if name_node else "<anonymous>"

        params_node = self._child_by_type(node, "parameter_list")
        params = self._extract_csharp_params(params_node)

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

    def _build_property_report(self, node: Any) -> MethodReport | None:
        """Build a ``MethodReport`` for a property declaration.

        Args:
            node: A ``property_declaration`` tree-sitter node.

        Returns:
            A ``MethodReport``, or ``None`` if the name cannot be determined.
        """
        name_node = self._child_by_type(node, "identifier")
        if name_node is None:
            return None
        name = self._node_text(name_node)

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        lines = end_line - start_line + 1

        return MethodReport(
            name=name,
            line=start_line,
            end_line=end_line,
            lines=lines,
            parameters=(),
            cyclomatic_complexity=self._cyclomatic_complexity(node),
            cognitive_complexity=self._cognitive_complexity(node),
            nesting_depth=0,
            is_constructor=False,
        )

    @staticmethod
    def _extract_csharp_params(params_node: Any) -> tuple[Any, ...]:
        """Extract parameters from a C# parameter_list node.

        Args:
            params_node: The ``parameter_list`` tree-sitter node.

        Returns:
            Tuple of ``ParameterReport`` objects.
        """
        from dev_stats.core.models import ParameterReport

        if params_node is None:
            return ()
        results: list[ParameterReport] = []
        for child in params_node.children:
            if child.type == "parameter":
                name = ""
                annotation = ""
                has_default = False
                for gc in child.children:
                    if gc.type == "identifier":
                        name = TreeSitterBase._node_text(gc)
                    elif gc.type in (
                        "predefined_type",
                        "identifier",
                        "generic_name",
                        "nullable_type",
                        "array_type",
                        "qualified_name",
                    ):
                        # If we already have a name, this is the type
                        if not annotation:
                            text = TreeSitterBase._node_text(gc)
                            # If this looks like a type (not the param name), store it
                            if gc.type != "identifier":
                                annotation = text
                    elif gc.type == "equals_value_clause":
                        has_default = True
                # In C#, parameter children are typically: type identifier [= default]
                # Re-extract properly: iterate children in order
                parts: list[str] = []
                for gc in child.children:
                    if gc.type == "identifier":
                        parts.append(TreeSitterBase._node_text(gc))
                    elif gc.type in (
                        "predefined_type",
                        "generic_name",
                        "nullable_type",
                        "array_type",
                        "qualified_name",
                    ):
                        annotation = TreeSitterBase._node_text(gc)
                if parts:
                    name = parts[-1]  # Last identifier is the parameter name
                    if len(parts) > 1 and not annotation:
                        annotation = parts[0]  # First identifier is the type
                if name:
                    results.append(
                        ParameterReport(
                            name=name,
                            type_annotation=annotation,
                            has_default=has_default,
                        )
                    )
        return tuple(results)

    # ── Functions (none in C#) ───────────────────────────────────────

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Return empty list (C# has no top-level functions).

        Args:
            source: C# source code.
            path: File path.

        Returns:
            Empty list.
        """
        return []

    # ── Imports ──────────────────────────────────────────────────────

    def _detect_imports(self, source: str) -> list[str]:
        """Detect ``using`` namespace directives using tree-sitter.

        Args:
            source: C# source code.

        Returns:
            Sorted, deduplicated list of top-level namespace names.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        modules: set[str] = set()
        self._collect_usings(root, modules)
        return sorted(modules)

    def _collect_usings(self, node: Any, modules: set[str]) -> None:
        """Recursively collect ``using`` directives from the tree.

        Args:
            node: Current tree-sitter node.
            modules: Accumulator set for namespace names.
        """
        for child in node.children:
            if child.type == "using_directive":
                ns = self._extract_using_namespace(child)
                if ns:
                    modules.add(ns.split(".")[0])
            elif child.type in (
                "namespace_declaration",
                "file_scoped_namespace_declaration",
            ):
                self._collect_usings(child, modules)

    def _extract_using_namespace(self, node: Any) -> str:
        """Extract the namespace string from a ``using_directive`` node.

        Args:
            node: A ``using_directive`` tree-sitter node.

        Returns:
            The full namespace string, or empty string.
        """
        for child in node.children:
            if child.type in ("qualified_name", "identifier"):
                return self._node_text(child)
        return ""
