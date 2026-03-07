# Tasks 23 — v0.2.0 Release & Community Readiness

Derived from planning/sprints/sprint_23.md.

## Checklist

### S23-01: CONTRIBUTING.md

- [ ] Dev setup instructions (uv sync, pre-commit install)
- [ ] Coding standards summary (link to CLAUDE.md for full rules)
- [ ] PR process: branch naming, commit messages, review expectations
- [ ] Testing requirements: all new code needs tests, coverage minimums

### S23-02: SECURITY.md

- [ ] Vulnerability reporting: email or GitHub security advisories
- [ ] Supported versions table
- [ ] Response timeline expectations

### S23-03: Issue templates

- [ ] `.github/ISSUE_TEMPLATE/bug_report.md` — steps to reproduce, expected/actual
- [ ] `.github/ISSUE_TEMPLATE/feature_request.md` — use case, proposed solution
- [ ] `.github/ISSUE_TEMPLATE/parser_improvement.md` — language, input sample, expected output

### S23-04: CHANGELOG.md v0.2.0

- [ ] Update CHANGELOG.md with v0.2.0 section
- [ ] Categories: Added (tree-sitter, cognitive complexity, watch mode, E2E tests, action)
- [ ] Categories: Changed (error handling, dashboard a11y, terminal UX)
- [ ] Categories: Fixed (cognitive complexity was hardcoded to 0, coverage gaps)

### S23-05: Version bump

- [ ] Update `version = "0.2.0"` in `pyproject.toml`
- [ ] Update any hardcoded version strings in source

### S23-06: README.md refresh

- [ ] Feature list updated with new capabilities
- [ ] Add screenshot/GIF of terminal output
- [ ] Add screenshot of dashboard
- [ ] Badge URLs point to real CI and PyPI
- [ ] Quick start section with installation + first run

### S23-07: Self-analysis

- [ ] Run `dev-stats analyse . --format all --output docs/showcase/`
- [ ] Commit dashboard output as docs showcase
- [ ] Link from README.md

### S23-08: Final coverage audit

- [ ] `pytest --cov` overall >= 92%
- [ ] `core/` >= 95%
- [ ] `output/` >= 90%
- [ ] `ci/` >= 90%
- [ ] `config/` >= 95%
- [ ] No individual file below 85%

### S23-09: Final validation

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] `dev-stats analyse . --fail-on-violations` passes

### S23-10: Tag and release

- [ ] `git tag v0.2.0`
- [ ] `git push origin v0.2.0`
- [ ] Verify release workflow triggers and publishes to PyPI
- [ ] Verify `pip install dev-stats==0.2.0` works

### Validation

- [ ] All of the above checked
- [ ] Commit & push
