"""Version flag callback for the CLI."""

import typer
from rich.console import Console

from dev_stats import __version__


class VersionCallback:
    """Callable that prints the version and exits when ``--version`` is passed.

    Designed to be used as a Typer callback for the global ``--version`` option.
    """

    def __call__(self, value: bool) -> None:
        """Print the version string and raise ``typer.Exit``.

        Args:
            value: ``True`` when the user passes ``--version``.
        """
        if value:
            console = Console(stderr=True)
            console.print(f"dev-stats {__version__}")
            raise typer.Exit
