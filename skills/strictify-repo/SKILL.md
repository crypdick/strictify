---
name: strictify-repo
description: This skill should be used when the user asks to "strictify a repo", "add code quality enforcement", "make this repo strict", "add pre-commit hooks", "add type checking", "enforce code quality", "set up linting", or runs the /strictify-repo command.
---

# Strictify Repo

## Overview

This skill enforces taste programmatically across 21 categories of Python code quality. It analyzes an existing repository (or bootstraps a new one), proposes strict-but-pragmatic defaults across static analysis, type safety, testing, architecture, and ongoing enforcement, then applies approved changes. Every rule exists because it improves code quality, not because a linter supports it.

The approach is inspired by the "AI Is Forcing Us to Write Good Code" thesis and OpenAI's "Harness Engineering" insight: AI agents amplify whatever quality level a codebase already has. The only guardrails are the ones that get set and enforced. The tooling, abstractions, and feedback loops that keep a codebase coherent are the primary leverage point. Agent legibility -- making code navigable by both humans and AI agents -- is a first-class goal alongside human readability.

## Philosophy

- **Enforce taste, not arbitrary strictness** -- every rule exists because it improves code quality
- **Bias for strict, but check in** -- propose aggressive defaults, let the user veto
- **Self-reinforcing** -- hookify rules capture new taste preferences during normal work
- **Parse, don't validate** -- coerce at the boundary, carry proof through types
- **Agent legibility** -- make code navigable by both humans and AI agents
- **Detect and fill gaps** -- works on both existing and new projects, merging strictness into whatever is already there

## Phase 1: Analyze

Scan the target repo to understand its current state. Check all of the following:

- [ ] **pyproject.toml** -- existence and current tool configs (ruff, mypy, pytest, coverage, vulture sections)
- [ ] **.pre-commit-config.yaml** -- existence and current hooks
- [ ] **Package layout** -- `src/` layout vs flat layout; identify the package name
- [ ] **Python version** -- from `pyproject.toml` `requires-python`, `.python-version`, or `python3 --version`
- [ ] **Package manager** -- uv (`uv.lock`), poetry (`poetry.lock`), pip (`requirements.txt`)
- [ ] **Beartype** -- already a dependency?
- [ ] **Test infrastructure** -- pytest config, test directory, coverage config
- [ ] **`__init__.py` contents** -- identify insertion point for beartype
- [ ] **Domain structure** -- directories, modules, apparent layers (for architectural analysis)
- [ ] **Documentation state** -- README, `docs/`, inline comments quality

## Phase 2: Propose

Present findings grouped by the 6 category groups below. For each category, show: **current state -> proposed change**. Ask the user to veto any categories they do not want. Default is to apply everything -- the user opts OUT, not in.

### Static Analysis & Type Safety (categories 1-6)

1. **Pre-commit framework** -- install if missing, add missing hooks. Read `references/pre-commit-config.md` for the full template.
2. **Ruff** -- lint rules (`E`, `W`, `F`, `I`, `B`, `UP`, `C4`, `SIM`, `RUF`) and format config. Read `references/pyproject-strict.md` for exact settings.
3. **mypy** -- `strict = true` with pragmatic exceptions for the project's frameworks. Read `references/pyproject-strict.md` for strict mypy config and framework overrides.
4. **Beartype** -- add dependency, insert `beartype_this_package()` in package `__init__.py`. Read `references/beartype-setup.md` for integration patterns and common issues.
5. **Semantic typing** -- hookify rule nudging toward `NewType`/`TypeAlias` for domain concepts (user IDs, amounts, slugs). Detects bare primitives used for domain values.
6. **Parse-don't-validate** -- hookify rule encouraging boundary parsing with constrained types (Pydantic models, frozen dataclasses, `NewType`) instead of scattered validation. Coerce at the boundary, carry proof through types.

### Code Health (categories 7-10)

7. **Vulture** -- dead code detection with sensible ignore list. Read `references/pyproject-strict.md` for `min_confidence` and ignore settings.
8. **Xenon** -- cyclomatic complexity ceiling (max-average C, max-modules C, max-absolute C). Read `references/pre-commit-config.md` for xenon hook config.
9. **Pyupgrade + flynt** -- modernize syntax to the project's target Python version. Automates f-string conversion and syntax upgrades.
10. **Structured logging** -- detect unstructured logging patterns (string concatenation, %-formatting, f-strings in log calls) and nudge toward structured `logger.info("message", key=value)` style.

### Testing & Coverage (categories 11-12)

11. **Coverage enforcement** -- `fail_under = 100`. Coverage report as explicit todo list. Curated `exclude_lines` for `TYPE_CHECKING`, `@abstractmethod`, `__repr__`, and other pragmatic exclusions. Read `references/pyproject-strict.md` for the full exclusion list.
12. **Fast test infrastructure** -- pytest-xdist parallel execution, test timeouts, `--failed-first` for fast feedback. Read `references/pyproject-strict.md` for pytest `addopts` config.

### Architecture & Organization (categories 13-15)

13. **Filesystem discipline** -- file length limits (400 lines). Hookify rule warning on `utils.py`/`helpers.py`/`misc.py` creation. The problem is not shared code -- it is anonymous shared code. If a shared utility is needed, name it after what it does.
14. **Architectural layer enforcement** -- analyze the project's domain structure and propose dependency direction rules. For a Django project: models -> services -> views -> urls. For a CLI tool: parsing -> domain -> output. For a data pipeline: extract -> transform -> load. Figure out the appropriate layers for the target project, create custom lint rules enforcing valid dependency edges, and document the architecture in `docs/ARCHITECTURE.md`. Keep constraints lightweight for small projects, more rigid for larger ones.
15. **Quality grades** -- create `docs/QUALITY.md` scorecard grading each module/domain on coverage, type safety, complexity, and test health. Assess the current state, produce initial grades, and include guidance on how to maintain and update the scorecard over time.

### Environment & Infrastructure (categories 16-17)

16. **Ephemeral environment** -- if uv detected, ensure `uv run` works as single-command entry. Add bootstrap script or documentation as needed.
17. **Per-worktree isolation** -- analyze what isolation means for the specific project (configurable ports, separate DB names, isolated caches). For simple projects this may just be confirming `uv run` works from any worktree. For complex ones it may involve environment variable templating or a dev setup script.

### Ongoing Enforcement (categories 18-21)

18. **Custom hooks** -- exception handling (`check_exception_handling.py`), print/logging bans (`check_print_statements.py`), timeless comments (`check_timeless_comments.py`), future annotations (`fix_future_annotations.py`). Read each script from `scripts/` to understand behavior and adapt to the target repo.
19. **Hygiene hooks** -- trailing whitespace, end-of-file-fixer, large files, merge conflicts, debug statements, private key detection. Standard pre-commit hooks from the pre-commit-hooks repository.
20. **Doc gardening** -- detect stale documentation that does not reflect actual code behavior. Set up infrastructure appropriate to the project's maturity: a pre-commit hook, a CI job, or guidance for a recurring agent task that scans for drift and opens fix-up PRs.
21. **Taste enforcer** -- hookify rule that captures ongoing user preferences. When the user expresses a coding preference, determine whether it can be codified as a pre-commit hook script, a hookify rule, or a pyproject.toml setting, then create or update the enforcement mechanism.

## Phase 3: Apply

For each approved category, perform the following. Read the referenced files before writing any config.

### Configuration merging

- **Merge into `pyproject.toml`** -- read `references/pyproject-strict.md` for strict tool configurations. Merge sections: never remove existing settings, only add or tighten. Create `pyproject.toml` if it does not exist.
- **Merge into `.pre-commit-config.yaml`** -- read `references/pre-commit-config.md` for the complete template. Add missing repos and hooks. Create the file if it does not exist.

### Scripts and assets

- **Copy and adapt scripts** -- read each script from `scripts/` (check_exception_handling.py, check_print_statements.py, check_file_length.py, check_timeless_comments.py, fix_future_annotations.py). Adapt paths and package names to the target repo. Write to `scripts/pre_commit_hooks/` in the target repo.
- **Beartype integration** -- read `references/beartype-setup.md`. Modify the package `__init__.py` to insert `beartype_this_package()`.
- **Hookify rules** -- copy from `assets/` (taste-enforcer, no-junk-drawers, parse-dont-validate, semantic-types) to the target repo's `.claude/` directory.

### Dev dependencies

Detect the package manager and run the appropriate install command:

- **uv**: `uv add --dev ruff mypy beartype vulture pytest pytest-xdist pytest-cov pytest-timeout pytest-asyncio xenon pyupgrade flynt pre-commit`
- **pip**: `pip install` equivalent
- **poetry**: `poetry add --group dev` equivalent

### Infrastructure setup

- Run `pre-commit install` to activate hooks.
- **Architecture**: analyze domain structure, create `docs/ARCHITECTURE.md` with layer definitions and dependency rules.
- **Quality scorecard**: create `docs/QUALITY.md` with initial grades per module.
- **Doc gardening**: set up stale-docs detection appropriate to project maturity.
- **Per-worktree**: configure if applicable (ports, DBs, caches).

## Conflict Handling

When existing configuration already exists:

- **Merge-up** -- read existing config, add missing strict settings, tighten existing ones
- **Never remove** user settings -- only add or tighten
- **Present diff** -- show current state -> proposed change for every modification
- **User veto** -- the user can reject any category before application
- **Bias strict** -- default is to apply everything; the user opts out, not in

## Resources

Detailed configs, scripts, and assets live in the skill's bundled resources. Read these before writing any configuration to the target repo.

### Reference Files

- **`references/pyproject-strict.md`** -- strict tool configurations for ruff, mypy, pytest, coverage, and vulture sections in pyproject.toml
- **`references/pre-commit-config.md`** -- complete .pre-commit-config.yaml template with all hook repos and local hook definitions
- **`references/beartype-setup.md`** -- beartype integration guide: `beartype_this_package()` snippet, `BeartypeConf` options, common issues, and install commands per package manager

### Scripts

Custom pre-commit hook scripts in `scripts/`. All scripts accept filenames as arguments, report violations as `{file}:{line}: {message} -- {remediation}` (agent-readable), exit nonzero on failure, and support `# allow: {hook-name}` per-line exemptions.

- **`scripts/check_exception_handling.py`** -- detects bare `except:`, swallowed exceptions, exception handlers with only `pass`
- **`scripts/check_print_statements.py`** -- bans `print()` in production code, detects unstructured logging patterns
- **`scripts/check_file_length.py`** -- enforces max 400 logical lines per file
- **`scripts/check_timeless_comments.py`** -- detects temporal keywords in comments (legacy, new, old, TODO, FIXME, HACK, temporary)
- **`scripts/fix_future_annotations.py`** -- ensures `from __future__ import annotations` is placed correctly; runs as a fixer

### Assets

Hookify rule files in `assets/`. Copy these to the target repo's `.claude/` directory.

- **`assets/hookify.taste-enforcer.local.md`** -- captures user taste preferences and codifies them as hooks, rules, or config
- **`assets/hookify.no-junk-drawers.local.md`** -- warns on junk-drawer module names (utils.py, helpers.py, misc.py)
- **`assets/hookify.parse-dont-validate.local.md`** -- nudges toward boundary parsing with constrained types
- **`assets/hookify.semantic-types.local.md`** -- detects bare primitives for domain concepts, nudges toward NewType
