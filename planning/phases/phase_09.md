# Phase 09 — Ecosystem & Release

**Sprints:** 22 · 23
**Goal:** Pre-commit hook integration, GitHub Actions reusable workflow,
v0.2.0 release to PyPI, and community-readiness.

**Done when:** Users can add dev-stats as a pre-commit hook, use it in
GitHub Actions with a single `uses:` line, and install v0.2.0 from PyPI.
CONTRIBUTING.md, issue templates, and security policy in place.

## Modules Delivered

```
ci/                 precommit_generator.py (improvements)
.github/            action.yml (reusable composite action)
docs/               CONTRIBUTING.md, SECURITY.md
```

## Risks

- Reusable action needs careful version pinning and caching strategy.
- Pre-commit hook performance must stay under 30s for developer experience.

> Sprints: sprint_22.md · sprint_23.md
