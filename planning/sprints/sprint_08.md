# Sprint 08 — Branch Analyzer & Blame Engine

**Phase:** 03 | **Duration:** 1 week
**Goal:** Branch deletability scoring works. Blame data extracted per file.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S08-01 | core/git/merge_detector.py — MergeDetector: exact, squash, rebase detection with confidence | 6 |
| S08-02 | core/git/activity_scorer.py — ActivityScorer: 0–100 scoring model               | 4   |
| S08-03 | core/git/remote_sync.py — RemoteSync: ahead/behind, tracking, has-remote check  | 3   |
| S08-04 | core/git/branch_analyzer.py — BranchAnalyzer: orchestrates all branch modules   | 5   |
| S08-05 | core/git/blame_engine.py — BlameEngine: git blame --line-porcelain, ownership, bus-factor | 7 |
| S08-06 | Wire BranchAnalyzer into branches_command.py, terminal table output              | 3   |
| S08-07 | --generate-script: write cleanup_branches.sh                                     | 2   |
| S08-08 | tests/unit/core/git/test_merge_detector.py — mocked, all three strategies       | 4   |
| S08-09 | tests/unit/core/git/test_activity_scorer.py — score clamped, protected=KEEP     | 3   |
| S08-10 | tests/unit/core/git/test_blame_engine.py — mocked porcelain, ownership sums 1.0 | 3   |
| S08-11 | Integration: branches on fake_repo lists feature branch correctly               | 2   |

## Acceptance Criteria

- merged branch + age > 90d = score ≥ 80
- BlameEngine returns bus_factor=1 for single-author file
- cleanup_branches.sh is executable, contains git branch -d commands
- `dev-stats branches . --show merged` lists only merged branches

→ tasks_08.md
