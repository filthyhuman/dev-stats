"""Unit tests for the file scanner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from dev_stats.config.analysis_config import AnalysisConfig
from dev_stats.core.scanner import ProgressEvent, ProgressObserver, Scanner


class TestScannerFindsFiles:
    """Scanner.scan() discovers source files."""

    def test_finds_python_files(self, tmp_path: Path) -> None:
        """Scanner yields Python files in the tree."""
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "b.py").write_text("y = 2\n")

        config = AnalysisConfig(repo_path=tmp_path, exclude_patterns=())
        scanner = Scanner(repo_path=tmp_path, config=config)
        found = sorted(scanner.scan())

        assert Path("a.py") in found
        assert Path("sub/b.py") in found


class TestScannerExcludes:
    """Scanner respects exclude patterns."""

    def test_excludes_configured_pattern(self, tmp_path: Path) -> None:
        """Files matching an exclude pattern are skipped."""
        (tmp_path / "keep.py").write_text("x = 1\n")
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / "lib.py").write_text("y = 2\n")

        config = AnalysisConfig(repo_path=tmp_path, exclude_patterns=("vendor",))
        scanner = Scanner(repo_path=tmp_path, config=config)
        found = list(scanner.scan())

        assert Path("keep.py") in found
        assert Path("vendor/lib.py") not in found

    def test_skips_dot_git(self, tmp_path: Path) -> None:
        """The .git directory is always excluded."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("[core]\n")
        (tmp_path / "a.py").write_text("x = 1\n")

        config = AnalysisConfig(repo_path=tmp_path, exclude_patterns=())
        scanner = Scanner(repo_path=tmp_path, config=config)
        found = list(scanner.scan())

        assert Path("a.py") in found
        assert not any(".git" in str(p) for p in found)

    def test_skips_pycache(self, tmp_path: Path) -> None:
        """__pycache__ directories are always excluded."""
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "mod.cpython-312.pyc").write_bytes(b"\x00")
        (tmp_path / "a.py").write_text("x = 1\n")

        config = AnalysisConfig(repo_path=tmp_path, exclude_patterns=())
        scanner = Scanner(repo_path=tmp_path, config=config)
        found = list(scanner.scan())

        assert not any("__pycache__" in str(p) for p in found)


class TestScannerGitignore:
    """Scanner honours .gitignore patterns."""

    def test_gitignore_pattern_excluded(self, tmp_path: Path) -> None:
        """Files matching .gitignore patterns are excluded."""
        (tmp_path / ".gitignore").write_text("*.log\n")
        (tmp_path / "app.py").write_text("x = 1\n")
        (tmp_path / "debug.log").write_text("log data\n")

        config = AnalysisConfig(repo_path=tmp_path, exclude_patterns=())
        scanner = Scanner(repo_path=tmp_path, config=config)
        found = list(scanner.scan())

        assert Path("app.py") in found
        assert Path("debug.log") not in found


class TestScannerProgress:
    """Scanner emits progress events."""

    def test_observer_called(self, tmp_path: Path) -> None:
        """Observers receive ProgressEvent for each file."""
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "b.py").write_text("y = 2\n")

        observer = MagicMock(spec=ProgressObserver)
        config = AnalysisConfig(repo_path=tmp_path, exclude_patterns=())
        scanner = Scanner(repo_path=tmp_path, config=config, observers=[observer])
        found = list(scanner.scan())

        assert len(found) == 2
        assert observer.on_progress.call_count == 2
        # Verify the event type
        event = observer.on_progress.call_args_list[0][0][0]
        assert isinstance(event, ProgressEvent)
        assert event.files_found == 1


class TestScannerErrors:
    """Scanner error handling."""

    def test_nonexistent_path_raises(self) -> None:
        """Scanner raises FileNotFoundError for missing repo path."""
        config = AnalysisConfig(repo_path=Path("/nonexistent"))
        try:
            Scanner(repo_path=Path("/nonexistent"), config=config)
        except FileNotFoundError:
            pass
        else:
            msg = "Expected FileNotFoundError"
            raise AssertionError(msg)
