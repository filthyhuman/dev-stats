"""Churn scorer computing per-file change frequency from commit data."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from dev_stats.core.models import FileChurn

if TYPE_CHECKING:
    from dev_stats.core.models import CommitRecord


class ChurnScorer:
    """Computes per-file churn scores from commit records.

    Churn is defined as insertions + deletions per file across all commits.
    High-churn files may indicate unstable or problematic code.
    """

    def score(self, commits: list[CommitRecord]) -> list[FileChurn]:
        """Compute churn scores per file from commit history.

        Args:
            commits: List of commit records with file changes.

        Returns:
            List of ``FileChurn`` sorted by churn score descending.
        """
        stats: dict[str, dict[str, int]] = defaultdict(lambda: {"commits": 0, "ins": 0, "del": 0})

        for commit in commits:
            for fc in commit.files:
                entry = stats[fc.path]
                entry["commits"] += 1
                entry["ins"] += fc.insertions
                entry["del"] += fc.deletions

        results: list[FileChurn] = []
        for path, data in stats.items():
            results.append(
                FileChurn(
                    path=path,
                    commit_count=data["commits"],
                    insertions=data["ins"],
                    deletions=data["del"],
                    churn_score=data["ins"] + data["del"],
                )
            )

        return sorted(results, key=lambda f: f.churn_score, reverse=True)
