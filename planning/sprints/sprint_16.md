# Sprint 16 — tree-sitter Parser Infrastructure

**Phase:** 06 | **Duration:** 1 week
**Goal:** Add tree-sitter as an optional dependency. Create a `TreeSitterParser`
base class. Migrate Java and JavaScript parsers from regex to tree-sitter.

## Stories

| #      | Story                                                                       | Pts |
|--------|-----------------------------------------------------------------------------|-----|
| S16-01 | Add `tree-sitter` + `tree-sitter-languages` to optional deps in pyproject   | 1   |
| S16-02 | Create `core/parsers/tree_sitter_base.py` — shared tree-sitter utilities    | 5   |
| S16-03 | Rewrite `java_parser.py` using tree-sitter (keep regex as fallback)         | 5   |
| S16-04 | Rewrite `javascript_parser.py` using tree-sitter (keep regex as fallback)   | 5   |
| S16-05 | Add fallback logic in `parser_registry.py` — prefer tree-sitter, fall back  | 2   |
| S16-06 | Unit tests: tree-sitter parsers match or exceed regex parser accuracy       | 3   |
| S16-07 | Integration test: parse real-world Java/JS files from fixtures              | 2   |

## Acceptance Criteria

- Java parser correctly extracts nested classes, generics, annotations
- JS parser correctly handles arrow functions, destructuring, template literals
- Regex parsers still work when tree-sitter is not installed
- All validation commands pass

> tasks_16.md
