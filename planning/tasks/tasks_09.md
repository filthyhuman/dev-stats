# Tasks 09 — Advanced Git Analysis

Derived from planning/sprints/sprint_09.md.

## Checklist

### S09-01: RefExplorer
- [x] Create `src/dev_stats/core/git/ref_explorer.py` — `RefExplorer`: tags (semver parsing, annotated vs lightweight), stashes, worktrees, notes

### S09-02: ContributorAnalyzer
- [x] Create `src/dev_stats/core/git/contributor_analyzer.py` — `ContributorAnalyzer`: profiles, alias merging (same name different emails), survival rate, work patterns

### S09-03: TimelineBuilder
- [x] Create `src/dev_stats/core/git/timeline_builder.py` — `TimelineBuilder`: LOC series, language evolution, team growth

### S09-04: PatternDetector
- [x] Create `src/dev_stats/core/git/pattern_detector.py` — `PatternDetector`: Chain of Responsibility, 14 anomaly detectors

### S09-05: Wire into Aggregator
- [x] Update `src/dev_stats/core/aggregator.py` — accept and pass through git analysis results

### S09-06: RefExplorer Tests
- [x] Create `tests/unit/core/git/test_ref_explorer.py` — semver parsing, annotated vs lightweight, stash, worktree, notes

### S09-07: ContributorAnalyzer Tests
- [x] Create `tests/unit/core/git/test_contributor_analyzer.py` — alias merging, work patterns, active days

### S09-08: PatternDetector Tests
- [x] Create `tests/unit/core/git/test_pattern_detector.py` — each detector with crafted fixtures

### Validation
- [x] `uv run ruff check .` passes
- [x] `uv run ruff format .` passes
- [x] `uv run mypy src/ --strict` passes
- [x] `uv run pytest` passes (all tests green)
- [x] Commit & push
