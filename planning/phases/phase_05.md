# Phase 05 — CI Integration & Release

**Sprints:** 13 · 14
**Goal:** All CI adapters production-ready, PyPI release, complete documentation.

**Done when:** Each CI adapter tested against a real CI run. Package installable
via `uv tool install dev-stats` and `pip install dev-stats`.

## Modules Delivered

```
ci/   abstract_ci_adapter.py, violation.py, jenkins_adapter.py, gitlab_adapter.py,
      teamcity_adapter.py, github_actions_adapter.py, precommit_generator.py
```

## Risks

- PyPI name `dev-stats` may be taken → check early, have fallback names ready.
- TeamCity escaping edge cases → test against their emulator.

→ Sprints: sprint_13.md · sprint_14.md
