# Sprint 04 — Language Parsers (Java, JS, TS, C++, C#, Go)

**Phase:** 02 | **Duration:** 1 week
**Goal:** All six language parsers implemented, registered, tested.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S04-01 | core/parsers/java_parser.py — class/method/field extraction, imports, CC approx | 5   |
| S04-02 | core/parsers/javascript_parser.py — class + function extraction, import/require | 5   |
| S04-03 | core/parsers/typescript_parser.py — extends JS, adds interface/enum             | 3   |
| S04-04 | core/parsers/cpp_parser.py — class/struct/function, #include                   | 4   |
| S04-05 | core/parsers/csharp_parser.py — class/interface/method, using                  | 4   |
| S04-06 | core/parsers/go_parser.py — struct/interface/func/method, import block          | 4   |
| S04-07 | Register all parsers in parser_registry.py                                       | 1   |
| S04-08 | Fixture files: tests/fixtures/sample_files/{java,js,ts,cpp,cs,go}/              | 2   |
| S04-09 | tests/unit/core/parsers/test_java_parser.py                                      | 3   |
| S04-10 | tests/unit/core/parsers/test_javascript_parser.py                               | 3   |
| S04-11 | tests/unit/core/parsers/test_typescript_parser.py                               | 2   |
| S04-12 | tests/unit/core/parsers/test_cpp_parser.py, test_csharp_parser.py, test_go_parser.py | 3 |
| S04-13 | Integration: Dispatcher routes each extension to correct parser                  | 2   |

## Acceptance Criteria

- All parsers handle malformed source gracefully (warning, partial report)
- Dispatcher routes .java → JavaParser, .ts → TypeScriptParser, etc.
- mypy --strict passes on all new parser files

→ tasks_04.md
