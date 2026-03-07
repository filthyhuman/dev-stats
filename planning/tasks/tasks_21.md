# Tasks 21 — Dashboard Polish & Accessibility

Derived from planning/sprints/sprint_21.md.

## Checklist

### S21-01: Responsive layout

- [ ] Add CSS media queries for breakpoints: 375px, 768px, 1024px, 1440px
- [ ] Tab navigation wraps on small screens
- [ ] Tables become horizontally scrollable on mobile
- [ ] Charts resize with container (responsive canvas)

### S21-02: WCAG AA contrast audit

- [ ] Audit all text/background colour pairs in `styles.css`
- [ ] Light theme: all pairs >= 4.5:1 contrast ratio
- [ ] Dark theme: all pairs >= 4.5:1 contrast ratio
- [ ] Fix any failing pairs (adjust colours, add background overlays)

### S21-03: Keyboard navigation

- [ ] All tabs reachable via Tab key
- [ ] Tab activation via Enter/Space
- [ ] Focus ring visible on all interactive elements
- [ ] `aria-selected`, `role="tablist"`, `role="tab"`, `role="tabpanel"` attributes
- [ ] Chart tooltips accessible via keyboard focus

### S21-04: Chart improvements

- [ ] Add tooltips showing exact values on hover
- [ ] Add legends with colour keys for all multi-series charts
- [ ] Add axis labels (X: dates/names, Y: values/counts)
- [ ] Improve colour palette for colour-blind accessibility (8-colour safe palette)

### S21-05: Loading state

- [ ] Show CSS skeleton/spinner while each tab content renders
- [ ] Replace skeleton with content when JS initialises the tab
- [ ] `<noscript>` fallback message

### S21-06: Print stylesheet

- [ ] Add `@media print` styles in `styles.css`
- [ ] Hide navigation tabs, show all sections stacked
- [ ] Charts render at fixed width for print
- [ ] Page breaks between major sections

### S21-07: File size budget

- [ ] Measure dashboard.html size for a 1000-file repo
- [ ] If > 2 MB: reduce JSON precision, compress data further, lazy-load charts
- [ ] Add test assertion: dashboard for fixture repo < expected size

### S21-08: Manual QA checklist

- [ ] Chrome latest: renders, tabs work, charts display, print works
- [ ] Firefox latest: same checks
- [ ] Safari latest: same checks
- [ ] Document any browser-specific issues in code comments

### S21-09: Dashboard template tests

- [ ] `tests/unit/output/dashboard/test_dashboard_rendering.py`
- [ ] Test with empty RepoReport (0 files, no git data)
- [ ] Test with minimal RepoReport (1 file, 1 commit)
- [ ] Test with full RepoReport (files, commits, branches, contributors, patterns)
- [ ] Assert HTML contains expected tab IDs and data attributes

### Validation

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] Commit & push
