# Tasks 19 — Error Handling Hardening

Derived from planning/sprints/sprint_19.md.

## Checklist

### S19-01: Audit analyse_command.py exception handling

- [ ] `line 163`: `except Exception:` during parsing -> `except (SyntaxError, OSError, ValueError):`
- [ ] `line 219`: `except Exception:` for git analysis -> `except (subprocess.CalledProcessError, OSError, ValueError):`
- [ ] `line 313`: outer `except Exception:` -> `except (ValueError, OSError, subprocess.CalledProcessError):`
- [ ] Ensure each handler logs context-appropriate messages

### S19-02: Visible git-data-missing warning

- [ ] When git analysis fails, show a Rich warning panel (not just a log line)
- [ ] Panel text: "Git analysis unavailable — showing code metrics only"
- [ ] Panel appears when: no `.git` dir, git not installed, or git commands fail
- [ ] Test: mock git failure, assert warning panel text in output

### S19-03: Parser-specific exceptions

- [ ] `python_parser.py`: already catches `SyntaxError` — verify
- [ ] Regex parsers: catch `re.error` for malformed regex matches
- [ ] All parsers: catch `OSError` on file read, `UnicodeDecodeError` on encoding
- [ ] Never let a single file failure abort the entire scan

### S19-04: --verbose / --quiet flags

- [ ] Add `--verbose` / `-v` flag to `analyse_command.py` -> sets `logging.DEBUG`
- [ ] Add `--quiet` / `-q` flag -> sets `logging.ERROR`, suppresses progress bars
- [ ] Mutually exclusive: raise error if both provided
- [ ] Wire into all CLI commands (analyse, branches, gitlog)

### S19-05: Rich logging handler

- [ ] Configure `rich.logging.RichHandler` as default handler in `cli/app.py`
- [ ] Timestamp + module name in debug output
- [ ] Coloured severity levels
- [ ] Test: `--verbose` shows git subprocess commands in output

### S19-06: Exporter error handling

- [ ] Each exporter's `export()`: catch `OSError`/`PermissionError` on file write
- [ ] Log error + continue (don't abort other exports)
- [ ] Show `[red]Failed to write {path}[/red]` in console
- [ ] Test: mock `Path.write_text` to raise `PermissionError`

### S19-07: Error path tests

- [ ] Test: analyse with unreadable file in scan list
- [ ] Test: export to read-only directory
- [ ] Test: git analysis with corrupt .git directory
- [ ] Test: `--verbose` and `--quiet` flag behaviour

### S19-08: Final audit

- [ ] `grep -r "except Exception" src/` returns zero results
- [ ] `grep -r "except:" src/` (bare except) returns zero results
- [ ] All new error paths have corresponding test coverage

### Validation

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` passes
- [ ] `uv run mypy src/ --strict` passes
- [ ] `uv run pytest` passes (all tests green)
- [ ] Commit & push
