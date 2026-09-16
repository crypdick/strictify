# Strict prek.toml reference

Use `prek` exclusively. Migrate `.pre-commit-config.yaml` or
`.pre-commit-config.yml` behavior into native `prek.toml`, verify it, then remove
the obsolete file. Do not keep competing configs or runners.

## Placeholders

Replace `{package_name}` with the production package directory and
`{python_version}` with the target minor version, such as `13`.

## Complete template

Include marked conditional blocks only when applicable. For architecture checks,
follow [boundary contracts](architecture-boundaries.md) and, if using the bundled
checker, its [installation guide](architecture-toolkit.md). Place the installed
command before pytest with `pass_filenames = false` and `always_run = true`.

```toml
minimum_prek_version = "0.3.2"
default_language_version.python = "python3"

# Native prek hygiene hooks. These need no network access or managed environment.
[[repos]]
repo = "builtin"
hooks = [
    {id = "trailing-whitespace"},
    {id = "end-of-file-fixer"},
    {id = "check-json"},
    {id = "check-toml"},
    {id = "check-yaml"},
    {id = "check-merge-conflict"},
    {id = "detect-private-key"},
    {id = "check-added-large-files"},
    {id = "check-case-conflict"},
    {id = "check-symlinks"},
    {id = "destroyed-symlinks"},
    {id = "fix-byte-order-marker"},
    {id = "mixed-line-ending"},
    {id = "check-executables-have-shebangs"},
    {id = "check-shebang-scripts-are-executable"},
]

# Entropy-based secret scanning. Bootstrap and audit .secrets.baseline before enabling.
[[repos]]
repo = "https://github.com/Yelp/detect-secrets"
rev = "v1.5.0"
hooks = [
    {id = "detect-secrets", args = ["--baseline", ".secrets.baseline"], exclude = "uv\\.lock"},
]

# Dead-code detection.
[[repos]]
repo = "https://github.com/jendrikseipp/vulture"
rev = "v2.14"
hooks = [
    {id = "vulture", args = [".", "--min-confidence", "80"]},
]

# Syntax modernization.
[[repos]]
repo = "https://github.com/asottile/pyupgrade"
rev = "v3.21.2"
hooks = [
    {id = "pyupgrade", args = ["--py3{python_version}-plus"]},
]

# More aggressive but semantics-preserving f-string conversion.
[[repos]]
repo = "https://github.com/ikamensh/flynt"
rev = "1.0.6"
hooks = [
    {id = "flynt"},
]

# CONDITIONAL: include when dependency metadata is authoritative.
[[repos]]
repo = "https://github.com/osprey-oss/deptry"
rev = "0.25.1"
hooks = [
    {id = "deptry"},
]

# CONDITIONAL: include when current schemas cover the configured tools. The actual
# tools remain authoritative if a schema release lags a valid new setting or rule.
[[repos]]
repo = "https://github.com/henryiii/validate-pyproject-schema-store"
rev = "2026.07.08"
hooks = [
    {id = "validate-pyproject"},
]

# CONDITIONAL: include only for a publishable Python distribution.
[[repos]]
repo = "https://github.com/henryiii/check-sdist"
rev = "v1.5.0"
hooks = [
    {id = "check-sdist-isolated", args = ["--inject-junk"]},
]

# Project-local checks, ordered from cheap static checks to the full test suite.
[[repos]]
repo = "local"

[[repos.hooks]]
id = "ruff-check"
name = "Ruff check"
entry = "uv run ruff check --fix --quiet"
language = "system"
types = ["python"]

[[repos.hooks]]
id = "ruff-format"
name = "Ruff format"
entry = "uv run ruff format --quiet"
language = "system"
types = ["python"]

[[repos.hooks]]
id = "mypy"
name = "mypy"
entry = "uv run mypy {package_name}/"
language = "system"
pass_filenames = false
always_run = true

[[repos.hooks]]
id = "check-exception-handling"
name = "Check exception handling"
entry = "python scripts/prek_hooks/check_exception_handling.py"
language = "system"
types = ["python"]

[[repos.hooks]]
id = "check-timeless-comments"
name = "Check timeless comments"
entry = "python scripts/prek_hooks/check_timeless_comments.py"
language = "system"
types = ["python"]

[[repos.hooks]]
id = "check-file-length"
name = "Check file length"
entry = "python scripts/prek_hooks/check_file_length.py"
language = "system"
types = ["python"]

[[repos.hooks]]
id = "check-private-test-imports"
name = "Forbid private imports in tests"
entry = "python scripts/prek_hooks/check_private_test_imports.py"
language = "system"
types = ["python"]

[[repos.hooks]]
id = "pytest"
name = "pytest"
entry = "uv run pytest"
language = "system"
pass_filenames = false
always_run = true
```

## Notes for the agent

- Replace `uv run` for other package managers. Scope or wrap hooks for each
  production package in a monorepo.
- Run `uvx detect-secrets scan`, review findings, and save the audited
  `.secrets.baseline` before enabling its hook.
- Deptry needs reliable metadata; schema validation must support actual tool
  settings; check-sdist requires a publishable distribution.
- Vulture hook arguments override `pyproject.toml`; synchronize them or remove
  the duplicate arguments.
- Update pins with `uvx prek update`, inspect the diff, and run affected tools.
- When replacing Strictify's `check-print-statements` and `fix-future-annotations`,
  preserve repo-specific behavior before removing their entries and scripts.
  Ruff owns print/logging and misplaced future imports (`F404`). Translate
  `# allow: print-statements` to `# noqa: T201` and logging exemptions to exact
  Ruff `G` codes.

Verify with `uvx prek run --all-files`, then activate with `uvx prek install`.
