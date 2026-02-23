"""Pre-commit hook YAML snippet generator."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_HOOK_YAML = """\
# dev-stats pre-commit hook
# Add this to your .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: dev-stats
        name: dev-stats quality check
        entry: dev-stats analyse --fail-on-violations
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
"""


class PrecommitGenerator:
    """Generates a ``.pre-commit-hooks.yaml`` snippet for dev-stats.

    Produces a ready-to-paste YAML block that configures dev-stats as a
    local pre-commit hook running ``--fail-on-violations``.
    """

    def generate(self) -> str:
        """Generate the pre-commit hook YAML snippet.

        Returns:
            YAML string for inclusion in ``.pre-commit-config.yaml``.
        """
        return _HOOK_YAML

    def write(self, output_dir: Path) -> Path:
        """Write the hook snippet to a file.

        Args:
            output_dir: Directory to write into.

        Returns:
            Path to the generated file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "dev-stats-precommit.yaml"
        out_path.write_text(_HOOK_YAML, encoding="utf-8")
        return out_path
