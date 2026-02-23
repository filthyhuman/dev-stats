"""Timeline builder producing LOC series, language evolution, and team growth."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from dev_stats.core.models import TimelinePoint

if TYPE_CHECKING:
    from dev_stats.core.models import CommitRecord


class TimelineBuilder:
    """Builds timeline series from commit records.

    Produces sorted data points for LOC evolution, language breakdown
    over time, and team growth (unique contributors over time).
    """

    def loc_timeline(self, commits: list[CommitRecord]) -> list[TimelinePoint]:
        """Build a cumulative LOC timeline.

        Each data point represents the running net line count at a
        given commit date.

        Args:
            commits: Commit records in any order.

        Returns:
            List of ``TimelinePoint`` sorted by date ascending.
        """
        if not commits:
            return []

        sorted_commits = sorted(commits, key=lambda c: c.authored_date)

        points: list[TimelinePoint] = []
        cumulative = 0
        for c in sorted_commits:
            cumulative += c.net_lines
            points.append(
                TimelinePoint(
                    date=c.authored_date,
                    value=cumulative,
                    label="loc",
                )
            )

        return points

    def language_timeline(
        self,
        commits: list[CommitRecord],
    ) -> dict[str, list[TimelinePoint]]:
        """Build per-language LOC evolution timelines.

        Groups file changes by extension and tracks cumulative lines
        per language over time.

        Args:
            commits: Commit records in any order.

        Returns:
            Mapping of language extension → sorted timeline points.
        """
        if not commits:
            return {}

        sorted_commits = sorted(commits, key=lambda c: c.authored_date)

        lang_cumulative: dict[str, int] = defaultdict(int)
        lang_series: dict[str, list[TimelinePoint]] = defaultdict(list)

        for c in sorted_commits:
            lang_deltas: dict[str, int] = defaultdict(int)
            for f in c.files:
                ext = self._file_extension(f.path)
                if ext:
                    lang_deltas[ext] += f.insertions - f.deletions

            for ext, delta in lang_deltas.items():
                lang_cumulative[ext] += delta
                lang_series[ext].append(
                    TimelinePoint(
                        date=c.authored_date,
                        value=lang_cumulative[ext],
                        label=ext,
                    )
                )

        return dict(lang_series)

    def team_growth(self, commits: list[CommitRecord]) -> list[TimelinePoint]:
        """Build a team growth timeline.

        Each data point represents the total number of unique
        contributors at that point in time.

        Args:
            commits: Commit records in any order.

        Returns:
            List of ``TimelinePoint`` sorted by date ascending.
        """
        if not commits:
            return []

        sorted_commits = sorted(commits, key=lambda c: c.authored_date)

        seen_authors: set[str] = set()
        points: list[TimelinePoint] = []

        for c in sorted_commits:
            seen_authors.add(c.author_email)
            points.append(
                TimelinePoint(
                    date=c.authored_date,
                    value=len(seen_authors),
                    label="contributors",
                )
            )

        return points

    @staticmethod
    def _file_extension(path: str) -> str:
        """Extract the file extension as a language proxy.

        Args:
            path: File path.

        Returns:
            Extension without dot (e.g. ``"py"``), or empty string.
        """
        if "." not in path:
            return ""
        return path.rsplit(".", 1)[-1].lower()
