---
name: strictify
description: This skill should be used when the user asks to "strictify a repo", "add code quality enforcement", "make this repo strict", "add prek hooks", "add type checking", "enforce code quality", "set up linting", or runs the /strictify command.
---

# Strictify

## Overview

This skill adds Python code-quality enforcement across 22 categories. It analyzes an existing repository or sets up a new one, proposes rules that fit the project, then applies approved changes.

Inspired by "AI Is Forcing Us to Write Good Code" and OpenAI's "Harness Engineering," strictify uses automated checks and documented conventions to help agents follow the project's standards. Code and documentation should be easy for both people and agents to navigate.

## Philosophy

- Choose rules for the problems they prevent.
- Judge each category against the repo's size, stack, domain, and maturity. Skip or adapt what doesn't fit: a 200-line script doesn't need architectural-layer lint rules, an offline library doesn't need third-party-call caching, and a repo with no shared services doesn't need per-worktree isolation.
- Propose strict defaults for the categories that fit, and let the user veto them.
- Capture coding preferences as hookify rules during normal work.
- Parse input at system boundaries and use types to preserve the resulting guarantees.
- Organize code so people and agents can find what they need.
- Add missing checks to existing projects and new ones, merging with the current configuration.

## Phase 1: Analyze

Scan the target repo to understand its current state. Check all of the following:

- [ ] **pyproject.toml** -- existence and current tool configs (ruff, mypy, pytest, coverage, vulture, deptry sections)
- [ ] **prek.toml** -- existence and current hooks
- [ ] **Legacy hook config** -- if `.pre-commit-config.yaml` or `.pre-commit-config.yml` exists, plan its one-way migration to native `prek.toml`; strictify does not retain the legacy runner or config
- [ ] **Package layout** -- `src/` layout vs flat layout; identify the package name
- [ ] **Python version** -- from `pyproject.toml` `requires-python`, `.python-version`, or `python3 --version`
- [ ] **Package manager** -- uv (`uv.lock`), poetry (`poetry.lock`), pip (`requirements.txt`)
- [ ] **Beartype** -- already a dependency?
- [ ] **Test infrastructure** -- pytest config, test directory, coverage config
- [ ] **`__init__.py` contents** -- identify insertion point for beartype
- [ ] **Domain structure** -- directories, modules, apparent layers (for architectural analysis)
- [ ] **Architecture enforcement** -- existing ownership manifests, public APIs, dependency contracts, composition roots, exceptions/baselines, and their hooks or CI checks; trace real cross-package imports before proposing boundaries
- [ ] **Documentation state** -- README, `docs/`, inline comments quality
- [ ] **Release automation** -- whether the repo publishes a package, current version source, release workflow, trusted-publishing setup, and retry/concurrency behavior

## Phase 2: Propose

Use the Phase 1 analysis to select categories that fit the repo, and briefly explain any you skip. Present the findings in the 6 groups below, showing **current state -> proposed change** for each category. Ask the user to veto any they do not want. Default to applying all relevant categories unless the user vetoes them.

### Static Analysis & Type Safety (categories 1-6)

1. **Prek hook framework** -- install `prek` if missing and use native `prek.toml` exclusively. Migrate any legacy YAML hook config and remove it once the replacement is verified. Read `references/prek-config.md` for the full template.
2. **Ruff** -- curated anti-slop lint rules (core `E`/`W`/`F`/`I`, `B`, `UP`, `C4`, `SIM`, `RUF`, complexity `C90`, selected annotation/docstring checks, plus high-signal families for async, exceptions, logging, performance, security, pytest, pathlib, suppressions, private access, debugger/print bans, executable scripts, and import/package boundaries) and format config. Do not enable `ALL`, top-level preview mode, or unsafe fixes. Exact preview lint rules may be enabled only with lint-scoped preview mode and `explicit-preview-rules = true`. Read `references/pyproject-strict.md` for exact settings. Ruff owns cyclomatic-complexity enforcement through `C901`; do not add a second complexity tool.
3. **mypy** -- `strict = true` with pragmatic exceptions for the project's frameworks. Read `references/pyproject-strict.md` for strict mypy config and framework overrides.
4. **Beartype** -- add dependency, insert `beartype_this_package()` in package `__init__.py`. Read `references/beartype-setup.md` for integration patterns and common issues.
5. **Semantic typing** -- recorded as a principle in the `CONVENTIONS.md` design doc (Phase 3): give domain concepts (user IDs, amounts, slugs) a distinct `NewType` instead of a bare primitive (`TypeAlias` only supplies another name for the same type). Deciding *which* primitives carry domain meaning is a judgment call, so it lives in the conventions doc for the agent to apply, not a regex hook.
6. **Parse-don't-validate** -- recorded as a principle in the `CONVENTIONS.md` design doc (Phase 3): coerce unstructured data into constrained types (Pydantic models, frozen dataclasses, `NewType`) at the boundary and carry proof through types, instead of re-validating downstream. Pydantic validators enforce runtime value constraints; use a distinct semantic type as well when static separation between concepts matters. Neither `NewType` nor a frozen dataclass validates untrusted input by itself.

### Code Health (categories 7-10)

7. **Vulture** -- dead code detection with sensible ignore list. Read `references/pyproject-strict.md` for `min_confidence` and ignore settings.
8. **Dependency and package integrity** -- when the repo has reliable dependency metadata, add `deptry` to catch missing, unused, transitive, and misplaced development dependencies. Validate `pyproject.toml` when the configured schemas cover the selected tools, but never weaken valid tool configuration to appease a stale third-party schema. For a publishable Python distribution, add `check-sdist`; skip it for applications and non-packaged repos. For uv-managed repos, set `exclude-newer = "3 days"` in `[tool.uv]` -- a dependency cooldown that delays adoption of freshly published releases; it reduces exposure but does not establish that a dependency is safe. For a uv-managed distribution published from GitHub, optionally offer automatic releases after successful `main` checks; do not add release automation to applications, private libraries, or repos whose release policy is unclear. Read `references/pyproject-strict.md`, `references/prek-config.md`, and `references/automatic-releases.md` for the conditional configuration.
9. **Pyupgrade + flynt** -- modernize syntax to the project's target Python version. Automates f-string conversion and syntax upgrades.
10. **Structured logging** -- use Ruff as the sole detector for print/logging checks; configure print exemptions in its per-file ignores and use narrow `# noqa` comments. Detect unstructured logging patterns (string concatenation, %-formatting, f-strings in log calls) and nudge toward stdlib-compatible structured `logger.info("message", extra={"key": value})` style.

### Testing & Coverage (categories 11-12)

11. **Coverage enforcement** -- collect branch coverage for the actual package, enforce `fail_under = 100` from `[tool.coverage.report]`, and render missing lines as an explicit todo list. Add exclusions with `exclude_also` so Coverage.py's defaults remain intact. Read `references/pyproject-strict.md` for the full configuration.
12. **Fast test infrastructure** -- pytest-xdist parallel execution, test timeouts, `--failed-first` for fast feedback. Read `references/pyproject-strict.md` for pytest `addopts` config. Separately, *only if the tests make real third-party/external calls* (HTTP APIs, SDKs, network services -- the usual source of slow, flaky suites): propose a record-replay layer (`vcrpy`/`pytest-recording`, `respx` for httpx, or `responses` for requests) that records real responses once and replays them on later runs. A recorded response assumes the third party is a pure function of the request, so pair it with a CI job that re-runs the suite *without* the recordings after PR approval, to catch where that assumption breaks.

### Architecture & Organization (categories 13-16)

13. **Filesystem discipline** -- limit files to 400 lines and add a hookify rule warning on `utils.py`/`helpers.py`/`misc.py` creation. Name shared utilities after what they do.
14. **Architecture codemap** -- maintain the repo's existing architecture map, or create `docs/ARCHITECTURE.md` if none exists. Include the problem it solves, the main packages and their relationships, and architectural invariants (e.g. "the domain layer never imports Django"). Name important files, modules, and types so readers can search for them. Link to executable policy rather than duplicating its allowlists. Every project should have this short map, regardless of size. Revisit the overview a couple of times a year; update policy links and changed invariants alongside code.
15. **Architecture boundary enforcement** -- read `references/architecture-boundaries.md` when this category fits. Derive package ownership, exact public surfaces, and allowed dependency directions from the target repo. Enforce visibility and direction independently, with named composition roots and exact, shrinking exceptions for existing debt. Prefer existing tools; otherwise use the bundled `scripts/architecture/` toolkit and `assets/architecture.toml` following `references/architecture-toolkit.md`. Include policy validation and, where shared root modules are a problem, direct-importer budgets. Use lightweight or no boundary checks for small projects; do not impose one role hierarchy or rewrite architecture merely to install enforcement.
16. **Quality grades** -- create `docs/QUALITY.md` scorecard grading each module/domain on coverage, type safety, complexity, and test health. Assess the current state, produce initial grades, and include guidance on how to maintain and update the scorecard over time.

### Environment & Infrastructure (categories 17-18)

17. **Ephemeral environment** -- create a single command that prepares a fresh development environment: create a git worktree, copy local-only config (`.env`, credentials, editor settings), install dependencies, and hand off to the agent. Aim for setup in seconds so agents can work concurrently in separate worktrees. For a uv project with no services, a `new-feature <name>` script can wrap `git worktree add`, `uv sync`, and an `.env` copy. Add service startup or other steps as the repo requires.
18. **Per-worktree isolation** -- give each worktree its own ports, database/schema names, caches on hardcoded paths (`/tmp/myapp-cache`, `~/.cache/myapp`), and shared service identifiers (redis db numbers, queue names). Derive these from the worktree name using an offset or hash, and pass them through environment variables to prevent collisions. Keep content-addressed global caches (`~/.cache/uv`, pip wheels) shared; their content hashes already separate entries. A project with no shared state may only need `uv run` to work from any worktree. Otherwise, add the isolation variables to the category-17 setup command. Containers may need per-worktree Docker compose project names or volumes.

### Ongoing Enforcement (categories 19-22)

19. **Custom hooks** -- exception handling (`check_exception_handling.py`), timeless comments (`check_timeless_comments.py`), and tests-verify-public-behaviour (`check_private_test_imports.py`, which forbids tests from importing leading-underscore first-party symbols so they exercise the public surface instead of internal shape). Read each script from `scripts/` to understand behavior and adapt to the target repo.
20. **Hygiene hooks** -- use `prek`'s native built-ins for trailing whitespace, end-of-file fixes, JSON/TOML/YAML validation, large files, merge conflicts, private keys, case-conflicting paths, broken/destroyed symlinks, byte-order markers, mixed line endings, and executable/shebang consistency; pair them with `detect-secrets` for entropy-based secret scanning. **Out of scope:** personal/prod strings (internal hostnames, real usernames, prod URLs). Any mechanism for these either commits the pattern (defeating the point) or requires per-user config strictify cannot bootstrap -- users who care should add a local hook that reads patterns from a gitignored file.
21. **Doc gardening** -- detect stale documentation that does not reflect actual code behavior. Set up infrastructure appropriate to the project's maturity: a prek hook, a CI job, or guidance for a recurring agent task that scans for drift and opens fix-up PRs. Pair with the *keep code and docs coupled* principle in the `CONVENTIONS.md` design doc (Phase 3): leave `NOTE:` back-pointers at code sites whose values are documented elsewhere, so the two don't drift.
22. **Taste enforcer** -- hookify rule that captures ongoing user preferences. When the user expresses a coding preference, determine whether it can be codified as a prek hook script, a hookify rule, or a pyproject.toml setting, then create or update the enforcement mechanism.

## Phase 3: Apply

For each approved category, perform the following. Read the referenced files before writing any config.

### Configuration merging

- **Merge into `pyproject.toml`** -- read `references/pyproject-strict.md` for strict tool configurations. Merge sections: never remove existing settings, only add or tighten. Create `pyproject.toml` if it does not exist.
- **Merge into `prek.toml`** -- read `references/prek-config.md` for the complete native template. Add missing repositories and hooks. Create the file if it does not exist. If a legacy YAML hook config exists, migrate its behavior into `prek.toml` and remove the legacy file; never leave two competing hook configs.

### Scripts and assets

- **Copy and adapt scripts** -- read each script from `scripts/` (check_exception_handling.py, check_file_length.py, check_timeless_comments.py, check_private_test_imports.py). Adapt paths and package names to the target repo. Write to `scripts/prek_hooks/` in the target repo. `check_private_test_imports.py` auto-detects first-party packages from the target's layout, and flat Python modules. For namespace packages or other layouts, pass explicit `--package` names identified during analysis.
- **Beartype integration** -- read `references/beartype-setup.md`. Modify the package `__init__.py` to insert `beartype_this_package()`.
- **Hookify rules** -- copy from `assets/` (taste-enforcer, no-junk-drawers) to the target repo's `.claude/` directory. These match prompt keywords and filenames. Design principles that require reading the code belong in `CONVENTIONS.md`.
- **Design conventions doc** -- copy `assets/CONVENTIONS.md-EXAMPLE` to the target as `CONVENTIONS.md`. Remove principles that do not fit, use the repo's types in examples, and add repo-specific conventions. The template covers composition over inheritance, parse-don't-validate, semantic types, and code/doc coupling. Append a pointer to `CLAUDE.md`/`AGENTS.md` (e.g. "See `CONVENTIONS.md` for design principles") so agents load it alongside `docs/ARCHITECTURE.md` and `docs/QUALITY.md`.

### Dependencies

Install only tools needed by the approved categories. Detect the package manager and persist the dependencies using its normal workflow:

- **uv**: select the required tools from `uv add --dev ruff mypy vulture pytest pytest-xdist pytest-cov pytest-timeout pytest-asyncio pyupgrade flynt prek`; add `deptry` only when category 8 applies
- **Runtime dependency:** when category 4 applies, run `uv add beartype` (or `poetry add beartype`); for pip, persist it in runtime requirements. Never put it only in a development group: production `__init__.py` imports it. Verify a package import in an environment installed without development dependencies.
- **pip**: add the selected tools to the project's development requirements file and install from it
- **poetry**: `poetry add --group dev` equivalent

### Infrastructure setup

- Run `prek install` to activate hooks.
- **Architecture codemap**: update the existing canonical map, or create `docs/ARCHITECTURE.md`. Link to the executable architecture policy and describe its intent; avoid duplicating allowlists or linking to specific source lines.
- **Architecture boundaries**: follow `references/architecture-boundaries.md` to configure the selected checker, validate its public behavior, and wire a whole-tree check into prek and the repo's CI. Link the policy and package migration procedure from `AGENTS.md`/`CLAUDE.md`. Keep enforcement setup separate from any broader migration not already authorized.
- **Quality scorecard**: create `docs/QUALITY.md` with initial grades per module.
- **Doc gardening**: set up stale-docs detection appropriate to project maturity; revisit the architecture overview a couple of times a year and keep executable-policy references coupled to code changes.
- **Per-worktree**: configure if applicable (ports, DBs, caches).
- **Automatic releases**: only when approved for a uv-managed publishable distribution, follow `references/automatic-releases.md`; preserve deliberate version bumps, update `pyproject.toml` and `uv.lock` with uv, serialize releases, reject stale runs, and verify before publishing.

## Conflict Handling

When the repo already has configuration:

- **Merge-up** -- read existing config, add missing strict settings, tighten existing ones
- **Never remove** user settings -- only add or tighten. The sole format-migration
  exception is a legacy YAML hook config: translate all of its behavior into
  `prek.toml`, verify the native config, then remove the obsolete file so there is
  one hook runner and one source of truth.
- **Present diff** -- show current state -> proposed change for every modification
- **User veto** -- the user can reject any category before application
- **Bias strict** -- default is to apply everything; the user opts out, not in

## Resources

Detailed configs, scripts, and assets live in the skill's bundled resources. Read these before writing any configuration to the target repo.

### Reference Files

- **`references/pyproject-strict.md`** -- strict tool configurations for ruff, mypy, pytest, coverage, vulture, and conditional deptry sections in pyproject.toml
- **`references/prek-config.md`** -- complete native `prek.toml` template with built-in, remote, conditional integrity, and local hook definitions
- **`references/beartype-setup.md`** -- beartype integration guide: `beartype_this_package()` snippet, `BeartypeConf` options, common issues, and install commands per package manager
- **`references/architecture-boundaries.md`** -- category 15: ownership, public APIs, dependency direction, composition roots, baseline ratcheting, and verification requirements for the target's selected checker
- **`references/architecture-toolkit.md`** -- bundled checker's installation, CLI, strict schema, starter policy, baseline format, limitations, and Strictify's own worked example
- **`references/automatic-releases.md`** -- optional main-branch release workflow for uv-managed publishable distributions, including version ownership, concurrency, retries, verification, trusted publishing, tags, and GitHub Releases

### Scripts

Single-file prek hooks in `scripts/` accept filenames as arguments, report violations as `{file}:{line}: {message} -- {remediation}` (agent-readable), exit nonzero on failure, and support `# allow: {hook-name}` exemptions. Place these on the relevant line; file-length exemptions belong in the first five lines of the file. Syntax and encoding errors are left to Ruff, which must run alongside these hooks. The architecture toolkit is different: copy its whole package, run its public `api` module over the configured tree, and use reviewed policy/baseline exceptions, never line suppressions.

- **`scripts/check_exception_handling.py`** -- detects bare `except:` and broad handlers without a direct raise or a call on a conventionally named logger
- **`scripts/check_file_length.py`** -- enforces max 400 logical lines per file
- **`scripts/check_timeless_comments.py`** -- detects temporal keywords in comments and docstrings (for example, legacy, new, old); explicit exemptions and TODO/FIXME comments are allowed
- **`scripts/check_private_test_imports.py`** -- forbids tests from importing leading-underscore first-party symbols; auto-detects first-party packages, supports `--package` overrides and a `# allow: private-test-imports` carve-out
- **`scripts/architecture/`** -- reusable stdlib-only package for architecture policy, import extraction, independent gates, cycle checks, direct-importer budgets, and exact baseline ratcheting; copy the complete directory including `LICENSE`

### Assets

Files in `assets/`. Copy these to the target repo.

- **`assets/architecture.toml`** -- starter executable architecture policy; adapt actual source roots and responsibilities before enabling the checker

- **`assets/hookify.taste-enforcer.md`** -- hookify rule (prompt event) that captures user taste preferences and codifies them as hooks, rules, or config. Copy to `.claude/`.
- **`assets/hookify.no-junk-drawers.md`** -- hookify rule (file event) that warns on junk-drawer module names (utils.py, helpers.py, misc.py) by filename match. Copy to `.claude/`.
- **`assets/CONVENTIONS.md-EXAMPLE`** -- template for the `CONVENTIONS.md` design-conventions doc: judgment-based principles (composition over inheritance, parse-don't-validate, semantic types, code/doc coupling) that an agent reads and applies with judgment rather than a regex. Copy to the repo root as `CONVENTIONS.md`, adapt per repo, and reference from `CLAUDE.md`/`AGENTS.md`.
- **`assets/agents.red-green-tdd.md`** -- red/green TDD agent directive. Copy to `.claude/`.
