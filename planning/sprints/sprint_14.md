# Sprint 14 — Release, Docs & Self-Analysis

**Phase:** 05 | **Duration:** 1 week
**Goal:** Package on PyPI. Docs complete. Tool passes its own quality gates.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S14-01 | docs/architecture.md — data-flow diagram, pattern table, model hierarchy        | 2   |
| S14-02 | docs/dashboard_guide.md — all 10 tabs explained with descriptions               | 3   |
| S14-03 | docs/ci_integration.md — detailed setup for all 4 CI platforms + pre-commit     | 3   |
| S14-04 | CHANGELOG.md — complete Keep-a-Changelog for 0.1.0                              | 1   |
| S14-05 | .github/workflows/release.yml — uv build + uv publish on tag                   | 2   |
| S14-06 | Check PyPI name, register dev-stats                                              | 1   |
| S14-07 | uv build smoke test: wheel installs, dev-stats --version works in clean venv    | 2   |
| S14-08 | Self-analysis: dev-stats analyse . --output all --ci github on own repo         | 3   |
| S14-09 | Commit self-analysis dashboard to docs/ as showcase                             | 1   |
| S14-10 | Performance regression: analysis of own repo < 10 s                             | 2   |
| S14-11 | E2E: install from wheel in tmp venv, run analyse, assert exit 0                 | 3   |
| S14-12 | Update README.md badge URLs to real CI and PyPI                                 | 1   |
| S14-13 | Docstring review: all public symbols complete, Google style                      | 2   |
| S14-14 | Final coverage check: all modules meet minimums                                  | 2   |

## Acceptance Criteria

- pip install dev-stats works from PyPI
- uv tool install dev-stats works
- dev-stats passes its own --fail-on-violations check
- All docs pages complete and internally link-consistent

→ tasks_14.md
