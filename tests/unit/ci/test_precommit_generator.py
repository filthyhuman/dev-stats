"""Tests for the pre-commit generator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dev_stats.ci.precommit_generator import PrecommitGenerator

if TYPE_CHECKING:
    from pathlib import Path


class TestPrecommitGenerator:
    """Tests for PrecommitGenerator."""

    def test_generate_default(self) -> None:
        """Default generation produces valid YAML with dev-stats hook."""
        gen = PrecommitGenerator()
        result = gen.generate()
        assert "dev-stats" in result
        assert "--fail-on-violations" in result
        assert "repos:" in result

    def test_generate_with_languages(self) -> None:
        """Languages are passed as --lang flags."""
        gen = PrecommitGenerator()
        result = gen.generate(languages=("python", "java"))
        assert "--lang python" in result
        assert "--lang java" in result

    def test_generate_with_exclude(self) -> None:
        """Exclude patterns are passed as --exclude flags."""
        gen = PrecommitGenerator()
        result = gen.generate(exclude_patterns=("tests/*",))
        assert "--exclude tests/*" in result

    def test_generate_quiet_mode(self) -> None:
        """Quiet mode adds --quiet flag."""
        gen = PrecommitGenerator()
        result = gen.generate(quiet=True)
        assert "--quiet" in result

    def test_generate_no_quiet(self) -> None:
        """Non-quiet mode omits --quiet."""
        gen = PrecommitGenerator()
        result = gen.generate(quiet=False)
        assert "--quiet" not in result

    def test_write_creates_file(self, tmp_path: Path) -> None:
        """write() creates .pre-commit-config.yaml."""
        gen = PrecommitGenerator()
        path = gen.write(tmp_path)
        assert path.exists()
        assert path.name == ".pre-commit-config.yaml"
        assert "dev-stats" in path.read_text()

    def test_contains_hook_id(self) -> None:
        """The snippet contains the dev-stats hook id."""
        gen = PrecommitGenerator()
        result = gen.generate()
        assert "id: dev-stats" in result

    def test_contains_entry_with_fail_on_violations(self) -> None:
        """The snippet contains the dev-stats entry command with --fail-on-violations."""
        gen = PrecommitGenerator()
        result = gen.generate()
        assert "entry: dev-stats analyse . --fail-on-violations" in result

    def test_contains_repos_key(self) -> None:
        """The snippet is valid .pre-commit-config.yaml structure."""
        gen = PrecommitGenerator()
        result = gen.generate()
        assert "repos:" in result
        assert "- repo: local" in result

    def test_write_file_content(self, tmp_path: Path) -> None:
        """The written file contains the same content as generate()."""
        gen = PrecommitGenerator()
        path = gen.write(tmp_path)
        assert path.read_text(encoding="utf-8") == gen.generate()

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        """write() creates parent directories if needed."""
        gen = PrecommitGenerator()
        deep = tmp_path / "a" / "b"
        path = gen.write(deep)
        assert path.exists()
        assert deep.exists()

    def test_types_or_field(self) -> None:
        """The generated YAML uses types_or with multiple languages."""
        gen = PrecommitGenerator()
        result = gen.generate()
        assert "types_or:" in result


class TestInitHooksCommand:
    """Tests for the init-hooks CLI command."""

    def test_init_hooks_creates_file(self, tmp_path: Path) -> None:
        """init-hooks creates config file."""
        from typer.testing import CliRunner

        from dev_stats.cli.app import app

        runner = CliRunner()
        result = runner.invoke(app, ["init-hooks", str(tmp_path)])
        assert result.exit_code == 0
        config_file = tmp_path / ".pre-commit-config.yaml"
        assert config_file.exists()
