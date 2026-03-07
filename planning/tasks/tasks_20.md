# Tasks 20 — Watch Mode & Terminal UX

Derived from planning/sprints/sprint_20.md.

## Checklist

### S20-01: Add watchfiles dependency

- [ ] Add `watchfiles>=0.21` to `[project.optional-dependencies]` under `watch` extra
- [ ] `uv sync --all-extras` succeeds

### S20-02: Implement --watch mode

- [ ] Create `cli/watch_runner.py` — encapsulates watch loop logic
- [ ] Use `watchfiles.watch()` with filter for source file extensions
- [ ] Debounce: wait 500ms after last change before re-running analysis
- [ ] Clear terminal and re-display report on each run
- [ ] Show "Watching for changes... (Ctrl-C to stop)" between runs
- [ ] Handle `ImportError` for watchfiles: show error "Install with `pip install dev-stats[watch]`"

### S20-03: Graceful Ctrl-C

- [ ] Catch `KeyboardInterrupt` in watch loop
- [ ] Print "[dim]Watch stopped.[/dim]" and exit cleanly (code 0)
- [ ] Ensure no orphan processes or temp files

### S20-04: Empty repo terminal output

- [ ] When 0 files found: print "No source files found." and exit 0 (not error)
- [ ] Skip all metric tables (don't render empty tables)
- [ ] Still show config summary (patterns, languages)

### S20-05: No-git terminal output

- [ ] When no `.git` dir: skip git section entirely
- [ ] Print "[dim]Not a git repository — git analysis skipped.[/dim]"
- [ ] All code-analysis sections still render normally

### S20-06: Single-file terminal output

- [ ] Module grouping works with 1 file (no crash on empty aggregation)
- [ ] Language summary shows 1 language, 1 file
- [ ] Test: single Python file produces complete report

### S20-07: --sort flag

- [ ] Add `--sort` option to `analyse_command.py`
- [ ] Accepts values from `sort_schema.py` (e.g. `complexity`, `lines`, `churn`)
- [ ] Sorts the main files table by the chosen metric descending
- [ ] Default: sort by `lines` (current behaviour)

### S20-08: Tests

- [ ] `tests/unit/cli/test_watch_runner.py` — mock watchfiles, assert debounce
- [ ] `tests/unit/output/test_terminal_edge_cases.py` — empty, no-git, single-file
- [ ] `tests/unit/cli/test_sort_flag.py` — assert sort order changes

### Validation

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] Commit & push
