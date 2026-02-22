# Phase 03 — Git Integration

**Sprints:** 07 · 08 · 09
**Goal:** Complete git history, branch analysis, blame, contributors, anomaly detection.

**Done when:** `dev-stats branches . --show merged` correctly identifies all
merged branches. `dev-stats gitlog .` produces contributor profiles and detects
≥ 5 anomaly types on a test repository.

## Modules Delivered

```
core/git/   log_harvester.py, commit_enricher.py, diff_engine.py, tree_walker.py,
            branch_analyzer.py, merge_detector.py, activity_scorer.py, remote_sync.py,
            blame_engine.py, ref_explorer.py, contributor_analyzer.py,
            timeline_builder.py, pattern_detector.py
```

## Risks

- 50k+ commit repos → use streaming, enforce `--depth` default.
- Squash detection false positives → add confidence threshold config.
- Blame on renamed files is slow → `--no-blame` escape hatch.

→ Sprints: sprint_07.md · sprint_08.md · sprint_09.md
