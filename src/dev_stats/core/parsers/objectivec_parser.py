"""Objective-C parser using regex for structural extraction."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from dev_stats.core.models import ClassReport, MethodReport, ParameterReport
from dev_stats.core.parsers.abstract_parser import AbstractParser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# ── @interface / @implementation detection ─────────────────────────────
_CLASS_RE = re.compile(
    r"^\s*@(?P<kind>interface|implementation)\s+"
    r"(?P<name>\w+)"
    r"(?:\s*\(\s*(?P<category>\w*)\s*\))?"
    r"(?:\s*:\s*(?P<base>\w+))?",
    re.MULTILINE,
)

# ── Method detection (-/+ instance/class methods) ─────────────────────
_METHOD_RE = re.compile(
    r"^\s*(?P<scope>[+-])\s*"
    r"\((?P<ret>[^)]+)\)\s*"
    r"(?P<selector>[^{;]+?)\s*\{",
    re.MULTILINE,
)

# ── #import / #include detection ──────────────────────────────────────
_IMPORT_RE = re.compile(
    r'^\s*#(?:import|include)\s+[<"](?P<header>[^>"]+)[>"]',
    re.MULTILINE,
)

# ── @protocol detection ──────────────────────────────────────────────
_PROTOCOL_RE = re.compile(
    r"^\s*@protocol\s+(?P<name>\w+)\s*(?:<[^>]*>)?\s*$",
    re.MULTILINE,
)

# ── CC branch tokens ─────────────────────────────────────────────────
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


def _line_number(source: str, pos: int) -> int:
    """Return the 1-based line number at character position *pos*.

    Args:
        source: Full source text.
        pos: Character offset.

    Returns:
        Line number (1-based).
    """
    return source[:pos].count("\n") + 1


def _parse_selector_params(selector: str) -> list[ParameterReport]:
    """Parse an Objective-C method selector into parameter reports.

    Handles selectors like ``initWithName:(NSString *)name age:(int)age``.

    Args:
        selector: The method selector string.

    Returns:
        List of ``ParameterReport`` objects.
    """
    params: list[ParameterReport] = []
    # Match each "label:(Type)name" segment
    param_re = re.compile(r"(\w+)\s*:\s*\(([^)]*)\)\s*(\w+)")
    for match in param_re.finditer(selector):
        type_ann = match.group(2).strip()
        name = match.group(3)
        params.append(ParameterReport(name=name, type_annotation=type_ann, has_default=False))
    return params


def _selector_name(selector: str) -> str:
    """Extract the method name from an Objective-C selector.

    For ``initWithName:(NSString *)name age:(int)age`` returns
    ``initWithName:age:``.  For ``dealloc`` returns ``dealloc``.

    Args:
        selector: The raw selector string.

    Returns:
        Canonical selector name.
    """
    parts: list[str] = []
    for token in re.split(r"\s*:\s*\([^)]*\)\s*\w+", selector):
        token = token.strip()
        if token:
            parts.append(token)
    colon_count = selector.count(":")
    if colon_count > 0:
        return ":".join(parts) + ":"
    return parts[0] if parts else selector.strip()


class ObjectiveCParser(AbstractParser):
    """Parser for Objective-C source files using regex extraction.

    Extracts ``@interface``/``@implementation`` classes, ``@protocol``
    declarations, instance/class methods, ``#import`` directives, and
    approximate cyclomatic complexity.
    """

    @property
    def language_name(self) -> str:
        """Return ``'objectivec'``."""
        return "objectivec"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return Objective-C extensions."""
        return (".m", ".mm")

    @property
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return ``('//',)``."""
        return ("//",)

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract @interface and @implementation definitions.

        Args:
            source: Objective-C source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects.
        """
        classes: list[ClassReport] = []
        seen: set[str] = set()

        for match in _CLASS_RE.finditer(source):
            name = match.group("name")
            category = match.group("category")
            # Include category in name if present
            full_name = f"{name}({category})" if category else name
            if full_name in seen:
                continue
            seen.add(full_name)

            base_classes: list[str] = []
            if match.group("base"):
                base_classes = [match.group("base")]

            # Find the @end for this class
            end_re = re.compile(r"^\s*@end\b", re.MULTILINE)
            end_match = end_re.search(source, match.end())
            class_body_end = end_match.start() if end_match else len(source)
            class_body = source[match.end() : class_body_end]

            methods = self._extract_methods_from_body(class_body, source, match.start())

            line = _line_number(source, match.start())
            end_line = _line_number(source, class_body_end)

            classes.append(
                ClassReport(
                    name=full_name,
                    line=line,
                    end_line=end_line,
                    lines=end_line - line + 1,
                    methods=tuple(methods),
                    base_classes=tuple(base_classes),
                )
            )

        # Also detect @protocol as classes
        for match in _PROTOCOL_RE.finditer(source):
            name = match.group("name")
            proto_name = f"{name} (protocol)"
            if proto_name in seen:
                continue
            seen.add(proto_name)

            end_re = re.compile(r"^\s*@end\b", re.MULTILINE)
            end_match = end_re.search(source, match.end())
            end_pos = end_match.start() if end_match else len(source)

            line = _line_number(source, match.start())
            end_line = _line_number(source, end_pos)

            classes.append(
                ClassReport(
                    name=proto_name,
                    line=line,
                    end_line=end_line,
                    lines=end_line - line + 1,
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
            body: Class body text (between @interface/@implementation and @end).
            full_source: Full source text (for line numbers).
            class_start: Character offset of the class in full_source.

        Returns:
            List of ``MethodReport`` objects.
        """
        methods: list[MethodReport] = []
        seen: set[str] = set()

        for match in _METHOD_RE.finditer(body):
            selector = match.group("selector").strip()
            name = _selector_name(selector)
            if name in seen:
                continue
            seen.add(name)

            params = _parse_selector_params(selector)
            method_body = _extract_body(body, match.end() - 1)
            cc = _approx_cc(method_body)
            line = _line_number(full_source, class_start) + _line_number(body, match.start())
            body_lines = method_body.count("\n") + 1

            is_init = name.startswith("init") or name == "dealloc"

            methods.append(
                MethodReport(
                    name=name,
                    line=line,
                    end_line=line + body_lines,
                    lines=body_lines,
                    parameters=tuple(params),
                    cyclomatic_complexity=cc,
                    is_constructor=is_init,
                )
            )

        return methods

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level C functions (outside @implementation blocks).

        Args:
            source: Objective-C source code.
            path: File path for error messages.

        Returns:
            List of ``MethodReport`` objects.
        """
        functions: list[MethodReport] = []

        # Determine class regions to exclude
        class_regions: list[tuple[int, int]] = []
        for match in _CLASS_RE.finditer(source):
            end_re = re.compile(r"^\s*@end\b", re.MULTILINE)
            end_match = end_re.search(source, match.end())
            end_pos = end_match.end() if end_match else len(source)
            class_regions.append((match.start(), end_pos))

        # Match C-style functions
        c_func_re = re.compile(
            r"^\s*(?:(?:static|inline|extern|const|unsigned|signed"
            r"|long|short|volatile|void|int|float|double|char|BOOL"
            r"|NSInteger|NSUInteger|CGFloat|id)\s+)+"
            r"(?P<name>\w+)\s*"
            r"\((?P<params>[^)]*)\)\s*\{",
            re.MULTILINE,
        )

        for match in c_func_re.finditer(source):
            if any(start <= match.start() <= end for start, end in class_regions):
                continue
            name = match.group("name")
            params_raw = match.group("params").strip()
            params: list[ParameterReport] = []
            if params_raw and params_raw != "void":
                for part in params_raw.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    tokens = part.split()
                    if len(tokens) >= 2:
                        pname = tokens[-1].lstrip("*&")
                        ptype = " ".join(tokens[:-1])
                    elif tokens:
                        pname = tokens[0].lstrip("*&")
                        ptype = ""
                    else:
                        continue
                    params.append(
                        ParameterReport(name=pname, type_annotation=ptype, has_default=False)
                    )

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
        """Detect ``#import`` and ``#include`` directives.

        Args:
            source: Objective-C source code.

        Returns:
            Sorted, deduplicated list of imported header names.
        """
        headers: set[str] = set()
        for match in _IMPORT_RE.finditer(source):
            header = match.group("header")
            base = header.split("/")[-1]
            name = base.split(".")[0] if "." in base else base
            headers.add(name)
        return sorted(headers)
