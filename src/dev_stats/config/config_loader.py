"""TOML configuration loading and merging utilities."""

from __future__ import annotations

import os
import tomllib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class ConfigLoader:
    """Loads TOML config files and merges with environment variable overrides.

    Provides three operations:
    1. ``load_toml`` — read a ``.toml`` file into a dict.
    2. ``deep_merge`` — recursively merge two dicts (override wins).
    3. ``apply_env_overrides`` — overlay ``DEV_STATS_*`` env vars onto a dict.
    """

    ENV_PREFIX: str = "DEV_STATS_"

    def load_toml(self, path: Path) -> dict[str, Any]:
        """Read a TOML file and return its contents as a dict.

        Args:
            path: Path to the TOML file.

        Returns:
            Parsed TOML data.

        Raises:
            FileNotFoundError: If *path* does not exist.
            tomllib.TOMLDecodeError: If the file is not valid TOML.
        """
        with path.open("rb") as fh:
            return tomllib.load(fh)

    def deep_merge(
        self,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """Recursively merge *override* into *base*.

        For nested dicts the merge is recursive; for all other types the
        *override* value wins.

        Args:
            base: Base configuration dictionary.
            override: Override dictionary whose values take precedence.

        Returns:
            A new merged dictionary — neither input is mutated.
        """
        merged: dict[str, Any] = dict(base)
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def apply_env_overrides(self, data: dict[str, Any]) -> dict[str, Any]:
        """Overlay ``DEV_STATS_*`` environment variables onto *data*.

        Environment variable names are lowered and split on ``__`` to represent
        nesting.  For example ``DEV_STATS_THRESHOLDS__MAX_FILE_LINES=800``
        maps to ``data["thresholds"]["max_file_lines"] = "800"``.

        Args:
            data: Existing configuration dictionary.

        Returns:
            A new dictionary with env-var overrides applied.
        """
        result: dict[str, Any] = dict(data)
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(self.ENV_PREFIX):
                continue
            raw = env_key[len(self.ENV_PREFIX) :].lower()
            parts = raw.split("__")
            target: dict[str, Any] = result
            for part in parts[:-1]:
                if part not in target or not isinstance(target[part], dict):
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = env_value
        return result
