# Sprint 20 — Watch Mode & Terminal UX

**Phase:** 08 | **Duration:** 1 week
**Goal:** Implement the `--watch` flag. Polish terminal output for edge cases.

## Stories

| #      | Story                                                                       | Pts |
|--------|-----------------------------------------------------------------------------|-----|
| S20-01 | Add `watchfiles` to optional dependencies                                   | 1   |
| S20-02 | Implement `--watch` mode with debounced re-analysis (500ms)                 | 5   |
| S20-03 | Graceful Ctrl-C handling in watch mode with cleanup                         | 2   |
| S20-04 | Terminal reporter: handle empty repos (0 files) gracefully                  | 2   |
| S20-05 | Terminal reporter: handle repos with no git init                            | 2   |
| S20-06 | Terminal reporter: handle single-file repos                                 | 1   |
| S20-07 | Add `--sort` flag to control table sort order via `sort_schema.py`          | 3   |
| S20-08 | Tests for watch mode, edge-case terminal output                             | 3   |

## Acceptance Criteria

- `dev-stats analyse . --watch` re-runs on file changes
- Ctrl-C cleanly stops watch mode
- Empty/no-git/single-file repos produce meaningful output (not crashes)
- All validation commands pass

> tasks_20.md
