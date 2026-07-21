# Strict prek.toml Reference

Complete native `prek.toml` template. Strictify uses `prek` exclusively: do not install
or invoke a fallback hook runner, and do not create a YAML hook configuration.

If the target contains `.pre-commit-config.yaml` or `.pre-commit-config.yml`, migrate its
hooks into `prek.toml`, preserve its intent, and remove the legacy file after the native
configuration is complete. Never leave both configurations in the repo.

Run all hooks with: `uvx prek run --all-files`

Install the Git hook with: `uvx prek install`

---

## Placeholders

| Placeholder | Example | Description |
|---|---|---|
| `{package_name}` | `my_project` | Importable production package directory |
| `{python_version}` | `13` | Target Python minor version |

---

## Complete template

Conditional blocks are explicitly marked. Include them only when the corresponding
strictify category fits the target repo.

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
id = "check-print-statements"
name = "Check print statements"
entry = "python scripts/prek_hooks/check_print_statements.py"
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
id = "fix-future-annotations"
name = "Fix future annotations"
entry = "python scripts/prek_hooks/fix_future_annotations.py"
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

---

## Notes for the agent

1. **Replace placeholders.** Substitute `{package_name}` and `{python_version}` before
   installing the hook.
2. **Keep one native config.** Migrate legacy YAML behavior into `prek.toml`, then remove
   the old file. Do not maintain parallel configurations.
3. **Bootstrap the secrets baseline.** Run `uvx detect-secrets scan`, review every
   finding, and save the audited `.secrets.baseline` before enabling its hook.
4. **Keep conditional blocks conditional.** Deptry needs trustworthy dependency
   metadata; schema validation must not overrule the actual tools; check-sdist belongs
   only in repos that publish a Python distribution.
5. **Keep Vulture configuration singular.** The hook arguments override matching
   `pyproject.toml` values. Keep them synchronized or remove the hook arguments.
6. **Update pins deliberately.** Use `uvx prek update`, inspect the resulting changes,
   and run the affected tools before accepting an update.
7. **Adapt execution commands.** Replace `uv run` for non-uv repositories with the
   target's package-manager invocation.
8. **Monorepos need explicit scope.** Duplicate or wrap package-scoped hooks when the
   target contains multiple importable packages.
