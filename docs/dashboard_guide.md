# Dashboard Guide

> How to generate, navigate, and customise the self-contained HTML dashboard.

---

## Generating the Dashboard

```bash
# Generate dashboard only
dev-stats analyse /path/to/repository -f dashboard

# Or generate all formats including dashboard
dev-stats analyse /path/to/repository -f all

# Dashboard file appears in the output directory
open dev-stats-output/dev-stats-dashboard.html
```

The dashboard is a single `.html` file containing all CSS, JavaScript, and
data inline. No web server, npm, or internet connection required — just
double-click the file in any modern browser.

---

## Dashboard Tabs

### Overview

The landing page with summary cards and high-level visualisations.

- **Hero cards** — total files, total lines of code, languages detected,
  number of classes and functions.
- **LOC donut chart** — proportional code vs. blank vs. comment lines.
- **Directory treemap** — modules sized by line count.
- **Commit heatmap** — activity calendar showing commit density per day.

### Languages

Per-language breakdown with sortable columns.

- File count, total lines, code lines, blank lines, comment lines per language.
- Comment ratio column for at-a-glance documentation coverage.

### Files

The complete file listing with inline metric badges.

- Sortable by path, language, total lines, code lines, blank lines,
  comment lines, class count, function count.
- Click column headers to sort ascending/descending.
- Use the filter bar to search by filename or language.

### Classes

All classes ranked by size and complexity.

- Columns: name, file, line number, total lines, method count, attribute count.
- Sorted by lines (descending) by default — largest classes first.

### Methods

All functions and methods ranked by complexity metrics.

- Columns: name, file, line number, lines, cyclomatic complexity,
  cognitive complexity, parameters, nesting depth.
- Sort by any column to find the most complex or deeply nested code.

### Hotspots

Scatter plot combining complexity and churn data.

- **X-axis**: churn score (how often the file changes).
- **Y-axis**: complexity (cyclomatic or cognitive).
- Files in the top-right quadrant are high-risk hotspots — complex and
  frequently changing.

### Dependencies

Module coupling analysis with instability metrics.

- Afferent coupling (Ca): modules depending on this one.
- Efferent coupling (Ce): modules this one depends on.
- Instability I = Ce / (Ca + Ce).
- Distance from main sequence D = |A + I - 1|.

### Branches

Branch management with deletability scoring.

- Merged/unmerged status, commits ahead/behind, last activity date.
- Deletability score (0–100) with colour-coded categories:
  **safe** (green), **caution** (amber), **keep** (red).
- Copy-to-clipboard button for safe-delete shell commands.

### Git Log

Expandable commit history browser.

- Five-level drill-down: entity → commits → detail → diff → blame.
- Each commit shows SHA, author, date, message, and file changes.
- Enriched with classification: merge, fixup, revert, conventional type.

### Quality Gates

Threshold pass/fail dashboard.

- Each quality gate (max file lines, max complexity, etc.) shown with
  current value vs. configured threshold.
- Pass/fail indicators for at-a-glance status.
- Violation count and severity breakdown.

---

## Interactivity Features

### Table Sorting

Click any column header to sort. Click again to reverse. The currently
sorted column is indicated with an arrow (▲/▼).

### Filter Bar

Type in the filter input to instantly search across all visible columns.
The filter applies to the currently active tab.

### Theme Toggle

Click the theme toggle button (top-right) to switch between light and dark
mode. The preference is saved in `localStorage`.

### URL Hash State

Sort state is encoded in the URL hash. Share a link to a specific sort
configuration — recipients see the same view.

### Virtual Scrolling

Tables with more than 200 rows use virtual scrolling for smooth performance.
Only visible rows are rendered in the DOM.

---

## Size Limits

The dashboard builder enforces size limits to prevent browser issues:

- **Warning** at 30 MB — a console warning is logged but the file is still
  generated.
- **Error** at 50 MB — a `DashboardSizeError` is raised and generation is
  aborted.

To reduce dashboard size:
- Use `--exclude` to skip vendored or generated directories.
- Use `--lang` to restrict to specific languages.
- Use `--top N` to limit ranking tables.

---

## Customisation

### Custom Thresholds

Quality gates shown in the dashboard use the same thresholds as the CLI:

```toml
# thresholds.toml
[thresholds]
max_cyclomatic_complexity = 15
max_function_lines = 60
max_class_lines = 400
```

```bash
dev-stats analyse /path/to/repository --config thresholds.toml -f all
```

### Embedding in CI

Generate the dashboard as a CI artifact:

```yaml
# GitHub Actions
- run: dev-stats analyse . -f dashboard --ci github
- uses: actions/upload-artifact@v4
  with:
    name: dev-stats-dashboard
    path: dev-stats-output/dev-stats-dashboard.html
```
