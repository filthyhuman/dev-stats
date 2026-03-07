"""Typer application -- single entry point for all dev-stats commands."""

from __future__ import annotations

import logging
from typing import Annotated

import typer

from dev_stats.cli.analyse_command import AnalyseCommand
from dev_stats.cli.branches_command import BranchesCommand
from dev_stats.cli.gitlog_command import GitlogCommand
from dev_stats.cli.version_callback import VersionCallback

_version_callback = VersionCallback()

app = typer.Typer(
    name="dev-stats",
    help="Git repository analysis and statistics tool.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

_analyse_command = AnalyseCommand()
_branches_command = BranchesCommand()
_gitlog_command = GitlogCommand()


@app.callback()
def _main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=_version_callback.__call__,
            is_eager=True,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show debug output."),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress all but errors."),
    ] = False,
) -> None:
    """Dev-stats -- Git repository analysis and statistics tool."""
    from rich.logging import RichHandler

    if verbose and quiet:
        msg = "--verbose and --quiet are mutually exclusive"
        raise typer.BadParameter(msg)
    level = logging.DEBUG if verbose else logging.ERROR if quiet else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_time=verbose)],
        force=True,
    )


# Register the __call__ *method* (not the instance) so Typer can introspect
# type hints via ``typing.get_type_hints()``.
app.command(name="analyse")(_analyse_command.__call__)
app.command(name="branches")(_branches_command.__call__)
app.command(name="gitlog")(_gitlog_command.__call__)
