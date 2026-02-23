"""Unit tests for PatternDetector."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from dev_stats.core.git.pattern_detector import (
    BinaryFileDetector,
    ConventionalCommitDetector,
    EmptyCommitDetector,
    FixupChainDetector,
    HotspotDetector,
    LargeCommitDetector,
    NightOwlDetector,
    PatternDetector,
    RevertChainDetector,
    ShortMessageDetector,
    WeekendWarriorDetector,
    WipInMainDetector,
)
from dev_stats.core.models import (
    ChangeType,
    CommitRecord,
    EnrichedCommit,
    FileChange,
)


def _make_commit(
    *,
    sha: str = "abc123",
    message: str = "fix: something",
    insertions: int = 10,
    deletions: int = 5,
    files: tuple[FileChange, ...] | None = None,
    days_ago: int = 0,
    hour: int = 12,
    weekday_offset: int = 0,
    authored_date: datetime | None = None,
    committed_date: datetime | None = None,
) -> CommitRecord:
    """Create a test CommitRecord."""
    base = datetime(2024, 6, 10, hour, 0, 0, tzinfo=UTC)
    ad = authored_date or (base - timedelta(days=days_ago) + timedelta(days=weekday_offset))
    cd = committed_date or ad
    if files is None:
        files = (
            FileChange(
                path="main.py",
                change_type=ChangeType.MODIFIED,
                insertions=insertions,
                deletions=deletions,
            ),
        )
    return CommitRecord(
        sha=sha,
        author_name="Alice",
        author_email="alice@example.com",
        authored_date=ad,
        committer_name="Alice",
        committer_email="alice@example.com",
        committed_date=cd,
        message=message,
        files=files,
        insertions=insertions,
        deletions=deletions,
    )


def _enrich(commit: CommitRecord, **kwargs: object) -> EnrichedCommit:
    """Wrap a CommitRecord in an EnrichedCommit."""
    return EnrichedCommit(commit=commit, **kwargs)  # type: ignore[arg-type]


class TestWipInMainDetector:
    """Tests for WIP detection."""

    def test_detects_wip(self) -> None:
        """WIP: subject is detected."""
        detector = WipInMainDetector()
        commits = [_make_commit(message="WIP: work in progress")]
        result = detector.detect(commits, [], protected_branches=("main",))

        assert len(result) == 1
        assert result[0].name == "wip_in_main"

    def test_no_wip(self) -> None:
        """Normal commit is not detected as WIP."""
        detector = WipInMainDetector()
        commits = [_make_commit(message="fix: proper commit")]
        result = detector.detect(commits, [], protected_branches=("main",))

        assert len(result) == 0


class TestLargeCommitDetector:
    """Tests for large commit detection."""

    def test_detects_large(self) -> None:
        """Commit with >500 churn is detected."""
        detector = LargeCommitDetector()
        commits = [_make_commit(insertions=400, deletions=200)]
        result = detector.detect(commits, [])

        assert len(result) == 1
        assert result[0].name == "large_commits"

    def test_normal_size(self) -> None:
        """Normal size commit is not detected."""
        detector = LargeCommitDetector()
        commits = [_make_commit(insertions=50, deletions=20)]
        result = detector.detect(commits, [])

        assert len(result) == 0


class TestEmptyCommitDetector:
    """Tests for empty commit detection."""

    def test_detects_empty(self) -> None:
        """Commit with no files is detected."""
        detector = EmptyCommitDetector()
        commits = [_make_commit(files=())]
        result = detector.detect(commits, [])

        assert len(result) == 1
        assert result[0].name == "empty_commits"

    def test_normal_commit(self) -> None:
        """Commit with files is not detected."""
        detector = EmptyCommitDetector()
        commits = [_make_commit()]
        result = detector.detect(commits, [])

        assert len(result) == 0


class TestFixupChainDetector:
    """Tests for fixup detection."""

    def test_detects_fixup(self) -> None:
        """Fixup commits are detected."""
        detector = FixupChainDetector()
        commit = _make_commit(message="fixup! original commit")
        enriched = [_enrich(commit, is_fixup=True)]
        result = detector.detect([commit], enriched)

        assert len(result) == 1
        assert result[0].name == "unsquashed_fixups"

    def test_no_fixups(self) -> None:
        """Normal commits are not detected."""
        detector = FixupChainDetector()
        commit = _make_commit()
        enriched = [_enrich(commit)]
        result = detector.detect([commit], enriched)

        assert len(result) == 0


class TestRevertChainDetector:
    """Tests for revert-of-revert detection."""

    def test_detects_double_revert(self) -> None:
        """Revert of a revert is detected."""
        detector = RevertChainDetector()
        c1 = _make_commit(sha="a", message='Revert "fix bug"')
        c2 = _make_commit(sha="b", message='Revert "Revert "fix bug""')
        enriched = [_enrich(c1, is_revert=True), _enrich(c2, is_revert=True)]
        result = detector.detect([c1, c2], enriched)

        assert len(result) == 1
        assert result[0].name == "revert_chains"

    def test_single_revert_ok(self) -> None:
        """Single revert is not flagged."""
        detector = RevertChainDetector()
        c1 = _make_commit(sha="a", message='Revert "fix bug"')
        enriched = [_enrich(c1, is_revert=True)]
        result = detector.detect([c1], enriched)

        assert len(result) == 0


class TestWeekendWarriorDetector:
    """Tests for weekend activity detection."""

    def test_detects_weekend_heavy(self) -> None:
        """>30% weekend commits triggers detection."""
        detector = WeekendWarriorDetector()
        # Create 10 commits, 5 on weekends (Saturday=5)
        commits = [_make_commit(sha=f"wd{i}", weekday_offset=0) for i in range(5)] + [
            _make_commit(sha=f"we{i}", weekday_offset=5) for i in range(5)
        ]
        result = detector.detect(commits, [])

        assert len(result) == 1
        assert result[0].name == "weekend_warrior"

    def test_few_weekend_ok(self) -> None:
        """<30% weekend commits is not flagged."""
        detector = WeekendWarriorDetector()
        commits = [_make_commit(sha=f"wd{i}", weekday_offset=0) for i in range(8)] + [
            _make_commit(sha=f"we{i}", weekday_offset=5) for i in range(2)
        ]
        result = detector.detect(commits, [])

        assert len(result) == 0


class TestNightOwlDetector:
    """Tests for night-owl detection."""

    def test_detects_night_commits(self) -> None:
        """>20% late-night commits triggers detection."""
        detector = NightOwlDetector()
        commits = [_make_commit(sha=f"d{i}", hour=12) for i in range(7)] + [
            _make_commit(sha=f"n{i}", hour=2) for i in range(3)
        ]
        result = detector.detect(commits, [])

        assert len(result) == 1
        assert result[0].name == "night_owl"

    def test_normal_hours_ok(self) -> None:
        """Normal-hour commits are not flagged."""
        detector = NightOwlDetector()
        commits = [_make_commit(sha=f"d{i}", hour=10) for i in range(10)]
        result = detector.detect(commits, [])

        assert len(result) == 0


class TestBinaryFileDetector:
    """Tests for binary file detection."""

    def test_detects_binary(self) -> None:
        """Binary file extension triggers detection."""
        detector = BinaryFileDetector()
        commits = [
            _make_commit(
                files=(FileChange(path="image.png", change_type=ChangeType.ADDED),),
            )
        ]
        result = detector.detect(commits, [])

        assert len(result) == 1
        assert result[0].name == "binary_files"
        assert "image.png" in result[0].affected_files

    def test_source_files_ok(self) -> None:
        """Source files are not flagged."""
        detector = BinaryFileDetector()
        commits = [_make_commit()]
        result = detector.detect(commits, [])

        assert len(result) == 0


class TestShortMessageDetector:
    """Tests for short message detection."""

    def test_detects_short(self) -> None:
        """Short messages (<10 chars) trigger detection."""
        detector = ShortMessageDetector()
        commits = [_make_commit(sha=f"s{i}", message="fix") for i in range(5)]
        result = detector.detect(commits, [])

        assert len(result) == 1
        assert result[0].name == "short_messages"

    def test_normal_messages_ok(self) -> None:
        """Properly-sized messages are not flagged."""
        detector = ShortMessageDetector()
        commits = [
            _make_commit(sha=f"n{i}", message="fix: resolve login timeout issue") for i in range(5)
        ]
        result = detector.detect(commits, [])

        assert len(result) == 0


class TestConventionalCommitDetector:
    """Tests for conventional commit consistency detection."""

    def test_detects_inconsistent(self) -> None:
        """Mixed conventional and non-conventional triggers detection."""
        detector = ConventionalCommitDetector()
        commits = [_make_commit(sha=f"c{i}", message="feat: add feature") for i in range(5)] + [
            _make_commit(sha=f"n{i}", message="added something") for i in range(5)
        ]
        result = detector.detect(commits, [])

        assert len(result) == 1
        assert result[0].name == "inconsistent_conventional"


class TestHotspotDetector:
    """Tests for hotspot file detection."""

    def test_detects_hotspot(self) -> None:
        """File changed in >30% of commits is detected."""
        detector = HotspotDetector()
        commits = [
            _make_commit(
                sha=f"c{i}",
                files=(FileChange(path="hot.py", change_type=ChangeType.MODIFIED),),
            )
            for i in range(10)
        ]
        result = detector.detect(commits, [])

        assert len(result) == 1
        assert result[0].name == "hotspot_files"
        assert "hot.py" in result[0].affected_files


class TestPatternDetectorChain:
    """Tests for the full detector chain."""

    def test_empty_commits(self) -> None:
        """Empty commits return no patterns."""
        detector = PatternDetector()
        result = detector.detect_all([], [])

        assert result == []

    def test_multiple_patterns(self) -> None:
        """Multiple detectors can fire simultaneously."""
        detector = PatternDetector()
        commits = [
            _make_commit(sha="w1", message="WIP: something", insertions=600, deletions=100),
        ]
        enriched = [_enrich(c) for c in commits]
        result = detector.detect_all(commits, enriched)

        names = {p.name for p in result}
        assert "wip_in_main" in names
        assert "large_commits" in names
