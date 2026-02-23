# Tasks 12 — Dashboard Polish & Performance

Derived from planning/sprints/sprint_12.md.

## Checklist

### S12-01: Virtual scrolling for large tables
- [x] Update `src/dev_stats/output/dashboard/templates/assets/app.js` — add `VirtualScroller` class: renders only visible rows + buffer for tables > 500 rows, attaches to scroll container

### S12-02: DecompressionStream fallback
- [x] Update `src/dev_stats/output/dashboard/templates/assets/app.js` — add uncompressed JSON fallback in `DataLoader` when neither DecompressionStream nor pako available (raw JSON detection + UTF-8 decode fallback)

### S12-03: Size enforcement
- [x] Update `src/dev_stats/output/dashboard/dashboard_builder.py` — add `DashboardSizeError` exception class and `_check_size()`: warn at 30 MB, raise at 50 MB with clear message and CLI flags

### S12-04: Copy safe deletes button
- [x] Update `src/dev_stats/output/dashboard/templates/dashboard.html.jinja2` — add "Copy safe deletes" button in branches tab
- [x] Update `src/dev_stats/output/dashboard/templates/assets/app.js` — add `CopyDeleteScript` class: builds multi-line `git branch -d` script, copies to clipboard

### S12-05: URL hash sort state
- [x] Update `src/dev_stats/output/dashboard/templates/assets/app.js` — extend `TableSorter` to encode sort state in URL hash (`#sort=tableId:col:dir`) and restore on page load

### S12-06: Blame heat map colour scale
- [x] Update `src/dev_stats/output/dashboard/templates/assets/styles.css` — add `.blame-age-fresh`, `.blame-age-recent`, `.blame-age-old`, `.blame-age-ancient` colour classes
- [x] Update `src/dev_stats/output/dashboard/templates/assets/app.js` — add `BlameHeatMap` class: assigns age-based colour classes by date threshold (30/180/365 days)

### S12-07: Commit graph visualisation
- [x] Update `src/dev_stats/output/dashboard/templates/assets/app.js` — add `CommitGraph` class: canvas-based commit graph with zoom (wheel) and pan (drag)

### S12-08: Contributor activity heatmap
- [x] Update `src/dev_stats/output/dashboard/templates/assets/app.js` — add `ActivityHeatmap` class: 52-week calendar grid rendered from commit authored_date data

### S12-09: Print CSS
- [x] Update `src/dev_stats/output/dashboard/templates/assets/styles.css` — add `@media print` rules: tables paginate, charts inline, sidebar/filters/buttons hidden

### S12-10: Dark/light mode toggle
- [x] Update `src/dev_stats/output/dashboard/templates/assets/styles.css` — add `:root.light` theme variables with GitHub-light palette
- [x] Update `src/dev_stats/output/dashboard/templates/dashboard.html.jinja2` — add theme toggle button (&#9790;/&#9728;) in header
- [x] Update `src/dev_stats/output/dashboard/templates/assets/app.js` — add `ThemeToggle` class: switches root class, persists preference in localStorage

### S12-11: Performance & size tests
- [x] Create `tests/unit/output/test_dashboard_performance.py` — 5000 commits + 500 files < 45 MB and < 30 s; size warn/error threshold tests; DashboardSizeError attribute tests

### Validation
- [x] `uv run ruff check .` passes
- [x] `uv run ruff format .` passes
- [x] `uv run mypy src/ --strict` passes
- [x] `uv run pytest` passes (all tests green — 460 passed)
- [ ] Commit & push
