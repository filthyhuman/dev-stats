# dev-stats

> Pure-Python repository analysis tool — code metrics, deep Git exploration,
> branch management, and a self-contained HTML dashboard.
> No AI. No server. No build step.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-blue)](https://mypy-lang.org/)
[![CI](https://github.com/filthyhuman/dev-stats/actions/workflows/ci.yml/badge.svg)](https://github.com/filthyhuman/dev-stats/actions)

---

## What it does

dev-stats analyses any local Git repository and produces:

- **Code metrics** — LOC, cyclomatic/cognitive complexity, Halstead volume,
  coupling (Ce/Ca/instability), cohesion (LCOM), duplication, test-coverage
  integration across Python, Java, JS/TS, C++, C#, Go, and 40+ file types.
- **Deep Git exploration** — full commit history with expandable drill-down,
  per-file blame heat maps, contributor profiles, anomaly detection (hardcoded
  secrets, WIP commits, bus-factor warnings, force-push traces), release timelines.
- **Branch management** — merged/unmerged lists with exact, squash, and rebase
  merge detection; a 0–100 deletion-safety score; one-command shell script for
  batch cleanup.
- **Self-contained HTML dashboard** — every chart, sortable table, and
  five-level expandable Git log packed into one `.html` file. Open by
  double-click. Share by email. No npm, no CDN, no internet required.
- **CI-native output** — JUnit XML (Jenkins), Code Quality JSON (GitLab),
  Service Messages (TeamCity), Step Summary + annotations (GitHub Actions).

---

## Installation

```bash
# via uv (recommended)
uv tool install dev-stats

# via pip
pip install dev-stats

# from source
git clone https://github.com/filthyhuman/dev-stats
cd dev-stats
uv sync --all-extras
```

---

## Quick Start

```bash
# Terminal report (instant)
dev-stats analyse .

# Generate the HTML dashboard
dev-stats analyse . --output html
open dev-stats-dashboard.html

# All output formats at once
dev-stats analyse . --output all

# Branch cleanup recommendations
dev-stats branches . --show merged --min-score 80 --generate-script

# Deep Git history with blame
dev-stats gitlog . --blame-top 50
```

---

## CLI Reference

### `dev-stats analyse [PATH]`

| Flag | Default | Description |
|---|---|---|
| `--output` | `terminal` | `all` `html` `json` `csv` `xml` `terminal` `badges` — repeatable |
| `--ci` | `none` | `jenkins` `gitlab` `teamcity` `github` |
| `--config FILE` | — | Custom thresholds.toml |
| `--exclude PATTERN` | — | Glob exclude, repeatable |
| `--top N` | `20` | Rows in ranking lists |
| `--lang NAME` | — | Restrict to language(s), repeatable |
| `--diff BRANCH` | — | Delta report vs. another branch |
| `--fail-on-violations` | false | Exit 1 when thresholds breached |
| `--watch` | false | Re-analyse on file changes |

### `dev-stats branches [PATH]`

| Flag | Default | Description |
|---|---|---|
| `--target BRANCH` | `main` | Compare-against branch |
| `--show` | `all` | `all` `merged` `unmerged` `stale` `abandoned` |
| `--all` | false | Include remote-tracking branches |
| `--min-age DAYS` | — | Only branches older than N days |
| `--min-score N` | `0` | Minimum deletability score (0–100) |
| `--generate-script` | false | Write cleanup_branches.sh |
| `--sort ATTR` | `deletability_score` | Sort attribute |

### `dev-stats gitlog [PATH]`

| Flag | Default | Description |
|---|---|---|
| `--depth N` | all | Max commits to load |
| `--since DATE` | — | Lower date bound |
| `--author REGEX` | — | Filter by author |
| `--blame-top N` | `50` | Embed blame for top-N files |
| `--include-diffs` | false | Embed full diffs |
| `--no-blame` | false | Skip blame (faster) |
| `--no-patterns` | false | Skip anomaly detection |

---

## Dashboard Tabs

| Tab | Contents |
|---|---|
| Overview | Hero cards, LOC donut, directory treemap, commit heatmap |
| Languages | Per-language table with sparklines |
| Files | Sortable table with inline metric badges |
| Classes | Ranked: by LOC, by method count, by complexity |
| Methods | Ranked: by LOC, by cyclomatic CC, by parameters |
| Hotspots | Scatter plot: complexity vs. churn |
| Dependencies | Module coupling graph, instability chart |
| Branches | Merged/unmerged with scores and copy-delete buttons |
| Git Log | Five-level expandable: entity → commits → detail → diff → blame |
| Git Explorer | Commit graph, blame viewer, contributors, tag timeline, anomalies |
| Quality Gates | Threshold pass/fail with trend indicators |

---

## CI Integration

### Jenkins
```groovy
stage('Code Quality') {
    steps { sh 'dev-stats analyse . --ci jenkins --fail-on-violations' }
    post { always {
        junit 'dev-stats-report.xml'
        publishHTML([reportDir:'.', reportFiles:'dev-stats-dashboard.html', reportName:'Dev Stats'])
    }}
}
```

### GitLab CI
```yaml
dev-stats:
  script: dev-stats analyse . --ci gitlab --output html --fail-on-violations
  artifacts:
    reports:
      codequality: gl-code-quality-report.json
    paths: [dev-stats-dashboard.html]
```

### TeamCity
```
dev-stats analyse . --ci teamcity --fail-on-violations
```
Statistics appear automatically in build trend charts. No plugin required.

### GitHub Actions
```yaml
- run: dev-stats analyse . --ci github --output html --fail-on-violations
- uses: actions/upload-artifact@v4
  with:
    name: dev-stats-dashboard
    path: dev-stats-dashboard.html
```

---

## Configuration

```toml
# thresholds.toml
[thresholds]
max_cyclomatic_complexity = 15
max_method_loc            = 50
max_class_loc             = 500
max_parameters            = 7
min_comment_ratio         = 0.10
max_duplication_ratio     = 0.20

[branches]
default_target            = "main"
stale_threshold_days      = 14
abandoned_threshold_days  = 90
```

```bash
dev-stats analyse . --config thresholds.toml
```

---

## Documentation

- [User Manual](docs/user_manual.md)
- [API Reference](docs/api_reference.md)
- [Architecture](docs/architecture.md)
- [Dashboard Guide](docs/dashboard_guide.md)
- [CI Integration](docs/ci_integration.md)

---

## License

GPL-3.0 — see [LICENSE](LICENSE).
