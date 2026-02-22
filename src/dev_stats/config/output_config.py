"""Output-related configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OutputConfig(BaseModel):
    """Controls how analysis results are presented and exported.

    Attributes:
        top_n: Number of top items to display in tables.
        filenames: Whether to show full paths or just file names.
        compress_dashboard_json: GZIP-compress the JSON blob inside the dashboard.
    """

    top_n: int = Field(
        default=20,
        ge=1,
        description="Number of top items to show in ranked tables.",
    )
    filenames: bool = Field(
        default=False,
        description="Show bare filenames instead of repo-relative paths.",
    )
    compress_dashboard_json: bool = Field(
        default=True,
        description="GZIP-compress the embedded JSON in the HTML dashboard.",
    )

    model_config = {"frozen": True}
