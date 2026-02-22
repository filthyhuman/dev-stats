# CLAUDE.md — dev-stats Master Guide

> Read this file completely before touching any code.
> Update it whenever architecture decisions change.
> This is the single source of truth for AI-assisted development.

---

## Project Identity

**dev-stats** is a pure-Python, zero-AI, zero-cloud CLI tool that analyses a
local Git repository and produces comprehensive statistics: terminal output,
JSON/CSV/XML exports, SVG badges, and a fully self-contained single-file HTML
dashboard that opens by double-click in any browser — no web server, no npm,
no internet required.

**License:** GPL-3.0
**Python:** 3.12+
**Packaging:** uv + pyproject.toml (PEP 517/518/621)
**Entry point:** `dev-stats` CLI command

---

## Absolute Rules — No Exceptions

1. **One class per file.** Enums and pure dataclasses may share a `models.py`
   within their module, but every concrete class lives in its own file.
2. **Every public symbol has a Google-style docstring.**
3. **Every function and method is fully type-annotated.** `mypy --strict` must pass.
4. **No `print()` outside `terminal_reporter.py`.** Use `logging` or `rich.Console`.
5. **No bare `except:`.** Always catch specific exception types.
6. **No global mutable state.** No module-level dicts/lists written to at runtime.
7. **All file I/O via `pathlib.Path`.** Never `os.path`.
8. **All subprocess calls:** `subprocess.run([...], check=True, capture_output=True, text=True, timeout=N)`
9. **`ruff check . && ruff format .` must pass** before every commit.
10. **`mypy src/ --strict` must pass** before every commit.
11. **Every new feature ships with tests.** No PR without a corresponding test file.
12. **All sequences in frozen dataclasses use `tuple`, never `list`** (hashability).

---

## Technology Stack

| Concern          | Library            | Version | Reason                                  |
|------------------|--------------------|---------|-----------------------------------------|
| CLI framework    | `typer`            | ≥ 0.12  | Type-annotation-driven, Rich integration|
| Terminal output  | `rich`             | ≥ 13.7  | Tables, progress, markup                |
| Configuration    | `pydantic-settings`| ≥ 2.3   | Validated TOML + env vars               |
| Data models      | `pydantic`         | ≥ 2.7   | Config models only                      |
| Templating       | `jinja2`           | ≥ 3.1   | HTML dashboard templates                |
| Git access       | `gitpython`        | ≥ 3.1   | Object-graph traversal                  |
| Testing          | `pytest`           | ≥ 8.2   | Standard                                |
| Coverage         | `pytest-cov`       | ≥ 5.0   | ≥ 90% enforced                          |
| Mocking          | `pytest-mock`      | ≥ 3.14  | subprocess + filesystem isolation       |
| Time mocking     | `freezegun`        | ≥ 1.5   | Deterministic datetime tests            |
| Linting          | `ruff`             | ≥ 0.4   | Replaces flake8 + isort + pyupgrade     |
| Type checking    | `mypy`             | ≥ 1.10  | Strict mode                             |
| Packaging        | `uv` + `hatchling` | latest  | PEP 621, fastest resolver               |

**No runtime AI. No cloud services. No mandatory network access.**

---

## Architecture

### Design Patterns

| Pattern                  | Location                  | Purpose                                    |
|--------------------------|---------------------------|--------------------------------------------|
| Strategy                 | `dispatcher.py` → parsers | Swap language parsers at runtime           |
| Template Method          | `abstract_parser.py`      | Shared pipeline, language-specific hooks   |
| Composite                | `aggregator.py`           | File → Module → Repo report tree          |
| Observer                 | `scanner.py`              | Progress events decoupled from scanning    |
| Builder                  | `dashboard_builder.py`    | Step-by-step HTML assembly                 |
| Adapter                  | `ci/`                     | Uniform interface over divergent CI formats|
| Registry                 | `parser_registry.py`      | Extension → Parser class mapping           |
| Repository (DDD)         | `log_harvester.py`        | Abstracts all git subprocess calls         |
| Chain of Responsibility  | `pattern_detector.py`     | Each detector enriches the commit stream   |
| Facade                   | `cli/`                    | Single surface over all subsystems         |
| Value Object             | All frozen dataclasses    | Immutable, hashable metric records         |

### Data Flow

```
CLI (typer)
    │
    ▼
AnalysisConfig (Pydantic)  ◄── thresholds.toml / env vars
    │
    ▼
Scanner ──► [Path list]
    │              │
    │              ▼
    │         Dispatcher ──► ParserRegistry
    │              │
    │    ┌─────────┼──────────┐
    │    ▼         ▼          ▼
    │ PythonParser JavaParser GenericParser
    │              │
    │         FileReport (frozen)
    │
    ▼
GitSubsystem
    ├── LogHarvester      → CommitRecord[]
    ├── BranchAnalyzer    → BranchReport[]
    ├── BlameEngine       → FileBlameReport[]
    ├── ContributorAnalyzer → ContributorProfile[]
    └── PatternDetector   → DetectedPattern[]
    │
    ▼
MetricsLayer
    ├── ComplexityCalculator
    ├── DuplicationDetector
    ├── CouplingAnalyser
    └── ChurnScorer
    │
    ▼
Aggregator → RepoReport (frozen, single unified object)
    │
    ├── TerminalReporter
    ├── JsonExporter
    ├── CsvExporter
    ├── XmlExporter (JUnit)
    ├── BadgeGenerator (SVG)
    ├── DashboardBuilder → dashboard.html (self-contained)
    └── CIAdapter (Jenkins | GitLab | TeamCity | GitHub)
```

---

## Repository Layout

```
dev-stats/
├── CLAUDE.md                          ← THIS FILE
├── README.md
├── CHANGELOG.md
├── LICENSE                            ← GPL-3.0
├── pyproject.toml
├── uv.lock
├── .python-version                    ← 3.12
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── docs/
│   ├── user_manual.md
│   ├── api_reference.md
│   ├── architecture.md
│   ├── dashboard_guide.md
│   └── ci_integration.md
├── planning/
│   ├── phases/
│   │   ├── phase_01.md   (Phase 1: Foundation)
│   │   ├── phase_02.md   (Phase 2: Language Parsers & Metrics)
│   │   ├── phase_03.md   (Phase 3: Git Integration)
│   │   ├── phase_04.md   (Phase 4: Dashboard)
│   │   └── phase_05.md   (Phase 5: CI & Release)
│   ├── sprints/
│   │   ├── sprint_01.md  …  sprint_14.md
│   └── tasks/
│       ├── tasks_01.md   …  tasks_14.md
├── src/
│   └── dev_stats/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli/
│       │   ├── app.py                 ← Typer app instance
│       │   ├── analyse_command.py
│       │   ├── branches_command.py
│       │   ├── gitlog_command.py
│       │   └── version_callback.py
│       ├── config/
│       │   ├── analysis_config.py
│       │   ├── threshold_config.py
│       │   ├── branch_config.py
│       │   ├── gitlog_config.py
│       │   ├── output_config.py
│       │   ├── config_loader.py
│       │   └── defaults.toml
│       ├── core/
│       │   ├── models.py              ← All frozen dataclasses + enums
│       │   ├── scanner.py
│       │   ├── aggregator.py
│       │   ├── dispatcher.py
│       │   ├── parser_registry.py
│       │   ├── parsers/
│       │   │   ├── abstract_parser.py
│       │   │   ├── python_parser.py
│       │   │   ├── java_parser.py
│       │   │   ├── javascript_parser.py
│       │   │   ├── typescript_parser.py
│       │   │   ├── cpp_parser.py
│       │   │   ├── csharp_parser.py
│       │   │   ├── go_parser.py
│       │   │   └── generic_parser.py
│       │   ├── metrics/
│       │   │   ├── complexity_calculator.py
│       │   │   ├── duplication_detector.py
│       │   │   ├── coupling_analyser.py
│       │   │   ├── churn_scorer.py
│       │   │   └── test_coverage_reader.py
│       │   └── git/
│       │       ├── log_harvester.py
│       │       ├── commit_enricher.py
│       │       ├── blame_engine.py
│       │       ├── diff_engine.py
│       │       ├── tree_walker.py
│       │       ├── ref_explorer.py
│       │       ├── branch_analyzer.py
│       │       ├── merge_detector.py
│       │       ├── activity_scorer.py
│       │       ├── remote_sync.py
│       │       ├── contributor_analyzer.py
│       │       ├── timeline_builder.py
│       │       └── pattern_detector.py
│       ├── output/
│       │   ├── sort_schema.py
│       │   ├── exporters/
│       │   │   ├── abstract_exporter.py
│       │   │   ├── terminal_reporter.py
│       │   │   ├── json_exporter.py
│       │   │   ├── csv_exporter.py
│       │   │   ├── xml_exporter.py
│       │   │   └── badge_generator.py
│       │   └── dashboard/
│       │       ├── dashboard_builder.py
│       │       ├── asset_embedder.py
│       │       ├── data_compressor.py
│       │       └── templates/
│       │           ├── dashboard.html.jinja2
│       │           └── assets/
│       │               ├── chart.min.js
│       │               ├── styles.css
│       │               └── app.js
│       └── ci/
│           ├── abstract_ci_adapter.py
│           ├── violation.py
│           ├── jenkins_adapter.py
│           ├── gitlab_adapter.py
│           ├── teamcity_adapter.py
│           ├── github_actions_adapter.py
│           └── precommit_generator.py
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   └── sample_files/
    │       ├── python/sample.py
    │       ├── java/Sample.java
    │       └── javascript/sample.js
    ├── unit/
    │   ├── core/
    │   │   ├── parsers/
    │   │   ├── metrics/
    │   │   └── git/
    │   ├── output/
    │   └── ci/
    └── integration/
```

---

## Naming Conventions

```
Files:        snake_case.py
Classes:      PascalCase  (one per file, filename = snake_case of class name)
Methods:      snake_case
Constants:    UPPER_SNAKE_CASE
Private:      _single_underscore prefix
Type aliases: PascalCase

Examples:
  PythonParser        → python_parser.py
  DashboardBuilder    → dashboard_builder.py
  AbstractCIAdapter   → abstract_ci_adapter.py
```

---

## Import Order (ruff-enforced)

```python
from __future__ import annotations   # always first

# 1. stdlib
import ast
from dataclasses import dataclass
from pathlib import Path

# 2. third-party
import typer
from pydantic import BaseModel

# 3. first-party (absolute, never relative)
from dev_stats.core.models import FileReport
```

---

## Testing Rules

| Category    | Location              | Rules                                               |
|-------------|-----------------------|-----------------------------------------------------|
| Unit        | tests/unit/           | No filesystem, no subprocess. Mock everything.      |
| Integration | tests/integration/    | Uses fake_repo fixture (real temp git repo).        |
| CLI         | tests/integration/    | Typer CliRunner. Assert exit codes + output.        |

Coverage minimums:
- src/dev_stats/core/    ≥ 95%
- src/dev_stats/output/  ≥ 90%
- src/dev_stats/ci/      ≥ 90%
- src/dev_stats/config/  ≥ 95%
- Overall                ≥ 90%

---

## Development Workflow

```bash
# First-time setup
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-extras
uv run pre-commit install

# Daily commands
uv run dev-stats analyse .
uv run pytest
uv run pytest --cov=dev_stats --cov-report=term-missing
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/ --strict
```

---

## Starting Claude Code

Tell Claude Code exactly this at the start of each sprint:

> "Read CLAUDE.md fully. Then read planning/phases/phase_XX.md,
>  planning/sprints/sprint_XX.md, and planning/tasks/tasks_XX.md.
>  Implement every task in the checklist in order.
>  Do not move to the next sprint until all acceptance criteria pass."

Replace XX with the current sprint number (01, 02, 03 ...).

## Sprint Workflow

**Always follow this cycle for every sprint:**

1. **Implement** -- complete all tasks in the sprint checklist.
2. **Validate** -- `ruff check .`, `ruff format --check .`, `mypy src/ --strict`, `pytest` must all pass.
3. **Commit** -- create a single commit summarising the sprint's work.
4. **Push** -- push the commit to the remote.
5. **Ask for feedback** -- stop and ask the user for quality-gate feedback before starting the next sprint.

**Do not start the next sprint until the user explicitly approves.**

---

## Quick Reference

| Task                    | File(s) to create or edit                              |
|-------------------------|--------------------------------------------------------|
| Add CLI flag            | cli/<command>_command.py                               |
| Add config option       | config/<scope>_config.py + defaults.toml               |
| Add language parser     | core/parsers/<lang>_parser.py + parser_registry.py     |
| Add metric              | core/metrics/<metric>_calculator.py + aggregator.py    |
| Add git analysis        | core/git/<module>.py                                   |
| Add dashboard widget    | output/dashboard/templates/dashboard.html.jinja2       |
| Add sortable column     | output/sort_schema.py                                  |
| Add CI adapter          | ci/<name>_adapter.py + ci/__init__.py                  |
| Change quality gates    | config/defaults.toml                                   |
