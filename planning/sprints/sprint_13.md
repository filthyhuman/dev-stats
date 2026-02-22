# Sprint 13 — CI Adapters

**Phase:** 05 | **Duration:** 1 week
**Goal:** All 4 CI adapters production-ready. --fail-on-violations exits 1.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S13-01 | ci/violation.py — Violation frozen dataclass                                    | 1   |
| S13-02 | ci/abstract_ci_adapter.py — AbstractCIAdapter: check_violations, abstract emit  | 4   |
| S13-03 | ci/jenkins_adapter.py — JenkinsAdapter: JUnit XML + Jenkinsfile snippet          | 4   |
| S13-04 | ci/gitlab_adapter.py — GitlabAdapter: Code Quality JSON + badge JSON            | 4   |
| S13-05 | ci/teamcity_adapter.py — TeamCityAdapter: buildStatisticValue, inspection, buildProblem | 4 |
| S13-06 | ci/github_actions_adapter.py — GithubActionsAdapter: ::error:: + step summary   | 4   |
| S13-07 | ci/precommit_generator.py — PrecommitGenerator: hook yaml snippet               | 2   |
| S13-08 | --fail-on-violations: sys.exit(1) when violations and flag set                  | 2   |
| S13-09 | --diff BASE_BRANCH: delta mode, only new violations                             | 4   |
| S13-10 | tests/unit/ci/test_abstract_ci_adapter.py                                        | 3   |
| S13-11 | tests/unit/ci/test_teamcity_adapter.py                                           | 3   |
| S13-12 | tests/unit/ci/test_gitlab_adapter.py                                             | 2   |
| S13-13 | tests/unit/ci/test_jenkins_adapter.py                                            | 2   |
| S13-14 | tests/unit/ci/test_github_actions_adapter.py                                    | 2   |

## Acceptance Criteria

- --ci teamcity prints ##teamcity[buildStatisticValue key='LOC' value='...']
- --ci gitlab produces gl-code-quality-report.json
- Exit code 1 when violations exist and --fail-on-violations set
- --diff main only reports violations not on main

→ tasks_13.md
