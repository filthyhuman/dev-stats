# Sprint 22 — Pre-commit & GitHub Action

**Phase:** 09 | **Duration:** 1 week
**Goal:** Ship a reusable GitHub Action and a working pre-commit hook config.

## Stories

| #      | Story                                                                       | Pts |
|--------|-----------------------------------------------------------------------------|-----|
| S22-01 | Improve `precommit_generator.py` — generate `.pre-commit-config.yaml`      | 3   |
| S22-02 | Create `.github/action.yml` — composite action for dev-stats in CI         | 3   |
| S22-03 | Action: configurable inputs (format, fail-on-violations, since, etc.)       | 2   |
| S22-04 | Action: upload dashboard as artifact                                        | 2   |
| S22-05 | Test action locally with `act` or in a test workflow                        | 2   |
| S22-06 | Pre-commit hook: performance < 30s on medium repos                          | 2   |
| S22-07 | Docs: update `ci_integration.md` with action usage examples                 | 2   |
| S22-08 | Tests for precommit generator improvements                                  | 2   |

## Acceptance Criteria

- `dev-stats init-hooks` generates working `.pre-commit-config.yaml`
- GitHub Action works with `uses: filthyhuman/dev-stats@v0.2`
- Action uploads dashboard artifact on PR
- All validation commands pass

> tasks_22.md
