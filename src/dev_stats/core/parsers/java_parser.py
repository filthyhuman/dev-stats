"""Java parser using regex for structural extraction."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from dev_stats.core.models import ClassReport, MethodReport, ParameterReport
from dev_stats.core.parsers.abstract_parser import AbstractParser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# ── Class / interface / enum detection ──────────────────────────────────
_CLASS_RE = re.compile(
    r"^\s*(?:(?:public|protected|private|abstract|static|final|strictfp)\s+)*"
    r"(?P<kind>class|interface|enum)\s+"
    r"(?P<name>\w+)"
    r"(?:\s*<[^>]*>)?"
    r"(?:\s+extends\s+(?P<base>[\w.<>,\s]+))?"
    r"(?:\s+implements\s+(?P<ifaces>[\w.<>,\s]+))?"
    r"\s*\{",
    re.MULTILINE,
)

# ── Method detection ────────────────────────────────────────────────────
_METHOD_RE = re.compile(
    r"^\s*(?:(?:public|protected|private|static|final|abstract|synchronized|native"
    r"|default|strictfp|@\w+)\s+)*"
    r"(?P<ret>[\w<>\[\].,?\s]+?)\s+"
    r"(?P<name>\w+)\s*"
    r"\((?P<params>[^)]*)\)\s*"
    r"(?:throws\s+[\w.,\s]+)?\s*\{",
    re.MULTILINE,
)

# ── Constructor detection ───────────────────────────────────────────────
_CONSTRUCTOR_RE = re.compile(
    r"^\s*(?:(?:public|protected|private)\s+)?"
    r"(?P<name>[A-Z]\w*)\s*"
    r"\((?P<params>[^)]*)\)\s*"
    r"(?:throws\s+[\w.,\s]+)?\s*\{",
    re.MULTILINE,
)

# ── Import detection ────────────────────────────────────────────────────
_IMPORT_RE = re.compile(
    r"^\s*import\s+(?:static\s+)?(?P<pkg>[\w.]+)\s*;",
    re.MULTILINE,
)

# ── CC branch tokens ───────────────────────────────────────────────────
_CC_PATTERN = re.compile(
    r"\b(?:if|else\s+if|for|while|case|catch|\?\s*[^:]*\s*:)\b"
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
        The text between the matching braces (exclusive).
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
    """Parse a Java parameter list string into reports.

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
        # Remove annotations like @NonNull
        part = re.sub(r"@\w+\s*", "", part).strip()
        # Remove final keyword
        part = re.sub(r"\bfinal\s+", "", part).strip()
        tokens = part.split()
        if len(tokens) >= 2:
            name = tokens[-1]
            annotation = " ".join(tokens[:-1])
        else:
            name = tokens[0] if tokens else part
            annotation = ""
        # Handle varargs
        name = name.replace("...", "")
        annotation = annotation.replace("...", "")
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


class JavaParser(AbstractParser):
    """Parser for Java source files using regex extraction.

    Extracts classes, interfaces, enums, methods, constructors,
    parameters, imports, and approximate cyclomatic complexity.
    """

    @property
    def language_name(self) -> str:
        """Return ``'java'``."""
        return "java"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return ``('.java',)``."""
        return (".java",)

    @property
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return ``('//',)``."""
        return ("//",)

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract class, interface, and enum definitions.

        Args:
            source: Java source code.
            path: File path for error messages.

        Returns:
            List of ``ClassReport`` objects.
        """
        classes: list[ClassReport] = []
        class_names: set[str] = set()

        for match in _CLASS_RE.finditer(source):
            name = match.group("name")
            if name in class_names:
                continue
            class_names.add(name)

            base_classes: list[str] = []
            if match.group("base"):
                base_classes.extend(b.strip() for b in match.group("base").split(",") if b.strip())
            if match.group("ifaces"):
                base_classes.extend(
                    b.strip() for b in match.group("ifaces").split(",") if b.strip()
                )

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
            seen.add(f"__init__{cname}")

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
            key = name
            if key in seen:
                continue
            seen.add(key)

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
        """Return empty list (Java has no top-level functions).

        Args:
            source: Java source code.
            path: File path.

        Returns:
            Empty list.
        """
        return []

    def _detect_imports(self, source: str) -> list[str]:
        """Detect imported package names from ``import`` statements.

        Args:
            source: Java source code.

        Returns:
            Sorted, deduplicated list of top-level package names.
        """
        modules: set[str] = set()
        for match in _IMPORT_RE.finditer(source):
            pkg = match.group("pkg")
            modules.add(pkg.split(".")[0])
        return sorted(modules)
