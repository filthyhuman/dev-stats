# Sprint 19 — Error Handling Hardening

**Phase:** 07 | **Duration:** 1 week
**Goal:** Replace all broad `except Exception` with specific types. Add
user-visible warnings when git data is missing. Improve logging throughout.

## Stories

| #      | Story                                                                       | Pts |
|--------|-----------------------------------------------------------------------------|-----|
| S19-01 | Audit `analyse_command.py` — replace `except Exception` with specifics      | 3   |
| S19-02 | Git analysis: surface clear warning to console when git data unavailable    | 2   |
| S19-03 | Parser errors: specific exceptions (`SyntaxError`, `OSError`, `ValueError`) | 2   |
| S19-04 | Add `--verbose` / `--quiet` flags to CLI for log-level control              | 2   |
| S19-05 | Add structured logging with `rich.logging.RichHandler`                      | 2   |
| S19-06 | Exporter errors: catch `OSError`/`PermissionError` on file writes           | 2   |
| S19-07 | Unit tests for all new error paths                                          | 3   |
| S19-08 | Ensure no bare `except:` or `except Exception:` remains in codebase        | 1   |

## Acceptance Criteria

- Zero `except Exception:` in source (grep must find none)
- `--verbose` shows debug-level git subprocess output
- `--quiet` suppresses all but errors
- Missing git data shows a clear Rich warning panel
- All validation commands pass

> tasks_19.md
