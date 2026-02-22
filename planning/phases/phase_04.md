# Phase 04 — Dashboard

**Sprints:** 10 · 11 · 12
**Goal:** Self-contained HTML dashboard, all 10 tabs, full interactivity, no server.

**Done when:** Generated `dev-stats-dashboard.html` opens by double-click,
all tabs render correctly, Git Log drills down 5 levels, file is ≤ 50 MB
for a 2k-commit / 200-file repo.

## Modules Delivered

```
output/dashboard/   dashboard_builder.py, asset_embedder.py, data_compressor.py
                    templates/dashboard.html.jinja2
                    templates/assets/chart.min.js, styles.css, app.js
```

## Risks

- `DecompressionStream` not in all browsers → feature-detect, fallback to uncompressed.
- Virtual scrolling complexity → implement flat rendering first, virtualise after.
- Dashboard size → enforce `--max-html-mb` hard cap with clear error message.

→ Sprints: sprint_10.md · sprint_11.md · sprint_12.md
