# Sprint 05 — Metrics Layer

**Phase:** 02 | **Duration:** 1 week
**Goal:** All code quality metrics implemented and wired into Aggregator.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S05-01 | core/metrics/complexity_calculator.py — cyclomatic, cognitive, halstead, nesting_depth | 6 |
| S05-02 | Wire ComplexityCalculator into PythonParser, replace placeholder values          | 2   |
| S05-03 | core/metrics/duplication_detector.py — Rabin-Karp rolling hash, per-file ratio  | 5   |
| S05-04 | core/metrics/coupling_analyser.py — import graph, Ce/Ca/I/A/D per module        | 5   |
| S05-05 | core/metrics/churn_scorer.py — git log --stat per file, churn score             | 3   |
| S05-06 | core/metrics/test_coverage_reader.py — .coverage + lcov.info reader             | 4   |
| S05-07 | Wire all metrics into Aggregator                                                  | 3   |
| S05-08 | tests/unit/core/metrics/test_complexity_calculator.py                            | 5   |
| S05-09 | tests/unit/core/metrics/test_duplication_detector.py                            | 3   |
| S05-10 | tests/unit/core/metrics/test_coupling_analyser.py                               | 3   |
| S05-11 | tests/unit/core/metrics/test_test_coverage_reader.py                            | 2   |

## Acceptance Criteria

- ComplexityCalculator.cyclomatic() within 10% of radon for same functions
- DuplicationDetector finds exact copy of 10+ lines
- CouplingAnalyser: module that only imports = I=1.0
- TestCoverageReader returns 0.0 when no coverage file found (no exception)

→ tasks_05.md
