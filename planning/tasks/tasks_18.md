# Tasks 18 — End-to-End Integration Tests

Derived from planning/sprints/sprint_18.md.

## Checklist

### S18-01: Enhanced fake_repo fixture

- [ ] Update `tests/conftest.py` `fake_repo` fixture (or create new one)
- [ ] Fixture creates a temp git repo with: Python, Java, JS files
- [ ] Fixture creates multiple commits with different authors
- [ ] Fixture creates branches (active, stale, merged)
- [ ] Use `freezegun` for deterministic timestamps
- [ ] Fixture yields `(repo_path, expected_stats)` for assertion convenience

### S18-02: E2E analyse test

- [ ] Create `tests/integration/test_e2e_analyse.py`
- [ ] Use `typer.testing.CliRunner` to invoke `dev-stats analyse <fake_repo>`
- [ ] Assert exit code 0
- [ ] Assert terminal output contains file count, language breakdown, LOC
- [ ] Assert terminal output contains git history section

### S18-03: E2E export tests

- [ ] Create `tests/integration/test_e2e_exports.py`
- [ ] Test `--format json` -> valid JSON file exists, parseable, has expected keys
- [ ] Test `--format csv` -> valid CSV with header row and data rows
- [ ] Test `--format xml` -> well-formed XML with JUnit structure
- [ ] Test `--format badges` -> SVG files exist and contain `<svg>` tag
- [ ] Test `--format dashboard` -> HTML file exists, contains `<!DOCTYPE html>`
- [ ] Test `--format all` -> all of the above

### S18-04: E2E git analysis tests

- [ ] Create `tests/integration/test_e2e_git_analysis.py`
- [ ] Assert `--format json` output contains `commits`, `contributors`, `branches_report`
- [ ] Assert commit count matches number of commits in fake_repo
- [ ] Assert contributor names appear correctly
- [ ] Assert `--since` flag filters commits

### S18-05: E2E CI adapter tests

- [ ] Create `tests/integration/test_e2e_ci.py`
- [ ] Test `--ci github` -> output contains `::warning` or `::error` annotations
- [ ] Test `--ci gitlab` -> output contains GitLab Code Quality JSON
- [ ] Test `--ci jenkins` -> output contains JUnit-style XML
- [ ] Test `--ci teamcity` -> output contains `##teamcity` service messages

### S18-06: E2E edge-case tests

- [ ] Create `tests/integration/test_e2e_edge_cases.py`
- [ ] Test: empty directory (no files) -> exit 0, "Found 0 file(s)"
- [ ] Test: directory with no `.git` -> git analysis skipped gracefully
- [ ] Test: single Python file -> produces valid report
- [ ] Test: repo with binary files -> binary files excluded, no crash

### S18-07: Performance regression test

- [ ] Create `tests/integration/test_performance.py`
- [ ] `@pytest.mark.slow` marker
- [ ] Run `dev-stats analyse .` on own repo (or a fixture repo with 500+ files)
- [ ] Assert completes in < 10 seconds

### Validation

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] `uv run pytest -m integration` passes (all integration tests)
- [ ] Commit & push
