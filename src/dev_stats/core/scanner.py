"""File scanner that traverses a repository respecting exclude patterns."""

from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from dev_stats.config.analysis_config import AnalysisConfig

logger = logging.getLogger(__name__)

# Patterns that are always excluded regardless of configuration.
_ALWAYS_EXCLUDED: tuple[str, ...] = (".git", "__pycache__", "*.pyc")


@dataclass(frozen=True)
class ProgressEvent:
    """Event emitted by the scanner as it discovers files.

    Attributes:
        files_found: Running count of files discovered so far.
        current_file: Path to the most recently discovered file.
    """

    files_found: int
    current_file: Path


@runtime_checkable
class ProgressObserver(Protocol):
    """Observer that receives scanner progress events."""

    def on_progress(self, event: ProgressEvent) -> None:
        """Handle a progress event.

        Args:
            event: The progress event to handle.
        """
        ...


class Scanner:
    """Traverse a repository tree yielding source-file paths.

    Respects exclude patterns from configuration, ``.gitignore``, and
    hard-coded exclusions (``.git``, ``__pycache__``, ``*.pyc``).

    The scanner is lazy: :meth:`scan` is a generator that yields paths
    one at a time without loading the full file list into memory.
    """

    def __init__(
        self,
        repo_path: Path,
        config: AnalysisConfig,
        observers: list[ProgressObserver] | None = None,
    ) -> None:
        """Initialise the scanner.

        Args:
            repo_path: Root directory to scan.
            config: Analysis configuration (provides exclude patterns).
            observers: Optional progress observers to notify.

        Raises:
            FileNotFoundError: If *repo_path* does not exist.
        """
        if not repo_path.exists():
            msg = f"Repository path does not exist: {repo_path}"
            raise FileNotFoundError(msg)
        self._repo_path = repo_path.resolve()
        self._config = config
        self._observers: list[ProgressObserver] = observers or []
        self._exclude_patterns = (
            *_ALWAYS_EXCLUDED,
            *config.exclude_patterns,
            *self._parse_gitignore(),
        )

    def scan(self) -> Generator[Path, None, None]:
        """Yield repository-relative paths for all non-excluded files.

        Yields:
            Paths relative to the repository root.
        """
        count = 0
        for path in self._repo_path.rglob("*"):
            if path.is_dir():
                continue
            relative = path.relative_to(self._repo_path)
            if self._is_excluded(relative):
                continue
            count += 1
            self._emit_progress(count, relative)
            yield relative

    def _is_excluded(self, path: Path) -> bool:
        """Check whether *path* matches any exclude pattern.

        Args:
            path: Repository-relative path to check.

        Returns:
            ``True`` if the path should be excluded.
        """
        path_str = str(path)
        parts = path.parts
        for pattern in self._exclude_patterns:
            # Match against the full path string.
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Match against any individual path component.
            for part in parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        return False

    def _parse_gitignore(self) -> list[str]:
        """Read ``.gitignore`` from the repo root and return patterns.

        Returns:
            A list of gitignore patterns (comments and blanks stripped).
        """
        gitignore = self._repo_path / ".gitignore"
        if not gitignore.is_file():
            return []
        patterns: list[str] = []
        try:
            for line in gitignore.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    patterns.append(stripped)
        except OSError:
            logger.warning("Could not read .gitignore at %s", gitignore)
        return patterns

    def _emit_progress(self, count: int, path: Path) -> None:
        """Notify all observers of a progress event.

        Args:
            count: Current file count.
            path: Path of the newly discovered file.
        """
        event = ProgressEvent(files_found=count, current_file=path)
        for observer in self._observers:
            observer.on_progress(event)
