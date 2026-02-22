# Sprint 09 — Advanced Git Analysis

**Phase:** 03 | **Duration:** 1 week
**Goal:** Contributors, tags, anomalies, timeline data all populated in RepoReport.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S09-01 | core/git/ref_explorer.py — RefExplorer: TagRecord, StashRecord, WorktreeRecord, NoteRecord | 5 |
| S09-02 | core/git/contributor_analyzer.py — ContributorAnalyzer: profiles, aliases, survival rate, work patterns | 6 |
| S09-03 | core/git/timeline_builder.py — TimelineBuilder: LOC series, language evolution, team growth | 4 |
| S09-04 | core/git/pattern_detector.py — PatternDetector: Chain of Responsibility, 15 anomaly detectors | 8 |
| S09-05 | Wire all git modules into Aggregator                                              | 3   |
| S09-06 | tests/unit/core/git/test_ref_explorer.py — semver parsing, annotated vs lightweight | 3 |
| S09-07 | tests/unit/core/git/test_contributor_analyzer.py — alias merging, survival rate  | 3   |
| S09-08 | tests/unit/core/git/test_pattern_detector.py — each detector with crafted fixtures | 5  |
| S09-09 | Integration: full gitlog on fake_repo populates all top-level fields             | 2   |

## Acceptance Criteria

- PatternDetector detects wip_in_main for "WIP:" subject on protected branch
- ContributorAnalyzer merges aliases (same name, different emails)
- TimelineBuilder produces sorted (date, loc_total) list
- RefExplorer parses "v1.2.3-rc.1" as semver tag

→ tasks_09.md
