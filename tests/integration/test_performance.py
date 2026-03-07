"""Performance regression tests."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dev_stats.cli.app import app

runner = CliRunner()


@pytest.mark.slow
class TestPerformance:
    """Performance regression tests."""

    def test_analyse_own_repo_under_10s(self) -> None:
        """Analysing the dev-stats repo itself takes less than 10 seconds."""
        repo = Path(__file__).resolve().parents[2]  # tests/ -> dev-stats/
        start = time.monotonic()
        result = runner.invoke(app, ["analyse", str(repo)])
        elapsed = time.monotonic() - start
        assert result.exit_code == 0
        assert elapsed < 10.0, f"Analysis took {elapsed:.1f}s (limit: 10s)"
