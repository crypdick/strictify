---
name: strictify
description: This skill should be used when the user asks to "strictify a repo", "add code quality enforcement", "make this repo strict", "add pre-commit hooks", "add type checking", "enforce code quality", "set up linting", or runs the /strictify command.
---

# Strictify

## Overview

This skill enforces taste programmatically across 22 categories of Python code quality. It analyzes an existing repository (or bootstraps a new one), proposes strict-but-pragmatic defaults across static analysis, type safety, testing, architecture, and ongoing enforcement, then applies approved changes. Every rule exists because it improves code quality, not because a linter supports it.

The approach is inspired by the "AI Is Forcing Us to Write Good Code" thesis and OpenAI's "Harness Engineering" insight: AI agents amplify whatever quality level a codebase already has. The only guardrails are the ones that get set and enforced. The tooling, abstractions, and feedback loops that keep a codebase coherent are the primary leverage point. Agent legibility -- making code navigable by both humans and AI agents -- is a first-class goal alongside human readability.

## Philosophy

- **Enforce taste, not arbitrary strictness** -- every rule exists because it improves code quality
- **Fit before force** -- these categories are a menu of good patterns, not a checklist to apply wholesale. Not every pattern suits every repo, so first read the target and judge whether each directive even makes sense for its size, stack, domain, and maturity; skip or soften what does not earn its place (no architectural-layer lint rules for a 200-line script, no third-party-call caching for an offline library, no per-worktree isolation for a repo with no shared services). Then bias strict on what remains.
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

First, use the Phase 1 analysis to filter to the categories that actually fit this repo (see *Fit before force*), setting aside the rest with a brief reason. Then present the remaining findings grouped by the 6 category groups below. For each category, show: **current state -> proposed change**. Ask the user to veto any categories they do not want. Within the relevant set, default is to apply everything -- the user opts OUT, not in.

### Static Analysis & Type Safety (categories 1-6)

1. **Pre-commit framework** -- install if missing, add missing hooks. Read `references/pre-commit-config.md` for the full template.
2. **Ruff** -- anti-slop lint rules (core `E`/`W`/`F`/`I`, `B`, `UP`, `C4`, `SIM`, `RUF`, complexity `C90`, selected annotation/docstring checks, plus high-signal families for async, exceptions, logging, performance, security, pytest, pathlib, suppressions, private access, debugger/print bans, executable scripts, and import/package boundaries) and format config. Read `references/pyproject-strict.md` for exact settings.
3. **mypy** -- `strict = true` with pragmatic exceptions for the project's frameworks. Read `references/pyproject-strict.md` for strict mypy config and framework overrides.
4. **Beartype** -- add dependency, insert `beartype_this_package()` in package `__init__.py`. Read `references/beartype-setup.md` for integration patterns and common issues.
5. **Semantic typing** -- recorded as a principle in the `CONVENTIONS.md` design doc (Phase 3): give domain concepts (user IDs, amounts, slugs) a distinct `NewType`/`TypeAlias` instead of a bare primitive. Deciding *which* primitives carry domain meaning is a judgment call, so it lives in the conventions doc for the agent to apply, not a regex hook.
6. **Parse-don't-validate** -- recorded as a principle in the `CONVENTIONS.md` design doc (Phase 3): coerce unstructured data into constrained types (Pydantic models, frozen dataclasses, `NewType`) at the boundary and carry proof through types, instead of re-validating downstream. Includes the Pydantic-validator caveat -- a `@field_validator` that doesn't change the static type is a check-and-discard, not a parse.

### Code Health (categories 7-10)

7. **Vulture** -- dead code detection with sensible ignore list. Read `references/pyproject-strict.md` for `min_confidence` and ignore settings.
8. **Ruff C901** -- cyclomatic complexity ceiling through Ruff's mccabe rule (`C90` select plus `[tool.ruff.lint.mccabe] max-complexity`). Read `references/pyproject-strict.md` for config.
9. **Pyupgrade + flynt** -- modernize syntax to the project's target Python version. Automates f-string conversion and syntax upgrades.
10. **Structured logging** -- detect unstructured logging patterns (string concatenation, %-formatting, f-strings in log calls) and nudge toward structured `logger.info("message", key=value)` style.

### Testing & Coverage (categories 11-12)

11. **Coverage enforcement** -- `fail_under = 100`. Coverage report as explicit todo list. Curated `exclude_lines` for `TYPE_CHECKING`, `@abstractmethod`, `__repr__`, and other pragmatic exclusions. Read `references/pyproject-strict.md` for the full exclusion list.
12. **Fast test infrastructure** -- pytest-xdist parallel execution, test timeouts, `--failed-first` for fast feedback. Read `references/pyproject-strict.md` for pytest `addopts` config. Separately, *only if the tests make real third-party/external calls* (HTTP APIs, SDKs, network services -- the usual source of slow, flaky suites): propose a record-replay layer (`vcrpy`/`pytest-recording`, `respx` for httpx, or `responses` for requests) that records real responses once and replays them on later runs. A recorded response assumes the third party is a pure function of the request, so pair it with a CI job that re-runs the suite *without* the recordings after PR approval, to catch where that assumption breaks.

### Architecture & Organization (categories 13-16)

13. **Filesystem discipline** -- file length limits (400 lines). Hookify rule warning on `utils.py`/`helpers.py`/`misc.py` creation. The problem is not shared code -- it is anonymous shared code. If a shared utility is needed, name it after what it does.
14. **Architecture codemap** -- create `docs/ARCHITECTURE.md`: a short bird's-eye map that tells a newcomer (human or agent) *where* things live, not *how* they work. Include a one-paragraph statement of the problem the codebase solves, a codemap of the coarse-grained modules/packages and how they relate, and the load-bearing architectural invariants -- including things deliberately *absent* (e.g. "the domain layer never imports Django"). Name important files, modules, and types explicitly so they are greppable. Keep it short and do not link to specific lines (links rot); it is a mental model, not an index. This is the primary agent-legibility artifact -- valuable for every project regardless of size. Revisit it a couple of times a year rather than syncing it to every change.
15. **Architectural layer enforcement** -- analyze the project's domain structure and propose dependency-direction rules. For a Django project: models -> services -> views -> urls. For a CLI tool: parsing -> domain -> output. For a data pipeline: extract -> transform -> load. Figure out the appropriate layers for the target project, create custom lint rules enforcing valid dependency edges, and record the layers and their invariants in the `docs/ARCHITECTURE.md` codemap (category 14). Scale to project size: lightweight or no lint rules for small projects (the category-14 codemap still applies), more rigid for larger ones.
16. **Quality grades** -- create `docs/QUALITY.md` scorecard grading each module/domain on coverage, type safety, complexity, and test health. Assess the current state, produce initial grades, and include guidance on how to maintain and update the scorecard over time.

### Environment & Infrastructure (categories 17-18)

17. **Ephemeral environment** -- the goal is a *single command* that stands up a fresh, ready-to-work dev environment -- create a git worktree, copy local-only config (`.env`, credentials, editor settings), install dependencies, hand off to the agent -- fast enough (seconds, not minutes) to make concurrent agents in separate worktrees practical. Build the version that fits the target: for a uv project with no services, a thin `new-feature <name>` script wrapping `git worktree add` + `uv sync` + `.env` copy; for a heavier stack, whatever else it needs to boot. Adapt the essence (one command, ephemeral, automated) to the repo rather than shipping a fixed script.
18. **Per-worktree isolation** -- worktrees must not collide when several run at once. **The rule: any state at a fixed shared location must be keyed per-worktree** -- ports, database/schema names, caches on hardcoded paths (`/tmp/myapp-cache`, `~/.cache/myapp`), and shared service instances (redis db numbers, queue names). Derive each from the worktree (an offset or hash of its name) via environment variables, or concurrent worktrees clobber each other. The exception is content-addressed global caches (`~/.cache/uv`, pip wheels): keyed by content hash, so sharing them is safe -- leave them alone. A project with no shared state may just need `uv run` to work from any worktree; a complex one should template the isolating env vars into the category-17 setup command so isolation is automatic, not manual. With containers, isolation may mean per-worktree Docker compose project names or volumes.

### Ongoing Enforcement (categories 19-22)

19. **Custom hooks** -- exception handling (`check_exception_handling.py`), print/logging bans (`check_print_statements.py`), timeless comments (`check_timeless_comments.py`), future annotations (`fix_future_annotations.py`), and tests-verify-public-behaviour (`check_private_test_imports.py`, which forbids tests from importing leading-underscore first-party symbols so they exercise the public surface instead of internal shape). Read each script from `scripts/` to understand behavior and adapt to the target repo.
20. **Hygiene hooks** -- trailing whitespace, end-of-file-fixer, large files, merge conflicts, debug statements, private key detection, plus `detect-secrets` for entropy-based secret scanning. Standard pre-commit hooks from the pre-commit-hooks repo and `Yelp/detect-secrets`. **Out of scope:** personal/prod strings (internal hostnames, real usernames, prod URLs). Any mechanism for these either commits the pattern (defeating the point) or requires per-user config strictify cannot bootstrap -- users who care should add a local hook that reads patterns from a gitignored file.
21. **Doc gardening** -- detect stale documentation that does not reflect actual code behavior. Set up infrastructure appropriate to the project's maturity: a pre-commit hook, a CI job, or guidance for a recurring agent task that scans for drift and opens fix-up PRs. Pair with the *keep code and docs coupled* principle in the `CONVENTIONS.md` design doc (Phase 3): leave `NOTE:` back-pointers at code sites whose values are documented elsewhere, so the two don't drift.
22. **Taste enforcer** -- hookify rule that captures ongoing user preferences. When the user expresses a coding preference, determine whether it can be codified as a pre-commit hook script, a hookify rule, or a pyproject.toml setting, then create or update the enforcement mechanism.

## Phase 3: Apply

For each approved category, perform the following. Read the referenced files before writing any config.

### Configuration merging

- **Merge into `pyproject.toml`** -- read `references/pyproject-strict.md` for strict tool configurations. Merge sections: never remove existing settings, only add or tighten. Create `pyproject.toml` if it does not exist.
- **Merge into `.pre-commit-config.yaml`** -- read `references/pre-commit-config.md` for the complete template. Add missing repos and hooks. Create the file if it does not exist.

### Scripts and assets

- **Copy and adapt scripts** -- read each script from `scripts/` (check_exception_handling.py, check_print_statements.py, check_file_length.py, check_timeless_comments.py, check_private_test_imports.py, fix_future_annotations.py). Adapt paths and package names to the target repo. Write to `scripts/pre_commit_hooks/` in the target repo. `check_private_test_imports.py` auto-detects first-party packages from the target's layout, so it needs no per-repo edit (pass `--package` only to override).
- **Beartype integration** -- read `references/beartype-setup.md`. Modify the package `__init__.py` to insert `beartype_this_package()`.
- **Hookify rules** -- copy from `assets/` (taste-enforcer, no-junk-drawers) to the target repo's `.claude/` directory. Only these two are shipped as hooks: a prompt-keyword trigger and a filename match, both mechanical and low-false-positive. The judgment-based design principles that used to be hookify rules now live in the `CONVENTIONS.md` design doc (see *Infrastructure setup* below).
- **Design conventions doc** -- copy `assets/CONVENTIONS.md-EXAMPLE` to the target as `CONVENTIONS.md`, then adapt it: trim principles that do not fit, sharpen examples to use the repo's real types, add repo-specific conventions. It seeds judgment-based principles too nuanced for a regex hook -- composition over inheritance, parse-don't-validate, semantic types, and code/doc coupling. Append a pointer line to the repo's `CLAUDE.md`/`AGENTS.md` (e.g. "See `CONVENTIONS.md` for design principles") so agents load it. This is an agent-legibility artifact alongside `docs/ARCHITECTURE.md` and `docs/QUALITY.md`.

### Dev dependencies

Detect the package manager and run the appropriate install command:

- **uv**: `uv add --dev ruff mypy beartype vulture pytest pytest-xdist pytest-cov pytest-timeout pytest-asyncio pyupgrade flynt pre-commit`
- **pip**: `pip install` equivalent
- **poetry**: `poetry add --group dev` equivalent

### Infrastructure setup

- Run `pre-commit install` to activate hooks.
- **Architecture codemap**: create `docs/ARCHITECTURE.md` -- a short bird's-eye problem statement, a codemap of the coarse-grained modules and how they relate, and the load-bearing invariants (including deliberate absences). Name entities so they are greppable; do not link to specific lines.
- **Architectural layers**: if the project warrants it, add dependency-direction lint rules and record the layers in the codemap.
- **Quality scorecard**: create `docs/QUALITY.md` with initial grades per module.
- **Doc gardening**: set up stale-docs detection appropriate to project maturity; put `docs/ARCHITECTURE.md` on a "revisit a couple times a year" cadence rather than gating every change on it.
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
- **`scripts/check_private_test_imports.py`** -- forbids tests from importing leading-underscore first-party symbols; auto-detects first-party packages, supports `--package` overrides and a `# allow: private-test-imports` carve-out
- **`scripts/fix_future_annotations.py`** -- ensures `from __future__ import annotations` is placed correctly; runs as a fixer

### Assets

Files in `assets/`. Copy these to the target repo.

- **`assets/hookify.taste-enforcer.md`** -- hookify rule (prompt event) that captures user taste preferences and codifies them as hooks, rules, or config. Copy to `.claude/`.
- **`assets/hookify.no-junk-drawers.md`** -- hookify rule (file event) that warns on junk-drawer module names (utils.py, helpers.py, misc.py) by filename match. Copy to `.claude/`.
- **`assets/CONVENTIONS.md-EXAMPLE`** -- template for the `CONVENTIONS.md` design-conventions doc: judgment-based principles (composition over inheritance, parse-don't-validate, semantic types, code/doc coupling) that an agent reads and applies with judgment rather than a regex. Copy to the repo root as `CONVENTIONS.md`, adapt per repo, and reference from `CLAUDE.md`/`AGENTS.md`.
- **`assets/agents.red-green-tdd.md`** -- red/green TDD agent directive. Copy to `.claude/`.
