"""Dispatcher that routes files to the appropriate language parser."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.core.models import FileReport
    from dev_stats.core.parser_registry import ParserRegistry

logger = logging.getLogger(__name__)


class Dispatcher:
    """Routes source files to the correct parser via the registry.

    Errors during parsing are logged and skipped so that a single broken
    file does not halt the entire analysis.
    """

    def __init__(self, registry: ParserRegistry, repo_root: Path) -> None:
        """Initialise the dispatcher.

        Args:
            registry: Parser registry to look up parsers by extension.
            repo_root: Repository root path (passed to parsers).
        """
        self._registry = registry
        self._repo_root = repo_root

    def parse(self, path: Path) -> FileReport:
        """Parse a single file and return its report.

        Args:
            path: Repository-relative path to the file.

        Returns:
            A ``FileReport`` for the file.
        """
        absolute = self._repo_root / path
        parser = self._registry.get_or_default(path)
        return parser.parse(absolute, self._repo_root)

    def parse_many(self, paths: list[Path]) -> list[FileReport]:
        """Parse multiple files, logging and skipping failures.

        Args:
            paths: Repository-relative paths to parse.

        Returns:
            A list of ``FileReport`` objects for successfully parsed files.
        """
        reports: list[FileReport] = []
        for path in paths:
            try:
                reports.append(self.parse(path))
            except Exception:
                logger.exception("Failed to parse %s", path)
        return reports
