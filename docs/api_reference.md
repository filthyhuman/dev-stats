# dev-stats API Reference

All public classes grouped by module. One class per file.

---

## core.models — Frozen Dataclasses & Enums

All report objects are `@dataclass(frozen=True)`. All sequences use `tuple`.

### Enums

| Enum                  | Values                                                    |
|-----------------------|-----------------------------------------------------------|
| `MergeType`           | EXACT · SQUASH · REBASE · UNKNOWN                        |
| `BranchStatus`        | ACTIVE · STALE · ABANDONED                               |
| `DeletabilityCategory`| SAFE_TO_DELETE · LIKELY_DELETABLE · UNCERTAIN · KEEP     |
| `ChangeType`          | ADDED · MODIFIED · DELETED · RENAMED · COPIED            |
| `CommitSizeCategory`  | TINY · SMALL · MEDIUM · LARGE · MASSIVE                  |
| `AnomalySeverity`     | INFO · WARNING · CRITICAL                                |

### ParameterReport
`name: str` · `type_annotation: str|None` · `has_default: bool`

### MethodReport
`name` · `start_line` · `end_line` · `loc` · `cyclomatic_complexity`
· `cognitive_complexity` · `halstead_volume` · `parameters: tuple[ParameterReport,...]`
· `local_variables` · `nesting_depth_max` · `return_statements`
· `exception_handlers` · `todo_count` · `is_constructor` · `is_static`
· `is_abstract` · `is_property`

### ClassReport
`name` · `start_line` · `end_line` · `loc` · `methods: tuple[MethodReport,...]`
· `attributes: tuple[str,...]` · `base_classes` · `inheritance_depth`
· `wmc` · `lcom` · `is_abstract` · `is_interface`
Properties: `num_methods` · `num_attributes` · `num_constructors`

### FileReport
`path: Path` · `language` · `extension` · `size_bytes` · `encoding`
· `loc_total` · `loc_code` · `loc_comment` · `loc_blank`
· `classes: tuple[ClassReport,...]` · `functions: tuple[MethodReport,...]`
· `imports: tuple[str,...]` · `todo_count` · `duplication_ratio` · `churn_score`
Properties: `comment_ratio` · `num_classes` · `num_functions`

### RepoReport
Root object produced by `Aggregator`. Contains all files, modules,
languages, branches, commits, contributors, tags, blame reports, patterns.

---

## core.parsers

### AbstractParser (abstract_parser.py)
Template Method base class.
```
can_parse(path: Path) -> bool
parse(path: Path) -> FileReport          # template method
_extract_classes(source, path) -> list   # abstract hook
_extract_functions(source, path) -> list # abstract hook
_detect_imports(source, path) -> list    # abstract hook
```

### Concrete Parsers

| Class               | File                    | Strategy            |
|---------------------|-------------------------|---------------------|
| PythonParser        | python_parser.py        | stdlib ast          |
| JavaParser          | java_parser.py          | regex + heuristics  |
| JavaScriptParser    | javascript_parser.py    | regex + heuristics  |
| TypeScriptParser    | typescript_parser.py    | extends JS parser   |
| CppParser           | cpp_parser.py           | regex + heuristics  |
| CsharpParser        | csharp_parser.py        | regex + heuristics  |
| GoParser            | go_parser.py            | regex + heuristics  |
| GenericParser       | generic_parser.py       | LOC only, any file  |

### ParserRegistry (parser_registry.py)
```
register(parser: AbstractParser) -> None
get(extension: str) -> AbstractParser         # raises KeyError
get_or_default(path: Path) -> AbstractParser  # falls back to GenericParser
supported_languages() -> dict[str, list[str]]
```

### Dispatcher (dispatcher.py)
```
parse(path: Path) -> FileReport
parse_many(paths: list[Path]) -> list[FileReport]
```

---

## core.metrics

### ComplexityCalculator (complexity_calculator.py)
```
cyclomatic(node: ast.AST) -> int
cognitive(node: ast.AST) -> int
halstead(node: ast.AST) -> HalsteadMetrics
nesting_depth(node: ast.AST) -> int
```

### DuplicationDetector (duplication_detector.py)
```
detect(files: list[FileReport]) -> dict[Path, float]
```

### CouplingAnalyser (coupling_analyser.py)
```
analyse(files: list[FileReport]) -> list[ModuleReport]
```

### ChurnScorer (churn_scorer.py)
```
score(repo_path: Path, files: list[Path]) -> dict[Path, float]
```

### TestCoverageReader (test_coverage_reader.py)
```
read(repo_path: Path) -> dict[Path, float]   # returns 0.0 if no coverage file
```

---

## core.git

### LogHarvester (log_harvester.py)
```
harvest(*, depth, since, until, author, branch) -> list[CommitRecord]
head_info() -> tuple[str, str]     # (full_hash, short_hash)
current_branch() -> str
```

### BranchAnalyzer (branch_analyzer.py)
```
analyse(*, include_remote, local_only) -> BranchesReport
```

### MergeDetector (merge_detector.py)
```
detect(branch_name: str) -> MergeStatus
```

### ActivityScorer (activity_scorer.py)
```
score(branch, merge_status, head_hash) -> tuple[int, DeletabilityCategory]
```

### BlameEngine (blame_engine.py)
```
blame(file_path: Path, *, follow_renames: bool) -> FileBlameReport
blame_at(file_path: Path, commit_hash: str) -> FileBlameReport
```

### ContributorAnalyzer (contributor_analyzer.py)
```
analyse(commits: list[CommitRecord]) -> list[ContributorProfile]
```

### PatternDetector (pattern_detector.py)
```
detect(commits: list[EnrichedCommit]) -> list[DetectedPattern]
```

---

## output.exporters

### AbstractExporter (abstract_exporter.py)
```
export(output_dir: Path) -> list[Path]   # abstract
```

### Concrete Exporters

| Class             | File                          | Output                     |
|-------------------|-------------------------------|----------------------------|
| TerminalReporter  | terminal_reporter.py          | Rich tables to stdout       |
| JsonExporter      | json_exporter.py              | dev-stats-report.json       |
| CsvExporter       | csv_exporter.py               | dev-stats-csv/ directory    |
| XmlExporter       | xml_exporter.py               | JUnit XML                   |
| BadgeGenerator    | badge_generator.py            | SVG badges                  |
| DashboardBuilder  | dashboard/dashboard_builder.py| dev-stats-dashboard.html    |

---

## ci

### AbstractCIAdapter (abstract_ci_adapter.py)
```
check_violations() -> list[Violation]
emit(output_dir: Path) -> list[Path]   # abstract
has_violations: bool                    # property
```

### Concrete Adapters

| Class                  | File                       | Platform      |
|------------------------|----------------------------|---------------|
| JenkinsAdapter         | jenkins_adapter.py         | JUnit XML     |
| GitlabAdapter          | gitlab_adapter.py          | Code Quality  |
| TeamCityAdapter        | teamcity_adapter.py        | Service Msgs  |
| GithubActionsAdapter   | github_actions_adapter.py  | Annotations   |
| PrecommitGenerator     | precommit_generator.py     | Git hook      |
