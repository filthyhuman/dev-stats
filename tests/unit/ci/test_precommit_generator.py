"""Tests for PrecommitGenerator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dev_stats.ci.precommit_generator import PrecommitGenerator

if TYPE_CHECKING:
    from pathlib import Path


class TestGenerate:
    """YAML snippet generation tests."""

    def test_returns_string(self) -> None:
        """generate() returns a non-empty string."""
        gen = PrecommitGenerator()
        result = gen.generate()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_hook_id(self) -> None:
        """The snippet contains the dev-stats hook id."""
        gen = PrecommitGenerator()
        result = gen.generate()

        assert "id: dev-stats" in result

    def test_contains_entry(self) -> None:
        """The snippet contains the dev-stats entry command."""
        gen = PrecommitGenerator()
        result = gen.generate()

        assert "entry: dev-stats analyse --fail-on-violations" in result

    def test_contains_repos_key(self) -> None:
        """The snippet is valid .pre-commit-config.yaml structure."""
        gen = PrecommitGenerator()
        result = gen.generate()

        assert "repos:" in result
        assert "- repo: local" in result


class TestWrite:
    """File writing tests."""

    def test_write_creates_file(self, tmp_path: Path) -> None:
        """write() creates a YAML file in the output directory."""
        gen = PrecommitGenerator()
        path = gen.write(tmp_path)

        assert path.exists()
        assert path.name == "dev-stats-precommit.yaml"

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
