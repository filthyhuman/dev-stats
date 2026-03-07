"""Python parser using the ``ast`` module for full structural extraction."""

from __future__ import annotations

import ast
import logging
from typing import TYPE_CHECKING

from dev_stats.core.models import ClassReport, MethodReport, ParameterReport
from dev_stats.core.parsers.abstract_parser import AbstractParser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# AST node types that increase cyclomatic complexity.
_COMPLEXITY_NODES: tuple[type[ast.AST], ...] = (
    ast.If,
    ast.For,
    ast.While,
    ast.ExceptHandler,
    ast.With,
    ast.Assert,
    ast.comprehension,
)

# AST node types that increase nesting depth.
_NESTING_NODES: tuple[type[ast.AST], ...] = (
    ast.If,
    ast.For,
    ast.While,
    ast.With,
    ast.Try,
    ast.TryStar,
)


def _cyclomatic_complexity(node: ast.AST) -> int:
    """Compute McCabe cyclomatic complexity for a function/method node.

    Args:
        node: An ``ast.FunctionDef`` or ``ast.AsyncFunctionDef``.

    Returns:
        The cyclomatic complexity (minimum 1).
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, _COMPLEXITY_NODES):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            # Each additional operand in ``and``/``or`` adds a branch.
            complexity += len(child.values) - 1
    return complexity


def _cognitive_complexity(node: ast.AST) -> int:
    """Compute cognitive complexity for a function/method node.

    Follows the SonarSource specification:

    * **+1** for each flow-breaking structure (``if``, ``elif``, ``for``,
      ``while``, ``except``).
    * **+1 nesting increment** for each level of nesting when a flow-break
      is encountered inside a nested block.
    * **+1** for each ``else``, ``finally`` branch.
    * **+1** for each boolean operator sequence (``and``/``or``), counting
      one per *sequence* of identical operators, plus one for each switch
      between different operators.
    * **+1** for recursion (calling the function's own name).

    Args:
        node: An ``ast.FunctionDef`` or ``ast.AsyncFunctionDef``.

    Returns:
        The cognitive complexity score (minimum 0).
    """
    func_name = getattr(node, "name", "")
    score = 0

    def _walk(n: ast.AST, nesting: int) -> None:
        nonlocal score

        for child in ast.iter_child_nodes(n):
            increment = 0
            nest_change = 0

            # --- Flow-breaking structures: +1 + nesting ---
            if isinstance(child, (ast.If, ast.For, ast.While)):
                is_elif = isinstance(child, ast.If) and _is_elif(n, child)
                if is_elif:
                    # elif: +1 flat, no nesting increment
                    increment = 1
                else:
                    increment = 1 + nesting
                    nest_change = 1

            elif isinstance(child, ast.IfExp):
                # Ternary expression: ``x if cond else y``
                increment = 1 + nesting
                nest_change = 1

            elif isinstance(child, ast.ExceptHandler):
                increment = 1 + nesting
                nest_change = 1

            # --- Boolean operator sequences ---
            elif isinstance(child, ast.BoolOp):
                score += _bool_op_increment(child)
                _walk(child, nesting)
                continue

            # --- Try: no nesting for handlers, walk body/handlers separately ---
            elif isinstance(child, (ast.Try, ast.TryStar)):
                if child.finalbody:
                    score += 1
                if child.orelse:
                    score += 1
                # Walk try body at current nesting (try does not add nesting).
                # Score each except handler explicitly, then walk its body
                # with nesting+1 (the handler itself is a nesting structure).
                for stmt in child.body:
                    _walk(stmt, nesting)
                for handler in child.handlers:
                    score += 1 + nesting
                    _walk(handler, nesting + 1)
                for stmt in child.orelse:
                    _walk(stmt, nesting)
                for stmt in child.finalbody:
                    _walk(stmt, nesting)
                continue

            # --- With/Lambda/nested function: nesting only ---
            elif isinstance(
                child,
                (ast.With, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda),
            ):
                nest_change = 1

            # --- Recursion detection ---
            elif isinstance(child, ast.Call):
                if _is_recursive_call(child, func_name):
                    score += 1

            score += increment

            # Check for else branches (+1 each, flat)
            if isinstance(child, (ast.If, ast.For, ast.While)):
                orelse = child.orelse
                if orelse:
                    first = orelse[0]
                    is_elif_chain = (
                        isinstance(child, ast.If) and isinstance(first, ast.If) and len(orelse) == 1
                    )
                    if not is_elif_chain:
                        score += 1

            if isinstance(child, ast.IfExp):
                # The else branch of a ternary
                score += 1

            _walk(child, nesting + nest_change)

    _walk(node, 0)
    return score


def _is_elif(parent: ast.AST, child: ast.If) -> bool:
    """Return ``True`` if *child* is an ``elif`` branch of *parent*.

    Args:
        parent: The parent AST node.
        child: An ``ast.If`` node.

    Returns:
        ``True`` when *child* is the sole element in *parent*'s ``orelse``.
    """
    orelse = getattr(parent, "orelse", None)
    return orelse is not None and len(orelse) == 1 and orelse[0] is child


def _bool_op_increment(node: ast.BoolOp) -> int:
    """Compute the cognitive complexity increment for a boolean operation.

    A sequence of the same operator (``a and b and c``) counts as +1.
    Each switch between operators adds another +1.

    Args:
        node: An ``ast.BoolOp`` node.

    Returns:
        The increment value.
    """
    # A single BoolOp with N values = 1 sequence.
    # Nested BoolOps with a different op = separate sequences handled
    # when the walker reaches those child BoolOps.
    return 1


def _is_recursive_call(node: ast.Call, func_name: str) -> bool:
    """Return ``True`` if *node* is a call to *func_name*.

    Args:
        node: An ``ast.Call`` node.
        func_name: The name of the enclosing function.

    Returns:
        ``True`` for a recursive call.
    """
    if not func_name:
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == func_name:
        return True
    return isinstance(func, ast.Attribute) and func.attr == func_name


def _nesting_depth(node: ast.AST, current: int = 0) -> int:
    """Compute maximum nesting depth inside *node*.

    Args:
        node: AST node to traverse.
        current: Current depth (used in recursion).

    Returns:
        Maximum nesting depth found.
    """
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _NESTING_NODES):
            max_depth = max(max_depth, _nesting_depth(child, current + 1))
        else:
            max_depth = max(max_depth, _nesting_depth(child, current))
    return max_depth


def _extract_parameters(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ParameterReport]:
    """Extract parameters from a function definition, excluding ``self``/``cls``.

    Args:
        func_node: AST function node.

    Returns:
        List of ``ParameterReport`` objects.
    """
    params: list[ParameterReport] = []
    args = func_node.args

    # Number of args that have defaults (right-aligned).
    num_defaults = len(args.defaults)
    num_args = len(args.args)

    for i, arg in enumerate(args.args):
        if arg.arg in ("self", "cls"):
            continue
        annotation = ast.unparse(arg.annotation) if arg.annotation else ""
        has_default = i >= (num_args - num_defaults)
        params.append(
            ParameterReport(
                name=arg.arg,
                type_annotation=annotation,
                has_default=has_default,
            )
        )

    for arg in args.kwonlyargs:
        annotation = ast.unparse(arg.annotation) if arg.annotation else ""
        # kw_defaults aligns with kwonlyargs; None means no default.
        idx = args.kwonlyargs.index(arg)
        has_default = idx < len(args.kw_defaults) and args.kw_defaults[idx] is not None
        params.append(
            ParameterReport(
                name=arg.arg,
                type_annotation=annotation,
                has_default=has_default,
            )
        )

    if args.vararg:
        annotation = ast.unparse(args.vararg.annotation) if args.vararg.annotation else ""
        params.append(
            ParameterReport(
                name=f"*{args.vararg.arg}",
                type_annotation=annotation,
                has_default=False,
            )
        )

    if args.kwarg:
        annotation = ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else ""
        params.append(
            ParameterReport(
                name=f"**{args.kwarg.arg}",
                type_annotation=annotation,
                has_default=False,
            )
        )

    return params


def _collect_attributes(class_node: ast.ClassDef) -> list[str]:
    """Collect instance attribute names from a class definition.

    Scans ``__init__`` for ``self.x = ...`` and ``self.x: ... = ...`` patterns.

    Args:
        class_node: AST class node.

    Returns:
        Deduplicated list of attribute names.
    """
    attrs: list[str] = []
    seen: set[str] = set()
    for node in ast.walk(class_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in ("self", "cls")
                    and target.attr not in seen
                ):
                    attrs.append(target.attr)
                    seen.add(target.attr)
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id in ("self", "cls")
                and target.attr not in seen
            ):
                attrs.append(target.attr)
                seen.add(target.attr)
    return attrs


def _build_method_report(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    source_lines: list[str],
) -> MethodReport:
    """Build a ``MethodReport`` from an AST function node.

    Args:
        func_node: AST function node.
        source_lines: Full source split into lines.

    Returns:
        A frozen ``MethodReport``.
    """
    end_line = func_node.end_lineno or func_node.lineno
    lines = end_line - func_node.lineno + 1

    decorators: list[str] = []
    for dec in func_node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            decorators.append(ast.unparse(dec))
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)
            elif isinstance(dec.func, ast.Attribute):
                decorators.append(ast.unparse(dec.func))

    docstring = ast.get_docstring(func_node)
    first_line = docstring.split("\n")[0] if docstring else None

    return MethodReport(
        name=func_node.name,
        line=func_node.lineno,
        end_line=end_line,
        lines=lines,
        parameters=tuple(_extract_parameters(func_node)),
        cyclomatic_complexity=_cyclomatic_complexity(func_node),
        cognitive_complexity=_cognitive_complexity(func_node),
        nesting_depth=_nesting_depth(func_node),
        is_constructor=func_node.name == "__init__",
        docstring=first_line,
        decorators=tuple(decorators),
    )


class PythonParser(AbstractParser):
    """Parser for Python source files using the ``ast`` module.

    Extracts classes, methods, functions, parameters, attributes,
    imports, cyclomatic complexity, and nesting depth.
    """

    @property
    def language_name(self) -> str:
        """Return ``'python'``."""
        return "python"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return ``('.py', '.pyi')``."""
        return (".py", ".pyi")

    @property
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return ``('#',)``."""
        return ("#",)

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract class definitions using ``ast.parse``.

        Args:
            source: Python source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            logger.warning("Syntax error in %s, skipping class extraction", path)
            return []

        source_lines = source.splitlines()
        classes: list[ClassReport] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            methods = [
                _build_method_report(child, source_lines)
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]

            end_line = node.end_lineno or node.lineno
            base_classes = [ast.unparse(b) for b in node.bases]
            decorators = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    decorators.append(dec.id)
                elif isinstance(dec, ast.Attribute):
                    decorators.append(ast.unparse(dec))
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)

            docstring = ast.get_docstring(node)
            first_line = docstring.split("\n")[0] if docstring else None

            classes.append(
                ClassReport(
                    name=node.name,
                    line=node.lineno,
                    end_line=end_line,
                    lines=end_line - node.lineno + 1,
                    methods=tuple(methods),
                    attributes=tuple(_collect_attributes(node)),
                    base_classes=tuple(base_classes),
                    docstring=first_line,
                    decorators=tuple(decorators),
                )
            )

        return classes

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level functions (not methods inside classes).

        Args:
            source: Python source code.
            path: File path for error messages.

        Returns:
            List of ``MethodReport`` objects for module-level functions.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            logger.warning("Syntax error in %s, skipping function extraction", path)
            return []

        source_lines = source.splitlines()
        functions: list[MethodReport] = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(_build_method_report(node, source_lines))

        return functions

    def _detect_imports(self, source: str) -> list[str]:
        """Detect imported module names from the source.

        Args:
            source: Python source code.

        Returns:
            Sorted, deduplicated list of top-level module names.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])

        return sorted(modules)
