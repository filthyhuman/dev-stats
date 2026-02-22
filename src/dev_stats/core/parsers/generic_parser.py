"""Generic parser with a broad extension map for line counting."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dev_stats.core.parsers.abstract_parser import AbstractParser

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.core.models import ClassReport, FileReport, MethodReport

# (language_name, comment_prefixes)
_EXT_MAP: dict[str, tuple[str, tuple[str, ...]]] = {
    ".sh": ("shell", ("#",)),
    ".bash": ("shell", ("#",)),
    ".zsh": ("shell", ("#",)),
    ".rb": ("ruby", ("#",)),
    ".pl": ("perl", ("#",)),
    ".pm": ("perl", ("#",)),
    ".r": ("r", ("#",)),
    ".R": ("r", ("#",)),
    ".yml": ("yaml", ("#",)),
    ".yaml": ("yaml", ("#",)),
    ".toml": ("toml", ("#",)),
    ".ini": ("ini", (";", "#")),
    ".cfg": ("ini", (";", "#")),
    ".conf": ("config", ("#",)),
    ".properties": ("properties", ("#",)),
    ".makefile": ("makefile", ("#",)),
    ".mk": ("makefile", ("#",)),
    ".cmake": ("cmake", ("#",)),
    ".dockerfile": ("dockerfile", ("#",)),
    ".tf": ("terraform", ("#",)),
    ".sql": ("sql", ("--",)),
    ".lua": ("lua", ("--",)),
    ".hs": ("haskell", ("--",)),
    ".elm": ("elm", ("--",)),
    ".erl": ("erlang", ("%",)),
    ".ex": ("elixir", ("#",)),
    ".exs": ("elixir", ("#",)),
    ".clj": ("clojure", (";",)),
    ".lisp": ("lisp", (";",)),
    ".scm": ("scheme", (";",)),
    ".m": ("matlab", ("%",)),
    ".f90": ("fortran", ("!",)),
    ".f95": ("fortran", ("!",)),
    ".html": ("html", ()),
    ".htm": ("html", ()),
    ".xml": ("xml", ()),
    ".css": ("css", ()),
    ".scss": ("scss", ()),
    ".less": ("less", ()),
    ".json": ("json", ()),
    ".md": ("markdown", ()),
    ".rst": ("restructuredtext", ()),
    ".txt": ("text", ()),
    ".csv": ("csv", ()),
    ".svg": ("svg", ()),
    ".proto": ("protobuf", ("//",)),
    ".gradle": ("gradle", ("//",)),
    ".swift": ("swift", ("//",)),
    ".kt": ("kotlin", ("//",)),
    ".kts": ("kotlin", ("//",)),
    ".scala": ("scala", ("//",)),
    ".groovy": ("groovy", ("//",)),
    ".dart": ("dart", ("//",)),
    ".v": ("v", ("//",)),
    ".zig": ("zig", ("//",)),
    ".nim": ("nim", ("#",)),
    ".jl": ("julia", ("#",)),
}


class GenericParser(AbstractParser):
    """Fallback parser that counts lines for any file type.

    Uses ``_EXT_MAP`` to detect language and comment prefixes from the
    file extension.  No structural analysis is performed.
    """

    @property
    def language_name(self) -> str:
        """Return ``'generic'`` (overridden per-file in :meth:`parse`)."""
        return "generic"

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return an empty tuple (this parser accepts anything via :meth:`can_parse`)."""
        return ()

    def can_parse(self, path: Path) -> bool:
        """Return ``True`` for any file (this is the fallback parser).

        Args:
            path: File path.

        Returns:
            Always ``True``.
        """
        return True

    def parse(self, path: Path, repo_root: Path) -> FileReport:
        """Parse a file using extension-based language detection.

        Args:
            path: Absolute path to the file.
            repo_root: Repository root for relative paths.

        Returns:
            A :class:`FileReport` with line counts and detected language.
        """
        from dev_stats.core.models import FileReport
        from dev_stats.core.parsers.abstract_parser import RawLOCCounts, count_loc, detect_encoding

        lang, prefixes = self._lookup(path)
        encoding = detect_encoding(path)
        try:
            source = path.read_text(encoding=encoding, errors="replace")
        except OSError:
            return FileReport(
                path=path.relative_to(repo_root),
                language=lang,
                total_lines=0,
                code_lines=0,
                blank_lines=0,
                comment_lines=0,
            )

        loc: RawLOCCounts = count_loc(source, prefixes)
        return FileReport(
            path=path.relative_to(repo_root),
            language=lang,
            total_lines=loc.total,
            code_lines=loc.code,
            blank_lines=loc.blank,
            comment_lines=loc.comment,
        )

    def _extract_classes(self, source: str, path: Path) -> list[ClassReport]:
        """Return empty list (no structural analysis).

        Args:
            source: File contents.
            path: File path.

        Returns:
            Empty list.
        """
        return []

    def _extract_functions(self, source: str, path: Path) -> list[MethodReport]:
        """Return empty list (no structural analysis).

        Args:
            source: File contents.
            path: File path.

        Returns:
            Empty list.
        """
        return []

    def _detect_imports(self, source: str) -> list[str]:
        """Return empty list (no import detection).

        Args:
            source: File contents.

        Returns:
            Empty list.
        """
        return []

    @staticmethod
    def _lookup(path: Path) -> tuple[str, tuple[str, ...]]:
        """Look up language and comment prefixes for *path*.

        Args:
            path: File path.

        Returns:
            ``(language, comment_prefixes)`` tuple.
        """
        info = _EXT_MAP.get(path.suffix)
        if info is not None:
            return info
        # Check for extensionless files by name.
        name = path.name.lower()
        if name in ("makefile", "gnumakefile"):
            return ("makefile", ("#",))
        if name == "dockerfile":
            return ("dockerfile", ("#",))
        return ("generic", ("#",))
