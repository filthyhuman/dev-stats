# Tasks 01 — Project Skeleton & Config

One task = one atomic unit of work (one file, one method, one test class).
Check off each item. A task is done only when ruff, mypy, and tests all pass.

## Setup & Tooling

- [ ] T01-001  Run: git init && uv init --name dev-stats --python 3.12
- [ ] T01-002  Create LICENSE — full GPL-3.0 text (copy from https://www.gnu.org/licenses/gpl-3.0.txt)
- [ ] T01-003  Create .python-version with content: 3.12
- [ ] T01-004  Create pyproject.toml — hatchling build, all metadata, script entry dev-stats, all deps, dev extras, ruff/mypy/pytest config
- [ ] T01-005  Create .pre-commit-config.yaml — ruff, ruff-format, pre-commit-hooks, mypy
- [ ] T01-006  Create .github/workflows/ci.yml — lint, typecheck, test, build jobs
- [ ] T01-007  Create .github/workflows/release.yml — publish on tag v*

## Package Init

- [ ] T01-008  Create src/dev_stats/__init__.py — __version__ = "0.1.0", __all__ = ["__version__"]
- [ ] T01-009  Create src/dev_stats/__main__.py — imports app from cli.app, calls app()

## CLI Layer

- [ ] T01-010  Create src/dev_stats/cli/__init__.py — empty
- [ ] T01-011  Create src/dev_stats/cli/version_callback.py — class VersionCallback with __call__(value: bool) -> None, prints version with Rich, raises typer.Exit
- [ ] T01-012  Create src/dev_stats/cli/app.py — app = typer.Typer(...), add_typer for analyse/branches/gitlog, attach VersionCallback as --version option
- [ ] T01-013  Create src/dev_stats/cli/analyse_command.py — class AnalyseCommand with __call__ as typer command; declare ALL flags (output, ci, config, exclude, top, lang, diff, fail-on-violations, watch, since); body: console.print("not yet implemented")
- [ ] T01-014  Create src/dev_stats/cli/branches_command.py — class BranchesCommand, all flags, no-op body
- [ ] T01-015  Create src/dev_stats/cli/gitlog_command.py — class GitlogCommand, all flags, no-op body

## Config Layer

- [ ] T01-016  Create src/dev_stats/config/__init__.py — empty
- [ ] T01-017  Create src/dev_stats/config/threshold_config.py — class ThresholdConfig(BaseModel): all 15 threshold fields with Field() defaults and ge/le validators
- [ ] T01-018  Create src/dev_stats/config/output_config.py — class OutputConfig(BaseModel): top_n, filenames, compress_dashboard_json
- [ ] T01-019  Create src/dev_stats/config/branch_config.py — class BranchConfig(BaseModel): default_target, protected_patterns, stale/abandoned days, min_deletability_score
- [ ] T01-020  Create src/dev_stats/config/gitlog_config.py — class GitlogConfig(BaseModel): max_commits, blame_top_files, include_diffs, follow_renames, max_dashboard_mb
- [ ] T01-021  Create src/dev_stats/config/analysis_config.py — class AnalysisConfig(BaseSettings): repo_path, exclude_patterns, languages, composes all sub-configs; model_config frozen=True; classmethod load(config_path, repo_path, exclude_patterns, languages)
- [ ] T01-022  Create src/dev_stats/config/config_loader.py — class ConfigLoader: load_toml(path) -> dict, deep_merge(base, override) -> dict (recursive), apply_env_overrides(data) -> dict (prefix DEV_STATS_)
- [ ] T01-023  Create src/dev_stats/config/defaults.toml — all sections with values matching Pydantic field defaults

## Tests

- [ ] T01-024  Create all __init__.py files: tests/, tests/unit/, tests/unit/core/, tests/unit/core/parsers/, tests/unit/core/metrics/, tests/unit/core/git/, tests/unit/output/, tests/unit/ci/, tests/integration/
- [ ] T01-025  Create tests/conftest.py — functions: make_parameter(), make_method(), make_class(), make_file_report(), make_repo_report(); fixture fake_repo(tmp_path) that inits git, makes 2 commits, creates 1 feature branch
- [ ] T01-026  Create tests/unit/test_config.py — test ThresholdConfig defaults, min/max validation errors, ConfigLoader.deep_merge (base wins, override wins, nested merge), TOML load round-trip, env var override with DEV_STATS_ prefix
- [ ] T01-027  Create tests/integration/test_cli.py — CliRunner tests: --version exits 0 and prints version, --help exits 0, analyse . exits 0 and prints something, branches . exits 0, gitlog . exits 0
