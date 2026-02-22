"""JSON exporter producing full or summary reports."""

from __future__ import annotations

import dataclasses
import enum
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.output.exporters.abstract_exporter import AbstractExporter

if TYPE_CHECKING:
    from dev_stats.config.analysis_config import AnalysisConfig
    from dev_stats.core.models import RepoReport


class JsonExporter(AbstractExporter):
    """Exports the analysis report as JSON.

    Supports two modes:

    * **full** — Every field of ``RepoReport`` serialised, including nested
      classes, methods, and per-file details.
    * **summary** — Top-level statistics only (counts, language breakdown).

    Dates are formatted as ISO 8601 strings.
    """

    def __init__(
        self,
        report: RepoReport,
        config: AnalysisConfig,
        *,
        summary: bool = False,
    ) -> None:
        """Initialise the JSON exporter.

        Args:
            report: The analysis report to export.
            config: Analysis configuration.
            summary: If ``True``, export summary mode instead of full.
        """
        super().__init__(report, config)
        self._summary = summary

    def export(self, output_dir: Path) -> list[Path]:
        """Write JSON report to *output_dir*.

        Args:
            output_dir: Directory to write the JSON file into.

        Returns:
            Single-element list with the path to the generated file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        if self._summary:
            data = self._build_summary()
            filename = "dev-stats-summary.json"
        else:
            data = self._build_full()
            filename = "dev-stats.json"

        out_path = output_dir / filename
        out_path.write_text(
            json.dumps(data, indent=2, default=self._json_default, ensure_ascii=False) + "\n"
        )
        return [out_path]

    def _build_full(self) -> dict[str, object]:
        """Build the full JSON payload from the report.

        Returns:
            Dictionary ready for JSON serialisation.
        """
        return self._dataclass_to_dict(self._report)

    def _build_summary(self) -> dict[str, object]:
        """Build the summary JSON payload.

        Returns:
            Dictionary with top-level aggregate statistics.
        """
        rpt = self._report
        total_files = len(rpt.files)
        total_lines = sum(f.total_lines for f in rpt.files)
        code_lines = sum(f.code_lines for f in rpt.files)
        blank_lines = sum(f.blank_lines for f in rpt.files)
        comment_lines = sum(f.comment_lines for f in rpt.files)
        total_classes = sum(f.num_classes for f in rpt.files)
        total_functions = sum(f.num_functions for f in rpt.files)
        total_methods = sum(len(c.methods) for f in rpt.files for c in f.classes)

        summary: dict[str, object] = {
            "root": str(rpt.root),
            "files": total_files,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
            "classes": total_classes,
            "methods": total_methods,
            "functions": total_functions,
            "languages": [self._dataclass_to_dict(lang) for lang in rpt.languages],
        }

        if rpt.duplication is not None:
            summary["duplication_ratio"] = rpt.duplication.duplication_ratio
        if rpt.coverage is not None:
            summary["coverage_ratio"] = rpt.coverage.overall_ratio
        if rpt.coupling is not None:
            summary["coupling_modules"] = len(rpt.coupling.modules)

        return summary

    @staticmethod
    def _json_default(obj: object) -> object:
        """Default handler for non-serialisable types.

        Args:
            obj: The object to convert.

        Returns:
            JSON-compatible representation.

        Raises:
            TypeError: If the object cannot be serialised.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        msg = f"Object of type {type(obj).__name__} is not JSON serializable"
        raise TypeError(msg)

    @classmethod
    def _dataclass_to_dict(cls, obj: object) -> dict[str, object]:
        """Recursively convert a dataclass to a plain dictionary.

        Handles nested dataclasses, tuples, ``Path``, and ``datetime``.
        Enum values are converted to their ``.value`` string.

        Args:
            obj: A frozen dataclass instance.

        Returns:
            Plain dictionary suitable for ``json.dumps``.
        """
        if not dataclasses.is_dataclass(obj) or isinstance(obj, type):
            msg = f"Expected a dataclass instance, got {type(obj).__name__}"
            raise TypeError(msg)

        result: dict[str, object] = {}
        for fld in dataclasses.fields(obj):
            value = getattr(obj, fld.name)
            result[fld.name] = cls._convert_value(value)
        return result

    @classmethod
    def _convert_value(cls, value: object) -> object:
        """Convert a single value for JSON serialisation.

        Args:
            value: Any value from a dataclass field.

        Returns:
            JSON-compatible value.
        """
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, enum.Enum):
            return value.value
        if isinstance(value, (list, tuple)):
            return [cls._convert_value(item) for item in value]
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            return cls._dataclass_to_dict(value)
        return str(value)
