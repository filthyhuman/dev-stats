"""Abstract base class for language parsers."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.core.models import FileReport


class AbstractParser(abc.ABC):
    """Base class that all language parsers must extend.

    Subclasses implement :meth:`parse` to produce a :class:`FileReport`
    from a source file, and declare :attr:`language` and :attr:`extensions`.
    """

    @property
    @abc.abstractmethod
    def language(self) -> str:
        """Return the canonical lowercase language name."""

    @property
    @abc.abstractmethod
    def extensions(self) -> tuple[str, ...]:
        """Return file extensions handled by this parser (e.g. ``('.py',)``)."""

    @abc.abstractmethod
    def parse(self, path: Path, repo_root: Path) -> FileReport:
        """Parse a source file and return a ``FileReport``.

        Args:
            path: Absolute path to the file.
            repo_root: Repository root for computing relative paths.

        Returns:
            A frozen ``FileReport`` with analysis results.
        """
