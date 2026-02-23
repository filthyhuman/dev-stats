"""Contributor analyzer building per-author profiles with alias merging."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from dev_stats.core.models import ContributorProfile, WorkPattern

if TYPE_CHECKING:
    from dev_stats.core.models import CommitRecord


class ContributorAnalyzer:
    """Analyses contributor profiles from commit records.

    Merges aliases (same name, different emails), computes per-author
    statistics, survival rates, and temporal work patterns.
    """

    def analyse(
        self,
        commits: list[CommitRecord],
        *,
        alias_map: dict[str, str] | None = None,
    ) -> list[ContributorProfile]:
        """Build contributor profiles from commit records.

        Args:
            commits: Commit records to analyse.
            alias_map: Optional mapping of email → canonical email.

        Returns:
            List of ``ContributorProfile`` sorted by commit count descending.
        """
        if not commits:
            return []

        resolved_map = alias_map or self._auto_detect_aliases(commits)
        grouped = self._group_by_author(commits, resolved_map)

        profiles: list[ContributorProfile] = []
        for canonical_email, author_commits in grouped.items():
            profile = self._build_profile(canonical_email, author_commits, resolved_map)
            profiles.append(profile)

        return sorted(profiles, key=lambda p: p.commit_count, reverse=True)

    def work_patterns(self, commits: list[CommitRecord]) -> list[WorkPattern]:
        """Compute temporal work patterns for each contributor.

        Args:
            commits: Commit records to analyse.

        Returns:
            List of ``WorkPattern`` per contributor.
        """
        if not commits:
            return []

        by_email: dict[str, list[CommitRecord]] = defaultdict(list)
        for c in commits:
            by_email[c.author_email].append(c)

        patterns: list[WorkPattern] = []
        for email, author_commits in by_email.items():
            hours = [0] * 24
            weekdays = [0] * 7
            tz_counts: dict[str, int] = defaultdict(int)

            for c in author_commits:
                hours[c.authored_date.hour] += 1
                weekdays[c.authored_date.weekday()] += 1
                tz_str = c.authored_date.strftime("%z") or "+0000"
                tz_counts[tz_str] += 1

            most_common_tz = max(tz_counts, key=tz_counts.get) if tz_counts else "+0000"  # type: ignore[arg-type]

            patterns.append(
                WorkPattern(
                    author_email=email,
                    hour_distribution=tuple(hours),
                    weekday_distribution=tuple(weekdays),
                    timezone=most_common_tz,
                )
            )

        return patterns

    @staticmethod
    def _auto_detect_aliases(
        commits: list[CommitRecord],
    ) -> dict[str, str]:
        """Detect aliases by matching author names across emails.

        Authors with the same display name but different emails are
        considered aliases. The email with the most commits wins.

        Args:
            commits: Commit records.

        Returns:
            Mapping of email → canonical email.
        """
        name_to_emails: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for c in commits:
            name_to_emails[c.author_name.lower()][c.author_email] += 1

        alias_map: dict[str, str] = {}
        for _name, email_counts in name_to_emails.items():
            if len(email_counts) <= 1:
                continue
            canonical = max(email_counts, key=email_counts.get)  # type: ignore[arg-type]
            for email in email_counts:
                alias_map[email] = canonical

        return alias_map

    @staticmethod
    def _group_by_author(
        commits: list[CommitRecord],
        alias_map: dict[str, str],
    ) -> dict[str, list[CommitRecord]]:
        """Group commits by canonical author email.

        Args:
            commits: Commit records.
            alias_map: Email → canonical email mapping.

        Returns:
            Mapping of canonical email → commits.
        """
        grouped: dict[str, list[CommitRecord]] = defaultdict(list)
        for c in commits:
            canonical = alias_map.get(c.author_email, c.author_email)
            grouped[canonical].append(c)
        return grouped

    @staticmethod
    def _build_profile(
        canonical_email: str,
        commits: list[CommitRecord],
        alias_map: dict[str, str],
    ) -> ContributorProfile:
        """Build a contributor profile from grouped commits.

        Args:
            canonical_email: The canonical email for this contributor.
            commits: All commits attributed to this contributor.
            alias_map: Email → canonical email mapping.

        Returns:
            A ``ContributorProfile``.
        """
        # Find all aliases for this canonical email
        aliases = tuple(
            email
            for email, canon in alias_map.items()
            if canon == canonical_email and email != canonical_email
        )

        # Use the most recent name
        sorted_commits = sorted(commits, key=lambda c: c.authored_date)
        name = sorted_commits[-1].author_name

        # Compute stats
        dates = [c.authored_date for c in commits]
        first_date = min(dates)
        last_date = max(dates)
        total_insertions = sum(c.insertions for c in commits)
        total_deletions = sum(c.deletions for c in commits)

        all_files: set[str] = set()
        for c in commits:
            for f in c.files:
                all_files.add(f.path)

        active_days = len({d.date() for d in dates})

        return ContributorProfile(
            name=name,
            email=canonical_email,
            aliases=aliases,
            commit_count=len(commits),
            first_commit_date=first_date,
            last_commit_date=last_date,
            insertions=total_insertions,
            deletions=total_deletions,
            files_touched=len(all_files),
            active_days=active_days,
        )
