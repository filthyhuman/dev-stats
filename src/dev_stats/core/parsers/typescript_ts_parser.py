"""TypeScript parser using tree-sitter for structural extraction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from dev_stats.core.models import ClassReport, MethodReport
from dev_stats.core.parsers.tree_sitter_base import TreeSitterBase

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class TypeScriptTreeSitterParser(TreeSitterBase):
    """Parser for TypeScript source files using tree-sitter.

    Extracts classes, interfaces, enums, methods, constructors,
    parameters, imports, top-level functions, arrow functions,
    cyclomatic complexity, and cognitive complexity.  Also handles
    TypeScript-specific constructs such as type aliases, decorators,
    and generics.
    """

    @property
    def language_name(self) -> str:
        """Return ``'typescript'``."""
        return "typescript"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return ``('.ts', '.tsx')``."""
        return (".ts", ".tsx")

    @property
    def _ts_language(self) -> str:
        """Return ``'typescript'``."""
        return "typescript"

    # ── Class / interface / enum extraction ───────────────────────────

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract class, interface, and enum definitions using tree-sitter.

        Args:
            source: TypeScript source code.
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
        """Recursively collect class, interface, and enum declarations.

        Args:
            node: Current tree-sitter node.
            classes: Accumulator list for found classes.
        """
        for child in node.children:
            if child.type == "export_statement":
                # Unwrap export wrappers to find declarations inside
                self._collect_classes(child, classes)
            elif child.type == "class_declaration":
                report = self._build_class_report(child)
                if report is not None:
                    classes.append(report)
                # Nested classes inside class body
                body = self._child_by_type(child, "class_body")
                if body is not None:
                    self._collect_classes(body, classes)
            elif child.type in (
                "interface_declaration",
                "abstract_class_declaration",
            ):
                report = self._build_interface_report(child)
                if report is not None:
                    classes.append(report)
            elif child.type == "enum_declaration":
                report = self._build_enum_report(child)
                if report is not None:
                    classes.append(report)
            else:
                self._collect_classes(child, classes)

    def _build_class_report(self, node: Any) -> ClassReport | None:
        """Build a ``ClassReport`` from a ``class_declaration`` node.

        Args:
            node: A ``class_declaration`` tree-sitter node.

        Returns:
            A ``ClassReport``, or ``None`` if the name cannot be determined.
        """
        name_node = self._child_by_type(node, "type_identifier") or self._child_by_type(
            node, "identifier"
        )
        if name_node is None:
            return None
        name = self._node_text(name_node)

        base_classes = self._extract_heritage(node)
        decorators = self._extract_decorators(node)

        # Methods
        body = self._child_by_type(node, "class_body")
        methods: list[MethodReport] = []
        if body is not None:
            methods = self._extract_class_methods(body, name)

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        return ClassReport(
            name=name,
            line=start_line,
            end_line=end_line,
            lines=end_line - start_line + 1,
            methods=tuple(methods),
            base_classes=tuple(base_classes),
            decorators=tuple(decorators),
        )

    def _build_interface_report(self, node: Any) -> ClassReport | None:
        """Build a ``ClassReport`` for an interface or abstract class declaration.

        Args:
            node: An ``interface_declaration`` or ``abstract_class_declaration``
                tree-sitter node.

        Returns:
            A ``ClassReport`` with ``decorators=("interface",)`` for interfaces,
            or ``None`` if the name cannot be determined.
        """
        name_node = self._child_by_type(node, "type_identifier") or self._child_by_type(
            node, "identifier"
        )
        if name_node is None:
            return None
        name = self._node_text(name_node)

        base_classes: list[str] = []
        # interface Foo extends Bar, Baz { ... }
        extends_clause = self._child_by_type(node, "extends_type_clause")
        if extends_clause is not None:
            for child in extends_clause.children:
                if child.type in ("type_identifier", "generic_type"):
                    base_classes.append(self._node_text(child))

        is_interface = node.type == "interface_declaration"
        decorators: tuple[str, ...] = ("interface",) if is_interface else ()

        # Interface methods (from interface body / object type)
        methods: list[MethodReport] = []
        body = (
            self._child_by_type(node, "interface_body")
            or self._child_by_type(node, "object_type")
            or self._child_by_type(node, "class_body")
        )
        if body is not None and not is_interface:
            methods = self._extract_class_methods(body, name)

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        return ClassReport(
            name=name,
            line=start_line,
            end_line=end_line,
            lines=end_line - start_line + 1,
            methods=tuple(methods),
            base_classes=tuple(base_classes),
            decorators=decorators,
        )

    def _build_enum_report(self, node: Any) -> ClassReport | None:
        """Build a ``ClassReport`` for an ``enum_declaration`` node.

        Args:
            node: An ``enum_declaration`` tree-sitter node.

        Returns:
            A ``ClassReport`` with ``decorators=("enum",)``, or ``None``.
        """
        name_node = self._child_by_type(node, "identifier")
        if name_node is None:
            return None
        name = self._node_text(name_node)

        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        return ClassReport(
            name=name,
            line=start_line,
            end_line=end_line,
            lines=end_line - start_line + 1,
            decorators=("enum",),
        )

    # ── Heritage (extends / implements) ──────────────────────────────

    def _extract_heritage(self, node: Any) -> list[str]:
        """Extract base class and implemented interface names.

        The TypeScript tree-sitter grammar wraps ``extends_clause`` and
        ``implements_clause`` inside a ``class_heritage`` node.

        Args:
            node: A class declaration tree-sitter node.

        Returns:
            List of base class / interface names.
        """
        bases: list[str] = []

        # The grammar nests extends/implements inside class_heritage.
        heritage = self._child_by_type(node, "class_heritage")
        search_root = heritage if heritage is not None else node

        for clause in search_root.children if search_root is not None else []:
            if clause.type in ("extends_clause", "implements_clause"):
                self._collect_type_names(clause, bases)

        return bases

    def _collect_type_names(self, clause: Any, bases: list[str]) -> None:
        """Collect type names from an extends/implements clause.

        Args:
            clause: An ``extends_clause`` or ``implements_clause`` node.
            bases: Accumulator list for extracted names.
        """
        for child in clause.children:
            if child.type in ("identifier", "type_identifier"):
                bases.append(self._node_text(child))
            elif child.type == "generic_type":
                id_node = self._child_by_type(child, "type_identifier") or self._child_by_type(
                    child, "identifier"
                )
                if id_node is not None:
                    bases.append(self._node_text(id_node))

    # ── Decorators ───────────────────────────────────────────────────

    def _extract_decorators(self, node: Any) -> list[str]:
        """Extract decorator names preceding a class declaration.

        Args:
            node: A class declaration tree-sitter node.

        Returns:
            List of decorator names (without ``@``).
        """
        decorators: list[str] = []
        for child in node.children:
            if child.type == "decorator":
                # decorator → @identifier or @call_expression
                for gc in child.children:
                    if gc.type == "identifier":
                        decorators.append(self._node_text(gc))
                    elif gc.type == "call_expression":
                        func = self._child_by_type(gc, "identifier")
                        if func is not None:
                            decorators.append(self._node_text(func))
        return decorators

    # ── Class method extraction ──────────────────────────────────────

    def _extract_class_methods(self, body: Any, class_name: str) -> list[MethodReport]:
        """Extract methods from a class body.

        Args:
            body: A ``class_body`` tree-sitter node.
            class_name: Name of the enclosing class (for constructor naming).

        Returns:
            List of ``MethodReport`` objects.
        """
        methods: list[MethodReport] = []
        for child in body.children:
            if child.type == "method_definition":
                mname_node = self._child_by_type(child, "property_identifier")
                mname = self._node_text(mname_node) if mname_node else "<anonymous>"
                is_ctor = mname == "constructor"
                methods.append(self._build_method_report(child, name=mname, is_constructor=is_ctor))
            elif child.type == "public_field_definition":
                # Arrow function class fields: foo = (x) => { ... }
                arrow = self._child_by_type(child, "arrow_function")
                if arrow is not None:
                    fname_node = self._child_by_type(child, "property_identifier")
                    if fname_node is not None:
                        fname = self._node_text(fname_node)
                        methods.append(self._build_method_report(arrow, name=fname))
        return methods

    # ── Top-level function extraction ────────────────────────────────

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level functions and arrow function assignments.

        Args:
            source: TypeScript source code.
            path: File path for error messages.

        Returns:
            List of ``MethodReport`` objects.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        functions: list[MethodReport] = []
        class_ranges = self._class_ranges(root)

        for node in root.children:
            if node.type == "function_declaration":
                functions.append(self._build_method_report(node))
            elif node.type in ("lexical_declaration", "variable_declaration"):
                for decl in node.children:
                    if decl.type == "variable_declarator":
                        arrow = self._extract_arrow_function(decl, class_ranges)
                        if arrow is not None:
                            functions.append(arrow)
            elif node.type == "export_statement":
                for child in node.children:
                    if child.type == "function_declaration":
                        functions.append(self._build_method_report(child))
                    elif child.type in ("lexical_declaration", "variable_declaration"):
                        for decl in child.children:
                            if decl.type == "variable_declarator":
                                arrow = self._extract_arrow_function(decl, class_ranges)
                                if arrow is not None:
                                    functions.append(arrow)

        return functions

    def _extract_arrow_function(
        self, decl_node: Any, class_ranges: list[tuple[int, int]]
    ) -> MethodReport | None:
        """Extract an arrow function from a ``variable_declarator``.

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

    # ── Import detection ─────────────────────────────────────────────

    def _detect_imports(self, source: str) -> list[str]:
        """Detect imported module names using tree-sitter.

        Args:
            source: TypeScript source code.

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

        return sorted(modules)
