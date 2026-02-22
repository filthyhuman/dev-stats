# Sprint 11 — Dashboard HTML & All Tabs

**Phase:** 04 | **Duration:** 2 weeks
**Goal:** Complete functional dashboard with all 10 tabs.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S11-01 | output/dashboard/dashboard_builder.py — DashboardBuilder: Jinja2 render, single HTML out | 4 |
| S11-02 | dashboard.html.jinja2 — layout: sidebar, 10 tab panels, hero cards, footer      | 3   |
| S11-03 | Tab: Overview — hero cards, LOC donut, treemap, LOC-over-time, commit heatmap   | 5   |
| S11-04 | Tab: Languages — table with sparklines, bar chart                                | 3   |
| S11-05 | Tab: Files — sortable table with colour badges                                   | 3   |
| S11-06 | Tab: Classes — ranked lists by LOC / methods / WMC                              | 3   |
| S11-07 | Tab: Methods — ranked lists by LOC / CC / parameters                            | 3   |
| S11-08 | Tab: Hotspots — scatter plot X=churn Y=CC                                        | 3   |
| S11-09 | Tab: Dependencies — module table, instability chart                              | 4   |
| S11-10 | Tab: Branches — Merged / Unmerged / Overview sub-tabs with all columns           | 5   |
| S11-11 | Tab: Git Log — 5-level expandable: entity→commits→detail→diff→blame             | 10  |
| S11-12 | Tab: Git Explorer — 6 sub-tabs: graph, file history, blame, contributors, tags, anomalies, DNA | 8 |
| S11-13 | Tab: Quality Gates — threshold table with pass/fail and trend arrows            | 3   |
| S11-14 | app.js — lazy DOM: render tab content only on first activation                  | 3   |
| S11-15 | Integration: generate from fake_repo, assert all 10 tab IDs in HTML             | 3   |

## Acceptance Criteria

- Dashboard opens offline in Chrome, Firefox, Safari — no console errors
- All 10 tabs activate and render
- Git Log expands to level 3 (commit detail) on click
- Branch tab shows copy-delete button

→ tasks_11.md
