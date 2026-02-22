"""JavaScript parser using regex for structural extraction."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from dev_stats.core.models import ClassReport, MethodReport, ParameterReport
from dev_stats.core.parsers.abstract_parser import AbstractParser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# ── Class detection ─────────────────────────────────────────────────────
_CLASS_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?class\s+"
    r"(?P<name>\w+)"
    r"(?:\s+extends\s+(?P<base>\w+))?"
    r"\s*\{",
    re.MULTILINE,
)

# ── Method inside class body ────────────────────────────────────────────
_METHOD_RE = re.compile(
    r"^\s*(?:(?:async|static|get|set)\s+)*"
    r"(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*\{",
    re.MULTILINE,
)

# ── Top-level function ──────────────────────────────────────────────────
_FUNCTION_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+"
    r"(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*\{",
    re.MULTILINE,
)

# ── Arrow function assigned to const/let/var ────────────────────────────
_ARROW_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+"
    r"(?P<name>\w+)\s*=\s*(?:async\s+)?"
    r"(?:\([^)]*\)|[^=])\s*=>\s*[\{(]?",
    re.MULTILINE,
)

# ── Import detection ────────────────────────────────────────────────────
_IMPORT_RE = re.compile(
    r"^\s*import\s+.*?from\s+['\"](?P<mod>[^'\"]+)['\"]",
    re.MULTILINE,
)
_REQUIRE_RE = re.compile(
    r"""require\s*\(\s*['"](?P<mod>[^'"]+)['"]\s*\)""",
)

# ── CC branch tokens ───────────────────────────────────────────────────
_CC_PATTERN = re.compile(
    r"\b(?:if|else\s+if|for|while|case|catch)\b"
    r"|\?\s*[^:]*\s*:"
    r"|&&|\|\|",
)


def _approx_cc(body: str) -> int:
    """Approximate cyclomatic complexity from a method body.

    Args:
        body: Source text of the method body.

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
    """Parse a JS parameter list string into reports.

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
        has_default = "=" in part
        name = part.split("=")[0].strip()
        # Handle destructuring
        if name.startswith("{") or name.startswith("["):
            name = name.strip("{}[] ")
        # Handle rest params
        name = name.lstrip(".")
        params.append(ParameterReport(name=name, type_annotation="", has_default=has_default))
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


class JavaScriptParser(AbstractParser):
    """Parser for JavaScript source files using regex extraction.

    Extracts classes, methods, functions, parameters, imports/requires,
    and approximate cyclomatic complexity.
    """

    @property
    def language_name(self) -> str:
        """Return ``'javascript'``."""
        return "javascript"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return ``('.js', '.jsx', '.mjs', '.cjs')``."""
        return (".js", ".jsx", ".mjs", ".cjs")

    @property
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return ``('//',)``."""
        return ("//",)

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract ES6 class definitions.

        Args:
            source: JavaScript source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects.
        """
        classes: list[ClassReport] = []

        for match in _CLASS_RE.finditer(source):
            name = match.group("name")
            base_classes: list[str] = []
            if match.group("base"):
                base_classes.append(match.group("base"))

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
        """Extract methods from a class body.

        Args:
            body: Class body text.
            full_source: Full source text (for line numbers).
            class_start: Character offset of the class in full_source.

        Returns:
            List of ``MethodReport`` objects.
        """
        methods: list[MethodReport] = []
        seen: set[str] = set()

        for match in _METHOD_RE.finditer(body):
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
        """Extract top-level function declarations.

        Args:
            source: JavaScript source code.
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
        """Detect imported module names from import/require statements.

        Args:
            source: JavaScript source code.

        Returns:
            Sorted, deduplicated list of module names.
        """
        modules: set[str] = set()
        for match in _IMPORT_RE.finditer(source):
            mod = match.group("mod")
            modules.add(mod.split("/")[0])
        for match in _REQUIRE_RE.finditer(source):
            mod = match.group("mod")
            modules.add(mod.split("/")[0])
        return sorted(modules)
