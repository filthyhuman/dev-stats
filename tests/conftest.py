"""Shared fixtures and factory functions for dev-stats tests."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Value-object stubs for factory functions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Parameter:
    """Stub for a function/method parameter."""

    name: str = "x"
    annotation: str = "int"
    default: str | None = None


@dataclass(frozen=True)
class Method:
    """Stub for a parsed method."""

    name: str = "do_thing"
    line: int = 1
    parameters: tuple[Parameter, ...] = ()
    cyclomatic_complexity: int = 1
    lines: int = 5


@dataclass(frozen=True)
class ClassRecord:
    """Stub for a parsed class."""

    name: str = "MyClass"
    line: int = 1
    methods: tuple[Method, ...] = ()
    lines: int = 20


@dataclass(frozen=True)
class FileReport:
    """Stub for a per-file analysis report."""

    path: Path = field(default_factory=lambda: Path("example.py"))
    language: str = "python"
    total_lines: int = 100
    code_lines: int = 80
    blank_lines: int = 10
    comment_lines: int = 10
    classes: tuple[ClassRecord, ...] = ()
    functions: tuple[Method, ...] = ()


@dataclass(frozen=True)
class RepoReport:
    """Stub for a whole-repository analysis report."""

    root: Path = field(default_factory=lambda: Path("."))
    files: tuple[FileReport, ...] = ()


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def make_parameter(**kwargs: object) -> Parameter:
    """Create a ``Parameter`` with optional overrides.

    Args:
        **kwargs: Field overrides forwarded to ``Parameter``.

    Returns:
        A ``Parameter`` instance.
    """
    return Parameter(**kwargs)  # type: ignore[arg-type]


def make_method(**kwargs: object) -> Method:
    """Create a ``Method`` with optional overrides.

    Args:
        **kwargs: Field overrides forwarded to ``Method``.

    Returns:
        A ``Method`` instance.
    """
    return Method(**kwargs)  # type: ignore[arg-type]


def make_class(**kwargs: object) -> ClassRecord:
    """Create a ``ClassRecord`` with optional overrides.

    Args:
        **kwargs: Field overrides forwarded to ``ClassRecord``.

    Returns:
        A ``ClassRecord`` instance.
    """
    return ClassRecord(**kwargs)  # type: ignore[arg-type]


def make_file_report(**kwargs: object) -> FileReport:
    """Create a ``FileReport`` with optional overrides.

    Args:
        **kwargs: Field overrides forwarded to ``FileReport``.

    Returns:
        A ``FileReport`` instance.
    """
    return FileReport(**kwargs)  # type: ignore[arg-type]


def make_repo_report(**kwargs: object) -> RepoReport:
    """Create a ``RepoReport`` with optional overrides.

    Args:
        **kwargs: Field overrides forwarded to ``RepoReport``.

    Returns:
        A ``RepoReport`` instance.
    """
    return RepoReport(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _run_git(cwd: Path, *args: str) -> None:
    """Run a git command inside *cwd*."""
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """Create a temporary Git repository with two commits and one branch.

    The repo contains a single ``hello.py`` file. Commit history::

        commit 1 — initial hello.py
        commit 2 — update hello.py  (on main)
        branch  — feature/test branched from commit 2

    Args:
        tmp_path: Pytest-provided temporary directory.

    Returns:
        Path to the repository root.
    """
    _run_git(tmp_path, "init", "--initial-branch", "main")
    _run_git(tmp_path, "config", "user.email", "test@example.com")
    _run_git(tmp_path, "config", "user.name", "Test User")

    hello = tmp_path / "hello.py"
    hello.write_text('"""Hello."""\n\ndef greet() -> str:\n    return "hi"\n')
    _run_git(tmp_path, "add", "hello.py")
    _run_git(tmp_path, "commit", "-m", "initial commit")

    hello.write_text(
        '"""Hello."""\n\ndef greet(name: str = "world") -> str:\n    return f"hi {name}"\n'
    )
    _run_git(tmp_path, "add", "hello.py")
    _run_git(tmp_path, "commit", "-m", "update greet signature")

    _run_git(tmp_path, "branch", "feature/test")

    return tmp_path
