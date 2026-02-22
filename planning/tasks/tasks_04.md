# Tasks 04 — Language Parsers (Java, JS, TS, C++, C#, Go)

Derived from planning/sprints/sprint_04.md.

## Checklist

### Fixture files

- [x] T04-01: Create tests/fixtures/sample_files/java/Sample.java
- [x] T04-02: Create tests/fixtures/sample_files/javascript/sample.js
- [x] T04-03: Create tests/fixtures/sample_files/typescript/sample.ts
- [x] T04-04: Create tests/fixtures/sample_files/cpp/sample.cpp
- [x] T04-05: Create tests/fixtures/sample_files/csharp/Sample.cs
- [x] T04-06: Create tests/fixtures/sample_files/go/sample.go

### Parser implementations

- [x] T04-07: Create core/parsers/java_parser.py (JavaParser)
- [x] T04-08: Create core/parsers/javascript_parser.py (JavaScriptParser)
- [x] T04-09: Create core/parsers/typescript_parser.py (TypeScriptParser extends JS)
- [x] T04-10: Create core/parsers/cpp_parser.py (CppParser)
- [x] T04-11: Create core/parsers/csharp_parser.py (CSharpParser)
- [x] T04-12: Create core/parsers/go_parser.py (GoParser)

### Registry

- [x] T04-13: Update parser_registry.py to register all 6 new parsers

### Tests

- [x] T04-14: Create tests/unit/core/parsers/test_java_parser.py
- [x] T04-15: Create tests/unit/core/parsers/test_javascript_parser.py
- [x] T04-16: Create tests/unit/core/parsers/test_typescript_parser.py
- [x] T04-17: Create tests/unit/core/parsers/test_cpp_parser.py
- [x] T04-18: Create tests/unit/core/parsers/test_csharp_parser.py
- [x] T04-19: Create tests/unit/core/parsers/test_go_parser.py
- [x] T04-20: Integration: verify Dispatcher routes each extension correctly

### Validation

- [x] T04-21: ruff check . && ruff format . pass
- [x] T04-22: mypy src/ --strict passes
- [x] T04-23: pytest passes (all tests green)
