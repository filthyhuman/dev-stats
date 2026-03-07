# Sprint 15 — Cognitive Complexity & Python Parser Depth

**Phase:** 06 | **Duration:** 1 week
**Goal:** Implement real cognitive complexity scoring. Fix the hardcoded `0` in
`python_parser.py`. Backfill cognitive complexity into `ComplexityCalculator`.

## Stories

| #      | Story                                                                       | Pts |
|--------|-----------------------------------------------------------------------------|-----|
| S15-01 | Implement `_cognitive_complexity()` in `python_parser.py` using AST         | 5   |
| S15-02 | Update `_build_method_report()` to call `_cognitive_complexity()`           | 1   |
| S15-03 | Add `cognitive()` method to `ComplexityCalculator` (regex heuristic)        | 3   |
| S15-04 | Unit tests for cognitive complexity: simple, nested, boolean chains         | 3   |
| S15-05 | Validate cognitive scores against known SonarQube reference cases           | 2   |
| S15-06 | Close `json_exporter.py` coverage gap (currently 77% -> target 90%+)       | 3   |
| S15-07 | Add tests for `abstract_parser.py` uncovered lines (89% -> 95%+)           | 2   |

## Acceptance Criteria

- `cognitive_complexity` field populated with real values for Python files
- `ComplexityCalculator.cognitive()` returns non-zero for complex functions
- `json_exporter.py` coverage >= 90%
- `abstract_parser.py` coverage >= 95%
- All validation commands pass

> tasks_15.md
