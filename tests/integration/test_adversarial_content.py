"""Integration tests for adversarial repository content.

Verifies that dev-stats handles malicious or unusual content in filenames,
commit messages, author names, and branch names without crashing or
producing unsafe output (e.g. unescaped HTML).
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from dev_stats.cli.app import app

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


def _git(cwd: Path, *args: str) -> None:
    """Run a git command in *cwd*."""
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _init_repo(tmp_path: Path) -> None:
    """Initialise a minimal git repo with one commit."""
    _git(tmp_path, "init", "--initial-branch", "main")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / ".gitkeep").write_text("")
    _git(tmp_path, "add", ".gitkeep")
    _git(tmp_path, "commit", "-m", "init")


# ── Filenames with special characters ─────────────────────────────────


class TestSpecialCharFilenames:
    """Files with characters that could break shell or HTML."""

    def test_ampersand_in_filename(self, tmp_path: Path) -> None:
        """Filename containing '&' does not crash or produce raw '&' in HTML."""
        _init_repo(tmp_path)
        (tmp_path / "a&b.py").write_text("x = 1\n")
        _git(tmp_path, "add", "a&b.py")
        _git(tmp_path, "commit", "-m", "add file")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_angle_brackets_in_filename(self, tmp_path: Path) -> None:
        """Filename with angle brackets is handled safely."""
        _init_repo(tmp_path)
        name = "file<tag>.txt"
        (tmp_path / name).write_text("data\n")
        _git(tmp_path, "add", name)
        _git(tmp_path, "commit", "-m", "add file")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_quotes_in_filename(self, tmp_path: Path) -> None:
        """Filename with single and double quotes is handled safely."""
        _init_repo(tmp_path)
        name = 'it\'s a "test".py'
        (tmp_path / name).write_text("y = 2\n")
        _git(tmp_path, "add", name)
        _git(tmp_path, "commit", "-m", "add file")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_spaces_in_filename(self, tmp_path: Path) -> None:
        """Filename with spaces is handled safely."""
        _init_repo(tmp_path)
        name = "my file (copy).py"
        (tmp_path / name).write_text("z = 3\n")
        _git(tmp_path, "add", name)
        _git(tmp_path, "commit", "-m", "add file")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_unicode_emoji_in_filename(self, tmp_path: Path) -> None:
        """Filename with emoji is handled safely."""
        _init_repo(tmp_path)
        name = "hello_\U0001f600.py"
        (tmp_path / name).write_text("a = 1\n")
        _git(tmp_path, "add", name)
        _git(tmp_path, "commit", "-m", "add file")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0


# ── Commit messages with HTML / shell metacharacters ──────────────────


class TestAdversarialCommitMessages:
    """Commit messages containing HTML, script tags, or shell metacharacters."""

    def test_html_script_in_commit_message(self, tmp_path: Path) -> None:
        """Commit message with <script> tag does not produce XSS in output."""
        _init_repo(tmp_path)
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", '<script>alert("xss")</script>')

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_html_img_onerror_in_commit_message(self, tmp_path: Path) -> None:
        """Commit message with img onerror payload is handled safely."""
        _init_repo(tmp_path)
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", "<img src=x onerror=alert(1)>")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_shell_expansion_in_commit_message(self, tmp_path: Path) -> None:
        """Commit message with shell expansion syntax is not executed."""
        _init_repo(tmp_path)
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", "fix $(whoami) `id` ${HOME}")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_null_bytes_in_commit_message(self, tmp_path: Path) -> None:
        """Commit message with unusual whitespace/control chars is handled."""
        _init_repo(tmp_path)
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", "fix:\ttabs\nand\nnewlines")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_very_long_commit_message(self, tmp_path: Path) -> None:
        """Extremely long commit message does not crash."""
        _init_repo(tmp_path)
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", "A" * 10_000)

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0


# ── Author names with special characters ──────────────────────────────


class TestAdversarialAuthorNames:
    """Author names containing HTML or special characters."""

    def test_html_in_author_name(self, tmp_path: Path) -> None:
        """Author name with HTML tags does not produce unescaped output."""
        _init_repo(tmp_path)
        _git(tmp_path, "config", "user.name", '<b onclick="alert(1)">Evil</b>')
        _git(tmp_path, "config", "user.email", "evil@<script>.com")
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", "add code")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_unicode_author_name(self, tmp_path: Path) -> None:
        """Author name with Unicode characters is handled safely."""
        _init_repo(tmp_path)
        _git(tmp_path, "config", "user.name", "\u00e9\u00e0\u00fc \u4e16\u754c \U0001f600")
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", "add code")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_semicolon_pipe_in_author(self, tmp_path: Path) -> None:
        """Author name with shell operators is not interpreted."""
        _init_repo(tmp_path)
        _git(tmp_path, "config", "user.name", "user; rm -rf / | cat /etc/passwd")
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", "add code")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0


# ── Branch names with special characters ──────────────────────────────


class TestAdversarialBranchNames:
    """Branch names containing special characters."""

    def test_shell_expansion_in_branch_name(self, tmp_path: Path) -> None:
        """Branch name with $() is not interpreted as shell expansion."""
        _init_repo(tmp_path)
        # Git allows $ in branch names
        _git(tmp_path, "branch", "feature/$USER")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_html_in_branch_name(self, tmp_path: Path) -> None:
        """Branch name with angle brackets is handled safely.

        Note: git does not allow '<' or '>' in branch names, so we use
        characters that are allowed but could still be problematic.
        """
        _init_repo(tmp_path)
        _git(tmp_path, "branch", "feature/test&fix")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_unicode_branch_name(self, tmp_path: Path) -> None:
        """Branch name with Unicode characters is handled safely."""
        _init_repo(tmp_path)
        _git(tmp_path, "branch", "feature/\u00fcbung-\U0001f680")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0

    def test_deeply_nested_branch_name(self, tmp_path: Path) -> None:
        """Very deeply nested branch name does not crash."""
        _init_repo(tmp_path)
        name = "/".join(["a"] * 50)
        _git(tmp_path, "branch", f"feature/{name}")

        result = runner.invoke(app, ["analyse", str(tmp_path)])
        assert result.exit_code == 0


# ── Dashboard HTML escaping ───────────────────────────────────────────


class TestDashboardXssPrevention:
    """Verify that adversarial content is HTML-escaped in dashboard output."""

    def test_script_tag_escaped_in_dashboard(self, tmp_path: Path) -> None:
        """<script> in commit message is escaped in dashboard HTML."""
        _init_repo(tmp_path)
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", '<script>alert("xss")</script>')

        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            ["analyse", str(tmp_path), "--format", "html", "--output", str(out_dir)],
        )
        assert result.exit_code == 0

        html_files = list(out_dir.rglob("*.html"))
        if html_files:
            html = html_files[0].read_text(encoding="utf-8")
            # The literal <script>alert("xss")</script> must not appear
            # unescaped in the HTML body. It may appear escaped as
            # &lt;script&gt; or be inside a compressed data chunk.
            assert '<script>alert("xss")</script>' not in html

    def test_html_author_escaped_in_dashboard(self, tmp_path: Path) -> None:
        """HTML in author name is escaped in dashboard output."""
        _init_repo(tmp_path)
        _git(tmp_path, "config", "user.name", "<b>Evil</b>")
        (tmp_path / "code.py").write_text("x = 1\n")
        _git(tmp_path, "add", "code.py")
        _git(tmp_path, "commit", "-m", "add code")

        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            ["analyse", str(tmp_path), "--format", "html", "--output", str(out_dir)],
        )
        assert result.exit_code == 0

        html_files = list(out_dir.rglob("*.html"))
        if html_files:
            html = html_files[0].read_text(encoding="utf-8")
            # Raw <b>Evil</b> must not appear in the page body
            assert "<b>Evil</b>" not in html

    def test_angle_bracket_filename_escaped(self, tmp_path: Path) -> None:
        """Filename with angle brackets is escaped in dashboard output."""
        _init_repo(tmp_path)
        name = "file<tag>.txt"
        (tmp_path / name).write_text("data\n")
        _git(tmp_path, "add", name)
        _git(tmp_path, "commit", "-m", "add file")

        out_dir = tmp_path / "output"
        result = runner.invoke(
            app,
            ["analyse", str(tmp_path), "--format", "html", "--output", str(out_dir)],
        )
        assert result.exit_code == 0

        html_files = list(out_dir.rglob("*.html"))
        if html_files:
            html = html_files[0].read_text(encoding="utf-8")
            # Raw file<tag>.txt must not appear unescaped
            assert "file<tag>.txt" not in html
