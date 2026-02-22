"""Go parser using regex for structural extraction."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from dev_stats.core.models import ClassReport, MethodReport, ParameterReport
from dev_stats.core.parsers.abstract_parser import AbstractParser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# ── Struct detection ────────────────────────────────────────────────────
_STRUCT_RE = re.compile(
    r"^\s*type\s+(?P<name>\w+)\s+struct\s*\{",
    re.MULTILINE,
)

# ── Interface detection ─────────────────────────────────────────────────
_INTERFACE_RE = re.compile(
    r"^\s*type\s+(?P<name>\w+)\s+interface\s*\{",
    re.MULTILINE,
)

# ── Top-level function detection ────────────────────────────────────────
_FUNC_RE = re.compile(
    r"^\s*func\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)",
    re.MULTILINE,
)

# ── Method detection (func with receiver) ───────────────────────────────
_METHOD_RE = re.compile(
    r"^\s*func\s+\(\s*(?P<recv>\w+)\s+\*?(?P<type>\w+)\s*\)\s+"
    r"(?P<name>\w+)\s*\((?P<params>[^)]*)\)",
    re.MULTILINE,
)

# ── Import detection ────────────────────────────────────────────────────
_IMPORT_SINGLE_RE = re.compile(
    r'^\s*import\s+"(?P<pkg>[^"]+)"',
    re.MULTILINE,
)
_IMPORT_BLOCK_RE = re.compile(
    r"^\s*import\s*\((?P<block>[^)]*)\)",
    re.MULTILINE | re.DOTALL,
)
_IMPORT_LINE_RE = re.compile(
    r'"(?P<pkg>[^"]+)"',
)

# ── CC branch tokens ───────────────────────────────────────────────────
_CC_PATTERN = re.compile(
    r"\b(?:if|else\s+if|for|case|select)\b"
    r"|&&|\|\|",
)


def _approx_cc(body: str) -> int:
    """Approximate cyclomatic complexity from a function body.

    Args:
        body: Source text of the function body.

    Returns:
        Estimated CC (minimum 1).
    """
    return 1 + len(_CC_PATTERN.findall(body))


def _extract_body(source: str, start: int) -> str:
    """Extract the brace-delimited body starting at *start*.

    Args:
        source: Full source text.
        start: Index of the opening brace.

    Returns:
        The text between matching braces (exclusive).
    """
    depth = 0
    i = start
    while i < len(source):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1 : i]
        i += 1
    return source[start + 1 :]


def _parse_params(raw: str) -> list[ParameterReport]:
    """Parse a Go parameter list string into reports.

    Args:
        raw: Comma-separated parameter declarations.

    Returns:
        List of ``ParameterReport`` objects.
    """
    params: list[ParameterReport] = []
    raw = raw.strip()
    if not raw:
        return params
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        if len(tokens) >= 2:
            name = tokens[0]
            annotation = " ".join(tokens[1:])
        elif tokens:
            # Might be just a type (grouped params like "a, b int")
            name = tokens[0]
            annotation = ""
        else:
            continue
        params.append(ParameterReport(name=name, type_annotation=annotation, has_default=False))
    return params


def _line_number(source: str, pos: int) -> int:
    """Return the 1-based line number at character position *pos*.

    Args:
        source: Full source text.
        pos: Character offset.

    Returns:
        Line number (1-based).
    """
    return source[:pos].count("\n") + 1


class GoParser(AbstractParser):
    """Parser for Go source files using regex extraction.

    Extracts structs, interfaces, functions, methods with receivers,
    parameters, imports, and approximate cyclomatic complexity.
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
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return ``('//',)``."""
        return ("//",)

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract struct and interface definitions.

        Args:
            source: Go source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects (structs and interfaces).
        """
        classes: list[ClassReport] = []
        seen: set[str] = set()

        # Extract structs
        for match in _STRUCT_RE.finditer(source):
            name = match.group("name")
            if name in seen:
                continue
            seen.add(name)

            body = _extract_body(source, match.end() - 1)

            # Find methods with this struct as receiver
            methods = self._find_methods_for_type(source, name)

            line = _line_number(source, match.start())
            end_pos = match.end() - 1 + len(body) + 2
            end_line = _line_number(source, min(end_pos, len(source) - 1))

            classes.append(
                ClassReport(
                    name=name,
                    line=line,
                    end_line=end_line,
                    lines=end_line - line + 1,
                    methods=tuple(methods),
                )
            )

        # Extract interfaces
        for match in _INTERFACE_RE.finditer(source):
            name = match.group("name")
            if name in seen:
                continue
            seen.add(name)

            body = _extract_body(source, match.end() - 1)
            line = _line_number(source, match.start())
            end_pos = match.end() - 1 + len(body) + 2
            end_line = _line_number(source, min(end_pos, len(source) - 1))

            classes.append(
                ClassReport(
                    name=name,
                    line=line,
                    end_line=end_line,
                    lines=end_line - line + 1,
                    decorators=("interface",),
                )
            )

        return classes

    def _find_methods_for_type(self, source: str, type_name: str) -> list[MethodReport]:
        """Find all methods with a receiver of the given type.

        Args:
            source: Full Go source code.
            type_name: Struct type name to match.

        Returns:
            List of ``MethodReport`` objects.
        """
        methods: list[MethodReport] = []

        for match in _METHOD_RE.finditer(source):
            if match.group("type") != type_name:
                continue
            name = match.group("name")
            params = _parse_params(match.group("params"))

            # Find the opening brace after the signature
            rest = source[match.end() :]
            brace_idx = rest.find("{")
            if brace_idx == -1:
                continue
            body = _extract_body(source, match.end() + brace_idx)
            cc = _approx_cc(body)
            line = _line_number(source, match.start())
            body_lines = body.count("\n") + 1

            methods.append(
                MethodReport(
                    name=name,
                    line=line,
                    end_line=line + body_lines,
                    lines=body_lines,
                    parameters=tuple(params),
                    cyclomatic_complexity=cc,
                )
            )

        return methods

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level functions (without receivers).

        Args:
            source: Go source code.
            path: File path for error messages.

        Returns:
            List of ``MethodReport`` objects.
        """
        functions: list[MethodReport] = []

        # Collect method positions to exclude
        method_positions: set[int] = set()
        for match in _METHOD_RE.finditer(source):
            method_positions.add(match.start())

        for match in _FUNC_RE.finditer(source):
            # Skip if this is actually a method with receiver
            if match.start() in method_positions:
                continue
            # Skip init and main if desired, but include them for counting
            name = match.group("name")
            params = _parse_params(match.group("params"))

            # Find the opening brace
            rest = source[match.end() :]
            brace_idx = rest.find("{")
            if brace_idx == -1:
                continue
            body = _extract_body(source, match.end() + brace_idx)
            cc = _approx_cc(body)
            line = _line_number(source, match.start())
            body_lines = body.count("\n") + 1

            functions.append(
                MethodReport(
                    name=name,
                    line=line,
                    end_line=line + body_lines,
                    lines=body_lines,
                    parameters=tuple(params),
                    cyclomatic_complexity=cc,
                )
            )

        return functions

    def _detect_imports(self, source: str) -> list[str]:
        """Detect imported package names from ``import`` statements.

        Args:
            source: Go source code.

        Returns:
            Sorted, deduplicated list of package names.
        """
        modules: set[str] = set()

        # Single imports
        for match in _IMPORT_SINGLE_RE.finditer(source):
            pkg = match.group("pkg")
            modules.add(pkg.split("/")[-1])

        # Import blocks
        for match in _IMPORT_BLOCK_RE.finditer(source):
            block = match.group("block")
            for line_match in _IMPORT_LINE_RE.finditer(block):
                pkg = line_match.group("pkg")
                modules.add(pkg.split("/")[-1])

        return sorted(modules)
