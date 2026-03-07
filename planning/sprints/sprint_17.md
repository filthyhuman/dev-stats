# Sprint 17 — Remaining tree-sitter Parsers & Parser Hardening

**Phase:** 06 | **Duration:** 1 week
**Goal:** Migrate TypeScript, C++, C#, Go parsers to tree-sitter.
Add cognitive complexity to all tree-sitter parsers.

## Stories

| #      | Story                                                                       | Pts |
|--------|-----------------------------------------------------------------------------|-----|
| S17-01 | Rewrite `typescript_parser.py` using tree-sitter                            | 4   |
| S17-02 | Rewrite `cpp_parser.py` using tree-sitter                                   | 4   |
| S17-03 | Rewrite `csharp_parser.py` using tree-sitter                                | 4   |
| S17-04 | Rewrite `go_parser.py` using tree-sitter                                    | 4   |
| S17-05 | Add cognitive complexity extraction to `TreeSitterBase`                      | 3   |
| S17-06 | Raise parser coverage: all parsers >= 92%                                   | 3   |
| S17-07 | Add edge-case fixtures: empty files, syntax errors, unicode, huge files     | 2   |

## Acceptance Criteria

- All 8 language parsers produce correct output on real-world samples
- Cognitive complexity populated for all languages
- All parser coverage >= 92%
- All validation commands pass

> tasks_17.md
