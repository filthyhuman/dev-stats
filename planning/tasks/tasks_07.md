# Tasks 07 — Log Harvester & Commit Model

Derived from planning/sprints/sprint_07.md.

## Checklist

### S07-00: New models
- [x] Add `DiffLine`, `DiffHunk`, `TreeEntry` frozen dataclasses to `models.py`

### S07-01: Log Harvester
- [x] Create `src/dev_stats/core/git/log_harvester.py` — `LogHarvester` with null-byte git log, full CommitRecord, --stat parsing, head_info(), current_branch()

### S07-03: Diff Engine
- [x] Create `src/dev_stats/core/git/diff_engine.py` — `DiffEngine` with unified diff parsing, DiffHunk/DiffLine extraction

### S07-04: Tree Walker
- [x] Create `src/dev_stats/core/git/tree_walker.py` — `TreeWalker` with git ls-tree, directory sizes, submodule detection

### S07-05: Commit Enricher
- [x] Create `src/dev_stats/core/git/commit_enricher.py` — `CommitEnricher` with cross-commit fields, streaks, is_reverted, wip_commit

### S07-06: CLI Wiring
- [x] Update `src/dev_stats/cli/gitlog_command.py` — wire LogHarvester + CommitEnricher

### S07-07: Log Harvester Tests
- [x] Create `tests/unit/core/git/test_log_harvester.py` — mocked subprocess, all parse cases

### S07-08: Diff Engine Tests
- [x] Create `tests/unit/core/git/test_diff_engine.py` — hunk header parsing

### S07-09: Commit Enricher Tests
- [x] Create `tests/unit/core/git/test_commit_enricher.py` — streak, is_reverted, percentile

### S07-10: Tree Walker Tests
- [x] Create `tests/unit/core/git/test_tree_walker.py`

### Validation
- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] Commit & push
