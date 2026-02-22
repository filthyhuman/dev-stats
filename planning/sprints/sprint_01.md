# Sprint 01 — Project Skeleton & Config

**Phase:** 01 | **Duration:** 1 week
**Goal:** Repo initialised, CI green, config loads from TOML, CLI skeleton responds.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S01-01 | Init repo: pyproject.toml, uv.lock, .python-version, LICENSE (GPL-3.0)           | 1   |
| S01-02 | Tooling: ruff.toml, mypy.ini (strict), .pre-commit-config.yaml                   | 1   |
| S01-03 | src/dev_stats/__init__.py — __version__, __all__                                 | 1   |
| S01-04 | src/dev_stats/__main__.py — python -m dev_stats entry                            | 1   |
| S01-05 | cli/version_callback.py — VersionCallback class                                  | 1   |
| S01-06 | cli/app.py — Typer app, register sub-commands, attach version callback           | 2   |
| S01-07 | cli/analyse_command.py — AnalyseCommand class, all flags, no-op body             | 2   |
| S01-08 | cli/branches_command.py — BranchesCommand skeleton                               | 1   |
| S01-09 | cli/gitlog_command.py — GitlogCommand skeleton                                   | 1   |
| S01-10 | config/threshold_config.py — ThresholdConfig(BaseModel), 15 fields              | 3   |
| S01-11 | config/output_config.py — OutputConfig(BaseModel)                               | 1   |
| S01-12 | config/branch_config.py — BranchConfig(BaseModel)                               | 1   |
| S01-13 | config/gitlog_config.py — GitlogConfig(BaseModel)                               | 1   |
| S01-14 | config/analysis_config.py — AnalysisConfig(BaseSettings) root model             | 2   |
| S01-15 | config/config_loader.py — ConfigLoader: load_toml, deep_merge, env overlay      | 3   |
| S01-16 | config/defaults.toml — all sections matching Pydantic defaults                   | 1   |
| S01-17 | .github/workflows/ci.yml — lint, typecheck, test, build jobs                    | 2   |
| S01-18 | .github/workflows/release.yml — publish on tag push                             | 1   |
| S01-19 | tests/conftest.py — fake_repo fixture + all factory functions                   | 3   |
| S01-20 | tests/unit/test_config.py — all config models, TOML merge, env overrides        | 3   |
| S01-21 | tests/integration/test_cli.py — --version, --help, analyse exits 0              | 2   |

## Acceptance Criteria

- `uv run dev-stats --version` prints version, exits 0
- `uv run dev-stats analyse --help` shows all flags
- `uv run dev-stats analyse .` exits 0 (placeholder output)
- `uv run ruff check . && uv run ruff format --check .` passes
- `uv run mypy src/ --strict` passes
- `uv run pytest` all green
- GitHub Actions CI is green

→ tasks_01.md
