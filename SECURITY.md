# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.2.x   | Yes                |
| < 0.2   | No                 |

## Reporting a Vulnerability

If you discover a security vulnerability in dev-stats, please report it
through [GitHub Security Advisories](https://github.com/filthyhuman/dev-stats/security/advisories/new).

**Do not** open a public issue for security vulnerabilities.

## Response Timeline

- **Acknowledgement:** within 48 hours of report submission.
- **Initial assessment:** within 5 business days.
- **Fix and disclosure:** coordinated with the reporter. We aim to release a
  patch within 14 days of confirming a vulnerability.

## Scope

dev-stats is a local CLI tool with no network access by default. Security
concerns primarily involve:

- Arbitrary code execution via maliciously crafted repository content.
- Path traversal in file scanning or output generation.
- Subprocess injection in Git command construction.
