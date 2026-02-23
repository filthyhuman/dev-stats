"""Pattern detector using Chain of Responsibility for anomaly detection."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dev_stats.core.models import AnomalySeverity, DetectedPattern

if TYPE_CHECKING:
    from dev_stats.core.models import CommitRecord, EnrichedCommit


class BaseDetector(ABC):
    """Abstract base for a single anomaly detector in the chain.

    Subclasses implement ``detect`` to inspect commits and return any
    detected patterns.
    """

    @abstractmethod
    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Run detection on the commit stream.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns (may be empty).
        """


class WipInMainDetector(BaseDetector):
    """Detects WIP commits on protected branches."""

    _WIP_RE = re.compile(r"^(?:wip|WIP|work.in.progress)\b", re.IGNORECASE)

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect WIP commits.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected WIP patterns.
        """
        wip_commits = [c for c in commits if self._WIP_RE.match(c.message.split("\n", 1)[0])]
        if not wip_commits:
            return []

        return [
            DetectedPattern(
                name="wip_in_main",
                description="WIP commits found on protected branch",
                severity=AnomalySeverity.MEDIUM,
                evidence=f"{len(wip_commits)} WIP commit(s): {wip_commits[0].sha[:8]}...",
            )
        ]


class LargeCommitDetector(BaseDetector):
    """Detects unusually large commits."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect large commits (>500 lines changed).

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected large commit patterns.
        """
        large = [c for c in commits if c.churn_score > 500]
        if not large:
            return []

        return [
            DetectedPattern(
                name="large_commits",
                description="Commits with >500 lines changed detected",
                severity=AnomalySeverity.LOW,
                evidence=(
                    f"{len(large)} large commit(s), "
                    f"largest: {max(c.churn_score for c in large)} lines"
                ),
            )
        ]


class ForceRebaseDetector(BaseDetector):
    """Detects potential force-push or rebase patterns."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect commits that look like force-push rewrites.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        # Detect when author and committer dates differ significantly
        suspicious = []
        for c in commits:
            delta = abs((c.authored_date - c.committed_date).total_seconds())
            if delta > 86400:  # >1 day difference
                suspicious.append(c)

        if not suspicious:
            return []

        return [
            DetectedPattern(
                name="possible_rebase",
                description="Commits with large author/committer date gaps (possible rebase)",
                severity=AnomalySeverity.LOW,
                evidence=f"{len(suspicious)} commit(s) with >1 day author/committer date gap",
            )
        ]


class EmptyCommitDetector(BaseDetector):
    """Detects empty commits (no file changes)."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect commits with no file changes.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        empty = [c for c in commits if not c.files]
        if not empty:
            return []

        return [
            DetectedPattern(
                name="empty_commits",
                description="Commits with no file changes",
                severity=AnomalySeverity.LOW,
                evidence=f"{len(empty)} empty commit(s)",
            )
        ]


class FixupChainDetector(BaseDetector):
    """Detects chains of fixup/squash commits."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect fixup/squash commits that weren't squashed.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        fixups = [ec for ec in enriched if ec.is_fixup]
        if not fixups:
            return []

        return [
            DetectedPattern(
                name="unsquashed_fixups",
                description="Fixup/squash commits that were not rebased",
                severity=AnomalySeverity.MEDIUM,
                evidence=f"{len(fixups)} unsquashed fixup commit(s)",
            )
        ]


class RevertChainDetector(BaseDetector):
    """Detects revert-of-revert chains."""

    _REVERT_RE = re.compile(r'^Revert\s+"?', re.IGNORECASE)

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect revert-of-revert patterns.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        reverts = [ec for ec in enriched if ec.is_revert]
        if len(reverts) < 2:
            return []

        # Check for reverts of reverts
        double_reverts = [
            ec for ec in reverts if ec.commit.message.lower().startswith('revert "revert')
        ]
        if not double_reverts:
            return []

        return [
            DetectedPattern(
                name="revert_chains",
                description="Revert-of-revert commits detected",
                severity=AnomalySeverity.HIGH,
                evidence=f"{len(double_reverts)} revert-of-revert commit(s)",
            )
        ]


class WeekendWarriorDetector(BaseDetector):
    """Detects significant weekend commit activity."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect heavy weekend activity.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        if len(commits) < 10:
            return []

        weekend = [c for c in commits if c.authored_date.weekday() >= 5]
        ratio = len(weekend) / len(commits)

        if ratio < 0.3:
            return []

        return [
            DetectedPattern(
                name="weekend_warrior",
                description="High proportion of weekend commits",
                severity=AnomalySeverity.LOW,
                evidence=f"{len(weekend)}/{len(commits)} commits ({ratio:.0%}) on weekends",
            )
        ]


class NightOwlDetector(BaseDetector):
    """Detects significant late-night commit activity."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect late-night commits (midnight to 5am).

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        if len(commits) < 10:
            return []

        late_night = [c for c in commits if c.authored_date.hour < 5]
        ratio = len(late_night) / len(commits)

        if ratio < 0.2:
            return []

        return [
            DetectedPattern(
                name="night_owl",
                description="Significant late-night commit activity (midnight-5am)",
                severity=AnomalySeverity.LOW,
                evidence=f"{len(late_night)}/{len(commits)} commits ({ratio:.0%}) late at night",
            )
        ]


class SingleFileCommitDetector(BaseDetector):
    """Detects repos dominated by single-file commits."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect when most commits touch only one file.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        if len(commits) < 10:
            return []

        single_file = [c for c in commits if len(c.files) == 1]
        ratio = len(single_file) / len(commits)

        if ratio < 0.7:
            return []

        return [
            DetectedPattern(
                name="single_file_commits",
                description="Most commits touch only one file",
                severity=AnomalySeverity.LOW,
                evidence=f"{len(single_file)}/{len(commits)} commits ({ratio:.0%}) touch one file",
            )
        ]


class BinaryFileDetector(BaseDetector):
    """Detects binary files being committed."""

    _BINARY_EXT = frozenset(
        {
            "exe",
            "dll",
            "so",
            "dylib",
            "bin",
            "zip",
            "tar",
            "gz",
            "jar",
            "war",
            "png",
            "jpg",
            "jpeg",
            "gif",
            "bmp",
            "ico",
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
        }
    )

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect binary files in commits.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        binary_files: set[str] = set()
        for c in commits:
            for f in c.files:
                ext = f.path.rsplit(".", 1)[-1].lower() if "." in f.path else ""
                if ext in self._BINARY_EXT:
                    binary_files.add(f.path)

        if not binary_files:
            return []

        return [
            DetectedPattern(
                name="binary_files",
                description="Binary files tracked in repository",
                severity=AnomalySeverity.MEDIUM,
                affected_files=tuple(sorted(binary_files)),
                evidence=f"{len(binary_files)} binary file(s) committed",
            )
        ]


class MergeHeavyDetector(BaseDetector):
    """Detects repos with high merge commit ratios."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect high merge commit ratio (>30%).

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        if len(enriched) < 10:
            return []

        merges = [ec for ec in enriched if ec.is_merge]
        ratio = len(merges) / len(enriched)

        if ratio < 0.3:
            return []

        return [
            DetectedPattern(
                name="merge_heavy",
                description="High proportion of merge commits",
                severity=AnomalySeverity.LOW,
                evidence=f"{len(merges)}/{len(enriched)} commits ({ratio:.0%}) are merges",
            )
        ]


class ShortMessageDetector(BaseDetector):
    """Detects commits with very short messages."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect commits with subject lines shorter than 10 chars.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        if len(commits) < 5:
            return []

        short = [c for c in commits if len(c.message.split("\n", 1)[0].strip()) < 10]
        ratio = len(short) / len(commits)

        if ratio < 0.2:
            return []

        return [
            DetectedPattern(
                name="short_messages",
                description="Many commits have very short messages (<10 chars)",
                severity=AnomalySeverity.MEDIUM,
                evidence=f"{len(short)}/{len(commits)} commits ({ratio:.0%}) have short subjects",
            )
        ]


class ConventionalCommitDetector(BaseDetector):
    """Detects inconsistent use of conventional commits."""

    _CONVENTIONAL_RE = re.compile(r"^(\w+)(?:\([^)]*\))?!?:\s")

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect inconsistent conventional commit usage.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        if len(commits) < 10:
            return []

        conventional = [
            c for c in commits if self._CONVENTIONAL_RE.match(c.message.split("\n", 1)[0])
        ]
        ratio = len(conventional) / len(commits)

        # Only flag if partially adopted (20-80%)
        if ratio < 0.2 or ratio > 0.8:
            return []

        return [
            DetectedPattern(
                name="inconsistent_conventional",
                description="Conventional commit format used inconsistently",
                severity=AnomalySeverity.LOW,
                evidence=(
                    f"{len(conventional)}/{len(commits)} commits "
                    f"({ratio:.0%}) use conventional format"
                ),
            )
        ]


class HotspotDetector(BaseDetector):
    """Detects files that are changed very frequently (hotspots)."""

    def detect(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Detect frequently changed files.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Names of protected branches.

        Returns:
            List of detected patterns.
        """
        if len(commits) < 10:
            return []

        file_counts: dict[str, int] = {}
        for c in commits:
            for f in c.files:
                file_counts[f.path] = file_counts.get(f.path, 0) + 1

        threshold = len(commits) * 0.3
        hotspots = {path: count for path, count in file_counts.items() if count > threshold}

        if not hotspots:
            return []

        top = sorted(hotspots.items(), key=lambda x: x[1], reverse=True)[:5]
        return [
            DetectedPattern(
                name="hotspot_files",
                description="Files changed in >30% of commits",
                severity=AnomalySeverity.LOW,
                affected_files=tuple(path for path, _ in top),
                evidence="; ".join(f"{path} ({count}x)" for path, count in top),
            )
        ]


class PatternDetector:
    """Chain of Responsibility pattern detector.

    Runs a chain of individual detectors over the commit stream and
    collects all detected patterns.
    """

    def __init__(self) -> None:
        """Initialise with all built-in detectors."""
        self._detectors: list[BaseDetector] = [
            WipInMainDetector(),
            LargeCommitDetector(),
            ForceRebaseDetector(),
            EmptyCommitDetector(),
            FixupChainDetector(),
            RevertChainDetector(),
            WeekendWarriorDetector(),
            NightOwlDetector(),
            SingleFileCommitDetector(),
            BinaryFileDetector(),
            MergeHeavyDetector(),
            ShortMessageDetector(),
            ConventionalCommitDetector(),
            HotspotDetector(),
        ]

    def detect_all(
        self,
        commits: list[CommitRecord],
        enriched: list[EnrichedCommit],
        *,
        protected_branches: tuple[str, ...] = (),
    ) -> list[DetectedPattern]:
        """Run all detectors and collect results.

        Args:
            commits: Raw commit records.
            enriched: Enriched commit records.
            protected_branches: Protected branch names.

        Returns:
            List of all detected patterns.
        """
        patterns: list[DetectedPattern] = []
        for detector in self._detectors:
            patterns.extend(
                detector.detect(
                    commits,
                    enriched,
                    protected_branches=protected_branches,
                )
            )
        return patterns
