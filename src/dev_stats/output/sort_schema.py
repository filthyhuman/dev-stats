"""Sort schema defining sortable attributes for analysis reports."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class SortType(enum.Enum):
    """Data type of a sortable attribute.

    Used by exporters and the dashboard to determine formatting and sort
    direction defaults.
    """

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"


@dataclass(frozen=True)
class SortAttribute:
    """Metadata for a single sortable column.

    Attributes:
        key: Unique dot-path key (e.g. ``"file.code_lines"``).
        label: Human-readable column header.
        sort_type: Data type for sorting/formatting.
        entity: Entity group (``file``, ``class``, ``method``, ``language``,
                ``module``, ``coupling``, ``churn``, ``coverage``, ``commit``).
        description: Short tooltip description.
        default_descending: Whether the default sort direction is descending.
        js_accessor: JavaScript accessor expression for the dashboard.
    """

    key: str
    label: str
    sort_type: SortType
    entity: str
    description: str = ""
    default_descending: bool = False
    js_accessor: str = ""


class SortSchema:
    """Registry of all sortable attributes across report entities.

    Provides ``attributes()`` for the full catalogue and ``for_entity()``
    to filter by entity type.
    """

    _ATTRIBUTES: tuple[SortAttribute, ...] = (
        # --- File attributes ---
        SortAttribute(
            key="file.path",
            label="Path",
            sort_type=SortType.STRING,
            entity="file",
            description="File path relative to repository root.",
            js_accessor="d.path",
        ),
        SortAttribute(
            key="file.language",
            label="Language",
            sort_type=SortType.STRING,
            entity="file",
            description="Detected programming language.",
            js_accessor="d.language",
        ),
        SortAttribute(
            key="file.total_lines",
            label="Total Lines",
            sort_type=SortType.INTEGER,
            entity="file",
            description="Total number of lines in the file.",
            default_descending=True,
            js_accessor="d.total_lines",
        ),
        SortAttribute(
            key="file.code_lines",
            label="Code Lines",
            sort_type=SortType.INTEGER,
            entity="file",
            description="Non-blank, non-comment lines.",
            default_descending=True,
            js_accessor="d.code_lines",
        ),
        SortAttribute(
            key="file.blank_lines",
            label="Blank Lines",
            sort_type=SortType.INTEGER,
            entity="file",
            description="Number of blank lines.",
            default_descending=True,
            js_accessor="d.blank_lines",
        ),
        SortAttribute(
            key="file.comment_lines",
            label="Comment Lines",
            sort_type=SortType.INTEGER,
            entity="file",
            description="Comment-only lines.",
            default_descending=True,
            js_accessor="d.comment_lines",
        ),
        SortAttribute(
            key="file.comment_ratio",
            label="Comment Ratio",
            sort_type=SortType.FLOAT,
            entity="file",
            description="Comment lines as a fraction of total lines.",
            default_descending=True,
            js_accessor="d.comment_ratio",
        ),
        SortAttribute(
            key="file.num_classes",
            label="Classes",
            sort_type=SortType.INTEGER,
            entity="file",
            description="Number of classes in the file.",
            default_descending=True,
            js_accessor="d.num_classes",
        ),
        SortAttribute(
            key="file.num_functions",
            label="Functions",
            sort_type=SortType.INTEGER,
            entity="file",
            description="Number of top-level functions.",
            default_descending=True,
            js_accessor="d.num_functions",
        ),
        # --- Class attributes ---
        SortAttribute(
            key="class.name",
            label="Name",
            sort_type=SortType.STRING,
            entity="class",
            description="Class name.",
            js_accessor="d.name",
        ),
        SortAttribute(
            key="class.line",
            label="Line",
            sort_type=SortType.INTEGER,
            entity="class",
            description="Start line number.",
            js_accessor="d.line",
        ),
        SortAttribute(
            key="class.lines",
            label="Lines",
            sort_type=SortType.INTEGER,
            entity="class",
            description="Total line count.",
            default_descending=True,
            js_accessor="d.lines",
        ),
        SortAttribute(
            key="class.num_methods",
            label="Methods",
            sort_type=SortType.INTEGER,
            entity="class",
            description="Number of methods.",
            default_descending=True,
            js_accessor="d.num_methods",
        ),
        SortAttribute(
            key="class.num_attributes",
            label="Attributes",
            sort_type=SortType.INTEGER,
            entity="class",
            description="Number of instance attributes.",
            default_descending=True,
            js_accessor="d.num_attributes",
        ),
        SortAttribute(
            key="class.num_constructors",
            label="Constructors",
            sort_type=SortType.INTEGER,
            entity="class",
            description="Number of constructor methods.",
            default_descending=True,
            js_accessor="d.num_constructors",
        ),
        # --- Method / function attributes ---
        SortAttribute(
            key="method.name",
            label="Name",
            sort_type=SortType.STRING,
            entity="method",
            description="Method or function name.",
            js_accessor="d.name",
        ),
        SortAttribute(
            key="method.line",
            label="Line",
            sort_type=SortType.INTEGER,
            entity="method",
            description="Start line number.",
            js_accessor="d.line",
        ),
        SortAttribute(
            key="method.lines",
            label="Lines",
            sort_type=SortType.INTEGER,
            entity="method",
            description="Total line count.",
            default_descending=True,
            js_accessor="d.lines",
        ),
        SortAttribute(
            key="method.cyclomatic_complexity",
            label="Cyclomatic Complexity",
            sort_type=SortType.INTEGER,
            entity="method",
            description="McCabe cyclomatic complexity.",
            default_descending=True,
            js_accessor="d.cyclomatic_complexity",
        ),
        SortAttribute(
            key="method.cognitive_complexity",
            label="Cognitive Complexity",
            sort_type=SortType.INTEGER,
            entity="method",
            description="Cognitive complexity score.",
            default_descending=True,
            js_accessor="d.cognitive_complexity",
        ),
        SortAttribute(
            key="method.nesting_depth",
            label="Nesting Depth",
            sort_type=SortType.INTEGER,
            entity="method",
            description="Maximum nesting depth.",
            default_descending=True,
            js_accessor="d.nesting_depth",
        ),
        SortAttribute(
            key="method.num_parameters",
            label="Parameters",
            sort_type=SortType.INTEGER,
            entity="method",
            description="Number of parameters.",
            default_descending=True,
            js_accessor="d.num_parameters",
        ),
        SortAttribute(
            key="method.is_constructor",
            label="Constructor",
            sort_type=SortType.BOOLEAN,
            entity="method",
            description="Whether this is a constructor.",
            js_accessor="d.is_constructor",
        ),
        # --- Language summary attributes ---
        SortAttribute(
            key="language.language",
            label="Language",
            sort_type=SortType.STRING,
            entity="language",
            description="Programming language name.",
            js_accessor="d.language",
        ),
        SortAttribute(
            key="language.file_count",
            label="Files",
            sort_type=SortType.INTEGER,
            entity="language",
            description="Number of files.",
            default_descending=True,
            js_accessor="d.file_count",
        ),
        SortAttribute(
            key="language.total_lines",
            label="Total Lines",
            sort_type=SortType.INTEGER,
            entity="language",
            description="Total lines across all files.",
            default_descending=True,
            js_accessor="d.total_lines",
        ),
        SortAttribute(
            key="language.code_lines",
            label="Code Lines",
            sort_type=SortType.INTEGER,
            entity="language",
            description="Code lines across all files.",
            default_descending=True,
            js_accessor="d.code_lines",
        ),
        SortAttribute(
            key="language.blank_lines",
            label="Blank Lines",
            sort_type=SortType.INTEGER,
            entity="language",
            description="Blank lines across all files.",
            default_descending=True,
            js_accessor="d.blank_lines",
        ),
        SortAttribute(
            key="language.comment_lines",
            label="Comment Lines",
            sort_type=SortType.INTEGER,
            entity="language",
            description="Comment lines across all files.",
            default_descending=True,
            js_accessor="d.comment_lines",
        ),
        # --- Module attributes ---
        SortAttribute(
            key="module.name",
            label="Name",
            sort_type=SortType.STRING,
            entity="module",
            description="Module / directory name.",
            js_accessor="d.name",
        ),
        SortAttribute(
            key="module.path",
            label="Path",
            sort_type=SortType.STRING,
            entity="module",
            description="Module path.",
            js_accessor="d.path",
        ),
        SortAttribute(
            key="module.file_count",
            label="Files",
            sort_type=SortType.INTEGER,
            entity="module",
            description="Number of files in the module.",
            default_descending=True,
            js_accessor="d.files.length",
        ),
        # --- Coupling attributes ---
        SortAttribute(
            key="coupling.name",
            label="Module",
            sort_type=SortType.STRING,
            entity="coupling",
            description="Module name.",
            js_accessor="d.name",
        ),
        SortAttribute(
            key="coupling.afferent",
            label="Ca",
            sort_type=SortType.INTEGER,
            entity="coupling",
            description="Afferent coupling (incoming dependencies).",
            default_descending=True,
            js_accessor="d.afferent",
        ),
        SortAttribute(
            key="coupling.efferent",
            label="Ce",
            sort_type=SortType.INTEGER,
            entity="coupling",
            description="Efferent coupling (outgoing dependencies).",
            default_descending=True,
            js_accessor="d.efferent",
        ),
        SortAttribute(
            key="coupling.instability",
            label="Instability",
            sort_type=SortType.FLOAT,
            entity="coupling",
            description="Instability I = Ce / (Ca + Ce).",
            default_descending=True,
            js_accessor="d.instability",
        ),
        SortAttribute(
            key="coupling.abstractness",
            label="Abstractness",
            sort_type=SortType.FLOAT,
            entity="coupling",
            description="Abstractness A = abstract / total classes.",
            default_descending=True,
            js_accessor="d.abstractness",
        ),
        SortAttribute(
            key="coupling.distance",
            label="Distance",
            sort_type=SortType.FLOAT,
            entity="coupling",
            description="Distance from the main sequence.",
            default_descending=True,
            js_accessor="d.distance",
        ),
        # --- Churn attributes ---
        SortAttribute(
            key="churn.path",
            label="Path",
            sort_type=SortType.STRING,
            entity="churn",
            description="File path.",
            js_accessor="d.path",
        ),
        SortAttribute(
            key="churn.commit_count",
            label="Commits",
            sort_type=SortType.INTEGER,
            entity="churn",
            description="Number of commits touching this file.",
            default_descending=True,
            js_accessor="d.commit_count",
        ),
        SortAttribute(
            key="churn.insertions",
            label="Insertions",
            sort_type=SortType.INTEGER,
            entity="churn",
            description="Total lines inserted.",
            default_descending=True,
            js_accessor="d.insertions",
        ),
        SortAttribute(
            key="churn.deletions",
            label="Deletions",
            sort_type=SortType.INTEGER,
            entity="churn",
            description="Total lines deleted.",
            default_descending=True,
            js_accessor="d.deletions",
        ),
        SortAttribute(
            key="churn.churn_score",
            label="Churn Score",
            sort_type=SortType.INTEGER,
            entity="churn",
            description="Total churn (insertions + deletions).",
            default_descending=True,
            js_accessor="d.churn_score",
        ),
        # --- Coverage attributes ---
        SortAttribute(
            key="coverage.path",
            label="Path",
            sort_type=SortType.STRING,
            entity="coverage",
            description="File path.",
            js_accessor="d.path",
        ),
        SortAttribute(
            key="coverage.covered_lines",
            label="Covered Lines",
            sort_type=SortType.INTEGER,
            entity="coverage",
            description="Number of covered lines.",
            default_descending=True,
            js_accessor="d.covered_lines",
        ),
        SortAttribute(
            key="coverage.total_lines",
            label="Total Lines",
            sort_type=SortType.INTEGER,
            entity="coverage",
            description="Total coverable lines.",
            default_descending=True,
            js_accessor="d.total_lines",
        ),
        SortAttribute(
            key="coverage.coverage_ratio",
            label="Coverage",
            sort_type=SortType.FLOAT,
            entity="coverage",
            description="Coverage ratio (covered / total).",
            default_descending=True,
            js_accessor="d.coverage_ratio",
        ),
        # --- Commit attributes ---
        SortAttribute(
            key="commit.sha",
            label="SHA",
            sort_type=SortType.STRING,
            entity="commit",
            description="Commit SHA (short).",
            js_accessor="d.sha",
        ),
        SortAttribute(
            key="commit.author_name",
            label="Author",
            sort_type=SortType.STRING,
            entity="commit",
            description="Author display name.",
            js_accessor="d.author_name",
        ),
        SortAttribute(
            key="commit.authored_date",
            label="Date",
            sort_type=SortType.DATE,
            entity="commit",
            description="Author timestamp.",
            default_descending=True,
            js_accessor="d.authored_date",
        ),
        SortAttribute(
            key="commit.insertions",
            label="Insertions",
            sort_type=SortType.INTEGER,
            entity="commit",
            description="Lines inserted.",
            default_descending=True,
            js_accessor="d.insertions",
        ),
        SortAttribute(
            key="commit.deletions",
            label="Deletions",
            sort_type=SortType.INTEGER,
            entity="commit",
            description="Lines deleted.",
            default_descending=True,
            js_accessor="d.deletions",
        ),
        SortAttribute(
            key="commit.churn_score",
            label="Churn",
            sort_type=SortType.INTEGER,
            entity="commit",
            description="Total churn (insertions + deletions).",
            default_descending=True,
            js_accessor="d.churn_score",
        ),
        SortAttribute(
            key="commit.message",
            label="Subject",
            sort_type=SortType.STRING,
            entity="commit",
            description="Commit subject line.",
            js_accessor="d.message",
        ),
        # --- Branch attributes ---
        SortAttribute(
            key="branch.name",
            label="Name",
            sort_type=SortType.STRING,
            entity="branch",
            description="Branch name.",
            js_accessor="d.name",
        ),
        SortAttribute(
            key="branch.status",
            label="Status",
            sort_type=SortType.STRING,
            entity="branch",
            description="Activity status (active/stale/abandoned).",
            js_accessor="d.status",
        ),
        SortAttribute(
            key="branch.commits_ahead",
            label="Ahead",
            sort_type=SortType.INTEGER,
            entity="branch",
            description="Commits ahead of target.",
            default_descending=True,
            js_accessor="d.commits_ahead",
        ),
        SortAttribute(
            key="branch.commits_behind",
            label="Behind",
            sort_type=SortType.INTEGER,
            entity="branch",
            description="Commits behind target.",
            default_descending=True,
            js_accessor="d.commits_behind",
        ),
        SortAttribute(
            key="branch.deletability_score",
            label="Score",
            sort_type=SortType.FLOAT,
            entity="branch",
            description="Deletability score (0-100).",
            default_descending=True,
            js_accessor="d.deletability_score",
        ),
        SortAttribute(
            key="branch.author_name",
            label="Author",
            sort_type=SortType.STRING,
            entity="branch",
            description="Branch author.",
            js_accessor="d.author_name",
        ),
        # --- Contributor attributes ---
        SortAttribute(
            key="contributor.name",
            label="Name",
            sort_type=SortType.STRING,
            entity="contributor",
            description="Contributor display name.",
            js_accessor="d.name",
        ),
        SortAttribute(
            key="contributor.email",
            label="Email",
            sort_type=SortType.STRING,
            entity="contributor",
            description="Contributor email.",
            js_accessor="d.email",
        ),
        SortAttribute(
            key="contributor.commit_count",
            label="Commits",
            sort_type=SortType.INTEGER,
            entity="contributor",
            description="Total commits.",
            default_descending=True,
            js_accessor="d.commit_count",
        ),
        SortAttribute(
            key="contributor.insertions",
            label="Insertions",
            sort_type=SortType.INTEGER,
            entity="contributor",
            description="Total lines inserted.",
            default_descending=True,
            js_accessor="d.insertions",
        ),
        SortAttribute(
            key="contributor.deletions",
            label="Deletions",
            sort_type=SortType.INTEGER,
            entity="contributor",
            description="Total lines deleted.",
            default_descending=True,
            js_accessor="d.deletions",
        ),
        SortAttribute(
            key="contributor.files_touched",
            label="Files",
            sort_type=SortType.INTEGER,
            entity="contributor",
            description="Unique files modified.",
            default_descending=True,
            js_accessor="d.files_touched",
        ),
        SortAttribute(
            key="contributor.active_days",
            label="Active Days",
            sort_type=SortType.INTEGER,
            entity="contributor",
            description="Distinct days with commits.",
            default_descending=True,
            js_accessor="d.active_days",
        ),
        # --- Pattern attributes ---
        SortAttribute(
            key="pattern.name",
            label="Pattern",
            sort_type=SortType.STRING,
            entity="pattern",
            description="Pattern identifier.",
            js_accessor="d.name",
        ),
        SortAttribute(
            key="pattern.severity",
            label="Severity",
            sort_type=SortType.STRING,
            entity="pattern",
            description="Severity level.",
            js_accessor="d.severity",
        ),
        SortAttribute(
            key="pattern.description",
            label="Description",
            sort_type=SortType.STRING,
            entity="pattern",
            description="Human-readable description.",
            js_accessor="d.description",
        ),
    )

    def attributes(self) -> tuple[SortAttribute, ...]:
        """Return all registered sortable attributes.

        Returns:
            Tuple of all ``SortAttribute`` instances.
        """
        return self._ATTRIBUTES

    def for_entity(self, entity: str) -> tuple[SortAttribute, ...]:
        """Return sortable attributes for a specific entity type.

        Args:
            entity: Entity name (e.g. ``"file"``, ``"method"``).

        Returns:
            Tuple of matching ``SortAttribute`` instances.
        """
        return tuple(a for a in self._ATTRIBUTES if a.entity == entity)

    def by_key(self, key: str) -> SortAttribute | None:
        """Look up a single attribute by its dot-path key.

        Args:
            key: Attribute key (e.g. ``"file.code_lines"``).

        Returns:
            The ``SortAttribute``, or ``None`` if not found.
        """
        for attr in self._ATTRIBUTES:
            if attr.key == key:
                return attr
        return None

    def entity_names(self) -> tuple[str, ...]:
        """Return all distinct entity names.

        Returns:
            Sorted tuple of unique entity names.
        """
        return tuple(sorted({a.entity for a in self._ATTRIBUTES}))
