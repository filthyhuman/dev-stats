"""TypeScript parser extending JavaScript parser with TS-specific constructs."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from dev_stats.core.models import ClassReport, MethodReport
from dev_stats.core.parsers.javascript_parser import (
    JavaScriptParser,
    _approx_cc,
    _parse_params,
)

if TYPE_CHECKING:
    from pathlib import Path

# ── TS class detection (handles implements) ─────────────────────────────
_TS_CLASS_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+"
    r"(?P<name>\w+)"
    r"(?:\s*<[^>]*>)?"
    r"(?:\s+extends\s+(?P<base>\w+))?"
    r"(?:\s+implements\s+(?P<ifaces>[\w,\s]+))?"
    r"\s*\{",
    re.MULTILINE,
)

# ── TS method detection (allows return type annotations) ────────────────
_TS_METHOD_RE = re.compile(
    r"^\s*(?:(?:async|static|get|set|public|private|protected|readonly|abstract)\s+)*"
    r"(?P<name>\w+)\s*\((?P<params>[^)]*)\)"
    r"(?:\s*:\s*[^{]+?)?\s*\{",
    re.MULTILINE,
)

# ── TS function detection (allows return type annotations) ──────────────
_TS_FUNCTION_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+"
    r"(?P<name>\w+)\s*\((?P<params>[^)]*)\)"
    r"(?:\s*:\s*[^{]+?)?\s*\{",
    re.MULTILINE,
)

# ── Interface detection ─────────────────────────────────────────────────
_INTERFACE_RE = re.compile(
    r"^\s*(?:export\s+)?interface\s+"
    r"(?P<name>\w+)"
    r"(?:\s+extends\s+(?P<base>[\w,\s]+))?"
    r"\s*\{",
    re.MULTILINE,
)

# ── Enum detection ──────────────────────────────────────────────────────
_ENUM_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const\s+)?enum\s+"
    r"(?P<name>\w+)\s*\{",
    re.MULTILINE,
)


def _line_number(source: str, pos: int) -> int:
    """Return the 1-based line number at character position *pos*.

    Args:
        source: Full source text.
        pos: Character offset.

    Returns:
        Line number (1-based).
    """
    return source[:pos].count("\n") + 1


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


class TypeScriptParser(JavaScriptParser):
    """Parser for TypeScript source files.

    Extends :class:`JavaScriptParser` with interface, enum, type annotation,
    and ``implements`` support.
    """

    @property
    def language_name(self) -> str:
        """Return ``'typescript'``."""
        return "typescript"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return ``('.ts', '.tsx')``."""
        return (".ts", ".tsx")

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract classes (with implements), interfaces, and enums.

        Args:
            source: TypeScript source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects.
        """
        classes: list[ClassReport] = []
        seen_names: set[str] = set()

        # Extract classes using TS-aware regex
        for match in _TS_CLASS_RE.finditer(source):
            name = match.group("name")
            if name in seen_names:
                continue
            seen_names.add(name)

            base_classes: list[str] = []
            if match.group("base"):
                base_classes.append(match.group("base"))
            if match.group("ifaces"):
                base_classes.extend(
                    b.strip() for b in match.group("ifaces").split(",") if b.strip()
                )

            body = _extract_body(source, match.end() - 1)
            methods = self._extract_ts_methods_from_body(body, source, match.start())

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
                    base_classes=tuple(base_classes),
                )
            )

        # Extract interfaces
        for match in _INTERFACE_RE.finditer(source):
            name = match.group("name")
            if name in seen_names:
                continue
            seen_names.add(name)

            iface_bases: list[str] = []
            if match.group("base"):
                iface_bases = [b.strip() for b in match.group("base").split(",") if b.strip()]

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
                    base_classes=tuple(iface_bases),
                    decorators=("interface",),
                )
            )

        # Extract enums
        for match in _ENUM_RE.finditer(source):
            name = match.group("name")
            if name in seen_names:
                continue
            seen_names.add(name)

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
                    decorators=("enum",),
                )
            )

        return classes

    def _extract_ts_methods_from_body(
        self,
        body: str,
        full_source: str,
        class_start: int,
    ) -> list[MethodReport]:
        """Extract methods from a TS class body (handles type annotations).

        Args:
            body: Class body text.
            full_source: Full source text (for line numbers).
            class_start: Character offset of the class in full_source.

        Returns:
            List of ``MethodReport`` objects.
        """
        methods: list[MethodReport] = []
        seen: set[str] = set()

        for match in _TS_METHOD_RE.finditer(body):
            name = match.group("name")
            if name in seen:
                continue
            seen.add(name)

            params = _parse_params(match.group("params"))
            method_body = _extract_body(body, match.end() - 1)
            cc = _approx_cc(method_body)
            line = _line_number(full_source, class_start) + _line_number(body, match.start())
            body_lines = method_body.count("\n") + 1

            methods.append(
                MethodReport(
                    name=name,
                    line=line,
                    end_line=line + body_lines,
                    lines=body_lines,
                    parameters=tuple(params),
                    cyclomatic_complexity=cc,
                    is_constructor=name == "constructor",
                )
            )

        return methods

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level function declarations (handles type annotations).

        Args:
            source: TypeScript source code.
            path: File path for error messages.

        Returns:
            List of ``MethodReport`` objects.
        """
        functions: list[MethodReport] = []

        # Determine class regions to exclude
        class_regions: list[tuple[int, int]] = []
        for match in _TS_CLASS_RE.finditer(source):
            body = _extract_body(source, match.end() - 1)
            class_regions.append((match.start(), match.end() + len(body) + 1))

        for match in _TS_FUNCTION_RE.finditer(source):
            if any(start <= match.start() <= end for start, end in class_regions):
                continue
            name = match.group("name")
            params = _parse_params(match.group("params"))
            body = _extract_body(source, match.end() - 1)
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
