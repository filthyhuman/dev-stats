# CI Integration

> Step-by-step setup for Jenkins, GitLab CI, TeamCity, GitHub Actions,
> and pre-commit hooks.

---

## Overview

dev-stats produces native output for four CI platforms. Each adapter
translates quality-gate violations into the platform's expected format:

| Platform       | Adapter    | Output Format                           | Report File(s)                       |
|----------------|------------|-----------------------------------------|--------------------------------------|
| Jenkins        | `jenkins`  | JUnit XML                               | `dev-stats-junit.xml`                |
| GitLab CI      | `gitlab`   | Code Quality JSON                       | `gl-code-quality-report.json`        |
| TeamCity       | `teamcity` | Service Messages (stdout)               | `dev-stats-teamcity.txt`             |
| GitHub Actions | `github`   | Workflow annotations + Step Summary     | `dev-stats-annotations.txt`, `dev-stats-step-summary.md` |

All adapters share the same violation-checking engine. Thresholds are
configured in `thresholds.toml` or via `DEV_STATS_*` environment variables.

---

## Common Flags

```bash
dev-stats analyse . \
    --ci <platform>        \   # jenkins | gitlab | teamcity | github
    --fail-on-violations   \   # exit 1 when any threshold is breached
    --diff <branch>        \   # only report violations in changed files
    --config <file>        \   # custom thresholds.toml
    --output <dir>             # where to write report files
```

---

## Jenkins

### Jenkinsfile

```groovy
pipeline {
    agent any
    stages {
        stage('Install') {
            steps {
                sh 'pip install dev-stats'
            }
        }
        stage('Code Quality') {
            steps {
                sh 'dev-stats analyse . --ci jenkins --fail-on-violations --output dev-stats-output'
            }
            post {
                always {
                    junit 'dev-stats-output/dev-stats-junit.xml'
                }
            }
        }
    }
}
```

### What Happens

1. dev-stats analyses the repository and checks all quality-gate thresholds.
2. Violations are written as JUnit XML test cases to `dev-stats-junit.xml`.
3. Each violation becomes a `<testcase>` inside a `<testsuite name="dev-stats">`.
4. ERROR-severity violations have `<failure>` elements with rule, value,
   threshold, file, and line details.
5. Jenkins parses the XML and displays results in the Test Result trend.
6. `--fail-on-violations` makes the build fail if any thresholds are breached.

---

## GitLab CI

### `.gitlab-ci.yml`

```yaml
dev-stats:
  stage: test
  image: python:3.12
  before_script:
    - pip install dev-stats
  script:
    - dev-stats analyse . --ci gitlab --fail-on-violations --output dev-stats-output
  artifacts:
    reports:
      codequality: dev-stats-output/gl-code-quality-report.json
    paths:
      - dev-stats-output/
```

### What Happens

1. dev-stats produces `gl-code-quality-report.json` in GitLab Code Quality format.
2. Each violation becomes a JSON object with:
   - `check_name`: the violated rule
   - `description`: human-readable message
   - `severity`: `info`, `minor`, or `major`
   - `fingerprint`: deterministic MD5 hash for deduplication
   - `location`: file path and line number
3. GitLab displays violations inline in merge request diffs.
4. Severity mapping: INFO → info, WARNING → minor, ERROR → major.

---

## TeamCity

### Build Step

Add a **Command Line** build step:

```
dev-stats analyse . --ci teamcity --fail-on-violations
```

### What Happens

1. dev-stats emits `##teamcity[...]` service messages to stdout.
2. TeamCity automatically picks up these messages:
   - `buildStatisticValue` — LOC, file count, violation count appear in
     build trend charts.
   - `inspectionType` — registers each rule as an inspection category.
   - `inspection` — individual violations with file, line, and severity.
   - `buildProblem` — ERROR-severity violations fail the build.
3. No plugin installation required — TeamCity parses service messages natively.

### Escaping

The adapter escapes special characters (`|`, `'`, `\n`, `\r`, `[`, `]`)
per TeamCity's service message protocol.

---

## GitHub Actions

### Workflow

```yaml
name: Code Quality
on: [push, pull_request]
jobs:
  dev-stats:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv pip install dev-stats
      - run: dev-stats analyse . --ci github --fail-on-violations --output dev-stats-output
      - name: Upload Step Summary
        if: always()
        run: cat dev-stats-output/dev-stats-step-summary.md >> "$GITHUB_STEP_SUMMARY"
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: dev-stats-report
          path: dev-stats-output/
```

### What Happens

1. dev-stats emits `::error::` and `::warning::` workflow commands to stdout.
2. GitHub Actions renders these as inline annotations on the PR diff.
3. A Markdown step summary is written to `dev-stats-step-summary.md`.
   Append it to `$GITHUB_STEP_SUMMARY` for a summary table in the Actions UI.
4. The summary includes file count, total lines, violation count, and a
   severity/rule/file/line/message table.

### Delta Mode

Use `--diff` to only report violations in files changed by the PR:

```yaml
- run: dev-stats analyse . --ci github --diff origin/main --fail-on-violations
```

---

## Pre-commit Hook

dev-stats can run as a [pre-commit](https://pre-commit.com/) hook.

### Setup

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: dev-stats
        name: dev-stats quality check
        entry: dev-stats analyse --fail-on-violations
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

### Generating the Snippet

```bash
# Print the YAML snippet to stdout
python -c "from dev_stats.ci.precommit_generator import PrecommitGenerator; print(PrecommitGenerator().generate())"

# Or write it to a file
python -c "from dev_stats.ci.precommit_generator import PrecommitGenerator; PrecommitGenerator().write(Path('.'))"
```

### What Happens

1. On every `git commit`, pre-commit runs `dev-stats analyse --fail-on-violations`.
2. If any quality gates are breached, the commit is rejected.
3. The hook runs on the full repository (`pass_filenames: false`, `always_run: true`).

---

## Quality-Gate Thresholds

All CI adapters share the same configurable thresholds:

| Threshold                    | Default | Severity |
|------------------------------|---------|----------|
| `max_file_lines`             | 500     | WARNING  |
| `max_function_lines`         | 50      | WARNING  |
| `max_cyclomatic_complexity`  | 10      | ERROR    |
| `max_cognitive_complexity`   | 15      | WARNING  |
| `max_parameters`             | 5       | WARNING  |
| `max_nesting_depth`          | 4       | WARNING  |
| `max_class_lines`            | 300     | WARNING  |
| `max_class_methods`          | 20      | WARNING  |
| `max_imports`                | 15      | WARNING  |
| `max_duplication_pct`        | 5.0%    | ERROR    |
| `min_test_coverage`          | 80.0%   | ERROR    |

Override via TOML:

```toml
# thresholds.toml
[thresholds]
max_cyclomatic_complexity = 15
max_function_lines = 80
max_duplication_pct = 10.0
```

Or via environment variables:

```bash
export DEV_STATS_THRESHOLDS__MAX_CYCLOMATIC_COMPLEXITY=15
```
