# Tasks 17 — Remaining tree-sitter Parsers & Hardening

Derived from planning/sprints/sprint_17.md.

## Checklist

### S17-01: TypeScript tree-sitter parser

- [ ] Create `core/parsers/typescript_ts_parser.py` extending `TreeSitterBase`
- [ ] Handle: interfaces, type aliases, enums, decorators, generics
- [ ] Handle: JSX/TSX if extension is `.tsx`
- [ ] Unit tests in `tests/unit/core/parsers/test_typescript_ts_parser.py`

### S17-02: C++ tree-sitter parser

- [ ] Create `core/parsers/cpp_ts_parser.py` extending `TreeSitterBase`
- [ ] Handle: classes, structs, namespaces, templates, operator overloads
- [ ] Handle: header files (`.h`, `.hpp`) — declarations vs definitions
- [ ] Unit tests in `tests/unit/core/parsers/test_cpp_ts_parser.py`

### S17-03: C# tree-sitter parser

- [ ] Create `core/parsers/csharp_ts_parser.py` extending `TreeSitterBase`
- [ ] Handle: classes, interfaces, records, structs, partial classes
- [ ] Handle: properties, indexers, events, LINQ expressions
- [ ] Unit tests in `tests/unit/core/parsers/test_csharp_ts_parser.py`

### S17-04: Go tree-sitter parser

- [ ] Create `core/parsers/go_ts_parser.py` extending `TreeSitterBase`
- [ ] Handle: structs, interfaces, methods with receivers, goroutines
- [ ] Handle: multiple return values, named returns, defer/go
- [ ] Unit tests in `tests/unit/core/parsers/test_go_ts_parser.py`

### S17-05: Cognitive complexity in TreeSitterBase

- [ ] Implement `_cognitive_complexity_from_tree(node)` in `tree_sitter_base.py`
- [ ] Walk AST: +1 for branching/looping nodes, nesting increment per depth
- [ ] Wire into all tree-sitter parsers' `_build_method_report()` calls
- [ ] Test with reference functions across all languages

### S17-06: Parser coverage audit

- [ ] Run `pytest --cov` and check each parser file
- [ ] Add missing tests to bring all parsers to >= 92%
- [ ] Focus on uncovered branches (the lines flagged in coverage report)

### S17-07: Edge-case fixtures

- [ ] `tests/fixtures/sample_files/edge_cases/empty.py` (0 bytes)
- [ ] `tests/fixtures/sample_files/edge_cases/syntax_error.py` (invalid Python)
- [ ] `tests/fixtures/sample_files/edge_cases/unicode.py` (non-ASCII identifiers)
- [ ] `tests/fixtures/sample_files/edge_cases/huge.py` (10,000+ lines — generated)
- [ ] Assert all parsers handle these without crashing
- [ ] Assert empty file produces FileReport with all zeros

### Validation

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] All parser coverage >= 92%
- [ ] Commit & push
