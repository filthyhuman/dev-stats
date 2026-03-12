# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| < 0.2   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in dev-stats, please report it
through
[GitHub Security Advisories](https://github.com/filthyhuman/dev-stats/security/advisories/new).

**Do not** open a public issue for security vulnerabilities.

### Response Timeline

- **Acknowledgement:** within 48 hours of report submission.
- **Initial assessment:** within 5 business days.
- **Fix and disclosure:** coordinated with the reporter. We aim to release a
  patch within 14 days of confirming a vulnerability.

## Threat Model

dev-stats is a **local CLI tool** that analyses Git repositories on the
user's own machine. It produces terminal output, data exports (JSON, CSV,
XML), SVG badges, and a self-contained HTML dashboard. It makes **no network
connections** and requires **no cloud services**.

### Untrusted Input

Any Git repository may contain adversarial content. dev-stats treats the
following as **untrusted**:

- File contents (source code, configuration, data files)
- File names and directory paths
- Commit messages, author names, author emails
- Branch names, tag names, ref names
- `.gitignore` and other repository metadata

### Trusted Boundaries

- The **user invoking the CLI** is trusted. dev-stats does not elevate
  privileges or change filesystem permissions.
- The **local `git` binary** is trusted. dev-stats delegates to the
  system-installed git and assumes it behaves correctly.
- The **local filesystem permissions** are trusted. dev-stats reads files the
  invoking user already has access to.

### Out of Scope

- Attacks that require the attacker to already have code execution on the
  user's machine.
- Denial of service via extremely large repositories (dev-stats will be slow,
  but this is a resource issue, not a security issue).
- Vulnerabilities in the system-installed `git` binary itself.

## Security Architecture

### Subprocess Handling

All Git commands use **list-based arguments** passed to `subprocess.run()`.
No call uses `shell=True`, `os.system()`, or string interpolation into
shell commands.

```python
subprocess.run(
    ["git", "log", "--format=...", "--numstat"],
    cwd=repo_path,
    check=True,
    capture_output=True,
    text=True,
    timeout=30,
)
```

Every subprocess call enforces a **timeout** (30-120 seconds) to prevent
hangs on malformed repositories.

### File I/O and Path Traversal

- The repository root is resolved to an absolute path via `Path.resolve()`,
  which follows symlinks to their real location.
- All file paths are checked with `Path.relative_to(repo_root)` before
  processing, ensuring no file outside the repository is read.
- Over 100 binary file extensions are excluded by a hardcoded
  `frozenset` before any read attempt.
- Files are read with `errors="replace"` to handle malformed encodings
  without raising exceptions.

### HTML Dashboard and XSS Prevention

The dashboard embeds repository data (filenames, author names, commit
messages, branch names) into a single-file HTML page. Cross-site scripting
is mitigated by:

1. **Jinja2 autoescape** is enabled for all HTML templates
   (`autoescape=jinja2.select_autoescape(["html"])`).
2. **No `| safe` filters** or `Markup()` calls exist in the codebase.
3. **Data chunks** (file tables, commit logs, etc.) are serialised to JSON,
   compressed with zlib, and Base64-encoded before embedding in `<script>`
   tags. They are never injected as raw HTML.

### Configuration Loading

- Configuration is parsed from TOML using Python's standard-library
  `tomllib` module, which performs **no code execution**.
- All configuration values are validated through **Pydantic** models with
  strict type annotations.
- No `eval()`, `exec()`, or `pickle` is used anywhere in the codebase.

### Source Code Parsing

- Python files are parsed using the standard-library `ast` module, which
  builds a syntax tree **without executing** any code.
- Other languages use regex-based extraction only (no code execution).

### CI Adapters and Output Generation

- CI adapters write text reports (JSON, XML, YAML annotations) only.
- The pre-commit generator writes a `.pre-commit-config.yaml` file. It does
  **not** generate executable scripts or modify file permissions.
- No output path creates executable files.

## Dependency Policy

dev-stats uses a minimal set of well-maintained runtime dependencies:

| Dependency        | Purpose              | Maintainer              |
|-------------------|----------------------|-------------------------|
| typer             | CLI framework        | Tiangolo / Astral       |
| rich              | Terminal output      | Textualize              |
| pydantic          | Data validation      | Pydantic / Samuel Colvin|
| pydantic-settings | Config loading       | Pydantic / Samuel Colvin|
| jinja2            | HTML templating      | Pallets                 |
| gitpython         | Git object access    | GitPython maintainers   |

No dependency performs unsafe deserialisation (`pickle`, `yaml.load` without
`SafeLoader`), network access, or dynamic code execution.

Dependencies are pinned via `uv.lock` for reproducible builds.

## Known Limitations

- **No sandbox.** Parsed file content is processed in the same Python
  process. A bug in a parser could theoretically be triggered by crafted
  source files, though all parsers use safe operations (AST, regex).
- **Dashboard runs JavaScript.** The generated HTML file, when opened in a
  browser, runs embedded JavaScript for charts and tables. All data is
  autoescaped, but the file should be treated with the same trust level as
  the repository it was generated from.
- **Git binary trust.** dev-stats trusts the output of the local `git`
  binary. A compromised git installation could feed malicious data.

## EU Cyber Resilience Act (CRA)

dev-stats is a non-commercial, community-maintained, GPL-3.0 open-source
project. Under Regulation (EU) 2024/2847 Recital 18, free and open-source
software that is not monetised by its manufacturer is **exempt** from CRA
obligations. No commercial entity is behind this project, and no paid
support or services are offered.

Should this change in the future, this section will be updated accordingly.
