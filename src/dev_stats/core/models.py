"""Frozen dataclass models and enums for dev-stats analysis results.

Every model is ``frozen=True`` and uses ``tuple`` for sequences to guarantee
hashability and immutability.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MergeType(enum.Enum):
    """How a branch was merged into its target."""

    SQUASH = "squash"
    MERGE_COMMIT = "merge_commit"
    FAST_FORWARD = "fast_forward"
    NOT_MERGED = "not_merged"


class BranchStatus(enum.Enum):
    """Activity status of a branch."""

    ACTIVE = "active"
    STALE = "stale"
    ABANDONED = "abandoned"


class DeletabilityCategory(enum.Enum):
    """Recommendation strength for branch deletion."""

    SAFE = "safe"
    CAUTION = "caution"
    KEEP = "keep"


class ChangeType(enum.Enum):
    """Type of change applied to a file in a commit."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"


class CommitSizeCategory(enum.Enum):
    """T-shirt size classification of a commit."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENORMOUS = "enormous"


class AnomalySeverity(enum.Enum):
    """Severity level for detected patterns and anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Code-structure dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParameterReport:
    """A single parameter in a function/method signature.

    Attributes:
        name: Parameter name.
        type_annotation: Type annotation string, or empty if absent.
        has_default: Whether the parameter has a default value.
    """

    name: str
    type_annotation: str = ""
    has_default: bool = False


@dataclass(frozen=True)
class MethodReport:
    """Analysis report for a single function or method.

    Attributes:
        name: Function/method name.
        line: Start line number (1-based).
        end_line: End line number (1-based).
        lines: Total line count.
        parameters: Parameter list.
        cyclomatic_complexity: McCabe cyclomatic complexity.
        cognitive_complexity: Cognitive complexity score.
        nesting_depth: Maximum nesting depth.
        is_constructor: Whether this is an ``__init__`` method.
        docstring: First line of docstring, or ``None``.
        decorators: Decorator names.
    """

    name: str
    line: int
    end_line: int
    lines: int
    parameters: tuple[ParameterReport, ...] = ()
    cyclomatic_complexity: int = 1
    cognitive_complexity: int = 0
    nesting_depth: int = 0
    is_constructor: bool = False
    docstring: str | None = None
    decorators: tuple[str, ...] = ()

    @property
    def num_parameters(self) -> int:
        """Return the number of parameters."""
        return len(self.parameters)


@dataclass(frozen=True)
class ClassReport:
    """Analysis report for a single class.

    Attributes:
        name: Class name.
        line: Start line number (1-based).
        end_line: End line number (1-based).
        lines: Total line count.
        methods: Parsed methods.
        attributes: Instance attribute names.
        base_classes: Base class names.
        docstring: First line of docstring, or ``None``.
        decorators: Decorator names.
    """

    name: str
    line: int
    end_line: int
    lines: int
    methods: tuple[MethodReport, ...] = ()
    attributes: tuple[str, ...] = ()
    base_classes: tuple[str, ...] = ()
    docstring: str | None = None
    decorators: tuple[str, ...] = ()

    @property
    def num_methods(self) -> int:
        """Return the number of methods."""
        return len(self.methods)

    @property
    def num_attributes(self) -> int:
        """Return the number of attributes."""
        return len(self.attributes)

    @property
    def num_constructors(self) -> int:
        """Return the number of constructor methods (``__init__``)."""
        return sum(1 for m in self.methods if m.is_constructor)


@dataclass(frozen=True)
class FileReport:
    """Analysis report for a single source file.

    Attributes:
        path: Repository-relative file path.
        language: Detected language name (lowercase).
        total_lines: Total number of lines.
        code_lines: Non-blank, non-comment lines.
        blank_lines: Blank lines.
        comment_lines: Comment-only lines.
        classes: Parsed classes.
        functions: Top-level functions (not methods).
        imports: Import statements.
    """

    path: Path
    language: str
    total_lines: int
    code_lines: int
    blank_lines: int
    comment_lines: int
    classes: tuple[ClassReport, ...] = ()
    functions: tuple[MethodReport, ...] = ()
    imports: tuple[str, ...] = ()

    @property
    def comment_ratio(self) -> float:
        """Return comment lines as a fraction of total lines.

        Returns ``0.0`` when ``total_lines`` is zero.
        """
        if self.total_lines == 0:
            return 0.0
        return self.comment_lines / self.total_lines

    @property
    def num_classes(self) -> int:
        """Return the number of classes."""
        return len(self.classes)

    @property
    def num_functions(self) -> int:
        """Return the number of top-level functions."""
        return len(self.functions)


# ---------------------------------------------------------------------------
# Metrics dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DuplicateBlock:
    """A pair of duplicated code blocks.

    Attributes:
        file_a: Path of the first file.
        file_b: Path of the second file.
        line_a: Start line in file A.
        line_b: Start line in file B.
        length: Number of duplicated lines.
    """

    file_a: str
    file_b: str
    line_a: int
    line_b: int
    length: int


@dataclass(frozen=True)
class DuplicationReport:
    """Duplication analysis results for the entire repository.

    Attributes:
        duplicates: Detected duplicate blocks.
        total_duplicated_lines: Total duplicated line count.
        duplication_ratio: Duplicated lines / total code lines.
    """

    duplicates: tuple[DuplicateBlock, ...] = ()
    total_duplicated_lines: int = 0
    duplication_ratio: float = 0.0


@dataclass(frozen=True)
class ModuleCoupling:
    """Coupling metrics for a single module.

    Attributes:
        name: Module name.
        afferent: Afferent coupling (Ca) - modules that depend on this one.
        efferent: Efferent coupling (Ce) - modules this one depends on.
        instability: Instability I = Ce / (Ca + Ce).
        abstractness: Abstractness A = abstract classes / total classes.
        distance: Distance from main sequence D = |A + I - 1|.
    """

    name: str
    afferent: int = 0
    efferent: int = 0
    instability: float = 0.0
    abstractness: float = 0.0
    distance: float = 0.0


@dataclass(frozen=True)
class CouplingReport:
    """Coupling analysis results for the repository.

    Attributes:
        modules: Per-module coupling metrics.
    """

    modules: tuple[ModuleCoupling, ...] = ()


@dataclass(frozen=True)
class FileCoverage:
    """Coverage data for a single file.

    Attributes:
        path: File path.
        covered_lines: Number of covered lines.
        total_lines: Total coverable lines.
        coverage_ratio: Covered / total.
    """

    path: str
    covered_lines: int = 0
    total_lines: int = 0
    coverage_ratio: float = 0.0


@dataclass(frozen=True)
class CoverageReport:
    """Test coverage results for the repository.

    Attributes:
        files: Per-file coverage.
        overall_ratio: Overall coverage ratio.
    """

    files: tuple[FileCoverage, ...] = ()
    overall_ratio: float = 0.0


@dataclass(frozen=True)
class FileChurn:
    """Churn score for a single file.

    Attributes:
        path: File path.
        commit_count: Number of commits touching this file.
        insertions: Total lines inserted.
        deletions: Total lines deleted.
        churn_score: insertions + deletions.
    """

    path: str
    commit_count: int = 0
    insertions: int = 0
    deletions: int = 0
    churn_score: int = 0


@dataclass(frozen=True)
class ModuleReport:
    """Aggregated report for a directory (module).

    Attributes:
        name: Module/directory name.
        path: Repository-relative path.
        files: File reports within this module.
    """

    name: str
    path: Path
    files: tuple[FileReport, ...] = ()


@dataclass(frozen=True)
class LanguageSummary:
    """Aggregated statistics for a single language.

    Attributes:
        language: Language name (lowercase).
        file_count: Number of files.
        total_lines: Total lines across all files.
        code_lines: Code lines across all files.
        blank_lines: Blank lines across all files.
        comment_lines: Comment lines across all files.
    """

    language: str
    file_count: int
    total_lines: int
    code_lines: int
    blank_lines: int
    comment_lines: int


# ---------------------------------------------------------------------------
# Git dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FileChange:
    """A single file change within a commit.

    Attributes:
        path: File path after the change.
        change_type: Type of change.
        insertions: Lines added.
        deletions: Lines removed.
        old_path: Previous path (for renames/copies), or ``None``.
    """

    path: str
    change_type: ChangeType
    insertions: int = 0
    deletions: int = 0
    old_path: str | None = None


@dataclass(frozen=True)
class CommitRecord:
    """Raw commit metadata harvested from the Git log.

    Attributes:
        sha: Full commit SHA.
        author_name: Author display name.
        author_email: Author email.
        authored_date: Author timestamp.
        committer_name: Committer display name.
        committer_email: Committer email.
        committed_date: Committer timestamp.
        message: Full commit message.
        files: Per-file change details.
        insertions: Total lines inserted.
        deletions: Total lines deleted.
    """

    sha: str
    author_name: str
    author_email: str
    authored_date: datetime
    committer_name: str
    committer_email: str
    committed_date: datetime
    message: str
    files: tuple[FileChange, ...] = ()
    insertions: int = 0
    deletions: int = 0

    @property
    def net_lines(self) -> int:
        """Return net line change (insertions minus deletions)."""
        return self.insertions - self.deletions

    @property
    def churn_score(self) -> int:
        """Return churn score (insertions plus deletions)."""
        return self.insertions + self.deletions


@dataclass(frozen=True)
class EnrichedCommit:
    """A commit record enriched with classification metadata.

    Attributes:
        commit: The underlying raw commit record.
        is_merge: Whether this is a merge commit.
        is_fixup: Whether this is a fixup/squash commit.
        is_revert: Whether this is a revert commit.
        size_category: T-shirt size classification.
        conventional_type: Conventional-commit type prefix, or ``None``.
    """

    commit: CommitRecord
    is_merge: bool = False
    is_fixup: bool = False
    is_revert: bool = False
    size_category: CommitSizeCategory = CommitSizeCategory.SMALL
    conventional_type: str | None = None


@dataclass(frozen=True)
class BlameLine:
    """A single line from ``git blame`` output.

    Attributes:
        line_number: 1-based line number.
        author_name: Author display name.
        author_email: Author email.
        date: Commit date for this line.
        commit_sha: SHA of the commit that last touched this line.
    """

    line_number: int
    author_name: str
    author_email: str
    date: datetime
    commit_sha: str


@dataclass(frozen=True)
class AuthorBlameStat:
    """Aggregated blame statistics for one author on one file.

    Attributes:
        author_name: Author display name.
        author_email: Author email.
        line_count: Number of lines attributed to this author.
        percentage: Percentage of total file lines.
    """

    author_name: str
    author_email: str
    line_count: int
    percentage: float


@dataclass(frozen=True)
class FileBlameReport:
    """Blame report for a single file.

    Attributes:
        path: Repository-relative file path.
        total_lines: Total lines in the file.
        authors: Per-author blame statistics.
        lines: Per-line blame data.
    """

    path: str
    total_lines: int
    authors: tuple[AuthorBlameStat, ...] = ()
    lines: tuple[BlameLine, ...] = ()


# ---------------------------------------------------------------------------
# Branch / contributor dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MergeStatus:
    """Merge status of a branch.

    Attributes:
        merged_into_default: Merged into the default branch (e.g. main).
        merged_into_target: Merged into the configured target branch.
        has_pull_request: Associated with a pull request.
    """

    merged_into_default: bool = False
    merged_into_target: bool = False
    has_pull_request: bool = False

    @property
    def is_merged(self) -> bool:
        """Return ``True`` if merged via any path."""
        return self.merged_into_default or self.merged_into_target or self.has_pull_request

    @property
    def merge_type(self) -> MergeType:
        """Return the detected merge type.

        Returns ``MergeType.NOT_MERGED`` if the branch is not merged.
        Otherwise returns ``MergeType.MERGE_COMMIT`` as the default detected type.
        """
        if not self.is_merged:
            return MergeType.NOT_MERGED
        return MergeType.MERGE_COMMIT


@dataclass(frozen=True)
class BranchReport:
    """Analysis report for a single Git branch.

    Attributes:
        name: Branch name.
        is_remote: Whether this is a remote-tracking branch.
        last_commit_date: Timestamp of the latest commit.
        last_commit_sha: SHA of the latest commit.
        commits_ahead: Commits ahead of target.
        commits_behind: Commits behind target.
        author_name: Branch creator / last committer.
        author_email: Author email.
        status: Activity status.
        merge_status: Merge detection result.
        deletability_score: Computed deletability score (0-100).
        deletability_category: Recommendation category.
    """

    name: str
    is_remote: bool
    last_commit_date: datetime
    last_commit_sha: str
    commits_ahead: int
    commits_behind: int
    author_name: str
    author_email: str
    status: BranchStatus
    merge_status: MergeStatus
    deletability_score: float
    deletability_category: DeletabilityCategory


@dataclass(frozen=True)
class BranchesReport:
    """Aggregated report for all branches in a repository.

    Attributes:
        branches: Individual branch reports.
        default_branch: Name of the default branch.
        target_branch: Name of the configured target branch.
        total_branches: Total branch count.
        stale_count: Number of stale branches.
        abandoned_count: Number of abandoned branches.
        deletable_count: Number of branches recommended for deletion.
    """

    branches: tuple[BranchReport, ...]
    default_branch: str
    target_branch: str
    total_branches: int
    stale_count: int
    abandoned_count: int
    deletable_count: int


@dataclass(frozen=True)
class ContributorProfile:
    """Aggregated contribution statistics for a single author.

    Attributes:
        name: Author display name.
        email: Author email.
        commit_count: Total commits.
        first_commit_date: Earliest commit timestamp.
        last_commit_date: Latest commit timestamp.
        insertions: Total lines inserted.
        deletions: Total lines deleted.
        files_touched: Number of unique files modified.
    """

    name: str
    email: str
    commit_count: int
    first_commit_date: datetime
    last_commit_date: datetime
    insertions: int
    deletions: int
    files_touched: int


@dataclass(frozen=True)
class TagRecord:
    """A Git tag.

    Attributes:
        name: Tag name.
        sha: Commit SHA the tag points to.
        date: Tag or commit date.
        message: Tag message, or ``None`` for lightweight tags.
    """

    name: str
    sha: str
    date: datetime
    message: str | None = None


@dataclass(frozen=True)
class DetectedPattern:
    """An anomaly or pattern detected in the repository.

    Attributes:
        name: Short pattern identifier.
        description: Human-readable description.
        severity: Severity level.
        affected_files: Paths of affected files.
        evidence: Supporting evidence text.
    """

    name: str
    description: str
    severity: AnomalySeverity
    affected_files: tuple[str, ...] = ()
    evidence: str = ""


# ---------------------------------------------------------------------------
# Root report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RepoReport:
    """Top-level analysis result aggregating all sub-reports.

    Attributes:
        root: Absolute path to the repository root.
        files: Per-file analysis reports.
        modules: Per-directory module reports.
        languages: Per-language summaries.
        duplication: Duplication analysis results.
        coupling: Coupling analysis results.
        coverage: Test coverage results.
        file_churn: Per-file churn scores.
        commits: Raw commit records (``None`` if git analysis skipped).
        enriched_commits: Enriched commit records.
        branches_report: Branch analysis report.
        contributors: Contributor profiles.
        tags: Repository tags.
        patterns: Detected anomalies/patterns.
        blame_reports: Per-file blame reports.
    """

    root: Path
    files: tuple[FileReport, ...] = ()
    modules: tuple[ModuleReport, ...] = ()
    languages: tuple[LanguageSummary, ...] = ()
    duplication: DuplicationReport | None = None
    coupling: CouplingReport | None = None
    coverage: CoverageReport | None = None
    file_churn: tuple[FileChurn, ...] | None = None
    commits: tuple[CommitRecord, ...] | None = None
    enriched_commits: tuple[EnrichedCommit, ...] | None = None
    branches_report: BranchesReport | None = None
    contributors: tuple[ContributorProfile, ...] | None = None
    tags: tuple[TagRecord, ...] | None = None
    patterns: tuple[DetectedPattern, ...] | None = None
    blame_reports: tuple[FileBlameReport, ...] | None = field(default=None)
