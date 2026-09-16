# Strict pyproject.toml reference

Use these configs for `pyproject.toml`. Adapt only where the notes or target repo
require it; replace `{package_name}` with the production package.

## [tool.ruff] -- Linting and formatting

Default line length is 110; use 88 for Black-compatible projects. Keep the curated
selection: no `ALL`, top-level preview, unsafe fixes, or formatter-conflicting
`COM`, `Q`, or `ISC` families. Lint-scoped preview with
`explicit-preview-rules = true` enables only exact preview codes. Formatter
preview stays disabled.

Selected `D` and `DOC` rules detect empty or stale docstrings without requiring
filler documentation. Do not enable either whole family. For `ANN401`, parse
untrusted input into domain models, `TypedDict`, `Protocol`, or narrowed `object`.
Reserve narrow exemptions for boundaries that cannot be typed honestly.

`E501` defers to formatting; `TRY003` permits simple domain errors.

```toml
[tool.ruff]
line-length = 110

[tool.ruff.lint]
preview = true
explicit-preview-rules = true
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
    "DOC102",
    "DOC202",
    "DOC403",
    "DTZ",
    "E",
    "ERA",
    "EXE",
    "F",
    "FA",
    "FBT",
    "FURB101",
    "FURB103",
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
    "ISC004",
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
    "PLR1702",
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

Ruff owns complexity through `C901`. Default: 15; use 10 for new projects, or
20 only for unavoidable data-pipeline branching with an explanatory comment.

```toml
[tool.ruff.lint.mccabe]
max-complexity = 15
```

### Per-file ignores

Ruff owns print/logging checks and misplaced future imports (`F404`). The patterns
below permit CLI/test/tool output and relax test/script complexity. Logging checks
still apply. Use narrow `# noqa: T201` or specific `G` codes elsewhere.

For Django, add `"migrations/**/*.py" = ["E501", "RUF012"]`. For FastAPI,
consider `"**/routers/**/*.py" = ["B008"]` for `Depends()` defaults.

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN", "ARG", "C901", "FBT", "F841", "PLR0912", "PLR0913", "PLR0915", "S101", "SLF", "T201"]
"scripts/**/*.py" = ["C901", "PLR0912", "PLR0915", "S603", "S607", "T20"]
"test_*.py" = ["T201"]
"**/tools/**/*.py" = ["T201"]
"**/_tools/**/*.py" = ["T201"]
"**/scripts/**/*.py" = ["T201"]
"**/tests/**/*.py" = ["T201"]
"**/{cli,main,__main__}.py" = ["T201"]
```

## [tool.mypy] -- Static type checking

Run strict mypy before adding exceptions. Check framework plugins and stubs first;
scope further suppressions to affected modules and error codes. Do not disable
correctness checks such as `attr-defined`, `override`, or `call-arg` project-wide.

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

Use this override only if the project intentionally excludes tests. Fixtures and
mocks alone do not justify it. Adapt module names to the test layout.

```toml
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_untyped_calls = false
check_untyped_defs = false
ignore_errors = true
```

For missing third-party stubs, scope `ignore_missing_imports = true` to the affected
module, such as `ortools.*`. Never enable it globally.

## [tool.pytest.ini_options] -- Test runner

- Omit `asyncio_mode` when the project has no async code.
- Remove `-n auto` for tests sharing state that prevents parallel execution.
- `--cov={package_name}` starts collection; report flags alone do not. Use
  `uv run pytest --no-cov` for a quick run without coverage.
- Default timeout: 20 seconds. Use 60 for service integration tests or
  `@pytest.mark.timeout(60)` for individual tests. Choose `signal` only for
  Unix-only projects where thread timeouts are unreliable.

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
addopts = "--no-header -n auto -q --durations=5 --durations-min=1.0 --cov={package_name} --cov-report=term-missing --cov-report=html --failed-first"
timeout = 20
timeout_method = "thread"
```

For Django, set `DJANGO_SETTINGS_MODULE` and consider `--reuse-db`. Data pipelines
may need `timeout = 120` and serial execution for shared heavyweight fixtures.

## [tool.coverage] -- Code coverage

Collect branch coverage and target 100%. On adoption, start at measured coverage
rounded down, then raise the threshold as coverage improves. Put `fail_under`
and `skip_empty` under `[tool.coverage.report]`; they are not run settings.
Use `exclude_also` to preserve built-in exclusions.

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

To exclude test infrastructure, add
`omit = ["*/tests/*", "*/test_*.py", "*/__pycache__/*", "*/conftest.py"]` under
`[tool.coverage.run]`. For Django, consider `"*/migrations/*"` and `"*/admin.py"`.
`exclude_also` matches source text, not filenames. Test CLI behavior through
subprocesses or a public callable.

## [tool.vulture] -- Dead code detection

Start at confidence 80; use 60 for more candidates or 90 for heavy metaprogramming.
Prefer specific `ignore_names` for known framework callbacks such as `on_*` or
`watch_*` before raising confidence.

```toml
[tool.vulture]
min_confidence = 80
exclude = [".venv/"]
```

Set `paths = ["{package_name}", "tests"]` for explicit scope. Exclude generated
framework files, such as Django migrations and `admin.py`, where needed.

## [tool.deptry] -- Dependency integrity

Use authoritative dependency metadata. Skip ad hoc environments, vendored trees,
and plugins whose host intentionally supplies imports. Deptry checks missing,
unused, transitive, and development-only dependencies in production imports.
Keep exceptions narrow and rule-specific.

```toml
[tool.deptry]
extend_exclude = ["scripts/prek_hooks"]

# Add only when a project.optional-dependencies group contains development tools.
# optional_dependencies_dev_groups = ["dev"]
```

Set `optional_dependencies_dev_groups` when development tools live in
`[project.optional-dependencies]`; `[dependency-groups]` needs no such setting.
Exclude generated or host-loaded code only after confirming deptry cannot model it.

## [tool.uv] -- Dependency cooldown

For uv-managed repos, delay releases published within three days. Requires
uv >= 0.9.17. The cutoff becomes a timestamp in `uv.lock` and advances when the
lockfile is invalidated, such as with `--upgrade`, avoiding daily lockfile churn.
A cooldown gives maintainers time to withdraw bad releases; it does not prove safety.
For an urgent fix, override that package with `exclude-newer-package` using a
timestamp, shorter duration, or `false`, rather than relaxing the global limit.

```toml
[tool.uv]
# Delay adoption of fresh releases; this is not a guarantee of dependency safety.
exclude-newer = "3 days"
```
