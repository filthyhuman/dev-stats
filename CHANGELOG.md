# Changelog

All notable changes to dev-stats will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

## [0.2.0] — 2026-03-07

### Added
- SonarSource-style cognitive complexity for Python parser
- Tree-sitter parsers for Java, JavaScript, TypeScript, C++, C#, Go with automatic fallback
- End-to-end integration test suite (41 tests across 7 test files)
- `--verbose` / `--quiet` CLI flags with Rich logging
- `--sort` flag for file table ordering (lines/code/complexity/name)
- `--watch` mode with watchfiles for continuous re-analysis
- `init-hooks` CLI command for pre-commit configuration generation
- GitHub Action (`.github/action.yml`) for CI integration
- Dashboard ARIA roles and keyboard navigation
- Dashboard rendering tests

### Changed
- All broad `except Exception` replaced with specific exception types
- Pre-commit generator now produces configurable `.pre-commit-config.yaml`
- Dashboard CSS: responsive 375px breakpoint, focus-visible outlines, table scroll wrappers
- Print stylesheet improvements

### Fixed
- Cognitive complexity was hardcoded to 0 in Python parser
- JSON exporter coverage gaps (77% to 96%)
- Abstract parser coverage gaps (89% to 100%)

## [0.1.0] — 2026-02-23

### Added
- **Analysis pipeline** — full code analysis for Python (AST-based), Java,
  JavaScript, TypeScript, C++, C#, Go (regex-based), and 40+ file types
  (generic line-count fallback).
- **Frozen dataclass models** — immutable, hashable `RepoReport` tree with
  `FileReport`, `ClassReport`, `MethodReport`, `ParameterReport`, and 30+
  supporting models.
- **Code metrics** — cyclomatic and cognitive complexity, Halstead volume,
  duplication detection, coupling analysis (Ce/Ca/instability/distance),
  churn scoring, test-coverage integration.
- **Git integration** — log harvesting, commit enrichment (merge/fixup/revert
  detection, conventional-commit parsing, size classification), blame engine,
  diff engine, tree walker, ref explorer, branch analyser, merge detector,
  activity scorer, contributor analyser, timeline builder, pattern detector
  (anomaly detection for secrets, WIP commits, force-push traces).
- **Branch management** — merged/unmerged detection (exact, squash, rebase),
  deletability scoring (0-100), cleanup script generation, stale/abandoned
  classification.
- **Terminal reporter** — Rich-powered tables with colour-coded metrics.
- **Export formats** — JSON, CSV, XML (JUnit), SVG badges.
- **Self-contained HTML dashboard** — 10 interactive tabs (Overview, Languages,
  Files, Classes, Methods, Hotspots, Dependencies, Branches, Git Log, Quality
  Gates) with table sorting, filtering, theme toggle, virtual scrolling, and
  URL hash state persistence. All CSS, JS, and data inlined via Jinja2 +
  zlib compression + base64 encoding.
- **CI adapters** — Jenkins (JUnit XML), GitLab (Code Quality JSON), TeamCity
  (service messages), GitHub Actions (workflow annotations + step summary).
- **Pre-commit hook** — YAML snippet generator for local pre-commit integration.
- **Quality gates** — 15 configurable thresholds with `--fail-on-violations`
  exit-code support and `--diff` delta mode for changed-files-only checking.
- **Configuration** — Pydantic-based settings with TOML file support,
  `DEV_STATS_*` environment variable overrides, and sensible defaults.
- **CLI** — three commands (`analyse`, `branches`, `gitlog`) powered by Typer
  with Rich integration.
- **Documentation** — user manual, API reference, architecture guide, dashboard
  guide, CI integration guide.
- **CI/CD** — GitHub Actions workflows for lint/typecheck/test/build (ci.yml)
  and PyPI publishing on tag (release.yml).

[Unreleased]: https://github.com/filthyhuman/dev-stats/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/filthyhuman/dev-stats/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/filthyhuman/dev-stats/releases/tag/v0.1.0
