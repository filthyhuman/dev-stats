"""Aggregator that assembles per-file reports into a unified RepoReport."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from dev_stats.core.models import (
    FileReport,
    LanguageSummary,
    ModuleReport,
    RepoReport,
)

if TYPE_CHECKING:
    from pathlib import Path


class Aggregator:
    """Builds a :class:`RepoReport` from a list of :class:`FileReport` objects.

    Computes totals, averages, per-language summaries, and per-module
    groupings.
    """

    def aggregate(
        self,
        files: list[FileReport],
        repo_root: Path,
    ) -> RepoReport:
        """Aggregate file reports into a single repository report.

        Args:
            files: Individual file analysis results.
            repo_root: Absolute path to the repository root.

        Returns:
            A frozen :class:`RepoReport`.
        """
        return RepoReport(
            root=repo_root,
            files=tuple(files),
            modules=self._compute_module_reports(files),
            languages=self._compute_language_summaries(files),
        )

    @staticmethod
    def _compute_language_summaries(
        files: list[FileReport],
    ) -> tuple[LanguageSummary, ...]:
        """Group files by language and compute per-language summaries.

        Args:
            files: File reports to group.

        Returns:
            Tuple of :class:`LanguageSummary` sorted by file count descending.
        """
        by_lang: dict[str, list[FileReport]] = defaultdict(list)
        for f in files:
            by_lang[f.language].append(f)

        summaries: list[LanguageSummary] = []
        for lang, lang_files in by_lang.items():
            summaries.append(
                LanguageSummary(
                    language=lang,
                    file_count=len(lang_files),
                    total_lines=sum(f.total_lines for f in lang_files),
                    code_lines=sum(f.code_lines for f in lang_files),
                    blank_lines=sum(f.blank_lines for f in lang_files),
                    comment_lines=sum(f.comment_lines for f in lang_files),
                )
            )

        return tuple(sorted(summaries, key=lambda s: s.file_count, reverse=True))

    @staticmethod
    def _compute_module_reports(
        files: list[FileReport],
    ) -> tuple[ModuleReport, ...]:
        """Group files by parent directory into module reports.

        Args:
            files: File reports to group.

        Returns:
            Tuple of :class:`ModuleReport` sorted by module name.
        """
        by_dir: dict[Path, list[FileReport]] = defaultdict(list)
        for f in files:
            parent = f.path.parent
            by_dir[parent].append(f)

        modules: list[ModuleReport] = []
        for dir_path, dir_files in by_dir.items():
            modules.append(
                ModuleReport(
                    name=str(dir_path) if str(dir_path) != "." else "(root)",
                    path=dir_path,
                    files=tuple(dir_files),
                )
            )

        return tuple(sorted(modules, key=lambda m: m.name))
