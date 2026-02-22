"""C# parser using regex for structural extraction."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from dev_stats.core.models import ClassReport, MethodReport, ParameterReport
from dev_stats.core.parsers.abstract_parser import AbstractParser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# ── Class / interface / struct / enum detection ─────────────────────────
_CLASS_RE = re.compile(
    r"^\s*(?:(?:public|protected|private|internal|abstract|sealed|static|partial)\s+)*"
    r"(?P<kind>class|interface|struct|enum)\s+"
    r"(?P<name>\w+)"
    r"(?:\s*<[^>]*>)?"
    r"(?:\s*:\s*(?P<base>[\w<>.,\s]+))?"
    r"\s*\{",
    re.MULTILINE,
)

# ── Method detection ────────────────────────────────────────────────────
_METHOD_RE = re.compile(
    r"^\s*(?:(?:public|protected|private|internal|static|virtual|override"
    r"|abstract|sealed|async|new|extern|partial)\s+)*"
    r"(?P<ret>[\w<>\[\].,?\s]+?)\s+"
    r"(?P<name>\w+)\s*"
    r"\((?P<params>[^)]*)\)\s*\{",
    re.MULTILINE,
)

# ── Constructor detection ───────────────────────────────────────────────
_CONSTRUCTOR_RE = re.compile(
    r"^\s*(?:(?:public|protected|private|internal|static)\s+)?"
    r"(?P<name>[A-Z]\w*)\s*"
    r"\((?P<params>[^)]*)\)\s*"
    r"(?::\s*(?:base|this)\s*\([^)]*\)\s*)?"
    r"\{",
    re.MULTILINE,
)

# ── Using detection ─────────────────────────────────────────────────────
_USING_RE = re.compile(
    r"^\s*using\s+(?:static\s+)?(?P<ns>[\w.]+)\s*;",
    re.MULTILINE,
)

# ── CC branch tokens ───────────────────────────────────────────────────
_CC_PATTERN = re.compile(
    r"\b(?:if|else\s+if|for|foreach|while|case|catch)\b"
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
    """Parse a C# parameter list string into reports.

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
        # Remove parameter modifiers
        part = re.sub(r"^\s*(?:ref|out|in|params|this)\s+", "", part)
        has_default = "=" in part
        decl = part.split("=")[0].strip()
        tokens = decl.split()
        if len(tokens) >= 2:
            name = tokens[-1]
            annotation = " ".join(tokens[:-1])
        elif tokens:
            name = tokens[0]
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


class CSharpParser(AbstractParser):
    """Parser for C# source files using regex extraction.

    Extracts classes, interfaces, structs, enums, methods, constructors,
    parameters, ``using`` directives, and approximate cyclomatic complexity.
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
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return ``('//',)``."""
        return ("//",)

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract class, interface, struct, and enum definitions.

        Args:
            source: C# source code.
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
            methods = self._extract_methods_from_body(body, name, source, match.start())

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
        class_name: str,
        full_source: str,
        class_start: int,
    ) -> list[MethodReport]:
        """Extract methods and constructors from a class body.

        Args:
            body: Class body text.
            class_name: Name of the enclosing class.
            full_source: Full source text (for line numbers).
            class_start: Character offset of the class in full_source.

        Returns:
            List of ``MethodReport`` objects.
        """
        methods: list[MethodReport] = []
        seen: set[str] = set()

        # Find constructors
        for match in _CONSTRUCTOR_RE.finditer(body):
            cname = match.group("name")
            if cname != class_name:
                continue
            if cname in seen:
                continue
            seen.add(f"__ctor__{cname}")

            params = _parse_params(match.group("params"))
            method_body = _extract_body(body, match.end() - 1)
            cc = _approx_cc(method_body)
            line = _line_number(full_source, class_start) + _line_number(body, match.start())
            body_lines = method_body.count("\n") + 1

            methods.append(
                MethodReport(
                    name=class_name,
                    line=line,
                    end_line=line + body_lines,
                    lines=body_lines,
                    parameters=tuple(params),
                    cyclomatic_complexity=cc,
                    is_constructor=True,
                )
            )

        # Find regular methods
        for match in _METHOD_RE.finditer(body):
            name = match.group("name")
            if name == class_name:
                continue
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
                    is_constructor=False,
                )
            )

        return methods

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Return empty list (C# has no top-level functions).

        Args:
            source: C# source code.
            path: File path.

        Returns:
            Empty list.
        """
        return []

    def _detect_imports(self, source: str) -> list[str]:
        """Detect ``using`` namespace directives.

        Args:
            source: C# source code.

        Returns:
            Sorted, deduplicated list of top-level namespace names.
        """
        modules: set[str] = set()
        for match in _USING_RE.finditer(source):
            ns = match.group("ns")
            modules.add(ns.split(".")[0])
        return sorted(modules)
