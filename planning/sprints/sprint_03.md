# Sprint 03 — Python Parser, Aggregator & Terminal Output

**Phase:** 01 | **Duration:** 1 week
**Goal:** Full end-to-end pipeline for Python files. `dev-stats analyse .` prints
a real terminal report on the project itself.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S03-01 | core/parsers/abstract_parser.py — AbstractParser ABC + count_loc, count_todos, detect_encoding utilities | 3 |
| S03-02 | core/parsers/generic_parser.py — GenericParser: 40+ type map, LOC counting, can_parse always True | 3 |
| S03-03 | core/parsers/python_parser.py — PythonParser: full ast extraction               | 8   |
| S03-04 | core/aggregator.py — Aggregator: totals, averages, language summaries, module reports | 5 |
| S03-05 | output/exporters/abstract_exporter.py — AbstractExporter ABC                   | 1   |
| S03-06 | output/exporters/terminal_reporter.py — TerminalReporter: hero cards, language table, top-N lists | 4 |
| S03-07 | Wire analyse_command.py: Scanner → Dispatcher → Aggregator → TerminalReporter  | 3   |
| S03-08 | tests/unit/core/parsers/test_python_parser.py — 25+ test cases                 | 6   |
| S03-09 | tests/unit/core/parsers/test_generic_parser.py — LOC, comment detection        | 2   |
| S03-10 | tests/unit/core/test_aggregator.py — known reports produce expected totals      | 3   |
| S03-11 | tests/fixtures/sample_files/python/sample.py — known structure for tests       | 1   |
| S03-12 | Integration test: analyse . on fake_repo exits 0, stdout contains "Python"     | 2   |

## Acceptance Criteria

- `dev-stats analyse .` on the project itself prints correct Python file count
- PythonParser: CC=3 for if/elif/else function
- PythonParser: extracts self.x from __init__ as attribute
- Syntax errors produce warning log, not exception
- All tests green, coverage ≥ 90%

→ tasks_03.md
