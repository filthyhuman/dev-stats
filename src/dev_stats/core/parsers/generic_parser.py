"""Generic parser that counts lines for any file type."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dev_stats.core.models import FileReport
from dev_stats.core.parsers.abstract_parser import AbstractParser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class GenericParser(AbstractParser):
    """Fallback parser that provides basic line counts for any file.

    No AST analysis is performed; only total, blank, and code lines
    are counted.
    """

    @property
    def language(self) -> str:
        """Return ``'generic'``."""
        return "generic"

    @property
    def extensions(self) -> tuple[str, ...]:
        """Return an empty tuple (matches no extension by default)."""
        return ()

    def parse(self, path: Path, repo_root: Path) -> FileReport:
        """Parse a file by counting lines.

        Args:
            path: Absolute path to the file.
            repo_root: Repository root for computing relative paths.

        Returns:
            A ``FileReport`` with line counts only.
        """
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            logger.warning("Could not read file: %s", path)
            return FileReport(
                path=path.relative_to(repo_root),
                language=self.language,
                total_lines=0,
                code_lines=0,
                blank_lines=0,
                comment_lines=0,
            )

        lines = text.splitlines()
        total = len(lines)
        blank = sum(1 for ln in lines if not ln.strip())
        code = total - blank

        return FileReport(
            path=path.relative_to(repo_root),
            language=self.language,
            total_lines=total,
            code_lines=code,
            blank_lines=blank,
            comment_lines=0,
        )
