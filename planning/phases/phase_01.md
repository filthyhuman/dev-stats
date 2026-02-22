# Phase 01 — Foundation

**Sprints:** 01 · 02 · 03
**Goal:** Runnable CLI, validated config, file scanning, Python parser, basic terminal output.

**Done when:** `dev-stats analyse .` runs on the project itself and prints
a correct terminal report showing Python file count, LOC, classes, and methods.

## Modules Delivered

```
cli/              app.py, analyse_command.py, branches_command.py,
                  gitlog_command.py, version_callback.py
config/           analysis_config.py, threshold_config.py, branch_config.py,
                  gitlog_config.py, output_config.py, config_loader.py, defaults.toml
core/             models.py, scanner.py, parser_registry.py, dispatcher.py, aggregator.py
core/parsers/     abstract_parser.py, python_parser.py, generic_parser.py
output/exporters/ abstract_exporter.py, terminal_reporter.py
```

## Risks

- `ast` syntax edge cases → log warning, return partial FileReport, never raise.
- Large repos → Scanner must be a generator (lazy), not load all paths into memory.

→ Sprints: sprint_01.md · sprint_02.md · sprint_03.md
