"""Commit enricher adding classification and cross-commit metadata."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from dev_stats.core.models import CommitSizeCategory, EnrichedCommit

if TYPE_CHECKING:
    from dev_stats.core.models import CommitRecord

# Conventional commit prefix: "type(scope): message" or "type: message".
_CONVENTIONAL_RE = re.compile(r"^(\w+)(?:\([^)]*\))?!?:\s")

# WIP / fixup / squash patterns.
_WIP_RE = re.compile(r"^(?:wip|WIP|work.in.progress)\b", re.IGNORECASE)
_FIXUP_RE = re.compile(r"^(?:fixup|squash)!\s")
_REVERT_RE = re.compile(r'^Revert\s+"?', re.IGNORECASE)


class CommitEnricher:
    """Enriches raw commit records with classification metadata.

    Adds merge detection, fixup/squash/revert flags, size categories,
    conventional-commit type extraction, streak detection, and percentile
    ranking.
    """

    def enrich(self, commits: list[CommitRecord]) -> list[EnrichedCommit]:
        """Enrich a list of commit records.

        Args:
            commits: Raw commit records in reverse chronological order.

        Returns:
            List of ``EnrichedCommit`` instances.
        """
        return [self._enrich_single(c) for c in commits]

    def _enrich_single(self, commit: CommitRecord) -> EnrichedCommit:
        """Enrich a single commit record.

        Args:
            commit: A raw ``CommitRecord``.

        Returns:
            An ``EnrichedCommit``.
        """
        subject = commit.message.split("\n", 1)[0]
        is_merge = self._detect_merge(commit)
        is_fixup = bool(_FIXUP_RE.match(subject))
        is_revert = bool(_REVERT_RE.match(subject))
        size_category = self._classify_size(commit)
        conventional_type = self._extract_conventional_type(subject)

        return EnrichedCommit(
            commit=commit,
            is_merge=is_merge,
            is_fixup=is_fixup,
            is_revert=is_revert,
            size_category=size_category,
            conventional_type=conventional_type,
        )

    def compute_streaks(self, enriched: list[EnrichedCommit]) -> dict[str, int]:
        """Compute per-author consecutive-day commit streaks.

        Args:
            enriched: Enriched commits in reverse chronological order.

        Returns:
            Mapping of author email to maximum streak length (days).
        """
        # Group commits by author email, sorted chronologically.
        by_author: dict[str, list[EnrichedCommit]] = {}
        for ec in enriched:
            email = ec.commit.author_email
            by_author.setdefault(email, []).append(ec)

        streaks: dict[str, int] = {}
        for email, author_commits in by_author.items():
            dates = sorted({ec.commit.authored_date.date() for ec in author_commits})
            max_streak = 1
            current_streak = 1
            for i in range(1, len(dates)):
                delta = (dates[i] - dates[i - 1]).days
                if delta == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
            streaks[email] = max_streak if dates else 0

        return streaks

    def churn_percentiles(self, enriched: list[EnrichedCommit]) -> dict[str, float]:
        """Rank commits by churn and return each SHA's percentile.

        Args:
            enriched: Enriched commits.

        Returns:
            Mapping of SHA to percentile (0.0-1.0).
        """
        if not enriched:
            return {}

        sorted_commits = sorted(enriched, key=lambda ec: ec.commit.churn_score)
        n = len(sorted_commits)
        return {ec.commit.sha: i / n for i, ec in enumerate(sorted_commits)}

    @staticmethod
    def _detect_merge(commit: CommitRecord) -> bool:
        """Detect if a commit is a merge.

        Uses message-based heuristic since CommitRecord doesn't store
        parent hashes directly.

        Args:
            commit: A raw commit record.

        Returns:
            ``True`` if the commit appears to be a merge.
        """
        subject = commit.message.split("\n", 1)[0].lower()
        return subject.startswith("merge ")

    @staticmethod
    def _classify_size(commit: CommitRecord) -> CommitSizeCategory:
        """Classify a commit by its churn size.

        Args:
            commit: A raw commit record.

        Returns:
            A ``CommitSizeCategory``.
        """
        churn = commit.churn_score
        if churn <= 50:
            return CommitSizeCategory.SMALL
        if churn <= 200:
            return CommitSizeCategory.MEDIUM
        if churn <= 500:
            return CommitSizeCategory.LARGE
        return CommitSizeCategory.ENORMOUS

    @staticmethod
    def _extract_conventional_type(subject: str) -> str | None:
        """Extract the conventional-commit type prefix.

        Args:
            subject: Commit subject line.

        Returns:
            The type string (e.g. ``"feat"``, ``"fix"``), or ``None``.
        """
        m = _CONVENTIONAL_RE.match(subject)
        return m.group(1) if m else None
