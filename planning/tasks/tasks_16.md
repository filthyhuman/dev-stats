# Tasks 16 — tree-sitter Parser Infrastructure (Java & JS)

Derived from planning/sprints/sprint_16.md.

## Checklist

### S16-01: Add tree-sitter dependencies

- [ ] Add `tree-sitter>=0.21` and `tree-sitter-languages>=1.10` to `[project.optional-dependencies]` as `parsers` extra
- [ ] `uv sync --all-extras` succeeds
- [ ] Document in README that tree-sitter is optional but recommended

### S16-02: TreeSitterBase class

- [ ] Create `core/parsers/tree_sitter_base.py`
- [ ] `TreeSitterBase(AbstractParser)` — loads grammar, provides `_parse_tree()` helper
- [ ] Shared node traversal: `_find_nodes(tree, type_name)` -> generator
- [ ] Shared extraction: `_node_text(node)`, `_node_line_range(node)`
- [ ] Method to compute cyclomatic + cognitive complexity from tree-sitter nodes
- [ ] Handle `ImportError` for tree-sitter gracefully (log warning, return empty)

### S16-03: Java parser rewrite

- [ ] Create `core/parsers/java_ts_parser.py` extending `TreeSitterBase`
- [ ] Extract: classes (including inner/nested), interfaces, enums
- [ ] Extract: methods with full parameter types, generics, annotations
- [ ] Extract: constructors (detect `<init>` pattern)
- [ ] Extract: imports (package-level)
- [ ] Compute cyclomatic + cognitive complexity from tree structure
- [ ] Keep `java_parser.py` (regex) as-is for fallback

### S16-04: JavaScript parser rewrite

- [ ] Create `core/parsers/javascript_ts_parser.py` extending `TreeSitterBase`
- [ ] Extract: classes, arrow functions, function declarations, function expressions
- [ ] Extract: methods within class bodies
- [ ] Handle: destructuring parameters, default parameters, rest parameters
- [ ] Handle: template literals, computed property names
- [ ] Extract: import/require statements
- [ ] Keep `javascript_parser.py` (regex) as-is for fallback

### S16-05: Registry fallback logic

- [ ] Modify `parser_registry.py` to prefer tree-sitter parsers when available
- [ ] `create_default_registry()` tries tree-sitter import; falls back to regex
- [ ] Add `--no-tree-sitter` CLI flag to force regex parsers

### S16-06: tree-sitter parser unit tests

- [ ] `tests/unit/core/parsers/test_java_ts_parser.py`
- [ ] `tests/unit/core/parsers/test_javascript_ts_parser.py`
- [ ] Compare output against regex parser output for same fixtures
- [ ] Test tree-sitter parser extracts things regex misses (nested classes, arrow fns)

### S16-07: Integration test with real files

- [ ] Add `tests/fixtures/sample_files/java/Complex.java` (nested classes, generics, annotations)
- [ ] Add `tests/fixtures/sample_files/javascript/complex.js` (arrow fns, destructuring, classes)
- [ ] Assert tree-sitter parsers produce correct ClassReport/MethodReport

### Validation

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] Commit & push
