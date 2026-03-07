# Sprint 18 — End-to-End Integration Tests

**Phase:** 07 | **Duration:** 1 week
**Goal:** Build a comprehensive E2E test suite that exercises the full pipeline
against a real temporary git repository.

## Stories

| #      | Story                                                                       | Pts |
|--------|-----------------------------------------------------------------------------|-----|
| S18-01 | Create `tests/conftest.py` `fake_repo` fixture with multi-language files    | 3   |
| S18-02 | `test_e2e_analyse.py` — run full analyse, assert terminal output            | 3   |
| S18-03 | `test_e2e_exports.py` — assert JSON/CSV/XML/badges/dashboard generated      | 3   |
| S18-04 | `test_e2e_git_analysis.py` — commits, branches, contributors in output      | 3   |
| S18-05 | `test_e2e_ci.py` — all 4 CI adapters produce valid output                   | 2   |
| S18-06 | `test_e2e_edge_cases.py` — empty repo, no git, single file, binary files    | 3   |
| S18-07 | `test_performance.py` — analyse own repo in < 10s (mark as `@slow`)        | 2   |

## Acceptance Criteria

- All E2E tests pass in CI
- E2E tests cover the full CLI surface (analyse, branches, gitlog)
- Edge-case tests prove graceful degradation (no crashes)
- All validation commands pass

> tasks_18.md
