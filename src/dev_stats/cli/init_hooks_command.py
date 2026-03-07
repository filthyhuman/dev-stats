"""The ``init-hooks`` sub-command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from dev_stats.ci.precommit_generator import PrecommitGenerator


class InitHooksCommand:
    """Generates a ``.pre-commit-config.yaml`` in the target directory."""

    def __call__(
        self,
        repo: Annotated[
            Path,
            typer.Argument(help="Target directory for the config file."),
        ] = Path("."),
    ) -> None:
        """Generate a .pre-commit-config.yaml for dev-stats.

        Args:
            repo: Target directory.
        """
        console = Console()
        generator = PrecommitGenerator()
        out_path = generator.write(repo)
        console.print(f"[green]wrote[/green] {out_path}")
