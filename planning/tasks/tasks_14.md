# Tasks 14 — Release, Docs & Self-Analysis

Derived from planning/sprints/sprint_14.md.

## Checklist

### S14-01: docs/architecture.md
- [ ] Create `docs/architecture.md` — data-flow diagram, design pattern table, model hierarchy

### S14-02: docs/dashboard_guide.md
- [ ] Create `docs/dashboard_guide.md` — all 10 tabs explained with descriptions and screenshots placeholders

### S14-03: docs/ci_integration.md
- [ ] Create `docs/ci_integration.md` — detailed setup for Jenkins, GitLab, TeamCity, GitHub Actions, and pre-commit

### S14-04: CHANGELOG.md
- [ ] Update `CHANGELOG.md` — finalize 0.1.0 release notes in Keep-a-Changelog format

### S14-05: release.yml
- [x] `.github/workflows/release.yml` already exists — verify uv build + uv publish on tag

### S14-06: PyPI name
- [ ] Note: PyPI name registration is a manual step (verify `dev-stats` availability)

### S14-07: uv build smoke test
- [ ] Run `uv build` and verify wheel is produced

### S14-08: Self-analysis
- [ ] Run `dev-stats analyse .` on own repo and verify exit 0

### S14-09: Self-analysis dashboard
- [ ] Commit self-analysis output to docs/ as showcase (if S14-08 succeeds)

### S14-10: Performance test
- [ ] Create `tests/integration/test_performance.py` — analysis of own repo < 10 s

### S14-11: E2E install test
- [ ] Create `tests/integration/test_e2e_install.py` — install from wheel in tmp venv, run analyse, assert exit 0

### S14-12: README.md badges
- [ ] Update `README.md` — replace `your-org` with real GitHub org in badge URLs

### S14-13: Docstring review
- [ ] Scan all public symbols for missing Google-style docstrings

### S14-14: Coverage check
- [ ] Run `pytest --cov` and verify all modules meet minimums

### Validation
- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] Commit & push
