# Tasks 15 — Cognitive Complexity & Coverage Gaps

Derived from planning/sprints/sprint_15.md.

## Checklist

### S15-01: Implement cognitive complexity for Python

- [ ] Create `_cognitive_complexity()` function in `python_parser.py`
- [ ] Algorithm: +1 for each `if/elif/for/while/except/with`, +1 nesting increment per level
- [ ] +1 for each `and`/`or` boolean chain (sequences, not per-operand)
- [ ] +1 for `else`/`finally` branches
- [ ] +1 for recursion (function calls matching the current function name)
- [ ] Nesting penalty: multiply by current nesting depth for flow-breaking nodes

### S15-02: Wire cognitive complexity into MethodReport

- [ ] Replace `cognitive_complexity=0` in `_build_method_report()` with `_cognitive_complexity(func_node)`
- [ ] Verify existing tests still pass (scores will change from 0 to real values)
- [ ] Update any test assertions that expected `cognitive_complexity=0`

### S15-03: ComplexityCalculator cognitive method

- [ ] Add `cognitive(self, source: str) -> int` to `ComplexityCalculator`
- [ ] Use regex heuristic: weight keywords by nesting depth
- [ ] Add unit tests for the heuristic with known inputs/outputs

### S15-04: Cognitive complexity tests

- [ ] `tests/unit/core/parsers/test_python_cognitive.py`
- [ ] Test cases: simple function (score=0), single if (score=1), nested if-for (high score)
- [ ] Test cases: boolean chains `a and b and c` (score=2 for the chain)
- [ ] Test cases: deeply nested function (score > 10)
- [ ] Test cases: recursive function

### S15-05: SonarQube reference validation

- [ ] Find 5+ reference functions with known SonarQube cognitive complexity scores
- [ ] Create fixture files with these functions
- [ ] Assert dev-stats scores match within +/- 1 of SonarQube

### S15-06: json_exporter coverage (77% -> 90%+)

- [ ] Read `json_exporter.py` and identify uncovered lines (110, 112, 114, 131-136, 152-153, 176, 180, 185)
- [ ] Add tests for summary mode export
- [ ] Add tests for git data serialisation (commits, branches, contributors)
- [ ] Add tests for empty/None optional fields

### S15-07: abstract_parser coverage (89% -> 95%+)

- [ ] Add test for `detect_encoding()` with non-UTF-8 file
- [ ] Add test for `parse()` when file cannot be read (`OSError`)
- [ ] Add test for `can_parse()` with various extensions

### Validation

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] `json_exporter.py` coverage >= 90%
- [ ] `abstract_parser.py` coverage >= 95%
- [ ] Commit & push
