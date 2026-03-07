# Phase 06 — Correctness & Depth

**Sprints:** 15 · 16 · 17
**Goal:** Fix hardcoded/stub values, implement cognitive complexity, upgrade
regex parsers to tree-sitter, harden error handling, and close coverage gaps.

**Done when:** Cognitive complexity is computed for all languages.
All parsers produce structurally correct output on real-world codebases.
`json_exporter` coverage >= 90%. No hardcoded `0` placeholder metrics remain.

## Modules Delivered

```
core/parsers/     tree-sitter backed parsers for Java, JS, TS, C++, C#, Go
core/parsers/     python_parser.py cognitive complexity implementation
core/metrics/     complexity_calculator.py cognitive complexity
output/exporters/ json_exporter.py coverage gap closed
```

## Risks

- tree-sitter bindings add native dependencies -> provide fallback to regex parsers.
- Cognitive complexity algorithm edge cases -> validate against SonarQube reference.

> Sprints: sprint_15.md · sprint_16.md · sprint_17.md
