# Strict .pre-commit-config.yaml Reference

Complete template for `.pre-commit-config.yaml`. The agent should copy this file into the
target repo and replace `{package_name}` with the actual Python package directory name and
`{python_version}` with the target Python minor version (e.g., `13` for Python 3.13).

Run all hooks with: `uvx pre-commit run --all-files`

---

## Placeholders

| Placeholder          | Example         | Description                                      |
|----------------------|-----------------|--------------------------------------------------|
| `{package_name}`     | `my_project`    | The importable package directory name             |
| `{python_version}`   | `13`            | Python minor version number (for pyupgrade)       |

---

## Complete Template

```yaml
# Run with: uvx pre-commit run --all-files
# Install hooks: uvx pre-commit install

repos:
  # ──────────────────────────────────────────────────────────────────────
  # Standard file hygiene hooks
  # These catch whitespace issues, broken configs, merge conflicts, and
  # accidentally committed secrets or large binaries. Cheap and fast --
  # always include these.
  # ──────────────────────────────────────────────────────────────────────
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: debug-statements
      - id: detect-private-key
      - id: check-added-large-files

  # ──────────────────────────────────────────────────────────────────────
  # Ruff -- linting and formatting
  # Replaces flake8, isort, pyupgrade (partially), and black.
  # --fix auto-corrects safe issues (import sorting, unused imports).
  # --quiet suppresses "all checks passed" noise in pre-commit output.
  # Configuration lives in pyproject.toml [tool.ruff].
  # ──────────────────────────────────────────────────────────────────────
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.12
    hooks:
      - id: ruff-check
        args: [--fix, --quiet]
      - id: ruff-format
        args: [--quiet]

  # ──────────────────────────────────────────────────────────────────────
  # Vulture -- dead code detection
  # Finds unused functions, variables, imports, and classes.
  # Configuration (min_confidence, exclude, ignore_names) lives in
  # pyproject.toml [tool.vulture].
  # ──────────────────────────────────────────────────────────────────────
  - repo: https://github.com/jendrikseipp/vulture
    rev: 'v2.14'
    hooks:
      - id: vulture
        args: [., --min-confidence, "80"]

  # ──────────────────────────────────────────────────────────────────────
  # pyupgrade -- modernize Python syntax
  # Automatically rewrites old-style constructs to use newer Python
  # features (e.g., dict comprehensions, f-strings, PEP 604 unions).
  # Replace {python_version} with the target minor version (e.g., 13).
  # ──────────────────────────────────────────────────────────────────────
  - repo: https://github.com/asottile/pyupgrade
    rev: v3.21.2
    hooks:
      - id: pyupgrade
        args: [--py3{python_version}-plus]

  # ──────────────────────────────────────────────────────────────────────
  # flynt -- convert .format() and % formatting to f-strings
  # Complements pyupgrade's f-string conversion with more aggressive
  # rewriting. Safe to run -- only converts when the result is equivalent.
  # ──────────────────────────────────────────────────────────────────────
  - repo: https://github.com/ikamensh/flynt/
    rev: '1.0.6'
    hooks:
      - id: flynt

  # ──────────────────────────────────────────────────────────────────────
  # Local hooks
  # These run project-specific checks using scripts and tools installed
  # in the project's virtual environment (via uv). They are ordered from
  # fastest to slowest, with pytest always last.
  # ──────────────────────────────────────────────────────────────────────
  - repo: local
    hooks:
      # ── Complexity gate ──────────────────────────────────────────────
      # xenon enforces maximum cyclomatic complexity at the module,
      # function, and average level. Grade C (max-absolute C) allows
      # up to complexity 25 per function -- strict but realistic.
      # Tighten to B for greenfield projects.
      - id: xenon
        name: xenon complexity check
        entry: uv run xenon --max-average C --max-modules C --max-absolute C {package_name}/
        language: system
        pass_filenames: false
        always_run: true

      # ── Type checking ───────────────────────────────────────────────
      # mypy runs in strict mode (configured in pyproject.toml).
      # pass_filenames is false because mypy needs to see the whole
      # package for cross-module type inference.
      - id: mypy
        name: mypy
        entry: uv run mypy {package_name}/
        language: system
        pass_filenames: false
        always_run: true

      # ── Custom lint hooks ───────────────────────────────────────────
      # These scripts live in scripts/pre_commit_hooks/ and enforce
      # project-specific coding standards. Each script should:
      #   - Accept file paths as arguments
      #   - Exit 0 on success, non-zero on failure
      #   - Print clear error messages with file:line references

      # Catches bare except, overly broad exception handlers (Exception),
      # and swallowed exceptions (except: pass).
      - id: check-exception-handling
        name: Check Exception Handling
        entry: python scripts/pre_commit_hooks/check_exception_handling.py
        language: system
        types: [python]

      # Catches print() statements that should be logger calls.
      # Exclude scripts/ since CLI scripts legitimately use print().
      - id: check-print-statements
        name: Check Print Statements
        entry: python scripts/pre_commit_hooks/check_print_statements.py
        language: system
        types: [python]

      # Catches time-anchored comments ("TODO: fix by Q3 2024",
      # "temporary workaround added 2023-01-15") that rot over time.
      - id: check-timeless-comments
        name: Check Timeless Comments
        entry: python scripts/pre_commit_hooks/check_timeless_comments.py
        language: system
        types: [python]

      # Enforces maximum file length to prevent god-modules.
      # Default limit is typically 500 lines; configure in the script.
      - id: check-file-length
        name: Check File Length
        entry: python scripts/pre_commit_hooks/check_file_length.py
        language: system
        types: [python]

      # Ensures `from __future__ import annotations` is present at
      # the top of every Python file for PEP 563 deferred evaluation.
      # This enables modern type syntax (X | Y) on older Pythons and
      # avoids circular import issues in type annotations.
      - id: fix-future-annotations
        name: Fix Future Annotations
        entry: python scripts/pre_commit_hooks/fix_future_annotations.py
        language: system
        types: [python]

      # ── Test suite ──────────────────────────────────────────────────
      # MUST be the last hook. Runs the full test suite after all other
      # checks pass, so developers don't waste time waiting for tests
      # if there are lint/type errors.
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        pass_filenames: false
        always_run: true
```

---

## Notes for the Agent

1. **Hook ordering matters.** Cheap, fast hooks (whitespace, YAML checks) run first.
   Expensive hooks (mypy, pytest) run last. This minimizes wasted time when trivial
   issues are present.

2. **Replace placeholders before committing.** Search for `{package_name}` and
   `{python_version}` and substitute the actual values.

3. **The custom hook scripts must exist.** The agent should verify that
   `scripts/pre_commit_hooks/` contains the referenced scripts or create them as part
   of the strictify process. Missing scripts will cause pre-commit to fail.

4. **vulture args vs pyproject.toml.** The `args: [., --min-confidence, "80"]` in the
   hook definition overrides any `min_confidence` in pyproject.toml. Keep them in sync
   or remove the args from the hook to let pyproject.toml be the single source of truth.

5. **Tag versions.** Update `rev` values periodically. The versions in this template are
   current as of early 2025. Use `uvx pre-commit autoupdate` to bump them.

6. **Django projects:** Add `--settings=myproject.settings.test` to the mypy entry if
   Django settings are required for type checking.

7. **Monorepos:** If the project has multiple packages, duplicate the xenon and mypy
   hooks for each package directory, or use a wrapper script that iterates over them.
