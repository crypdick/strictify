# Strict pyproject.toml Reference

This document contains the canonical strict tool configurations for `pyproject.toml`.
The agent should read each section's commentary and adapt settings to the target project's
framework, size, and conventions. Copy sections verbatim unless the commentary calls for
adjustment.

---

## [tool.ruff] -- Linting and Formatting

Ruff replaces flake8, isort, pyupgrade, and black in a single fast tool.

- `line-length = 110` is a pragmatic default -- long enough for modern screens, short enough
  to discourage run-on expressions. Adjust down to 88 for projects that follow strict
  black-compatible formatting.
- `preview = true` opts into newer rules that haven't yet stabilized. This is intentional:
  strict repos should catch issues early, and preview rules rarely produce false positives
  in well-typed codebases.
- The `select` list covers the most impactful rule families without being exhaustive.
  Add `"PLC"` and `"C90"` if the project has complexity concerns. Add `"UP"` if the
  project hasn't yet been modernized to the target Python version.
- `ignore = ["E501"]` defers line-length enforcement to the formatter rather than the
  linter, avoiding double-reporting.

```toml
[tool.ruff]
line-length = 110
preview = true

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "C4", "SIM", "RUF"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
```

### Complexity

- `max-complexity = 15` is lenient enough for real-world code but catches genuinely
  tangled functions. Lower to 10 for new greenfield projects. Raise to 20 only for
  data-pipeline code with unavoidable branching (and add a comment explaining why).

```toml
[tool.ruff.lint.mccabe]
max-complexity = 15
```

### Per-file ignores

- Test files commonly use unused variables (captured return values), high complexity
  (parameterized setup), and many arguments (fixtures). Suppress these categories
  wholesale for `tests/`.
- Scripts similarly get complexity exemptions since they are often one-shot utilities.
- For Django projects, add `"migrations/**/*.py" = ["E501", "RUF012"]` to suppress
  auto-generated migration noise.
- For FastAPI projects, consider adding `"**/routers/**/*.py" = ["B008"]` to allow
  `Depends()` default arguments.

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["F841", "C901", "PLR0912", "PLR0913", "PLR0915"]
"scripts/**/*.py" = ["C901", "PLR0912", "PLR0913", "PLR0915"]
```

---

## [tool.mypy] -- Static Type Checking

mypy with `strict = true` enables every strictness flag at once. The `disable_error_code`
list then carves out pragmatic exceptions.

- Start with the minimal `disable_error_code` below. The agent should expand this list
  only when the target project has specific framework needs (see notes below).
- `show_error_codes = true` and `pretty = true` are quality-of-life settings that help
  developers fix issues faster.
- The `warn_*` flags are redundant with `strict = true` but are listed explicitly so that
  the intent is clear even if someone later sets `strict = false`.

**When to adjust `disable_error_code`:**

- **Django:** Add `"no-any-return"`, `"attr-defined"`, `"override"` -- Django's ORM and
  class-based views use dynamic attributes and method overrides heavily.
- **FastAPI / Pydantic:** Add `"call-arg"` -- Pydantic model constructors often trigger
  false positives with `model_validate` and similar patterns.
- **CLI tools (click/typer):** The defaults below are usually sufficient. beartype
  warnings for click decorators are handled separately.
- **Data pipelines (pandas/numpy):** Add `"no-any-return"`, `"index"`, `"operator"` --
  pandas return types are often `Any` and operator overloads are imprecise.
- **Textual TUI:** Add `"attr-defined"`, `"override"`, `"union-attr"` -- Textual widgets
  use dynamic attributes and complex inheritance.

```toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
show_error_codes = true
pretty = true

# Pragmatic exceptions -- agent should adjust based on target project's frameworks
disable_error_code = ["no-untyped-call", "no-untyped-def"]
```

### Test file overrides

Tests should never block on type strictness. Fixtures, mocks, and parameterized tests
routinely violate type constraints by design. This override applies to all test modules.

```toml
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_untyped_calls = false
check_untyped_defs = false
ignore_errors = true
```

**Additional overrides the agent may need:**

- For libraries with missing stubs, add an override with `ignore_missing_imports = true`
  scoped to the specific third-party module (e.g., `module = ["ortools.*", "loguru.*"]`).
- Never set `ignore_missing_imports = true` globally -- it masks real import errors.

---

## [tool.pytest.ini_options] -- Test Runner

- `asyncio_mode = "auto"` removes boilerplate `@pytest.mark.asyncio` from every async
  test. Only omit this if the project has no async code at all.
- `-n auto` enables pytest-xdist parallel execution. Remove for projects with
  non-parallelizable tests (shared database state, file locks). If the project uses
  Django, use `--reuse-db` alongside `-n auto`.
- `--failed-first` re-runs failures before passing tests, tightening the feedback loop.
- `--cov-report=term-missing --cov-report=html` provides both terminal and browsable
  coverage output. The `--cov` flag itself is intentionally omitted here so developers
  can run `uv run pytest --no-cov` for speed during development.
- `timeout = 20` catches hanging tests early. Increase to 60 for integration tests that
  hit real services, or add `@pytest.mark.timeout(60)` on individual slow tests.
- `timeout_method = "thread"` works with both sync and async code. Use `"signal"` only
  on Unix-only projects where thread-based timeout is unreliable.

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
addopts = "--no-header -n auto -q --durations=5 --durations-min=1.0 --cov-report=term-missing --cov-report=html --failed-first"
timeout = 20
timeout_method = "thread"
```

**Framework-specific adjustments:**

- **Django:** Add `DJANGO_SETTINGS_MODULE = "myproject.settings.test"` and consider
  adding `--reuse-db` to `addopts`.
- **FastAPI:** The defaults above work well. Add `--asyncio-mode=auto` explicitly if
  using older pytest-asyncio versions.
- **Data pipelines:** Increase `timeout` to 120 and remove `-n auto` if tests share
  heavyweight fixtures (database connections, large DataFrames).

---

## [tool.coverage] -- Code Coverage

- `fail_under = 100` is the strict target. The agent should set this to the project's
  current coverage percentage rounded down to the nearest integer on first adoption,
  then ratchet it up over time. Setting it to 100 immediately on a legacy codebase will
  block all commits.
- `skip_empty = true` excludes `__init__.py` files and other empty modules from the
  coverage denominator.
- The `exclude_lines` patterns cover common boilerplate that is either untestable or
  tested implicitly (abstract methods, `TYPE_CHECKING` blocks, `__repr__` methods).

```toml
[tool.coverage.run]
fail_under = 100
skip_empty = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
    "@abc.abstractmethod",
]
```

**Adjustments:**

- Add a `source = ["{package_name}"]` under `[tool.coverage.run]` to restrict coverage
  measurement to the package itself (excluding tests, scripts, etc.).
- Add `omit = ["*/tests/*", "*/test_*.py", "*/__pycache__/*", "*/conftest.py"]` to
  `[tool.coverage.run]` to exclude test infrastructure from the coverage denominator.
- For Django, add `"*/migrations/*"` and `"*/admin.py"` to `omit`.
- For CLI tools, add `"*/cli.py"` or `"*/__main__.py"` to `exclude_lines` patterns if
  the CLI entry point is hard to test without subprocess calls.

---

## [tool.vulture] -- Dead Code Detection

Vulture finds unused Python code -- variables, functions, imports, classes, and attributes.

- `min_confidence = 80` is a good default that catches genuine dead code without too many
  false positives. Lower to 60 for aggressive cleanup; raise to 90 if the project uses
  heavy metaprogramming (ORMs, plugin systems).
- `exclude = [".venv/"]` prevents scanning vendored dependencies. Add framework-specific
  excludes as needed (e.g., `"migrations/"` for Django).
- For projects with Pydantic models, Textual widgets, or other frameworks that use
  "magic" attribute names, add an `ignore_names` list in pyproject.toml scoped to those
  patterns (e.g., `"model_config"`, `"on_*"`, `"watch_*"`).

```toml
[tool.vulture]
min_confidence = 80
exclude = [".venv/"]
```

**Adjustments:**

- Add `paths = ["{package_name}", "tests"]` to explicitly scope scanning.
- For Django projects, add `"*/migrations/"`, `"*/admin.py"` to `exclude`.
- For projects with many false positives, prefer adding specific names to `ignore_names`
  rather than raising `min_confidence` -- this keeps detection sensitive while silencing
  known framework patterns.
