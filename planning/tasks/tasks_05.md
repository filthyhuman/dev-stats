# Tasks 05 — Metrics Layer

Derived from planning/sprints/sprint_05.md.

## Checklist

### Models

- [x] T05-01: Add metrics-related models to core/models.py (DuplicationReport, CouplingReport, CoverageReport, FileMetrics)

### Metric implementations

- [x] T05-02: Create core/metrics/complexity_calculator.py (cyclomatic, cognitive, Halstead, nesting depth)
- [x] T05-03: Create core/metrics/duplication_detector.py (Rabin-Karp rolling hash)
- [x] T05-04: Create core/metrics/coupling_analyser.py (import graph, Ce/Ca/I/A/D)
- [x] T05-05: Create core/metrics/churn_scorer.py (churn score per file)
- [x] T05-06: Create core/metrics/test_coverage_reader.py (.coverage + lcov.info)

### Wiring

- [x] T05-07: Wire metrics into Aggregator (add metrics results to RepoReport)

### Tests

- [x] T05-08: tests/unit/core/metrics/test_complexity_calculator.py
- [x] T05-09: tests/unit/core/metrics/test_duplication_detector.py
- [x] T05-10: tests/unit/core/metrics/test_coupling_analyser.py
- [x] T05-11: tests/unit/core/metrics/test_churn_scorer.py
- [x] T05-12: tests/unit/core/metrics/test_test_coverage_reader.py

### Validation

- [x] T05-13: ruff check . && ruff format . pass
- [x] T05-14: mypy src/ --strict passes
- [x] T05-15: pytest passes (all tests green)
