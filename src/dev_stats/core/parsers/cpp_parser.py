"""C/C++ parser using regex for structural extraction."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from dev_stats.core.models import ClassReport, MethodReport, ParameterReport
from dev_stats.core.parsers.abstract_parser import AbstractParser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# ── Class / struct detection ────────────────────────────────────────────
_CLASS_RE = re.compile(
    r"^\s*(?:template\s*<[^>]*>\s*)?"
    r"(?P<kind>class|struct)\s+"
    r"(?P<name>\w+)"
    r"(?:\s*:\s*(?:public|protected|private)?\s*(?P<base>[\w:,\s]+))?"
    r"\s*\{",
    re.MULTILINE,
)

# ── Function / method detection (top-level or inside class body) ────────
_FUNCTION_RE = re.compile(
    r"^\s*(?:(?:static|inline|virtual|explicit|extern|constexpr|const"
    r"|unsigned|signed|long|short|volatile)\s+)*"
    r"(?P<ret>[\w:*&<>\[\]\s]+?)\s+"
    r"(?P<name>(?:operator\s*[^\s(]+|\~?\w+))\s*"
    r"\((?P<params>[^)]*)\)\s*"
    r"(?:const\s*)?"
    r"(?:override\s*)?"
    r"(?:noexcept\s*)?"
    r"(?:->[\w:*&<>\s]+?)?\s*\{",
    re.MULTILINE,
)

# ── Include detection ───────────────────────────────────────────────────
_INCLUDE_RE = re.compile(
    r'^\s*#include\s+[<"](?P<header>[^>"]+)[>"]',
    re.MULTILINE,
)

# ── CC branch tokens ───────────────────────────────────────────────────
_CC_PATTERN = re.compile(
    r"\b(?:if|else\s+if|for|while|case|catch)\b"
    r"|\?\s*[^:]*\s*:"
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
    """Parse a C++ parameter list string into reports.

    Args:
        raw: Comma-separated parameter declarations.

    Returns:
        List of ``ParameterReport`` objects.
    """
    params: list[ParameterReport] = []
    raw = raw.strip()
    if not raw or raw == "void":
        return params
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        has_default = "=" in part
        decl = part.split("=")[0].strip()
        tokens = decl.split()
        if len(tokens) >= 2:
            name = tokens[-1].lstrip("*&")
            annotation = " ".join(tokens[:-1])
        elif tokens:
            name = tokens[0].lstrip("*&")
            annotation = ""
        else:
            continue
        params.append(
            ParameterReport(name=name, type_annotation=annotation, has_default=has_default)
        )
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


class CppParser(AbstractParser):
    """Parser for C/C++ source files using regex extraction.

    Extracts classes, structs, functions, methods, parameters,
    ``#include`` directives, and approximate cyclomatic complexity.
    """

    @property
    def language_name(self) -> str:
        """Return ``'cpp'``."""
        return "cpp"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return C/C++ extensions."""
        return (".cpp", ".cxx", ".cc", ".c", ".hpp", ".hxx", ".h", ".hh")

    @property
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return ``('//',)``."""
        return ("//",)

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract class and struct definitions.

        Args:
            source: C++ source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects.
        """
        classes: list[ClassReport] = []
        seen: set[str] = set()

        for match in _CLASS_RE.finditer(source):
            name = match.group("name")
            if name in seen:
                continue
            seen.add(name)

            base_classes: list[str] = []
            if match.group("base"):
                base_classes = [b.strip() for b in match.group("base").split(",") if b.strip()]

            body = _extract_body(source, match.end() - 1)
            methods = self._extract_methods_from_body(body, source, match.start())

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

        return classes

    def _extract_methods_from_body(
        self,
        body: str,
        full_source: str,
        class_start: int,
    ) -> list[MethodReport]:
        """Extract methods from a class/struct body.

        Args:
            body: Class body text.
            full_source: Full source text (for line numbers).
            class_start: Character offset of the class in full_source.

        Returns:
            List of ``MethodReport`` objects.
        """
        methods: list[MethodReport] = []
        seen: set[str] = set()

        for match in _FUNCTION_RE.finditer(body):
            name = match.group("name")
            if name in seen:
                continue
            seen.add(name)

            params = _parse_params(match.group("params"))
            method_body = _extract_body(body, match.end() - 1)
            cc = _approx_cc(method_body)
            line = _line_number(full_source, class_start) + _line_number(body, match.start())
            body_lines = method_body.count("\n") + 1

            # Constructor detection: name matches class name or is ~destructor
            is_constructor = name.startswith("~") or (match.group("ret").strip() == "")

            methods.append(
                MethodReport(
                    name=name,
                    line=line,
                    end_line=line + body_lines,
                    lines=body_lines,
                    parameters=tuple(params),
                    cyclomatic_complexity=cc,
                    is_constructor=is_constructor,
                )
            )

        return methods

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level function definitions (outside classes).

        Args:
            source: C++ source code.
            path: File path for error messages.

        Returns:
            List of ``MethodReport`` objects.
        """
        functions: list[MethodReport] = []

        # Determine class regions to exclude
        class_regions: list[tuple[int, int]] = []
        for match in _CLASS_RE.finditer(source):
            body = _extract_body(source, match.end() - 1)
            class_regions.append((match.start(), match.end() + len(body) + 1))

        for match in _FUNCTION_RE.finditer(source):
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

    def _detect_imports(self, source: str) -> list[str]:
        """Detect ``#include`` directives.

        Args:
            source: C++ source code.

        Returns:
            Sorted, deduplicated list of included header names.
        """
        headers: set[str] = set()
        for match in _INCLUDE_RE.finditer(source):
            header = match.group("header")
            # Normalize: strip path, take base name without extension
            base = header.split("/")[-1]
            name = base.split(".")[0] if "." in base else base
            headers.add(name)
        return sorted(headers)
