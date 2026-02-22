# Sprint 02 — Core Models & File Scanner

**Phase:** 01 | **Duration:** 1 week
**Goal:** Complete frozen dataclass model hierarchy. Scanner traverses a repo
correctly, respects exclude patterns, emits progress events.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S02-01 | core/models.py — all 6 enums                                                    | 2   |
| S02-02 | core/models.py — code structure dataclasses: ParameterReport, MethodReport, ClassReport, FileReport, ModuleReport, LanguageSummary | 4 |
| S02-03 | core/models.py — git dataclasses: FileChange, CommitRecord, EnrichedCommit, BlameLine, AuthorBlameStat, FileBlameReport | 4 |
| S02-04 | core/models.py — branch/contributor dataclasses: MergeStatus, BranchReport, BranchesReport, ContributorProfile, TagRecord, DetectedPattern | 3 |
| S02-05 | core/models.py — RepoReport root dataclass                                      | 2   |
| S02-06 | core/scanner.py — ProgressEvent dataclass + ProgressObserver Protocol           | 1   |
| S02-07 | core/scanner.py — Scanner class: rglob, gitignore parsing, exclude patterns, progress events | 4 |
| S02-08 | core/parser_registry.py — ParserRegistry: register, get, get_or_default, supported_languages | 2 |
| S02-09 | core/dispatcher.py — Dispatcher: parse, parse_many                              | 2   |
| S02-10 | tests/unit/core/test_models.py — instantiation, frozen raises, all properties   | 4   |
| S02-11 | tests/unit/core/test_scanner.py — finds files, excludes, skips .git, progress  | 3   |
| S02-12 | tests/unit/core/test_parser_registry.py — register, get, fallback               | 2   |

## Acceptance Criteria

- All dataclasses are frozen=True, all sequences use tuple
- FileReport.comment_ratio returns correct float
- Scanner skips .git/ and node_modules/ by default
- ParserRegistry.get_or_default(Path("foo.xyz")) returns GenericParser instance
- mypy --strict passes on models.py

→ tasks_02.md
