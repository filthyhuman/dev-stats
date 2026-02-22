"""Threshold configuration for code-quality gates."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ThresholdConfig(BaseModel):
    """Quality-gate thresholds used by analysers and CI adapters.

    Every field carries a sensible default so the tool works out-of-the-box.
    Values can be overridden via TOML config or ``DEV_STATS_`` env vars.
    """

    max_file_lines: int = Field(
        default=500,
        ge=1,
        description="Maximum lines per file before a warning is raised.",
    )
    max_function_lines: int = Field(
        default=50,
        ge=1,
        description="Maximum lines per function/method.",
    )
    max_cyclomatic_complexity: int = Field(
        default=10,
        ge=1,
        description="Maximum cyclomatic complexity per function.",
    )
    max_cognitive_complexity: int = Field(
        default=15,
        ge=1,
        description="Maximum cognitive complexity per function.",
    )
    max_parameters: int = Field(
        default=5,
        ge=1,
        description="Maximum parameters per function signature.",
    )
    max_nesting_depth: int = Field(
        default=4,
        ge=1,
        description="Maximum nesting depth inside a function.",
    )
    max_class_methods: int = Field(
        default=20,
        ge=1,
        description="Maximum methods per class.",
    )
    max_class_lines: int = Field(
        default=300,
        ge=1,
        description="Maximum lines per class.",
    )
    max_imports: int = Field(
        default=15,
        ge=1,
        description="Maximum import statements per file.",
    )
    min_maintainability_index: float = Field(
        default=20.0,
        ge=0.0,
        le=100.0,
        description="Minimum maintainability index (0-100).",
    )
    max_duplication_pct: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="Maximum percentage of duplicated lines.",
    )
    max_coupling: int = Field(
        default=10,
        ge=0,
        description="Maximum afferent+efferent coupling per module.",
    )
    max_churn_rate: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Maximum churn rate (changes/total lines) per file.",
    )
    max_commit_size: int = Field(
        default=500,
        ge=1,
        description="Maximum changed lines in a single commit.",
    )
    min_test_coverage: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Minimum test-coverage percentage.",
    )

    model_config = {"frozen": True}
