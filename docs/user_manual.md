# dev-stats User Manual

## Table of Contents

1. [Installation](#installation)
2. [First Run](#first-run)
3. [Configuration](#configuration)
4. [Analyse Command](#analyse-command)
5. [Branches Command](#branches-command)
6. [Gitlog Command](#gitlog-command)
7. [Dashboard Guide](#dashboard-guide)
8. [Output Formats](#output-formats)
9. [Quality Gates](#quality-gates)
10. [Tips for Large Repositories](#tips-for-large-repositories)

---

## Installation

Requirements: Python 3.12+, Git 2.20+ on PATH.

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# From source (recommended)
git clone https://github.com/filthyhuman/dev-stats
cd dev-stats
uv tool install --from ./ dev-stats

# Or run without installing globally
uv run dev-stats analyse .

# From PyPI (when published)
uv tool install dev-stats
# or
pip install dev-stats

# Verify
dev-stats --version
```

### Updating

```bash
# From source — pull latest and reinstall
cd dev-stats
git pull
uv tool install --from ./ --force dev-stats

# From PyPI (when published)
uv tool upgrade dev-stats
# or
pip install --upgrade dev-stats
```

---

## First Run

```bash
dev-stats analyse /path/to/repository                    # terminal report
dev-stats analyse /path/to/repository -f dashboard       # generate dashboard
open dev-stats-output/dev-stats-dashboard.html           # macOS
xdg-open dev-stats-output/dev-stats-dashboard.html      # Linux
start dev-stats-output/dev-stats-dashboard.html          # Windows
```

---

## Configuration

```bash
# See all defaults
dev-stats config --print-defaults

# Use a custom config
dev-stats analyse /path/to/repository --config thresholds.toml
```

All configuration options with defaults:

```toml
[thresholds]
max_cyclomatic_complexity  = 15
max_cognitive_complexity   = 20
max_method_loc             = 50
max_class_loc              = 500
max_file_loc               = 1000
max_parameters             = 7
max_inheritance_depth      = 5
max_attributes_per_class   = 20
max_methods_per_class      = 30
max_nesting_depth          = 4
min_comment_ratio          = 0.10
max_duplication_ratio      = 0.20
max_instability            = 0.80
min_test_coverage          = 0.80
bus_factor_min             = 2

[branches]
default_target             = "main"
protected_patterns         = ["main", "master", "develop", "release/*", "hotfix/*"]
stale_threshold_days       = 14
abandoned_threshold_days   = 90
min_deletability_score     = 80

[gitlog]
blame_top_files            = 50
include_diffs              = false
follow_renames             = true
max_dashboard_mb           = 50

[output]
top_n                      = 20
dashboard_filename         = "dev-stats-dashboard.html"
json_filename              = "dev-stats-report.json"
junit_filename             = "dev-stats-report.xml"
```

---

## Analyse Command

The `analyse` command runs the full pipeline: file scanning, language parsing,
git history analysis (commits, branches, contributors, patterns, timeline),
metric aggregation, and reporting. Git analysis is automatic — if the target
path is a Git repository, commit history and branch data are included in the
report and dashboard. If git analysis fails (e.g. not a git repo, no commits),
file analysis still completes normally.

```bash
dev-stats analyse [PATH] [OPTIONS]

# Examples
dev-stats analyse /path/to/repository
dev-stats analyse /path/to/repository -f json
dev-stats analyse /path/to/repository -f all
dev-stats analyse /path/to/repository --lang python --lang java
dev-stats analyse /path/to/repository --top 50
dev-stats analyse /path/to/repository --diff main -f dashboard
dev-stats analyse /path/to/repository --exclude "vendor/**" --exclude "*.generated.py"
dev-stats analyse /path/to/repository --watch -f dashboard
dev-stats analyse /path/to/repository --since 2025-01-01
```

---

## Branches Command

```bash
dev-stats branches [PATH] [OPTIONS]

# Examples
dev-stats branches /path/to/repository                            # all branches
dev-stats branches /path/to/repository --show merged              # only merged
dev-stats branches /path/to/repository --show abandoned           # inactive > 90 days
dev-stats branches /path/to/repository --min-score 80             # safe-to-delete candidates
dev-stats branches /path/to/repository --min-age 30               # older than 30 days
dev-stats branches /path/to/repository --show merged --generate-script  # write cleanup_branches.sh
dev-stats branches /path/to/repository --all                      # include remote branches
```

### Deletability Score

| Score  | Category         | Meaning                         |
|--------|------------------|---------------------------------|
| 80–100 | SAFE TO DELETE   | Merged, inactive, no risk       |
| 50–79  | LIKELY DELETABLE | Probably merged, verify manually|
| 20–49  | UNCERTAIN        | Unmerged or recently active     |
| 0–19   | KEEP             | Active, protected, or HEAD      |

### Merge Detection Methods

1. **Exact** — `git branch --merged`. Reliable for standard merges.
2. **Squash** — empty tree-diff comparison. Detects squash-merges.
3. **Rebase** — patch-ID matching. Finds rebased commits.

---

## Gitlog Command

```bash
dev-stats gitlog [PATH] [OPTIONS]

# Examples
dev-stats gitlog /path/to/repository                        # all history
dev-stats gitlog /path/to/repository --depth 500            # last 500 commits
dev-stats gitlog /path/to/repository --author "Alice"       # filter by author
dev-stats gitlog /path/to/repository --blame-top 20         # blame for top 20 files
dev-stats gitlog /path/to/repository --no-blame             # skip blame (faster)
dev-stats gitlog /path/to/repository --since 2024-01-01    # from date
```

### Anomaly Detection

Automatically scanned for:
- Possible hardcoded secrets (API key regex patterns)
- WIP commits on protected branches
- Fixup/squash commits not yet squashed
- Files with bus factor 1 (single author > 80% ownership)
- Force push traces
- Direct commits to protected branches
- Commits larger than 500 LOC
- Friday releases and weekend deploys

---

## Dashboard Guide

All tabs are sortable, filterable, and searchable client-side.
No server required after the HTML file is generated.

### Interactivity

- **Sort**: click any column header. Click again to reverse.
- **Multi-sort**: Shift+Click a second column.
- **Search**: free-text box above each table.
- **Filter**: dropdown filters by language, status, severity.
- **Drill-down**: click any Git Log row to expand (5 levels deep).
- **Share**: sort state saved in URL hash — copy URL to share exact view.
- **Copy commands**: branch delete commands copy to clipboard in one click.

### Hotspot Matrix (most actionable view)

Scatter plot of complexity vs. churn.
Top-right quadrant = complex AND frequently changed = highest refactoring priority.

---

## Output Formats

| Format     | Flag        | Output                                    |
|------------|-------------|-------------------------------------------|
| Terminal   | *(default)* | Printed to stdout when no `-f` is given   |
| JSON       | `json`      | dev-stats-report.json                     |
| CSV        | `csv`       | dev-stats-csv/ (one file per entity type) |
| JUnit XML  | `xml`       | dev-stats-report.xml                      |
| SVG Badges | `badges`    | dev-stats-badges/                         |
| Dashboard  | `dashboard` | dev-stats-dashboard.html                  |
| All        | `all`       | All of the above                          |

---

## Quality Gates

```bash
dev-stats analyse /path/to/repository --fail-on-violations
echo $?   # 0 = all pass, 1 = violations found
```

---

## Tips for Large Repositories

| Situation              | Recommendation                                |
|------------------------|-----------------------------------------------|
| Repo > 10k commits     | Use `--depth 2000`                            |
| Blame data too large   | Reduce `--blame-top` or use `--no-blame`      |
| Dashboard > 50 MB      | Use `--no-diffs` and reduce `--blame-top`     |
| Analysis too slow      | Use `--lang python` to restrict to one lang   |
| Vendored files         | Use `--exclude "vendor/**"`                   |
| Monorepo               | Run per subdirectory                          |
