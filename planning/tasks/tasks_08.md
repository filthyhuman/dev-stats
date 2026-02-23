# Tasks 08 — Branch Analyzer & Blame Engine

Derived from planning/sprints/sprint_08.md.

## Checklist

### S08-01: Merge Detector
- [x] Create `src/dev_stats/core/git/merge_detector.py` — `MergeDetector`: exact, squash, rebase detection

### S08-02: Activity Scorer
- [x] Create `src/dev_stats/core/git/activity_scorer.py` — `ActivityScorer`: 0-100 scoring, status classification

### S08-03: Remote Sync
- [x] Create `src/dev_stats/core/git/remote_sync.py` — `RemoteSync`: ahead/behind, tracking, has-remote check

### S08-04: Branch Analyzer
- [x] Create `src/dev_stats/core/git/branch_analyzer.py` — `BranchAnalyzer`: orchestrates all branch modules

### S08-05: Blame Engine
- [x] Create `src/dev_stats/core/git/blame_engine.py` — `BlameEngine`: git blame --line-porcelain, ownership, bus-factor

### S08-06: CLI Wiring
- [x] Update `src/dev_stats/cli/branches_command.py` — wire BranchAnalyzer, terminal table output

### S08-08: Merge Detector Tests
- [x] Create `tests/unit/core/git/test_merge_detector.py`

### S08-09: Activity Scorer Tests
- [x] Create `tests/unit/core/git/test_activity_scorer.py`

### S08-10: Blame Engine Tests
- [x] Create `tests/unit/core/git/test_blame_engine.py`

### Validation
- [x] `uv run ruff check .` passes
- [x] `uv run ruff format .` passes
- [x] `uv run mypy src/ --strict` passes
- [x] `uv run pytest` passes (all tests green)
- [x] Commit & push
