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


# ---------------------------------------------------------------------------
# Content strings for rich_fake_repo
# ---------------------------------------------------------------------------

_HELLO_PY_V1 = '''\
"""Greeting utilities for dev-stats demo."""


class Greeter:
    """Produce styled greetings.

    Attributes:
        name: The person to greet.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self) -> str:
        """Return a greeting string."""
        # Choose formality based on name length
        if len(self.name) > 10:
            return f"Good day, {self.name}."
        else:
            return f"Hi, {self.name}!"


def repeat_greeting(name: str, times: int) -> list[str]:
    """Build a list of repeated greetings.

    Args:
        name: Recipient name.
        times: How many greetings to produce.

    Returns:
        A list of greeting strings.
    """
    greeter = Greeter(name)
    results: list[str] = []
    for _ in range(times):
        results.append(greeter.greet())
    return results
'''

_HELLO_PY_V2 = '''\
"""Greeting utilities for dev-stats demo."""

import logging

logger = logging.getLogger(__name__)


class Greeter:
    """Produce styled greetings.

    Attributes:
        name: The person to greet.
        formal: Whether to use formal style.
    """

    def __init__(self, name: str, *, formal: bool = False) -> None:
        self.name = name
        self.formal = formal

    def greet(self) -> str:
        """Return a greeting string."""
        # Choose formality based on flag or name length
        if self.formal or len(self.name) > 10:
            return f"Good day, {self.name}."
        else:
            return f"Hi, {self.name}!"

    def farewell(self) -> str:
        """Return a farewell string."""
        return f"Goodbye, {self.name}."


def repeat_greeting(name: str, times: int, formal: bool = False) -> list[str]:
    """Build a list of repeated greetings.

    Args:
        name: Recipient name.
        times: How many greetings to produce.
        formal: Use formal tone.

    Returns:
        A list of greeting strings.
    """
    greeter = Greeter(name, formal=formal)
    results: list[str] = []
    for i in range(times):
        if i % 2 == 0:
            results.append(greeter.greet())
        else:
            results.append(greeter.farewell())
    logger.debug("Generated %d messages for %s", times, name)
    return results
'''

_APP_JAVA = """\
/**
 * Simple application entry point.
 */
public class App {

    /** Application name constant. */
    private static final String NAME = "dev-stats";

    /**
     * Return a welcome message.
     *
     * @param user the user to welcome
     * @return a welcome string
     */
    public String welcome(String user) {
        if (user == null || user.isEmpty()) {
            return "Welcome, stranger!";
        }
        return "Welcome, " + user + "!";
    }

    /**
     * Main entry point.
     *
     * @param args command-line arguments
     */
    public static void main(String[] args) {
        App app = new App();
        String msg = app.welcome(args.length > 0 ? args[0] : null);
        System.out.println(msg);
    }
}
"""

_INDEX_JS = """\
/**
 * Utility helpers for the front-end.
 */

// Default configuration
const DEFAULT_TIMEOUT = 3000;

/**
 * Delay execution by a given number of milliseconds.
 * @param {number} ms - milliseconds to wait
 * @returns {Promise<void>}
 */
function delay(ms) {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

/**
 * Greet a user with an optional exclamation.
 * @param {string} name
 * @param {boolean} excited
 * @returns {string}
 */
const greet = (name, excited = false) => {
    // Build the greeting
    if (excited) {
        return `Hello, ${name}!!!`;
    }
    return `Hello, ${name}.`;
};

module.exports = { delay, greet, DEFAULT_TIMEOUT };
"""


@pytest.fixture
def rich_fake_repo(tmp_path: Path) -> Path:
    """Create a comprehensive temporary Git repository for E2E testing.

    The repo contains three source files across three languages and has
    three commits from two different authors plus two extra branches::

        commit 1 (Alice)  — add hello.py
        commit 2 (Bob)    — add App.java and index.js
        commit 3 (Alice)  — update hello.py with more code
        branch feature/new-stuff  — branched from commit 2
        branch stale/old-branch   — branched from commit 1

    Args:
        tmp_path: Pytest-provided temporary directory.

    Returns:
        Path to the repository root.
    """
    _run_git(tmp_path, "init", "--initial-branch", "main")
    _run_git(tmp_path, "config", "user.email", "ci@test.local")
    _run_git(tmp_path, "config", "user.name", "CI Bot")

    # -- Commit 1: hello.py (Alice) ----------------------------------------
    hello = tmp_path / "hello.py"
    hello.write_text(_HELLO_PY_V1)
    _run_git(tmp_path, "add", "hello.py")
    _run_git(
        tmp_path,
        "commit",
        "-m",
        "Add greeting utilities",
        "--author",
        "Alice <alice@example.com>",
    )

    # Branch stale/old-branch from commit 1
    _run_git(tmp_path, "branch", "stale/old-branch")

    # -- Commit 2: App.java + index.js (Bob) -------------------------------
    app_java = tmp_path / "App.java"
    app_java.write_text(_APP_JAVA)

    index_js = tmp_path / "index.js"
    index_js.write_text(_INDEX_JS)

    _run_git(tmp_path, "add", "App.java", "index.js")
    _run_git(
        tmp_path,
        "commit",
        "-m",
        "Add Java and JavaScript sources",
        "--author",
        "Bob <bob@example.com>",
    )

    # Branch feature/new-stuff from commit 2
    _run_git(tmp_path, "branch", "feature/new-stuff")

    # -- Commit 3: update hello.py (Alice) ---------------------------------
    hello.write_text(_HELLO_PY_V2)
    _run_git(tmp_path, "add", "hello.py")
    _run_git(
        tmp_path,
        "commit",
        "-m",
        "Extend Greeter with farewell and formal flag",
        "--author",
        "Alice <alice@example.com>",
    )

    return tmp_path
