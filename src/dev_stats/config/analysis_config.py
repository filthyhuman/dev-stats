"""Root analysis configuration assembled from sub-configs."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings

from dev_stats.config.branch_config import BranchConfig
from dev_stats.config.config_loader import ConfigLoader
from dev_stats.config.gitlog_config import GitlogConfig
from dev_stats.config.output_config import OutputConfig
from dev_stats.config.threshold_config import ThresholdConfig


class AnalysisConfig(BaseSettings):
    """Top-level configuration for a dev-stats analysis run.

    Composes all sub-configurations and supports loading from a TOML file,
    environment variables (prefix ``DEV_STATS_``), or both.

    Attributes:
        repo_path: Path to the Git repository to analyse.
        exclude_patterns: Glob patterns for files/directories to exclude.
        languages: Language filters (empty = all).
        thresholds: Quality-gate threshold settings.
        output: Output presentation settings.
        branches: Branch-analysis settings.
        gitlog: Git-log analysis settings.
    """

    _loader: ClassVar[ConfigLoader] = ConfigLoader()

    repo_path: Path = Field(
        default=Path("."),
        description="Path to the repository root.",
    )
    exclude_patterns: tuple[str, ...] = Field(
        default=(
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "*.pyc",
            ".mypy_cache",
            ".ruff_cache",
            ".pytest_cache",
        ),
        description="Glob patterns to exclude from scanning.",
    )
    languages: tuple[str, ...] = Field(
        default=(),
        description="Language filter (empty = all detected languages).",
    )
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    branches: BranchConfig = Field(default_factory=BranchConfig)
    gitlog: GitlogConfig = Field(default_factory=GitlogConfig)

    model_config = {"frozen": True, "env_prefix": "DEV_STATS_"}

    @classmethod
    def load(
        cls,
        config_path: Path | None = None,
        repo_path: Path = Path("."),
        exclude_patterns: tuple[str, ...] | None = None,
        languages: tuple[str, ...] | None = None,
    ) -> AnalysisConfig:
        """Build an ``AnalysisConfig`` from TOML + env vars + explicit overrides.

        Args:
            config_path: Optional path to a TOML configuration file.
            repo_path: Path to the repository to analyse.
            exclude_patterns: Optional glob patterns to exclude.
            languages: Optional language filter.

        Returns:
            A fully-resolved, frozen ``AnalysisConfig`` instance.
        """
        base: dict[str, object] = {}

        if config_path is not None:
            base = cls._loader.load_toml(config_path)

        base = cls._loader.apply_env_overrides(base)

        base["repo_path"] = str(repo_path)
        if exclude_patterns is not None:
            base["exclude_patterns"] = list(exclude_patterns)
        if languages is not None:
            base["languages"] = list(languages)

        return cls.model_validate(base)
