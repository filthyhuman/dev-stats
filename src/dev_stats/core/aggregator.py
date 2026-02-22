"""Aggregator that assembles per-file reports into a unified RepoReport."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from dev_stats.core.metrics.coupling_analyser import CouplingAnalyser
from dev_stats.core.models import (
    FileReport,
    LanguageSummary,
    ModuleReport,
    RepoReport,
)

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.core.models import (
        CommitRecord,
        CouplingReport,
        CoverageReport,
        DuplicationReport,
        FileChurn,
    )


class Aggregator:
    """Builds a :class:`RepoReport` from a list of :class:`FileReport` objects.

    Computes totals, averages, per-language summaries, per-module
    groupings, and optional metrics (duplication, coupling, coverage, churn).
    """

    def aggregate(
        self,
        files: list[FileReport],
        repo_root: Path,
        *,
        duplication: DuplicationReport | None = None,
        coverage: CoverageReport | None = None,
        commits: list[CommitRecord] | None = None,
    ) -> RepoReport:
        """Aggregate file reports into a single repository report.

        Args:
            files: Individual file analysis results.
            repo_root: Absolute path to the repository root.
            duplication: Pre-computed duplication report.
            coverage: Pre-computed coverage report.
            commits: Commit records for churn scoring.

        Returns:
            A frozen :class:`RepoReport`.
        """
        coupling = self._compute_coupling(files)
        churn = self._compute_churn(commits) if commits else None

        return RepoReport(
            root=repo_root,
            files=tuple(files),
            modules=self._compute_module_reports(files),
            languages=self._compute_language_summaries(files),
            duplication=duplication,
            coupling=coupling,
            coverage=coverage,
            file_churn=tuple(churn) if churn else None,
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

    @staticmethod
    def _compute_coupling(files: list[FileReport]) -> CouplingReport:
        """Compute coupling metrics from file imports.

        Args:
            files: File reports with import data.

        Returns:
            A ``CouplingReport``.
        """
        analyser = CouplingAnalyser()
        return analyser.analyse(files)

    @staticmethod
    def _compute_churn(
        commits: list[CommitRecord] | None,
    ) -> list[FileChurn] | None:
        """Compute per-file churn from commit records.

        Args:
            commits: Commit records with file changes.

        Returns:
            List of ``FileChurn`` or ``None`` if no commits.
        """
        if not commits:
            return None
        from dev_stats.core.metrics.churn_scorer import ChurnScorer

        scorer = ChurnScorer()
        return scorer.score(commits)
