# Phase 02 — Language Parsers & Metrics

**Sprints:** 04 · 05 · 06
**Goal:** Multi-language support, all code metrics, all export formats.

**Done when:** `dev-stats analyse . --output all` produces correct output
for a mixed Java/Python/JS fixture project. All metrics verified against
hand-crafted fixture files.

## Modules Delivered

```
core/parsers/   java_parser.py, javascript_parser.py, typescript_parser.py,
                cpp_parser.py, csharp_parser.py, go_parser.py
core/metrics/   complexity_calculator.py, duplication_detector.py,
                coupling_analyser.py, churn_scorer.py, test_coverage_reader.py
output/         sort_schema.py
output/exporters/ json_exporter.py, csv_exporter.py, xml_exporter.py, badge_generator.py
```

## Risks

- Regex parsers are imprecise for edge cases → document limitations, use LOC fallback.
- Duplication detection slow on large repos → add `--no-duplication` escape hatch.

→ Sprints: sprint_04.md · sprint_05.md · sprint_06.md
