---
name: strictify
description: Add Python code quality enforcement when asked to strictify a repo, add prek hooks or type checking, set up linting, or run /strictify.
---

# Strictify

Analyze the repo, propose changes across 22 categories, and apply approved changes.
Fit rules to its size, stack, and responsibilities. Propose strict defaults, explain
skipped categories, and let the user veto any category. Merge existing settings;
never remove or weaken them except for the verified hook migrations below.

## Phase 1: Analyze

Inspect:

- `pyproject.toml`, `prek.toml`, legacy YAML hook configs, Python version, and package manager.
- Package layout, `__init__.py`, Beartype, tests, coverage, and external service calls.
- Architecture docs, ownership, public APIs, actual cross-package imports, existing
  boundary checks, composition roots, and baselines.
- README, docs, comments, shared services, and worktree setup.
- Publication intent, version source, release workflow, trusted publishing, and retry behavior.

## Phase 2: Propose

Show current state → proposed change in these six groups. Apply relevant categories
within the user's approval; explain omissions. Read linked references before
writing the corresponding configuration.

### Static analysis and type safety (categories 1-6)

1. **Prek hook framework:** Use native `prek.toml` exclusively. Follow the
   [template and migration instructions](references/prek-config.md).
2. **Ruff:** Use the [curated policy](references/pyproject-strict.md), including
   formatting and `C901` complexity checks. No `ALL`, top-level preview, unsafe
   fixes, or second complexity tool. Select preview rules by exact code with
   lint-scoped preview and `explicit-preview-rules = true`.
3. **mypy:** Use `strict = true`; check framework plugins and stubs before adding
   narrow overrides. Settings are in the pyproject reference.
4. **Beartype:** Follow [runtime integration](references/beartype-setup.md).
5. **Semantic typing:** Adapt the conventions template to use `NewType` for domain
   distinctions. `TypeAlias` only renames a type; choosing domain types requires
   code review, not regex enforcement.
6. **Parse-don't-validate:** Document boundary parsing into constrained types.
   `NewType` and frozen dataclasses do not validate input themselves. Pydantic
   validators enforce values; semantic types add static separation.

### Code health (categories 7-10)

7. **Vulture:** Configure dead-code detection and framework exceptions from the
   pyproject reference.
8. **Dependency and package integrity:** Use `deptry` with reliable metadata,
   schema validation when schemas support the actual tool settings, and
   `check-sdist` only for publishable distributions. Never weaken valid config
   for a stale schema. Apply the uv dependency cooldown from the pyproject
   reference. Offer [automatic releases](references/automatic-releases.md) only
   for uv-managed distributions intended for publication from GitHub.
9. **Pyupgrade + flynt:** Modernize syntax and f-strings for the target Python version.
10. **Structured logging:** Let Ruff own print/logging checks and exemptions.
    Prefer `logger.info("message", extra={"key": value})` to formatted log strings.

### Testing and coverage (categories 11-12)

11. **Coverage enforcement:** Collect branch coverage for the actual package,
    target `fail_under = 100`, and report missing lines. Follow the pyproject
    reference for adoption and exclusions.
12. **Fast test infrastructure:** Configure xdist, timeouts, and `--failed-first`.
    Only for tests making external calls, propose record/replay with
    `vcrpy`/`pytest-recording`, `respx` for httpx, or `responses` for requests.
    Pair recordings with a CI run against live services after PR approval;
    recordings assume responses depend only on the request, which live runs must check.

### Architecture and organization (categories 13-16)

13. **Filesystem discipline:** Limit files to 400 logical lines and warn on generic
    module names with the no-junk-drawers asset.
14. **Architecture codemap:** Maintain the existing map or create
    `docs/ARCHITECTURE.md`, even for small projects. State purpose, searchable
    package/file/type names, relationships, and invariants. Link executable
    policy instead of duplicating allowlists. Review the overview twice yearly;
    update changed invariants and policy links with code.
15. **Architecture boundary enforcement:** Follow
    [boundary contracts](references/architecture-boundaries.md). Prefer existing
    enforcement; otherwise use the [bundled toolkit](references/architecture-toolkit.md)
    and [starter policy](assets/architecture.toml). Small projects may need only
    a documented invariant. Do not impose layers or expand into an unapproved migration.
16. **Quality grades:** Create `docs/QUALITY.md` with module/domain grades for
    coverage, type safety, complexity, and test health, plus maintenance guidance.

### Environment and infrastructure (categories 17-18)

17. **Ephemeral environment:** Provide one command to create a worktree, copy
    local-only config, credentials, and editor settings, install dependencies,
    start required services, and hand off to the agent. Aim for setup in seconds.
18. **Per-worktree isolation:** Where shared state exists, derive ports, databases,
    mutable cache paths, queues, Redis identifiers, and Compose projects/volumes
    from the worktree name using an offset or hash. Pass them through environment
    variables in the setup command. Keep content-addressed uv/pip caches shared.
    Projects without shared state may only need `uv run` from each worktree.

### Ongoing enforcement (categories 19-22)

19. **Custom hooks:** Install exception-handling, timeless-comment, and private-test-import
    checks from the scripts below. Copy the red/green TDD directive from assets.
20. **Hygiene hooks:** Use the native prek built-ins and audited `detect-secrets`
    baseline in the prek reference. Personal/production string scanning is out of
    scope; it needs user-managed patterns in a gitignored file.
21. **Doc gardening:** Use a hook, CI job, or recurring agent task that detects
    drift and opens fixes, according to project maturity. Add `NOTE:` back-pointers
    where prose duplicates code values, following the conventions template.
22. **Taste enforcer:** Install the hookify rule to capture durable coding
    preferences as tool settings, hooks, or rules.

## Phase 3: Apply

For approved categories:

- Merge the relevant pyproject and prek sections, creating files if absent.
  Migrate all legacy YAML hook behavior, verify native config, then remove the
  obsolete file. Preserve repo-specific behavior when replacing overlapping hooks.
- Copy and adapt the scripts and assets below. Read their contents before use.
- Persist required development tools through the detected package manager:
  `uv add --dev ruff mypy` for those checks, `poetry add --group dev`, or a
  development requirements file. Install only selected tools. Add Beartype at
  runtime with `uv add beartype` or the package-manager equivalent, then verify
  a package import without development dependencies.
- Set up approved docs, boundary checks, environments, and release automation.
  Run boundary checks over the whole tree in prek and CI. Link policy and package
  migration instructions from `AGENTS.md` or `CLAUDE.md`.
- Run `prek install`, verify changed behavior and the full hook suite, and report
  the changes and unresolved findings.

## Scripts and assets

Copy the four standalone, stdlib-only hooks to `scripts/prek_hooks/`:

| Script | Check |
|---|---|
| `scripts/check_exception_handling.py` | Bare `except:` or broad handlers without a direct raise or recognized logging call |
| `scripts/check_file_length.py` | More than 400 physical lines containing code, including continuation lines |
| `scripts/check_timeless_comments.py` | Temporal terms in comments/docstrings; permits TODO/FIXME and explicit exemptions |
| `scripts/check_private_test_imports.py` | Absolute `from` imports of private first-party symbols in tests; excludes relative test-helper imports |

Hooks accept filenames, emit `{file}:{line}: {message} -- {remediation}`, and exit
nonzero on violations. Use `# allow: {hook-name}` on the relevant line, or in the
first five lines for file length. Ruff must run alongside them for syntax and
encoding errors. Logger detection recognizes `logging`, `log`, `logger`, and
`*_logger` names without resolving imports or proving control flow. Private-import
checks detect flat modules/packages; pass `--package` for namespace or other layouts.

Copy `scripts/architecture/` as a complete package, including `LICENSE`, following
its guide. Run its public `api` module over configured roots; use reviewed policy
and baseline exceptions, never line suppressions.

- Copy `assets/hookify.taste-enforcer.md`, `assets/hookify.no-junk-drawers.md`, and
  `assets/agents.red-green-tdd.md` to `.claude/`. Hookify rules apply to Claude Code.
- Adapt `assets/CONVENTIONS.md-EXAMPLE` into root `CONVENTIONS.md`. Keep applicable
  principles, use repo types in examples, and add local conventions. Link it and
  the architecture/quality docs from `CLAUDE.md` or `AGENTS.md`.
