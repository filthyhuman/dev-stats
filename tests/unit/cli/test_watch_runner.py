"""Tests for the watch runner module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path


class TestWatchRunner:
    """Tests for WatchRunner."""

    def test_import_error_without_watchfiles(self, tmp_path: Path) -> None:
        """WatchRunner.run raises ImportError when watchfiles missing."""
        from dev_stats.cli.watch_runner import WatchRunner

        runner = WatchRunner(repo_path=tmp_path, run_analysis=lambda: None)
        with (
            patch.dict("sys.modules", {"watchfiles": None}),
            pytest.raises(ImportError, match="watchfiles"),
        ):
            runner.run()

    def test_filter_accepts_python_files(self, tmp_path: Path) -> None:
        """Filter accepts .py files."""
        from dev_stats.cli.watch_runner import WatchRunner

        runner = WatchRunner(repo_path=tmp_path, run_analysis=lambda: None)
        assert runner._filter(None, "/some/path/test.py") is True

    def test_filter_rejects_non_source_files(self, tmp_path: Path) -> None:
        """Filter rejects non-source extensions."""
        from dev_stats.cli.watch_runner import WatchRunner

        runner = WatchRunner(repo_path=tmp_path, run_analysis=lambda: None)
        assert runner._filter(None, "/some/path/readme.md") is False

    def test_filter_accepts_java_files(self, tmp_path: Path) -> None:
        """Filter accepts .java files."""
        from dev_stats.cli.watch_runner import WatchRunner

        runner = WatchRunner(repo_path=tmp_path, run_analysis=lambda: None)
        assert runner._filter(None, "/project/App.java") is True

    def test_custom_extensions(self, tmp_path: Path) -> None:
        """Custom extensions override defaults."""
        from dev_stats.cli.watch_runner import WatchRunner

        runner = WatchRunner(
            repo_path=tmp_path,
            run_analysis=lambda: None,
            extensions=frozenset({".txt"}),
        )
        assert runner._filter(None, "/path/notes.txt") is True
        assert runner._filter(None, "/path/code.py") is False

    def test_keyboard_interrupt_exits_cleanly(self, tmp_path: Path) -> None:
        """KeyboardInterrupt during watch stops cleanly."""
        from dev_stats.cli.watch_runner import WatchRunner

        mock_analysis = MagicMock()

        def fake_watch(*_args: object, **_kwargs: object) -> list[object]:
            """Simulate watch that raises KeyboardInterrupt."""
            raise KeyboardInterrupt

        runner = WatchRunner(repo_path=tmp_path, run_analysis=mock_analysis)
        with patch("dev_stats.cli.watch_runner.watch", fake_watch, create=True):
            # Patch the import inside run()
            mock_watchfiles = MagicMock()
            mock_watchfiles.watch = fake_watch
            with patch.dict("sys.modules", {"watchfiles": mock_watchfiles}):
                runner.run()

        # Initial analysis should have been called
        mock_analysis.assert_called_once()
