# Tasks 06 — Exporters & Badges

Derived from planning/sprints/sprint_06.md.

## Checklist

### S06-01: Sort Schema
- [x] Create `src/dev_stats/output/sort_schema.py` — `SortType` enum + `SortSchema` class with 45+ sortable attributes

### S06-02: JSON Exporter
- [x] Create `src/dev_stats/output/exporters/json_exporter.py` — `JsonExporter` with full + summary modes, ISO 8601 dates

### S06-03: CSV Exporter
- [x] Create `src/dev_stats/output/exporters/csv_exporter.py` — `CsvExporter`: one CSV per entity type

### S06-04: XML Exporter
- [x] Create `src/dev_stats/output/exporters/xml_exporter.py` — `XmlExporter`: JUnit XML format

### S06-05: Badge Generator
- [x] Create `src/dev_stats/output/exporters/badge_generator.py` — `BadgeGenerator`: SVG shields-style badges

### S06-06: CLI Wiring
- [x] Update `src/dev_stats/cli/analyse_command.py` — wire `--format` flag to dispatch exporters

### S06-07: JSON Exporter Tests
- [x] Create `tests/unit/output/test_json_exporter.py`

### S06-08: CSV Exporter Tests
- [x] Create `tests/unit/output/test_csv_exporter.py`

### S06-09: XML Exporter Tests
- [x] Create `tests/unit/output/test_xml_exporter.py`

### S06-10: Badge Generator Tests
- [x] Create `tests/unit/output/test_badge_generator.py`

### S06-11: Sort Schema Tests
- [x] Create `tests/unit/output/test_sort_schema.py`

### Validation
- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] Commit & push
