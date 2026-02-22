# Sprint 07 — Log Harvester & Commit Model

**Phase:** 03 | **Duration:** 1 week
**Goal:** Full structured commit history extracted from any git repo.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S07-01 | core/git/log_harvester.py — LogHarvester: null-byte git log, full CommitRecord, --stat parsing | 8 |
| S07-02 | core/git/log_harvester.py — head_info(), current_branch() helpers               | 1   |
| S07-03 | core/git/diff_engine.py — DiffEngine: unified diff parsing, DiffHunk/DiffLine models | 5 |
| S07-04 | core/git/tree_walker.py — TreeWalker: git ls-tree, directory sizes, submodule detection | 4 |
| S07-05 | core/git/commit_enricher.py — CommitEnricher: cross-commit fields, streaks, is_reverted, wip_commit | 5 |
| S07-06 | Wire LogHarvester + CommitEnricher into gitlog_command.py                        | 2   |
| S07-07 | tests/unit/core/git/test_log_harvester.py — mocked subprocess, all parse cases  | 5   |
| S07-08 | tests/unit/core/git/test_diff_engine.py — hunk header parsing                   | 3   |
| S07-09 | tests/unit/core/git/test_commit_enricher.py — streak, is_reverted, percentile   | 3   |
| S07-10 | Integration: harvest on fake_repo returns ≥ 2 commits with correct author        | 2   |

## Acceptance Criteria

- LogHarvester parses 1000 commits in < 5 seconds
- Merge commits have is_merge=True and len(parent_hashes) > 1
- CommitEnricher sets is_reverted=True for "Revert" subjects
- DiffEngine correctly parses @@ -10,5 +10,8 @@ hunk header

→ tasks_07.md
