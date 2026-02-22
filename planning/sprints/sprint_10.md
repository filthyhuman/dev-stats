# Sprint 10 — Dashboard Data Layer

**Phase:** 04 | **Duration:** 1 week
**Goal:** RepoReport fully serialised, compressed, embedded-ready.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S10-01 | output/sort_schema.py — complete 45+ attribute registry with JS column config JSON | 4  |
| S10-02 | output/dashboard/data_compressor.py — DataCompressor: thematic chunks, zlib, base64 | 5 |
| S10-03 | output/dashboard/asset_embedder.py — AssetEmbedder: base64 data: URIs for all assets | 3 |
| S10-04 | Vendor Chart.js 4.x into templates/assets/chart.min.js                          | 1   |
| S10-05 | templates/assets/styles.css — full dashboard CSS, sidebar, tabs, badges, responsive | 5  |
| S10-06 | templates/assets/app.js skeleton — TableSorter class, URL hash state, filter bar | 8  |
| S10-07 | tests/unit/output/test_data_compressor.py — valid base64, decompresses to JSON  | 3   |
| S10-08 | tests/unit/output/test_asset_embedder.py — data: URI prefix present             | 2   |
| S10-09 | Size budget test: 100 files + 1000 commits < 5 MB compressed                   | 2   |

## Acceptance Criteria

- DataCompressor output decompresses in browser via DecompressionStream
- AssetEmbedder produces chart_js_uri, css_uri, app_js_uri keys
- TableSorter sorts 100-row test table by two columns
- Generated CSS passes W3C validator

→ tasks_10.md
