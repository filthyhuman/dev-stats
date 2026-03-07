# Phase 07 — Robustness & Testing

**Sprints:** 18 · 19
**Goal:** End-to-end integration tests, error handling hardening,
performance benchmarks, and edge-case coverage.

**Done when:** Full E2E test suite runs `dev-stats analyse` against a real
temporary git repo and asserts on every output format. All `except Exception`
blocks replaced with specific types. Performance regression test passes.

## Modules Delivered

```
tests/integration/  test_e2e_analyse.py, test_e2e_exports.py,
                    test_e2e_git_analysis.py, test_performance.py
cli/                analyse_command.py (hardened error handling)
core/parsers/       edge-case fixes across all parsers
```

## Risks

- Integration tests are slower and may be flaky on CI -> use `@pytest.mark.slow`.
- Git fixtures must be deterministic -> use `freezegun` and scripted repos.

> Sprints: sprint_18.md · sprint_19.md
