# Tasks 10 — Dashboard Data Layer

Derived from planning/sprints/sprint_10.md.

## Checklist

### S10-01: Sort Schema expansion
- [x] Update `src/dev_stats/output/sort_schema.py` — add commit, branch, contributor, pattern entities (65+ total)

### S10-02: DataCompressor
- [x] Create `src/dev_stats/output/dashboard/data_compressor.py` — `DataCompressor`: thematic chunks, zlib, base64

### S10-03: AssetEmbedder
- [x] Create `src/dev_stats/output/dashboard/asset_embedder.py` — `AssetEmbedder`: base64 data: URIs for all assets

### S10-04: Chart.js vendor
- [x] Create `src/dev_stats/output/dashboard/templates/assets/chart.min.js` — Chart.js 4.x stub placeholder

### S10-05: Dashboard CSS
- [x] Create `src/dev_stats/output/dashboard/templates/assets/styles.css` — full dashboard CSS with sidebar, tabs, badges, responsive

### S10-06: Dashboard app.js skeleton
- [x] Create `src/dev_stats/output/dashboard/templates/assets/app.js` — TableSorter, FilterBar, TabManager, DataLoader

### S10-07: DataCompressor Tests
- [x] Create `tests/unit/output/test_data_compressor.py` — valid base64, decompresses to JSON, size budget

### S10-08: AssetEmbedder Tests
- [x] Create `tests/unit/output/test_asset_embedder.py` — data: URI prefix, embed_all, embed_file, inline

### Validation
- [x] `uv run ruff check .` passes
- [x] `uv run ruff format .` passes
- [x] `uv run mypy src/ --strict` passes
- [x] `uv run pytest` passes (all tests green)
- [x] Commit & push
