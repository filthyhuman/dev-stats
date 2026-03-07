# Contributing to dev-stats

Thank you for considering a contribution to dev-stats. This guide covers
everything you need to get started.

---

## Development Setup

```bash
# Clone the repository
git clone https://github.com/filthyhuman/dev-stats
cd dev-stats

# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies including dev extras
uv sync --all-extras

# Set up pre-commit hooks
uv run pre-commit install
```

---

## Coding Standards

dev-stats enforces strict quality rules. The full set of rules lives in
[CLAUDE.md](CLAUDE.md) -- read it before writing any code. Here is the
summary:

- **One class per file.** Enums and pure dataclasses may share a `models.py`,
  but every concrete class gets its own file named after the class in
  `snake_case`.
- **Google-style docstrings** on every public symbol.
- **Full type annotations** on every function and method. `mypy --strict` must
  pass.
- **No `print()` outside `terminal_reporter.py`.** Use `logging` or
  `rich.Console`.
- **No bare `except:`.** Always catch specific exception types.
- **No global mutable state.**
- **All file I/O via `pathlib.Path`** -- never `os.path`.
- **Import order:** `__future__`, stdlib, third-party, first-party (absolute
  imports only).

---

## Running Checks

Every change must pass all four gates before it can be merged:

```bash
# Lint and format
uv run ruff check . --fix
uv run ruff format .

# Type checking
uv run mypy src/ --strict

# Tests with coverage
uv run pytest --cov=dev_stats --cov-report=term-missing
```

---

## Pull Request Process

1. **Branch from `main`.** Use a descriptive branch name
   (e.g. `add-ruby-parser`, `fix-blame-engine-timeout`).
2. **Write descriptive commit messages.** Summarise *what* and *why*, not
   *how*.
3. **All tests must pass.** CI runs ruff, mypy, and pytest automatically.
4. **New code needs tests.** If you add a feature, add tests in the
   corresponding `tests/unit/` or `tests/integration/` directory.
5. **Minimum 90% overall coverage.** Core and config modules require 95%.
6. **One PR per logical change.** Keep PRs focused and reviewable.

---

## Testing Requirements

| Category    | Location            | Rules                                          |
|-------------|---------------------|------------------------------------------------|
| Unit        | `tests/unit/`       | No filesystem, no subprocess. Mock everything. |
| Integration | `tests/integration/`| Uses real temp git repos via fixtures.         |
| CLI         | `tests/integration/`| Typer `CliRunner`. Assert exit codes + output. |

Coverage minimums:

- `src/dev_stats/core/` -- 95%
- `src/dev_stats/config/` -- 95%
- `src/dev_stats/output/` -- 90%
- `src/dev_stats/ci/` -- 90%
- Overall -- 90%

---

## Questions?

Open an issue or start a discussion on GitHub. For the full set of
architecture decisions and development rules, see [CLAUDE.md](CLAUDE.md).
