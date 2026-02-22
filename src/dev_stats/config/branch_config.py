"""Branch-analysis configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BranchConfig(BaseModel):
    """Settings for the ``branches`` sub-command.

    Attributes:
        default_target: Name of the main integration branch.
        protected_patterns: Glob patterns for branches that must never be deleted.
        stale_days: Days of inactivity after which a branch is considered stale.
        abandoned_days: Days of inactivity after which a branch is considered abandoned.
        min_deletability_score: Minimum score (0-100) to recommend deletion.
    """

    default_target: str = Field(
        default="main",
        description="Default merge-target branch.",
    )
    protected_patterns: tuple[str, ...] = Field(
        default=("main", "master", "develop", "release/*"),
        description="Glob patterns for protected branches.",
    )
    stale_days: int = Field(
        default=30,
        ge=1,
        description="Days of inactivity before a branch is stale.",
    )
    abandoned_days: int = Field(
        default=90,
        ge=1,
        description="Days of inactivity before a branch is abandoned.",
    )
    min_deletability_score: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Minimum deletability score to recommend removal.",
    )

    model_config = {"frozen": True}
