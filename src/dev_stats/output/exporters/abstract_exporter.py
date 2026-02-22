"""Abstract base class for output exporters."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.config.analysis_config import AnalysisConfig
    from dev_stats.core.models import RepoReport


class AbstractExporter(abc.ABC):
    """Base class for all report exporters.

    Subclasses implement :meth:`export` to write reports in a specific format.
    """

    def __init__(self, report: RepoReport, config: AnalysisConfig) -> None:
        """Initialise the exporter.

        Args:
            report: The analysis report to export.
            config: Analysis configuration.
        """
        self._report = report
        self._config = config

    @abc.abstractmethod
    def export(self, output_dir: Path) -> list[Path]:
        """Export the report to *output_dir*.

        Args:
            output_dir: Directory to write output files into.

        Returns:
            List of paths to the generated files.
        """
