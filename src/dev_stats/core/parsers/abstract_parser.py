"""Abstract base class for language parsers with shared utilities."""

from __future__ import annotations

import abc
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.core.models import ClassReport, FileReport, MethodReport

logger = logging.getLogger(__name__)

_TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX|BUG)\b", re.IGNORECASE)


@dataclass(frozen=True)
class RawLOCCounts:
    """Raw line-of-code counts produced by :func:`count_loc`.

    Attributes:
        total: Total number of lines.
        code: Non-blank, non-comment lines.
        comment: Comment-only lines.
        blank: Blank lines.
    """

    total: int
    code: int
    comment: int
    blank: int


def count_loc(source: str, comment_prefixes: tuple[str, ...] = ("#",)) -> RawLOCCounts:
    """Count lines of code, comments, and blanks in *source*.

    Args:
        source: Full file contents as a string.
        comment_prefixes: Tuple of line-comment prefix strings.

    Returns:
        A frozen ``RawLOCCounts`` with the tallies.
    """
    lines = source.splitlines()
    total = len(lines)
    blank = 0
    comment = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif any(stripped.startswith(p) for p in comment_prefixes):
            comment += 1
    code = total - blank - comment
    return RawLOCCounts(total=total, code=code, comment=comment, blank=blank)


def count_todos(source: str) -> int:
    """Count TODO/FIXME/HACK/XXX/BUG markers in *source*.

    Args:
        source: Full file contents.

    Returns:
        Number of marker occurrences.
    """
    return len(_TODO_PATTERN.findall(source))


def detect_encoding(path: Path) -> str:
    """Detect the encoding of a file, falling back to UTF-8.

    Args:
        path: Path to the file.

    Returns:
        The detected encoding name.
    """
    try:
        path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "latin-1"
    except OSError:
        return "utf-8"
    return "utf-8"


class AbstractParser(abc.ABC):
    """Template-method base class for all language parsers.

    Subclasses must implement :attr:`language_name`, :attr:`supported_extensions`,
    and the extraction hooks :meth:`_extract_classes`, :meth:`_extract_functions`,
    and :meth:`_detect_imports`.

    The :meth:`parse` template method reads the file, counts lines, delegates
    to hooks, and assembles the final :class:`FileReport`.
    """

    @property
    @abc.abstractmethod
    def language_name(self) -> str:
        """Return the canonical lowercase language name."""

    @property
    @abc.abstractmethod
    def supported_extensions(self) -> tuple[str, ...]:
        """Return file extensions handled by this parser (e.g. ``('.py',)``)."""

    @property
    def comment_prefixes(self) -> tuple[str, ...]:
        """Return comment-line prefixes for this language.

        Defaults to ``('#',)``.  Override for languages with different
        comment syntax.
        """
        return ("#",)

    # Keep backward-compatible aliases used by ParserRegistry / Dispatcher.
    @property
    def language(self) -> str:
        """Alias for :attr:`language_name`."""
        return self.language_name

    @property
    def extensions(self) -> tuple[str, ...]:
        """Alias for :attr:`supported_extensions`."""
        return self.supported_extensions

    def can_parse(self, path: Path) -> bool:
        """Return whether this parser can handle *path*.

        Args:
            path: File path to check.

        Returns:
            ``True`` if the file's suffix is in :attr:`supported_extensions`.
        """
        return path.suffix in self.supported_extensions

    def parse(self, path: Path, repo_root: Path) -> FileReport:
        """Template method: read file, count LOC, extract structure.

        Args:
            path: Absolute path to the source file.
            repo_root: Repository root for computing relative paths.

        Returns:
            A frozen :class:`FileReport`.
        """
        from dev_stats.core.models import FileReport

        encoding = detect_encoding(path)
        try:
            source = path.read_text(encoding=encoding, errors="replace")
        except OSError:
            logger.warning("Could not read file: %s", path)
            return FileReport(
                path=path.relative_to(repo_root),
                language=self.language_name,
                total_lines=0,
                code_lines=0,
                blank_lines=0,
                comment_lines=0,
            )

        loc = count_loc(source, self.comment_prefixes)
        classes = self._extract_classes(source, path)
        functions = self._extract_functions(source, path)
        imports = self._detect_imports(source)

        return FileReport(
            path=path.relative_to(repo_root),
            language=self.language_name,
            total_lines=loc.total,
            code_lines=loc.code,
            blank_lines=loc.blank,
            comment_lines=loc.comment,
            classes=tuple(classes),
            functions=tuple(functions),
            imports=tuple(imports),
        )

    @abc.abstractmethod
    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Extract class definitions from *source*.

        Args:
            source: Full file contents.
            path: Absolute path (for error messages).

        Returns:
            A list of :class:`ClassReport` objects.
        """

    @abc.abstractmethod
    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Extract top-level functions from *source*.

        Args:
            source: Full file contents.
            path: Absolute path (for error messages).

        Returns:
            A list of :class:`MethodReport` objects.
        """

    @abc.abstractmethod
    def _detect_imports(self, source: str) -> list[str]:
        """Detect import statements in *source*.

        Args:
            source: Full file contents.

        Returns:
            A sorted, deduplicated list of imported module names.
        """
