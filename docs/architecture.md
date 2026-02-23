# Architecture

> Internal design reference for dev-stats contributors.

---

## Design Patterns

| Pattern                  | Location                         | Purpose                                    |
|--------------------------|----------------------------------|--------------------------------------------|
| Strategy                 | `dispatcher.py` → parsers        | Swap language parsers at runtime           |
| Template Method          | `abstract_parser.py`             | Shared pipeline, language-specific hooks   |
| Composite                | `aggregator.py`                  | File → Module → Repo report tree          |
| Observer                 | `scanner.py`                     | Progress events decoupled from scanning    |
| Builder                  | `dashboard_builder.py`           | Step-by-step HTML assembly                 |
| Adapter                  | `ci/`                            | Uniform interface over divergent CI formats|
| Registry                 | `parser_registry.py`             | Extension → Parser class mapping           |
| Repository (DDD)         | `log_harvester.py`               | Abstracts all git subprocess calls         |
| Chain of Responsibility  | `pattern_detector.py`            | Each detector enriches the commit stream   |
| Facade                   | `cli/`                           | Single surface over all subsystems         |
| Value Object             | All frozen dataclasses           | Immutable, hashable metric records         |

---

## Data Flow

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
    │ PythonParser JavaParser GenericParser  (+ 5 more)
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
    ├── TerminalReporter       → rich table to stdout
    ├── JsonExporter           → dev-stats-report.json
    ├── CsvExporter            → dev-stats-report.csv
    ├── XmlExporter            → dev-stats-report.xml (JUnit)
    ├── BadgeGenerator         → SVG badges
    ├── DashboardBuilder       → dashboard.html (self-contained)
    └── CIAdapter              → Jenkins | GitLab | TeamCity | GitHub
```

---

## Model Hierarchy

All analysis results are frozen dataclasses using `tuple` for sequences.

```
RepoReport
├── files: tuple[FileReport, ...]
│   ├── classes: tuple[ClassReport, ...]
│   │   └── methods: tuple[MethodReport, ...]
│   │       └── parameters: tuple[ParameterReport, ...]
│   └── functions: tuple[MethodReport, ...]
├── modules: tuple[ModuleReport, ...]
├── languages: tuple[LanguageSummary, ...]
├── duplication: DuplicationReport | None
│   └── duplicates: tuple[DuplicateBlock, ...]
├── coupling: CouplingReport | None
│   └── modules: tuple[ModuleCoupling, ...]
├── coverage: CoverageReport | None
│   └── files: tuple[FileCoverage, ...]
├── file_churn: tuple[FileChurn, ...] | None
├── commits: tuple[CommitRecord, ...] | None
│   └── files: tuple[FileChange, ...]
├── enriched_commits: tuple[EnrichedCommit, ...] | None
├── branches_report: BranchesReport | None
│   └── branches: tuple[BranchReport, ...]
├── contributors: tuple[ContributorProfile, ...] | None
├── tags: tuple[TagRecord, ...] | None
├── patterns: tuple[DetectedPattern, ...] | None
├── blame_reports: tuple[FileBlameReport, ...] | None
│   ├── authors: tuple[AuthorBlameStat, ...]
│   └── lines: tuple[BlameLine, ...]
├── timeline: tuple[TimelinePoint, ...] | None
├── work_patterns: tuple[WorkPattern, ...] | None
├── semver_tags: tuple[SemverTag, ...] | None
└── stashes: tuple[StashRecord, ...] | None
```

---

## Module Map

```
src/dev_stats/
├── cli/            Typer commands (Facade pattern)
│   ├── app.py              Typer app instance
│   ├── analyse_command.py  Main analysis pipeline
│   ├── branches_command.py Branch analysis pipeline
│   ├── gitlog_command.py   Git history pipeline
│   └── version_callback.py --version flag
├── config/         Pydantic configuration layer
│   ├── analysis_config.py  Root config (BaseSettings)
│   ├── threshold_config.py Quality-gate thresholds
│   ├── branch_config.py    Branch-analysis settings
│   ├── gitlog_config.py    Git-log analysis settings
│   ├── output_config.py    Output presentation settings
│   ├── config_loader.py    TOML file + env var loading
│   └── defaults.toml       Factory defaults
├── core/           Analysis engine
│   ├── models.py           All frozen dataclasses + enums
│   ├── scanner.py          Filesystem walker with exclusion
│   ├── aggregator.py       File → Module → Repo rollup
│   ├── dispatcher.py       Routes files to parsers
│   ├── parser_registry.py  Extension → parser mapping
│   ├── parsers/            Language-specific parsers
│   │   ├── abstract_parser.py    Template Method base
│   │   ├── python_parser.py      AST-based
│   │   ├── java_parser.py        Regex-based
│   │   ├── javascript_parser.py  Regex-based
│   │   ├── typescript_parser.py  Regex-based
│   │   ├── cpp_parser.py         Regex-based
│   │   ├── csharp_parser.py      Regex-based
│   │   ├── go_parser.py          Regex-based
│   │   └── generic_parser.py     Line-count fallback
│   ├── metrics/            Derived metrics calculators
│   │   ├── complexity_calculator.py
│   │   ├── duplication_detector.py
│   │   ├── coupling_analyser.py
│   │   ├── churn_scorer.py
│   │   └── test_coverage_reader.py
│   └── git/                Git integration layer
│       ├── log_harvester.py
│       ├── commit_enricher.py
│       ├── blame_engine.py
│       ├── diff_engine.py
│       ├── tree_walker.py
│       ├── ref_explorer.py
│       ├── branch_analyzer.py
│       ├── merge_detector.py
│       ├── activity_scorer.py
│       ├── remote_sync.py
│       ├── contributor_analyzer.py
│       ├── timeline_builder.py
│       └── pattern_detector.py
├── output/         Report generation
│   ├── sort_schema.py
│   ├── exporters/
│   │   ├── abstract_exporter.py
│   │   ├── terminal_reporter.py
│   │   ├── json_exporter.py
│   │   ├── csv_exporter.py
│   │   ├── xml_exporter.py
│   │   └── badge_generator.py
│   └── dashboard/
│       ├── dashboard_builder.py
│       ├── asset_embedder.py
│       ├── data_compressor.py
│       └── templates/
│           ├── dashboard.html.jinja2
│           └── assets/
│               ├── chart.min.js
│               ├── styles.css
│               └── app.js
└── ci/             CI system adapters
    ├── abstract_ci_adapter.py
    ├── violation.py
    ├── jenkins_adapter.py
    ├── gitlab_adapter.py
    ├── teamcity_adapter.py
    ├── github_actions_adapter.py
    └── precommit_generator.py
```

---

## Key Decisions

1. **Frozen dataclasses everywhere.** All models are `frozen=True` with `tuple`
   sequences. This guarantees immutability and hashability across the pipeline.

2. **No relative imports.** All imports use absolute paths from `dev_stats.*`.
   Enforced by ruff's isort configuration.

3. **One class per file.** Makes it trivial to locate any class by converting
   `PascalCase` to `snake_case.py`.

4. **TYPE_CHECKING for cross-layer imports.** Avoids circular import issues
   between the CLI, config, core, and output layers.

5. **subprocess for git.** GitPython is available but all git commands use
   `subprocess.run(check=True, capture_output=True, text=True, timeout=N)`
   for predictable behaviour and timeout safety.

6. **Self-contained dashboard.** All CSS, JS, and data are inlined into a
   single HTML file via Jinja2 templating + zlib compression + base64 encoding.
   No external dependencies at view-time.

7. **CI adapters share `check_violations()`.** The abstract base class owns
   threshold checking; concrete adapters only format output (JUnit XML,
   Code Quality JSON, TeamCity messages, GitHub annotations).
