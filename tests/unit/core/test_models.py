"""Unit tests for core frozen dataclass models and enums."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from pathlib import Path

from dev_stats.core.models import (
    AnomalySeverity,
    BlameLine,
    BranchReport,
    BranchStatus,
    ChangeType,
    ClassReport,
    CommitRecord,
    CommitSizeCategory,
    ContributorProfile,
    DeletabilityCategory,
    DetectedPattern,
    EnrichedCommit,
    FileBlameReport,
    FileChange,
    FileReport,
    LanguageSummary,
    MergeStatus,
    MergeType,
    MethodReport,
    ModuleReport,
    ParameterReport,
    RepoReport,
    TagRecord,
)

_NOW = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestEnums:
    """Verify all enums have expected members."""

    def test_merge_type_members(self) -> None:
        """MergeType has four members."""
        assert len(MergeType) == 4

    def test_branch_status_members(self) -> None:
        """BranchStatus has three members."""
        assert len(BranchStatus) == 3

    def test_deletability_category_members(self) -> None:
        """DeletabilityCategory has three members."""
        assert len(DeletabilityCategory) == 3

    def test_change_type_members(self) -> None:
        """ChangeType has five members."""
        assert len(ChangeType) == 5

    def test_commit_size_category_members(self) -> None:
        """CommitSizeCategory has four members."""
        assert len(CommitSizeCategory) == 4

    def test_anomaly_severity_members(self) -> None:
        """AnomalySeverity has three members."""
        assert len(AnomalySeverity) == 3


# ---------------------------------------------------------------------------
# Code-structure dataclasses
# ---------------------------------------------------------------------------


class TestParameterReport:
    """Tests for ParameterReport."""

    def test_instantiation(self) -> None:
        """Create a ParameterReport with defaults."""
        p = ParameterReport(name="x")
        assert p.name == "x"
        assert p.type_annotation == ""
        assert p.has_default is False

    def test_frozen(self) -> None:
        """ParameterReport is immutable."""
        p = ParameterReport(name="x")
        _assert_frozen(p, "name", "y")


class TestMethodReport:
    """Tests for MethodReport."""

    def test_instantiation(self) -> None:
        """Create a MethodReport with defaults."""
        m = MethodReport(name="foo", line=1, end_line=5, lines=5)
        assert m.name == "foo"
        assert m.cyclomatic_complexity == 1

    def test_frozen(self) -> None:
        """MethodReport is immutable."""
        m = MethodReport(name="foo", line=1, end_line=5, lines=5)
        _assert_frozen(m, "name", "bar")

    def test_num_parameters(self) -> None:
        """num_parameters returns correct count."""
        params = (ParameterReport(name="a"), ParameterReport(name="b"))
        m = MethodReport(name="foo", line=1, end_line=5, lines=5, parameters=params)
        assert m.num_parameters == 2


class TestClassReport:
    """Tests for ClassReport."""

    def test_properties(self) -> None:
        """ClassReport properties return correct values."""
        init = MethodReport(name="__init__", line=2, end_line=4, lines=3, is_constructor=True)
        other = MethodReport(name="do_thing", line=5, end_line=10, lines=6)
        cr = ClassReport(
            name="Foo",
            line=1,
            end_line=10,
            lines=10,
            methods=(init, other),
            attributes=("x", "y"),
        )
        assert cr.num_methods == 2
        assert cr.num_attributes == 2
        assert cr.num_constructors == 1

    def test_frozen(self) -> None:
        """ClassReport is immutable."""
        cr = ClassReport(name="Foo", line=1, end_line=10, lines=10)
        _assert_frozen(cr, "name", "Bar")


class TestFileReport:
    """Tests for FileReport."""

    def test_comment_ratio(self) -> None:
        """comment_ratio returns correct float."""
        fr = FileReport(
            path=Path("a.py"),
            language="python",
            total_lines=100,
            code_lines=80,
            blank_lines=10,
            comment_lines=10,
        )
        assert fr.comment_ratio == 0.1

    def test_comment_ratio_zero_lines(self) -> None:
        """comment_ratio returns 0.0 for empty files."""
        fr = FileReport(
            path=Path("empty.py"),
            language="python",
            total_lines=0,
            code_lines=0,
            blank_lines=0,
            comment_lines=0,
        )
        assert fr.comment_ratio == 0.0

    def test_num_classes_and_functions(self) -> None:
        """num_classes and num_functions return correct counts."""
        cls = ClassReport(name="A", line=1, end_line=5, lines=5)
        func = MethodReport(name="f", line=6, end_line=10, lines=5)
        fr = FileReport(
            path=Path("a.py"),
            language="python",
            total_lines=10,
            code_lines=10,
            blank_lines=0,
            comment_lines=0,
            classes=(cls,),
            functions=(func,),
        )
        assert fr.num_classes == 1
        assert fr.num_functions == 1

    def test_frozen(self) -> None:
        """FileReport is immutable."""
        fr = FileReport(
            path=Path("a.py"),
            language="python",
            total_lines=0,
            code_lines=0,
            blank_lines=0,
            comment_lines=0,
        )
        _assert_frozen(fr, "language", "java")


class TestModuleReport:
    """Tests for ModuleReport."""

    def test_instantiation(self) -> None:
        """Create a ModuleReport."""
        mr = ModuleReport(name="core", path=Path("src/core"))
        assert mr.name == "core"
        assert mr.files == ()


class TestLanguageSummary:
    """Tests for LanguageSummary."""

    def test_instantiation(self) -> None:
        """Create a LanguageSummary."""
        ls = LanguageSummary(
            language="python",
            file_count=5,
            total_lines=500,
            code_lines=400,
            blank_lines=50,
            comment_lines=50,
        )
        assert ls.file_count == 5


# ---------------------------------------------------------------------------
# Git dataclasses
# ---------------------------------------------------------------------------


class TestCommitRecord:
    """Tests for CommitRecord."""

    def test_properties(self) -> None:
        """net_lines and churn_score compute correctly."""
        cr = CommitRecord(
            sha="abc123",
            author_name="Test",
            author_email="test@example.com",
            authored_date=_NOW,
            committer_name="Test",
            committer_email="test@example.com",
            committed_date=_NOW,
            message="fix stuff",
            insertions=30,
            deletions=10,
        )
        assert cr.net_lines == 20
        assert cr.churn_score == 40

    def test_frozen(self) -> None:
        """CommitRecord is immutable."""
        cr = CommitRecord(
            sha="abc123",
            author_name="Test",
            author_email="test@example.com",
            authored_date=_NOW,
            committer_name="Test",
            committer_email="test@example.com",
            committed_date=_NOW,
            message="fix",
        )
        _assert_frozen(cr, "sha", "xyz")


class TestEnrichedCommit:
    """Tests for EnrichedCommit."""

    def test_defaults(self) -> None:
        """EnrichedCommit defaults are sensible."""
        cr = CommitRecord(
            sha="abc",
            author_name="A",
            author_email="a@b.com",
            authored_date=_NOW,
            committer_name="A",
            committer_email="a@b.com",
            committed_date=_NOW,
            message="m",
        )
        ec = EnrichedCommit(commit=cr)
        assert ec.is_merge is False
        assert ec.size_category == CommitSizeCategory.SMALL


class TestFileChange:
    """Tests for FileChange."""

    def test_instantiation(self) -> None:
        """Create a FileChange."""
        fc = FileChange(path="a.py", change_type=ChangeType.MODIFIED, insertions=5)
        assert fc.insertions == 5
        assert fc.old_path is None


class TestBlameModels:
    """Tests for BlameLine, AuthorBlameStat, FileBlameReport."""

    def test_blame_line(self) -> None:
        """Create a BlameLine."""
        bl = BlameLine(
            line_number=1,
            author_name="A",
            author_email="a@b.com",
            date=_NOW,
            commit_sha="abc",
        )
        assert bl.line_number == 1

    def test_file_blame_report(self) -> None:
        """Create a FileBlameReport."""
        fbr = FileBlameReport(path="a.py", total_lines=10)
        assert fbr.authors == ()


# ---------------------------------------------------------------------------
# Branch / contributor dataclasses
# ---------------------------------------------------------------------------


class TestMergeStatus:
    """Tests for MergeStatus."""

    def test_not_merged(self) -> None:
        """Default MergeStatus is not merged."""
        ms = MergeStatus()
        assert ms.is_merged is False
        assert ms.merge_type == MergeType.NOT_MERGED

    def test_merged_into_default(self) -> None:
        """is_merged is True when merged into default."""
        ms = MergeStatus(merged_into_default=True)
        assert ms.is_merged is True
        assert ms.merge_type == MergeType.MERGE_COMMIT

    def test_merged_via_pr(self) -> None:
        """is_merged is True when has_pull_request is True."""
        ms = MergeStatus(has_pull_request=True)
        assert ms.is_merged is True

    def test_merged_into_target(self) -> None:
        """is_merged is True when merged into target."""
        ms = MergeStatus(merged_into_target=True)
        assert ms.is_merged is True


class TestBranchReport:
    """Tests for BranchReport."""

    def test_frozen(self) -> None:
        """BranchReport is immutable."""
        br = BranchReport(
            name="feature/x",
            is_remote=False,
            last_commit_date=_NOW,
            last_commit_sha="abc",
            commits_ahead=2,
            commits_behind=0,
            author_name="A",
            author_email="a@b.com",
            status=BranchStatus.ACTIVE,
            merge_status=MergeStatus(),
            deletability_score=10.0,
            deletability_category=DeletabilityCategory.KEEP,
        )
        _assert_frozen(br, "name", "other")


class TestContributorProfile:
    """Tests for ContributorProfile."""

    def test_instantiation(self) -> None:
        """Create a ContributorProfile."""
        cp = ContributorProfile(
            name="A",
            email="a@b.com",
            commit_count=10,
            first_commit_date=_NOW,
            last_commit_date=_NOW,
            insertions=100,
            deletions=50,
            files_touched=5,
        )
        assert cp.commit_count == 10


class TestTagRecord:
    """Tests for TagRecord."""

    def test_instantiation(self) -> None:
        """Create a TagRecord."""
        tr = TagRecord(name="v1.0", sha="abc", date=_NOW)
        assert tr.message is None


class TestDetectedPattern:
    """Tests for DetectedPattern."""

    def test_instantiation(self) -> None:
        """Create a DetectedPattern."""
        dp = DetectedPattern(
            name="big-commit",
            description="Very large commit detected",
            severity=AnomalySeverity.HIGH,
        )
        assert dp.affected_files == ()


# ---------------------------------------------------------------------------
# Root report
# ---------------------------------------------------------------------------


class TestRepoReport:
    """Tests for RepoReport."""

    def test_defaults(self) -> None:
        """RepoReport optional fields default to None."""
        rr = RepoReport(root=Path("."))
        assert rr.files == ()
        assert rr.commits is None
        assert rr.branches_report is None

    def test_frozen(self) -> None:
        """RepoReport is immutable."""
        rr = RepoReport(root=Path("."))
        _assert_frozen(rr, "root", Path("/tmp"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_frozen(instance: object, attr: str, value: object) -> None:
    """Assert that setting *attr* on a frozen dataclass raises."""
    assert dataclasses.is_dataclass(instance)
    try:
        setattr(instance, attr, value)
        msg = f"Expected FrozenInstanceError when setting {attr}"
        raise AssertionError(msg)
    except dataclasses.FrozenInstanceError:
        pass
