# Tasks 22 — Pre-commit & GitHub Action

Derived from planning/sprints/sprint_22.md.

## Checklist

### S22-01: Improve precommit_generator.py

- [ ] Generate complete `.pre-commit-config.yaml` with dev-stats hook
- [ ] Hook runs `dev-stats analyse . --fail-on-violations --quiet`
- [ ] Configurable: languages, thresholds, exclude patterns
- [ ] Add `init-hooks` subcommand to CLI

### S22-02: GitHub Action composite

- [ ] Create `.github/action.yml` as composite action
- [ ] Steps: install uv, install dev-stats, run analyse
- [ ] Use action caching for uv and Python

### S22-03: Action inputs

- [ ] `format` input (default: `dashboard`)
- [ ] `fail-on-violations` input (default: `false`)
- [ ] `since` input (default: empty)
- [ ] `config` input (default: empty — uses repo's config)
- [ ] `args` input for arbitrary extra flags

### S22-04: Action artifact upload

- [ ] Upload `dev-stats-output/` directory as artifact
- [ ] Artifact name: `dev-stats-report`
- [ ] Retention: 30 days (configurable input)

### S22-05: Test action

- [ ] Create `.github/workflows/test-action.yml`
- [ ] Runs on push to test the action against the dev-stats repo itself
- [ ] Assert: action completes, artifact uploaded, exit code matches expectations

### S22-06: Pre-commit performance

- [ ] Benchmark pre-commit hook on a medium repo (500 files)
- [ ] Target: < 30 seconds
- [ ] If slow: add `--quick` mode that skips git analysis and metrics

### S22-07: Documentation

- [ ] Update `docs/ci_integration.md` with GitHub Action usage example
- [ ] Add pre-commit hook setup instructions
- [ ] Add "Quick start" section for CI

### S22-08: Tests

- [ ] `tests/unit/ci/test_precommit_generator.py` — assert valid YAML output
- [ ] Test `init-hooks` CLI command creates file in target directory

### Validation

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] Commit & push
