"""C/C++ parser using tree-sitter for structural extraction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from dev_stats.core.models import ClassReport, MethodReport, ParameterReport
from dev_stats.core.parsers.tree_sitter_base import TreeSitterBase

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class CppTreeSitterParser(TreeSitterBase):
    """Parser for C/C++ source files using tree-sitter.

    Extracts classes, structs, functions, methods, constructors, destructors,
    parameters, ``#include`` directives, namespaces, templates, operator
    overloads, cyclomatic complexity, and cognitive complexity.
    """

    @property
    def language_name(self) -> str:
        """Return ``'cpp'``."""
        return "cpp"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return C/C++ file extensions."""
        return (".cpp", ".cxx", ".cc", ".c", ".hpp", ".hxx", ".h", ".hh")

    @property
    def _ts_language(self) -> str:
        """Return ``'cpp'`` as the tree-sitter grammar name."""
        return "cpp"

    # ── Class / struct extraction ─────────────────────────────────────

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract class and struct definitions using tree-sitter.

        Args:
            source: C/C++ source code.
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
        """Recursively collect class and struct declarations.

        Args:
            node: Current tree-sitter node.
            classes: Accumulator list for found classes.
        """
        for child in node.children:
            if child.type in ("class_specifier", "struct_specifier"):
                report = self._build_class_report(child)
                if report is not None:
                    classes.append(report)
                # Look for nested classes inside the body
                body = self._child_by_type(child, "field_declaration_list")
                if body is not None:
                    self._collect_classes(body, classes)
            elif child.type == "template_declaration":
                # Template classes: look inside the template_declaration
                self._collect_classes(child, classes)
            elif child.type == "namespace_definition":
                # Recurse into namespace bodies
                body = self._child_by_type(child, "declaration_list")
                if body is not None:
                    self._collect_classes(body, classes)
            else:
                self._collect_classes(child, classes)

    def _build_class_report(self, node: Any) -> ClassReport | None:
        """Build a ``ClassReport`` from a class/struct specifier node.

        Args:
            node: A ``class_specifier`` or ``struct_specifier`` tree-sitter
                node.

        Returns:
            A ``ClassReport``, or ``None`` if the name cannot be determined.
        """
        name_node = self._child_by_type(node, "type_identifier")
        if name_node is None:
            # Anonymous struct/class
            return None
        name = self._node_text(name_node)

        # Extract base classes
        base_classes: list[str] = []
        base_clause = self._child_by_type(node, "base_class_clause")
        if base_clause is not None:
            for child in base_clause.children:
                if child.type in ("type_identifier", "qualified_identifier"):
                    base_classes.append(self._node_text(child))

        # Extract methods from the field_declaration_list (class body)
        body = self._child_by_type(node, "field_declaration_list")
        methods: list[MethodReport] = []
        if body is not None:
            self._collect_methods(body, methods, class_name=name)

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

    # ── Method extraction ─────────────────────────────────────────────

    def _collect_methods(
        self,
        body: Any,
        methods: list[MethodReport],
        *,
        class_name: str,
    ) -> None:
        """Collect methods and constructors from a class body.

        Args:
            body: The ``field_declaration_list`` tree-sitter node.
            methods: Accumulator list for found methods.
            class_name: Name of the enclosing class (for constructor detection).
        """
        for child in body.children:
            if child.type == "function_definition":
                report = self._build_cpp_method_report(child, class_name=class_name)
                if report is not None:
                    methods.append(report)
            elif child.type == "template_declaration":
                # Template methods inside a class body
                for gc in child.children:
                    if gc.type == "function_definition":
                        report = self._build_cpp_method_report(gc, class_name=class_name)
                        if report is not None:
                            methods.append(report)
            elif child.type == "declaration":
                # Inline method declarations that have a body
                func = self._child_by_type(child, "function_definition")
                if func is not None:
                    report = self._build_cpp_method_report(func, class_name=class_name)
                    if report is not None:
                        methods.append(report)
            elif child.type == "access_specifier":
                # public: / private: / protected: — skip
                pass

    def _build_cpp_method_report(
        self,
        node: Any,
        *,
        class_name: str = "",
    ) -> MethodReport | None:
        """Build a ``MethodReport`` from a C++ function_definition node.

        Args:
            node: A ``function_definition`` tree-sitter node.
            class_name: Enclosing class name (empty for top-level functions).

        Returns:
            A ``MethodReport``, or ``None`` if the name cannot be determined.
        """
        name = self._extract_function_name(node)
        if not name:
            return None

        # Detect constructor / destructor
        is_constructor = False
        if class_name:
            is_constructor = name == class_name or name.startswith("~")

        # Extract parameters
        params = self._extract_cpp_params(node)

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

    def _extract_function_name(self, node: Any) -> str:
        """Extract the function/method name from a function_definition node.

        Handles plain identifiers, destructors, operator overloads, and
        qualified identifiers.

        Args:
            node: A ``function_definition`` tree-sitter node.

        Returns:
            The function name, or an empty string if unrecognisable.
        """
        declarator = self._child_by_type(node, "function_declarator")
        if declarator is None:
            return ""

        for child in declarator.children:
            if child.type == "identifier":
                return self._node_text(child)
            if child.type == "field_identifier":
                return self._node_text(child)
            if child.type == "destructor_name":
                return self._node_text(child)
            if child.type == "operator_name":
                return self._node_text(child)
            if child.type == "qualified_identifier":
                return self._node_text(child)
        return ""

    def _extract_cpp_params(self, node: Any) -> tuple[ParameterReport, ...]:
        """Extract parameters from a C++ function_definition node.

        Args:
            node: A ``function_definition`` tree-sitter node.

        Returns:
            Tuple of ``ParameterReport`` objects.
        """
        declarator = self._child_by_type(node, "function_declarator")
        if declarator is None:
            return ()

        params_node = self._child_by_type(declarator, "parameter_list")
        if params_node is None:
            return ()

        results: list[ParameterReport] = []
        for child in params_node.children:
            if child.type in (
                "parameter_declaration",
                "optional_parameter_declaration",
                "variadic_parameter_declaration",
            ):
                name = ""
                annotation = ""
                has_default = False

                for gc in child.children:
                    if gc.type in ("identifier", "pointer_declarator", "reference_declarator"):
                        raw = self._node_text(gc).lstrip("*&")
                        if raw:
                            name = raw
                    elif gc.type in (
                        "type_identifier",
                        "primitive_type",
                        "sized_type_specifier",
                        "qualified_identifier",
                        "template_type",
                    ):
                        annotation = self._node_text(gc)
                    elif gc.type == "=":
                        has_default = True

                if child.type == "optional_parameter_declaration":
                    has_default = True

                if name:
                    results.append(
                        ParameterReport(
                            name=name,
                            type_annotation=annotation,
                            has_default=has_default,
                        )
                    )
        return tuple(results)

    # ── Top-level functions ───────────────────────────────────────────

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level (non-member) function definitions.

        Args:
            source: C/C++ source code.
            path: File path for error messages.

        Returns:
            List of ``MethodReport`` objects for top-level functions.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        functions: list[MethodReport] = []
        self._collect_top_level_functions(root, functions)
        return functions

    def _collect_top_level_functions(
        self,
        node: Any,
        functions: list[MethodReport],
    ) -> None:
        """Recursively collect top-level function definitions.

        Skips functions inside class/struct bodies.

        Args:
            node: Current tree-sitter node.
            functions: Accumulator list for found functions.
        """
        for child in node.children:
            if child.type == "function_definition":
                report = self._build_cpp_method_report(child)
                if report is not None:
                    functions.append(report)
            elif child.type == "template_declaration":
                # Template functions at top level
                for gc in child.children:
                    if gc.type == "function_definition":
                        report = self._build_cpp_method_report(gc)
                        if report is not None:
                            functions.append(report)
            elif child.type == "namespace_definition":
                body = self._child_by_type(child, "declaration_list")
                if body is not None:
                    self._collect_top_level_functions(body, functions)
            # Do NOT recurse into class_specifier / struct_specifier

    # ── Import detection ──────────────────────────────────────────────

    def _detect_imports(self, source: str) -> list[str]:
        """Detect ``#include`` directives using tree-sitter.

        Args:
            source: C/C++ source code.

        Returns:
            Sorted, deduplicated list of included header names.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        headers: set[str] = set()
        for child in root.children:
            if child.type == "preproc_include":
                path_node = self._child_by_type(child, "system_lib_string") or self._child_by_type(
                    child, "string_literal"
                )
                if path_node is not None:
                    raw = self._node_text(path_node).strip("<>\"'")
                    # Normalize: strip path, take base name without extension
                    base = raw.split("/")[-1]
                    name = base.split(".")[0] if "." in base else base
                    headers.add(name)
        return sorted(headers)
