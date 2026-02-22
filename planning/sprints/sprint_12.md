# Sprint 12 — Dashboard Polish & Performance

**Phase:** 04 | **Duration:** 1 week
**Goal:** Large repo support, size budget enforced, UX polished.

## Stories

| #      | Story                                                                            | Pts |
|--------|----------------------------------------------------------------------------------|-----|
| S12-01 | Virtual scrolling for commit lists > 500 rows                                    | 5   |
| S12-02 | DecompressionStream feature-detect + fallback to uncompressed JSON               | 2   |
| S12-03 | Size enforcement: warn 30 MB, error 50 MB, clear message + flags to reduce      | 2   |
| S12-04 | "Copy all safe deletes" button — multi-line shell script to clipboard            | 2   |
| S12-05 | URL hash sort state: encode + restore on page load                               | 3   |
| S12-06 | Blame heat map colour scale: fresh→recent→old→ancient                           | 2   |
| S12-07 | Commit graph: zoom + pan, minimap                                                | 3   |
| S12-08 | Contributor profile: 52-week activity heatmap                                   | 3   |
| S12-09 | Print CSS: tables paginate, charts inline                                        | 2   |
| S12-10 | Dark/light mode toggle                                                           | 2   |
| S12-11 | Performance test: 5000 commits + 500 files < 45 MB and < 30 s generation        | 3   |

## Acceptance Criteria

- 5000-commit dashboard scrolls without jank (> 30 FPS)
- Copy all safe deletes produces valid shell commands
- URL #sort=loc_total:desc restores that sort on page load
- Dashboard for dev-stats itself < 30 MB

→ tasks_12.md
