"""Unit tests for the configuration layer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import pytest
from pydantic import ValidationError

from dev_stats.config.config_loader import ConfigLoader
from dev_stats.config.threshold_config import ThresholdConfig

# ---------------------------------------------------------------------------
# ThresholdConfig
# ---------------------------------------------------------------------------


class TestThresholdConfigDefaults:
    """Verify every default value of ThresholdConfig."""

    def test_defaults_are_populated(self) -> None:
        """Creating ThresholdConfig with no args should succeed."""
        cfg = ThresholdConfig()
        assert cfg.max_file_lines == 500
        assert cfg.max_function_lines == 50
        assert cfg.max_cyclomatic_complexity == 10
        assert cfg.max_cognitive_complexity == 15
        assert cfg.max_parameters == 5
        assert cfg.max_nesting_depth == 4
        assert cfg.max_class_methods == 20
        assert cfg.max_class_lines == 300
        assert cfg.max_imports == 15
        assert cfg.min_maintainability_index == 20.0
        assert cfg.max_duplication_pct == 5.0
        assert cfg.max_coupling == 10
        assert cfg.max_churn_rate == 0.5
        assert cfg.max_commit_size == 500
        assert cfg.min_test_coverage == 80.0

    def test_custom_overrides(self) -> None:
        """Explicit values should replace defaults."""
        cfg = ThresholdConfig(max_file_lines=1000, max_parameters=8)
        assert cfg.max_file_lines == 1000
        assert cfg.max_parameters == 8


class TestThresholdConfigValidation:
    """Ensure Field validators reject invalid data."""

    def test_max_file_lines_too_low(self) -> None:
        """max_file_lines must be >= 1."""
        with pytest.raises(ValidationError):
            ThresholdConfig(max_file_lines=0)

    def test_min_maintainability_too_high(self) -> None:
        """min_maintainability_index must be <= 100."""
        with pytest.raises(ValidationError):
            ThresholdConfig(min_maintainability_index=101.0)

    def test_max_duplication_pct_negative(self) -> None:
        """max_duplication_pct must be >= 0."""
        with pytest.raises(ValidationError):
            ThresholdConfig(max_duplication_pct=-1.0)

    def test_max_churn_rate_over_one(self) -> None:
        """max_churn_rate must be <= 1.0."""
        with pytest.raises(ValidationError):
            ThresholdConfig(max_churn_rate=1.5)


# ---------------------------------------------------------------------------
# ConfigLoader — deep_merge
# ---------------------------------------------------------------------------


class TestDeepMerge:
    """Tests for ConfigLoader.deep_merge."""

    def setup_method(self) -> None:
        """Create a ConfigLoader instance."""
        self.loader = ConfigLoader()

    def test_override_wins_flat(self) -> None:
        """Override value replaces base value."""
        base: dict[str, Any] = {"a": 1, "b": 2}
        override: dict[str, Any] = {"b": 99}
        result = self.loader.deep_merge(base, override)
        assert result == {"a": 1, "b": 99}

    def test_base_preserved(self) -> None:
        """Keys only in base are kept."""
        base: dict[str, Any] = {"a": 1, "b": 2}
        override: dict[str, Any] = {"c": 3}
        result = self.loader.deep_merge(base, override)
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_nested_merge(self) -> None:
        """Nested dicts are merged recursively."""
        base: dict[str, Any] = {"x": {"a": 1, "b": 2}}
        override: dict[str, Any] = {"x": {"b": 9, "c": 3}}
        result = self.loader.deep_merge(base, override)
        assert result == {"x": {"a": 1, "b": 9, "c": 3}}

    def test_inputs_not_mutated(self) -> None:
        """Neither base nor override should be modified."""
        base: dict[str, Any] = {"a": {"b": 1}}
        override: dict[str, Any] = {"a": {"c": 2}}
        self.loader.deep_merge(base, override)
        assert base == {"a": {"b": 1}}
        assert override == {"a": {"c": 2}}


# ---------------------------------------------------------------------------
# ConfigLoader — load_toml
# ---------------------------------------------------------------------------


class TestLoadToml:
    """Tests for ConfigLoader.load_toml."""

    def setup_method(self) -> None:
        """Create a ConfigLoader instance."""
        self.loader = ConfigLoader()

    def test_round_trip(self, tmp_path: Path) -> None:
        """Load a TOML file and verify parsed values."""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text("[thresholds]\nmax_file_lines = 999\n\n[output]\ntop_n = 5\n")
        data = self.loader.load_toml(toml_file)
        assert data["thresholds"]["max_file_lines"] == 999
        assert data["output"]["top_n"] == 5

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Missing file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            self.loader.load_toml(tmp_path / "nope.toml")


# ---------------------------------------------------------------------------
# ConfigLoader — apply_env_overrides
# ---------------------------------------------------------------------------


class TestEnvOverrides:
    """Tests for ConfigLoader.apply_env_overrides."""

    def setup_method(self) -> None:
        """Create a ConfigLoader instance."""
        self.loader = ConfigLoader()

    def test_flat_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A flat DEV_STATS_ var should land at the top level."""
        monkeypatch.setenv("DEV_STATS_REPO_PATH", "/tmp/repo")
        data: dict[str, Any] = {}
        result = self.loader.apply_env_overrides(data)
        assert result["repo_path"] == "/tmp/repo"

    def test_nested_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Double-underscore separates nested keys."""
        monkeypatch.setenv("DEV_STATS_THRESHOLDS__MAX_FILE_LINES", "800")
        data: dict[str, Any] = {"thresholds": {"max_file_lines": 500}}
        result = self.loader.apply_env_overrides(data)
        assert result["thresholds"]["max_file_lines"] == "800"

    def test_unrelated_env_vars_ignored(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Env vars without DEV_STATS_ prefix should be ignored."""
        monkeypatch.setenv("OTHER_VAR", "nope")
        data: dict[str, Any] = {"a": 1}
        result = self.loader.apply_env_overrides(data)
        assert "other_var" not in result
        assert result == {"a": 1}
