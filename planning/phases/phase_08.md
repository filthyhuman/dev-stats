# Phase 08 — Dashboard & UX Polish

**Sprints:** 20 · 21
**Goal:** Production-quality dashboard, watch mode implementation,
improved terminal UX, and accessibility.

**Done when:** Dashboard renders correctly on all major browsers, passes
WCAG AA contrast checks, and `--watch` mode works with debounced re-analysis.
Terminal output handles edge cases (empty repos, single-file repos, no git).

## Modules Delivered

```
cli/                analyse_command.py (--watch implementation)
output/dashboard/   templates/assets/ (chart polish, responsive, a11y)
output/exporters/   terminal_reporter.py (edge-case handling)
```

## Risks

- Watch mode needs filesystem events -> `watchfiles` dependency or polling fallback.
- Dashboard browser testing requires manual QA or playwright -> defer automated browser tests.

> Sprints: sprint_20.md · sprint_21.md
