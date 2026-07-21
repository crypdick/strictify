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
- The rule set is curated and versioned deliberately. Do not enable `ALL`, global preview
  mode, or unsafe fixes: review new rule families and fix safety before opting into them.
- The `select` list covers the highest-signal anti-slop rule families for
  agent-managed repos: builtin shadowing (`A`), explicit annotations (`ANN`),
  unused arguments (`ARG`), async footguns (`ASYNC`), blind exceptions (`BLE`),
  bare-tuple comma bugs (`COM818`), naive datetimes (`DTZ`), commented-out code
  (`ERA`), executable-script hygiene (`EXE`), future annotations (`FA`),
  boolean-trap APIs (`FBT`), targeted refurb checks (`FURB`), logging hygiene
  (`G`, `LOG`), package initialization (`INP`), naming (`N`),
  performance/readability (`PERF`), precise
  suppressions (`PGH`), cleanup rules (`PIE`, `RET`, `RSE`), targeted Pylint
  checks (`PLC`, `PLE`, `PLW`, selected `PLR`), pytest style (`PT`), pathlib
  (`PTH`), security footguns (`S`), private-member access (`SLF`), slots on
  builtin subclasses (`SLOT`), debugger/print bans (`T10`, `T20`),
  type-checking imports (`TC`), import boundaries (`TID`), targeted exception
  rules (`TRY004`, `TRY201`, `TRY203`, `TRY300`, `TRY400`, `TRY401`), and
  Python-version traps (`YTT`).
- `C90` enables Ruff's mccabe `C901` cyclomatic-complexity check, so complexity
  enforcement stays inside the normal Ruff pass.
- Selected `D` rules catch empty or structurally misleading docstrings without
  requiring docstrings everywhere. Do not enable broad `D` or `DOC` by default:
  agents respond to missing-docstring gates by writing low-value filler.
- `ANN401` is intentionally strict. Prefer parsing untrusted input at boundaries
  into domain models, `TypedDict`s, `Protocol`s, or `object` plus narrowing. Use
  a narrow `# noqa: ANN401` only when a boundary is genuinely dynamic and cannot
  be typed honestly.
- This supports the parse-don't-validate convention: coerce unstructured data
  into constrained types at system boundaries so downstream code carries stronger
  type evidence instead of repeatedly re-validating raw `Any` blobs. See
  <https://www.ricardodecal.com/opinions/parse-don-t-validate-in-python/>.
- Do not enable broad `COM`, `Q`, or formatter-conflicting `ISC` settings while
  using Ruff format. The selected comma and implicit-concat rules are bug-shaped,
  not formatting policy.
- `ignore = ["E501", "TRY003"]` defers line-length enforcement to the formatter
  and avoids exception-class ceremony for simple domain errors.

```toml
[tool.ruff]
line-length = 110

[tool.ruff.lint]
select = [
    "A",
    "ANN001",
    "ANN002",
    "ANN003",
    "ANN201",
    "ANN202",
    "ANN204",
    "ANN205",
    "ANN206",
    "ANN401",
    "ARG",
    "ASYNC",
    "B",
    "BLE",
    "C4",
    "COM818",
    "C90",
    "D402",
    "D414",
    "D418",
    "D419",
    "DTZ",
    "E",
    "ERA",
    "EXE",
    "F",
    "FA",
    "FBT",
    "FURB122",
    "FURB129",
    "FURB132",
    "FURB157",
    "FURB161",
    "FURB162",
    "FURB168",
    "FURB169",
    "FURB171",
    "FURB177",
    "FURB181",
    "FURB188",
    "G",
    "I",
    "INP",
    "LOG",
    "N",
    "PERF",
    "PGH",
    "PIE",
    "PLC",
    "PLE",
    "PLR0124",
    "PLR0133",
    "PLR0206",
    "PLR0911",
    "PLR0912",
    "PLR0913",
    "PLR0915",
    "PLR1704",
    "PLR1711",
    "PLR1714",
    "PLR1716",
    "PLR1722",
    "PLR1733",
    "PLR1736",
    "PLR5501",
    "PLW",
    "PT",
    "PTH",
    "RET",
    "RSE",
    "RUF",
    "S",
    "SIM",
    "SLF",
    "SLOT",
    "T10",
    "T20",
    "TC",
    "TID",
    "TRY004",
    "TRY201",
    "TRY203",
    "TRY300",
    "TRY400",
    "TRY401",
    "UP",
    "W",
    "YTT",
]
ignore = [
    "E501",
    "TRY003",
]

[tool.ruff.format]
quote-style = "double"
```

### Complexity

- `max-complexity = 15` is lenient enough for real-world code but catches genuinely
  tangled functions. Lower to 10 for new greenfield projects. Raise to 20 only for
  data-pipeline code with unavoidable branching (and add a comment explaining why).
  This backs Ruff's `C901` rule.

```toml
[tool.ruff.lint.mccabe]
max-complexity = 15
```

### Per-file ignores

- Test files commonly use unused variables (captured return values), high complexity
  (parameterized setup), many arguments (fixtures), asserts, private-member access,
  and boolean positional helpers. Suppress these categories wholesale for `tests/`.
- Scripts similarly get complexity exemptions since they are often one-shot utilities.
- For Django projects, add `"migrations/**/*.py" = ["E501", "RUF012"]` to suppress
  auto-generated migration noise.
- For FastAPI projects, consider adding `"**/routers/**/*.py" = ["B008"]` to allow
  `Depends()` default arguments.

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN", "ARG", "C901", "FBT", "F841", "PLR0912", "PLR0913", "PLR0915", "S101", "SLF"]
"scripts/**/*.py" = ["C901", "PLR0912", "PLR0915", "S603", "S607", "T20"]
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
- `--cov={package_name}` activates pytest-cov and restricts measurement to production
  code. Reporting flags alone do not start coverage collection. Developers can still use
  `uv run pytest --no-cov` for a faster one-off run.
- `--cov-report=term-missing --cov-report=html` provides both terminal and browsable
  coverage output.
- `timeout = 20` catches hanging tests early. Increase to 60 for integration tests that
  hit real services, or add `@pytest.mark.timeout(60)` on individual slow tests.
- `timeout_method = "thread"` works with both sync and async code. Use `"signal"` only
  on Unix-only projects where thread-based timeout is unreliable.

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
addopts = "--no-header -n auto -q --durations=5 --durations-min=1.0 --cov={package_name} --cov-report=term-missing --cov-report=html --failed-first"
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

- `branch = true` measures decision outcomes as well as executed lines. Without it, a
  conditional can count as covered even when only one branch was exercised.
- `fail_under = 100` is the strict target. The agent should set this to the project's
  current coverage percentage rounded down to the nearest integer on first adoption,
  then ratchet it up over time. Setting it to 100 immediately on a legacy codebase will
  block all commits.
- `skip_empty = true` excludes `__init__.py` files and other empty modules from the
  coverage denominator.
- `fail_under` and `skip_empty` are report settings, not run settings. Putting them under
  `[tool.coverage.run]` makes Coverage.py ignore the intended enforcement.
- The `exclude_also` patterns cover common boilerplate that is either untestable or
  tested implicitly (abstract methods, `TYPE_CHECKING` blocks, `__repr__` methods) while
  preserving Coverage.py's built-in exclusions.

```toml
[tool.coverage.run]
branch = true
source = ["{package_name}"]

[tool.coverage.report]
fail_under = 100
skip_empty = true
exclude_also = [
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

- Add `omit = ["*/tests/*", "*/test_*.py", "*/__pycache__/*", "*/conftest.py"]` to
  `[tool.coverage.run]` to exclude test infrastructure from the coverage denominator.
- For Django, add `"*/migrations/*"` and `"*/admin.py"` to `omit`.
- For CLI tools, add `"*/cli.py"` or `"*/__main__.py"` to `exclude_also` patterns if
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

---

## [tool.deptry] -- Dependency Integrity

Use deptry only when the repo has authoritative dependency metadata in `pyproject.toml`
or another supported format. Skip it for scripts with ad hoc environments, vendored
trees, and plugin hosts whose imports are intentionally supplied by the host process.

Deptry catches four distinct declaration failures:

- imported packages missing from declared dependencies;
- declared runtime dependencies that production code does not use;
- imports that work only because another dependency brings them in transitively;
- development dependencies imported by production code.

Keep exceptions narrow and rule-specific. Do not globally disable missing- or
transitive-dependency checks merely because one framework has dynamic imports.

```toml
[tool.deptry]
extend_exclude = ["scripts/prek_hooks"]

# Add only when a project.optional-dependencies group contains development tools.
# optional_dependencies_dev_groups = ["dev"]
```

**Adjustments:**

- Set `optional_dependencies_dev_groups` to the target repo's actual group names when
  development tools live under `[project.optional-dependencies]`. Standard
  `[dependency-groups]` entries are recognized as development dependencies directly.
- Add generated code, migrations, or host-loaded plugin modules to `extend_exclude`
  only after confirming deptry cannot model the import boundary accurately.
