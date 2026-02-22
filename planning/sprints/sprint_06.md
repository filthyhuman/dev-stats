# Sprint 06 — Exporters & Badges

**Phase:** 02 | **Duration:** 1 week
**Goal:** All output formats working. `--output all` produces every file type.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S06-01 | output/sort_schema.py — SortSchema: 45+ attributes with SortType, Python + JS metadata | 4 |
| S06-02 | output/exporters/json_exporter.py — JsonExporter: full + summary modes, ISO 8601 dates | 3 |
| S06-03 | output/exporters/csv_exporter.py — CsvExporter: one CSV per entity type         | 3   |
| S06-04 | output/exporters/xml_exporter.py — XmlExporter: JUnit XML, violation as testcase| 3   |
| S06-05 | output/exporters/badge_generator.py — BadgeGenerator: SVG shields-style         | 3   |
| S06-06 | Wire all exporters into analyse_command.py via --output flag                     | 2   |
| S06-07 | tests/unit/output/test_json_exporter.py                                          | 2   |
| S06-08 | tests/unit/output/test_csv_exporter.py                                           | 2   |
| S06-09 | tests/unit/output/test_xml_exporter.py                                           | 2   |
| S06-10 | tests/unit/output/test_badge_generator.py                                        | 2   |
| S06-11 | Integration: --output all on fake_repo produces all expected files               | 2   |

## Acceptance Criteria

- --output json produces valid parseable JSON
- --output csv produces files.csv with correct headers
- --output xml produces valid JUnit XML
- --output badges produces ≥ 5 SVG files
- All exporter export() return list of created paths

→ tasks_06.md
