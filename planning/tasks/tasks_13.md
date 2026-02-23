# Tasks 13 — CI Adapters

Derived from planning/sprints/sprint_13.md.

## Checklist

### S13-01: Violation dataclass
- [x] Create `src/dev_stats/ci/violation.py` — `Violation` frozen dataclass: rule, message, file_path, line, severity, value, threshold

### S13-02: AbstractCIAdapter
- [x] Create `src/dev_stats/ci/abstract_ci_adapter.py` — `AbstractCIAdapter`: `check_violations()` from report + thresholds, abstract `emit()`, abstract `write_report()`

### S13-03: JenkinsAdapter
- [x] Create `src/dev_stats/ci/jenkins_adapter.py` — `JenkinsAdapter`: JUnit XML output with testsuites/testsuite/testcase elements, failures as violation details

### S13-04: GitlabAdapter
- [x] Create `src/dev_stats/ci/gitlab_adapter.py` — `GitlabAdapter`: Code Quality JSON (gl-code-quality-report.json) compatible with GitLab CI

### S13-05: TeamCityAdapter
- [x] Create `src/dev_stats/ci/teamcity_adapter.py` — `TeamCityAdapter`: ##teamcity service messages (buildStatisticValue, inspectionType, inspection, buildProblem)

### S13-06: GithubActionsAdapter
- [x] Create `src/dev_stats/ci/github_actions_adapter.py` — `GithubActionsAdapter`: `::error::` / `::warning::` annotations + step summary markdown

### S13-07: PrecommitGenerator
- [x] Create `src/dev_stats/ci/precommit_generator.py` — `PrecommitGenerator`: generates `.pre-commit-hooks.yaml` snippet for dev-stats

### S13-08: --fail-on-violations wiring
- [x] Update `src/dev_stats/cli/analyse_command.py` — wire `--ci` flag to adapters, `--fail-on-violations` exits 1 when violations found

### S13-09: --diff delta mode
- [x] Update `src/dev_stats/cli/analyse_command.py` — `--diff BASE_BRANCH` filters violations to only new ones not present on base

### S13-10: AbstractCIAdapter tests
- [x] Create `tests/unit/ci/test_abstract_ci_adapter.py` — check_violations finds file-too-long, function-too-complex, etc.

### S13-11: TeamCityAdapter tests
- [x] Create `tests/unit/ci/test_teamcity_adapter.py` — ##teamcity output format, buildStatisticValue, inspectionType, buildProblem

### S13-12: GitlabAdapter tests
- [x] Create `tests/unit/ci/test_gitlab_adapter.py` — valid JSON, fingerprint, severity mapping

### S13-13: JenkinsAdapter tests
- [x] Create `tests/unit/ci/test_jenkins_adapter.py` — valid JUnit XML, testsuites structure, failures

### S13-14: GithubActionsAdapter tests
- [x] Create `tests/unit/ci/test_github_actions_adapter.py` — ::error:: format, step summary markdown

### Validation
- [x] `uv run ruff check .` passes
- [x] `uv run ruff format .` passes
- [x] `uv run mypy src/ --strict` passes
- [x] `uv run pytest` passes (all 520 tests green)
- [ ] Commit & push
