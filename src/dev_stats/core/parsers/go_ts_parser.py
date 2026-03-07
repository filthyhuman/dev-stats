"""Go parser using tree-sitter for structural extraction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from dev_stats.core.models import ClassReport, MethodReport, ParameterReport
from dev_stats.core.parsers.tree_sitter_base import TreeSitterBase

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class GoTreeSitterParser(TreeSitterBase):
    """Parser for Go source files using tree-sitter.

    Extracts structs, interfaces, functions, methods with receivers,
    parameters, imports, cyclomatic complexity, and cognitive complexity.
    """

    @property
    def language_name(self) -> str:
        """Return ``'go'``."""
        return "go"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return ``('.go',)``."""
        return (".go",)

    @property
    def _ts_language(self) -> str:
        """Return ``'go'``."""
        return "go"

    @property
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return ``('//',)``."""
        return ("//",)

    # ── Class extraction ─────────────────────────────────────────────

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract struct and interface definitions using tree-sitter.

        Methods with receivers are associated with their receiver struct.

        Args:
            source: Go source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects (structs and interfaces).
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        classes: list[ClassReport] = []

        # First pass: collect all method_declarations grouped by receiver type
        receiver_methods: dict[str, list[MethodReport]] = {}
        for node in self._find_nodes_recursive(root, "method_declaration"):
            receiver_type = self._extract_receiver_type(node)
            if receiver_type:
                report = self._build_go_method_report(node)
                receiver_methods.setdefault(receiver_type, []).append(report)

        # Second pass: collect structs and interfaces
        for node in root.children:
            if node.type == "type_declaration":
                spec = self._child_by_type(node, "type_spec")
                if spec is None:
                    continue
                name_node = self._child_by_type(spec, "type_identifier")
                if name_node is None:
                    continue
                name = self._node_text(name_node)

                struct_type = self._child_by_type(spec, "struct_type")
                interface_type = self._child_by_type(spec, "interface_type")

                if struct_type is not None:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    methods = tuple(receiver_methods.get(name, []))
                    classes.append(
                        ClassReport(
                            name=name,
                            line=start_line,
                            end_line=end_line,
                            lines=end_line - start_line + 1,
                            methods=methods,
                        )
                    )
                elif interface_type is not None:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    classes.append(
                        ClassReport(
                            name=name,
                            line=start_line,
                            end_line=end_line,
                            lines=end_line - start_line + 1,
                            decorators=("interface",),
                        )
                    )

        return classes

    def _extract_receiver_type(self, node: Any) -> str:
        """Extract the receiver type name from a method_declaration node.

        Handles both value receivers ``(s Server)`` and pointer receivers
        ``(s *Server)``.

        Args:
            node: A ``method_declaration`` tree-sitter node.

        Returns:
            The receiver type name, or an empty string if not found.
        """
        param_list = self._child_by_type(node, "parameter_list")
        if param_list is None:
            return ""
        # The receiver parameter_list contains a parameter_declaration
        for child in param_list.children:
            if child.type == "parameter_declaration":
                # Look for type_identifier directly or inside pointer_type
                type_id = self._child_by_type(child, "type_identifier")
                if type_id is not None:
                    return self._node_text(type_id)
                pointer = self._child_by_type(child, "pointer_type")
                if pointer is not None:
                    type_id = self._child_by_type(pointer, "type_identifier")
                    if type_id is not None:
                        return self._node_text(type_id)
        return ""

    def _build_go_method_report(self, node: Any) -> MethodReport:
        """Build a ``MethodReport`` from a Go method/function node.

        Uses ``parameter_list`` instead of ``formal_parameters`` for Go.

        Args:
            node: A ``method_declaration`` or ``function_declaration`` node.

        Returns:
            A frozen ``MethodReport``.
        """
        name_node = self._child_by_type(node, "field_identifier") or self._child_by_type(
            node, "identifier"
        )
        name = self._node_text(name_node) if name_node else "<anonymous>"

        # For methods, the first parameter_list is the receiver, the second
        # is the actual parameters.  For functions there is only one.
        param_lists = self._find_nodes(node, "parameter_list")
        if node.type == "method_declaration" and len(param_lists) >= 2:
            params_node = param_lists[1]
        elif param_lists:
            params_node = param_lists[0]
        else:
            params_node = None

        params = self._extract_go_params(params_node)

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
        )

    @staticmethod
    def _extract_go_params(params_node: Any) -> tuple[ParameterReport, ...]:
        """Extract parameters from a Go ``parameter_list`` node.

        Go parameter declarations can group names sharing a type, e.g.
        ``(a, b int, c string)``.

        Args:
            params_node: A ``parameter_list`` tree-sitter node.

        Returns:
            Tuple of ``ParameterReport`` objects.
        """
        if params_node is None:
            return ()
        results: list[ParameterReport] = []
        for child in params_node.children:
            if child.type == "parameter_declaration":
                # Collect identifiers and the type
                names: list[str] = []
                annotation = ""
                for gc in child.children:
                    if gc.type == "identifier":
                        names.append(TreeSitterBase._node_text(gc))
                    elif gc.type in (
                        "type_identifier",
                        "pointer_type",
                        "slice_type",
                        "array_type",
                        "map_type",
                        "interface_type",
                        "struct_type",
                        "function_type",
                        "channel_type",
                        "qualified_type",
                    ):
                        annotation = TreeSitterBase._node_text(gc)
                if not names:
                    # Type-only parameter (e.g. in interface method signatures)
                    if annotation:
                        results.append(
                            ParameterReport(
                                name=annotation,
                                type_annotation="",
                                has_default=False,
                            )
                        )
                else:
                    for n in names:
                        results.append(
                            ParameterReport(
                                name=n,
                                type_annotation=annotation,
                                has_default=False,
                            )
                        )
            elif child.type == "variadic_parameter_declaration":
                name = ""
                annotation = ""
                for gc in child.children:
                    if gc.type == "identifier":
                        name = TreeSitterBase._node_text(gc)
                    elif gc.type in ("type_identifier", "qualified_type"):
                        annotation = TreeSitterBase._node_text(gc)
                if name:
                    results.append(
                        ParameterReport(
                            name=f"...{name}",
                            type_annotation=annotation,
                            has_default=False,
                        )
                    )
        return tuple(results)

    # ── Function extraction ──────────────────────────────────────────

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level functions (without receivers).

        Args:
            source: Go source code.
            path: File path for error messages.

        Returns:
            List of ``MethodReport`` objects.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        functions: list[MethodReport] = []
        for node in root.children:
            if node.type == "function_declaration":
                functions.append(self._build_go_method_report(node))
        return functions

    # ── Import detection ─────────────────────────────────────────────

    def _detect_imports(self, source: str) -> list[str]:
        """Detect imported package names using tree-sitter.

        Extracts the last path component of each import path, matching the
        behaviour of the regex-based Go parser.

        Args:
            source: Go source code.

        Returns:
            Sorted, deduplicated list of package short names.
        """
        root = self._parse_tree(source)
        if root is None:
            return []

        modules: set[str] = set()
        for node in root.children:
            if node.type == "import_declaration":
                self._collect_import_specs(node, modules)
        return sorted(modules)

    def _collect_import_specs(self, node: Any, modules: set[str]) -> None:
        """Recursively collect import path strings from an import node.

        Handles both single imports and grouped import blocks.

        Args:
            node: An ``import_declaration`` or child node.
            modules: Accumulator set of package short names.
        """
        for child in node.children:
            if child.type == "import_spec":
                path_node = self._child_by_type(child, "interpreted_string_literal")
                if path_node is not None:
                    raw = self._node_text(path_node).strip('"')
                    short = raw.split("/")[-1]
                    if short:
                        modules.add(short)
            elif child.type == "import_spec_list":
                self._collect_import_specs(child, modules)
            elif child.type == "interpreted_string_literal":
                # Single import without spec wrapper
                raw = self._node_text(child).strip('"')
                short = raw.split("/")[-1]
                if short:
                    modules.add(short)
