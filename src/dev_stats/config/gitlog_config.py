"""Git-log analysis configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GitlogConfig(BaseModel):
    """Settings for the ``gitlog`` sub-command.

    Attributes:
        max_commits: Maximum commits to process (0 = unlimited).
        blame_top_files: Number of top-churn files to run ``git blame`` on.
        include_diffs: Include diff stats in commit records.
        follow_renames: Honour ``--follow`` for file rename tracking.
        max_dashboard_mb: Size cap (MB) for dashboard data payload.
    """

    max_commits: int = Field(
        default=0,
        ge=0,
        description="Max commits to harvest (0 = unlimited).",
    )
    blame_top_files: int = Field(
        default=10,
        ge=0,
        description="Number of top-churn files to blame.",
    )
    include_diffs: bool = Field(
        default=True,
        description="Include per-commit diff statistics.",
    )
    follow_renames: bool = Field(
        default=True,
        description="Follow file renames in git log.",
    )
    max_dashboard_mb: float = Field(
        default=5.0,
        ge=0.1,
        description="Maximum dashboard data payload in megabytes.",
    )

    model_config = {"frozen": True}
