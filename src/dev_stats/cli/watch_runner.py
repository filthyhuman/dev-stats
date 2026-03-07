"""Watch mode runner for continuous file change detection."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

logger = logging.getLogger(__name__)

_DEBOUNCE_MS = 500


class WatchRunner:
    """Watches a directory for file changes and re-runs analysis.

    Uses ``watchfiles`` for efficient filesystem monitoring with a
    configurable debounce interval.

    Args:
        repo_path: Directory to watch.
        run_analysis: Callable that performs the analysis.
        extensions: File extensions to monitor.
    """

    def __init__(
        self,
        repo_path: Path,
        run_analysis: Callable[[], None],
        extensions: frozenset[str] | None = None,
    ) -> None:
        """Initialise the watch runner.

        Args:
            repo_path: Directory to watch for changes.
            run_analysis: Zero-argument callable that runs the analysis.
            extensions: Optional set of extensions to filter (e.g. {'.py', '.java'}).
        """
        self._repo_path = repo_path
        self._run_analysis = run_analysis
        self._extensions = extensions or frozenset(
            {
                ".py",
                ".java",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".cpp",
                ".cc",
                ".cxx",
                ".c",
                ".h",
                ".hpp",
                ".cs",
                ".go",
                ".m",
                ".mm",
            }
        )

    def run(self) -> None:
        """Start watching and re-running analysis on changes.

        Blocks until the user presses Ctrl-C.

        Raises:
            ImportError: If ``watchfiles`` is not installed.
        """
        try:
            from watchfiles import watch
        except ImportError:
            msg = (
                "watchfiles is required for --watch mode. "
                "Install with: pip install dev-stats[watch]"
            )
            raise ImportError(msg) from None

        from rich.console import Console

        console = Console()

        # Initial run
        self._run_analysis()
        console.print("\n[dim]Watching for changes... (Ctrl-C to stop)[/dim]")

        try:
            for changes in watch(
                self._repo_path,
                debounce=_DEBOUNCE_MS,
                step=100,
                watch_filter=self._filter,
            ):
                changed_paths = [str(p) for _, p in changes]
                logger.debug("Changes detected: %s", changed_paths)
                console.clear()
                self._run_analysis()
                console.print("\n[dim]Watching for changes... (Ctrl-C to stop)[/dim]")
        except KeyboardInterrupt:
            console.print("\n[dim]Watch stopped.[/dim]")

    def _filter(self, change: Any, path: str) -> bool:  # noqa: ANN401
        """Filter watch events to only monitored extensions.

        Args:
            change: The type of change (unused but required by watchfiles API).
            path: Absolute path to the changed file.

        Returns:
            ``True`` if the file has a monitored extension.
        """
        from pathlib import Path as _Path

        _ = change  # unused but required by watchfiles callback signature
        return _Path(path).suffix in self._extensions
