# Tasks 02 — Core Models & File Scanner

## Core Models (all in src/dev_stats/core/models.py)

- [ ] T02-001  Create src/dev_stats/core/__init__.py — empty
- [ ] T02-002  Add enums to models.py: MergeType, BranchStatus, DeletabilityCategory, ChangeType, CommitSizeCategory, AnomalySeverity — each with Google docstring
- [ ] T02-003  Add ParameterReport dataclass — frozen=True, fields: name, type_annotation, has_default
- [ ] T02-004  Add MethodReport dataclass — frozen=True, all fields, property num_parameters = len(parameters)
- [ ] T02-005  Add ClassReport dataclass — frozen=True, all fields, properties: num_methods, num_attributes, num_constructors
- [ ] T02-006  Add FileReport dataclass — frozen=True, all fields, properties: comment_ratio, num_classes, num_functions
- [ ] T02-007  Add ModuleReport dataclass — frozen=True
- [ ] T02-008  Add LanguageSummary dataclass — frozen=True
- [ ] T02-009  Add FileChange dataclass — frozen=True
- [ ] T02-010  Add CommitRecord dataclass — frozen=True, properties: net_lines = insertions - deletions, churn_score = insertions + deletions
- [ ] T02-011  Add EnrichedCommit dataclass — extends CommitRecord pattern (use composition or inheritance carefully to keep frozen), all enrichment fields
- [ ] T02-012  Add BlameLine, AuthorBlameStat, FileBlameReport dataclasses — frozen=True
- [ ] T02-013  Add MergeStatus dataclass — frozen=True, properties: is_merged (OR of all three), merge_type -> MergeType enum
- [ ] T02-014  Add BranchReport, BranchesReport dataclasses — frozen=True
- [ ] T02-015  Add ContributorProfile, TagRecord, DetectedPattern dataclasses — frozen=True
- [ ] T02-016  Add RepoReport dataclass — frozen=True, all fields with Optional defaults for git data
- [ ] T02-017  Verify: run mypy --strict on models.py alone, fix all errors

## Scanner

- [ ] T02-018  Create src/dev_stats/core/scanner.py — ProgressEvent frozen dataclass: files_found: int, current_file: Path
- [ ] T02-019  Add ProgressObserver Protocol to scanner.py — runtime_checkable, method on_progress(event: ProgressEvent) -> None
- [ ] T02-020  Add Scanner class — __init__(repo_path: Path, config: AnalysisConfig, observers: list[ProgressObserver] = []), validate repo_path exists
- [ ] T02-021  Implement Scanner.scan() -> Generator[Path, None, None] — use repo_path.rglob("*"), skip directories, call _is_excluded(), emit ProgressEvent, yield file paths
- [ ] T02-022  Implement Scanner._is_excluded(path: Path) -> bool — check against config.exclude_patterns (fnmatch), always exclude .git/**, __pycache__/**, *.pyc
- [ ] T02-023  Implement Scanner._parse_gitignore() -> list[str] — read .gitignore if present, return list of patterns

## Registry & Dispatcher

- [ ] T02-024  Create src/dev_stats/core/parser_registry.py — class ParserRegistry: _registry: dict[str, AbstractParser] (private), register(parser), get(ext) raises KeyError, get_or_default(path) fallback to GenericParser, supported_languages() -> dict[str, list[str]]
- [ ] T02-025  Create src/dev_stats/core/dispatcher.py — class Dispatcher: __init__(registry: ParserRegistry), parse(path: Path) -> FileReport, parse_many(paths: list[Path]) -> list[FileReport] (logs errors, continues)

## Tests

- [ ] T02-026  Create tests/unit/core/test_models.py — test each dataclass: instantiates, is frozen (raises FrozenInstanceError on setattr), properties return correct values, MergeStatus.is_merged logic, ClassReport.num_constructors counts __init__
- [ ] T02-027  Create tests/unit/core/test_scanner.py — with tmp_path: creates files, Scanner.scan() finds them, excludes vendor/ pattern, skips hidden .git dir, progress events fired, gitignore patterns respected
- [ ] T02-028  Create tests/unit/core/test_parser_registry.py — register a mock parser, get() returns it by extension, get_or_default() for unknown extension returns GenericParser, supported_languages format
