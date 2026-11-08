---
name: strictify
description: Add Python code quality enforcement when asked to strictify a repo, add prek hooks or type checking, set up linting, or run /strictify.
---

# Strictify

Analyze the repo, propose relevant changes across 22 categories, and apply only
approved changes. Fit strict defaults to the project's needs. Preserve existing
settings unless replacing them through a verified migration.

## Analyze and propose

Inspect existing tooling, package boundaries, tests, runtime dependencies, and
worktree setup. Check publication intent before proposing releases. Summarize
current gaps and proposed changes; explain consequential trade-offs and skipped
categories. Let the user veto any category. Read linked references when configuring
the corresponding tools.

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
5. **Semantic typing:** Use the sibling
   [coding-conventions skill](../coding-conventions/SKILL.md) for domain type
   decisions. Enforce chosen distinctions through mypy, not name-based regexes.
6. **Parse-don't-validate:** Use coding-conventions to document boundary parsing
   into validated types. Adopt the project's existing validation approach.

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

13. **Filesystem discipline:** Limit files to 400 code-containing physical lines. Use
    coding-conventions for module naming and ownership guidance.
14. **Architecture codemap:** Maintain the existing map or create
    `docs/ARCHITECTURE.md`. Keep it proportional to the project: purpose, searchable
    code names, relationships, and invariants. Link executable policy rather than
    duplicating it; update the map when architecture changes.
15. **Architecture boundary enforcement:** Follow
    [boundary contracts](references/architecture-boundaries.md). Prefer existing
    enforcement; otherwise use the [bundled toolkit](references/architecture-toolkit.md)
    and [starter policy](assets/architecture.toml). Small projects may need only
    a documented invariant. Do not impose layers or expand into an unapproved migration.
16. **Quality grades:** Use `docs/QUALITY.md` to identify module/domain quality
    gaps and maintenance priorities. Prefer existing tool reports over duplicate
    scorekeeping.

### Environment and infrastructure (categories 17-18)

17. **Ephemeral environment:** Make a fresh worktree ready to use with one command,
    including required local config, dependencies, and services. Reuse existing setup.
18. **Per-worktree isolation:** Isolate mutable state and service identifiers between
    worktrees; derive names or ports from the worktree where useful. Share
    content-addressed uv/pip caches. Stateless projects may only need `uv run`.

### Ongoing enforcement (categories 19-22)

19. **Custom hooks:** Install exception-handling, timeless-comment, and private-test-import
    checks from the scripts below. Copy the behavior-testing directive from assets.
20. **Hygiene hooks:** Use the native prek built-ins and audited `detect-secrets`
    baseline in the prek reference. Personal/production string scanning is out of
    scope; it needs user-managed patterns in a gitignored file.
21. **Doc gardening:** Keep docs aligned with code. Use back-pointers for duplicated
    values; automate drift detection where recurring drift justifies it.
22. **Durable preferences:** Use coding-conventions to preserve durable guidance
    in linked project conventions. Prefer existing tool settings and checks for
    mechanical rules. Follow [advisory migration](references/advisory-migration.md)
    when replacing Hookify reminders; keep blocking policy intact.

## Apply

Merge approved config and adapt the scripts/assets below after reading them.
Preserve repo-specific behavior during hook replacement; verify native prek config
before removing legacy YAML. Keep architecture checks whole-tree in prek and CI,
and link policy and migration guidance from agent instructions.

Persist selected tools through the project's package manager, e.g.
`uv add --dev ruff mypy`, Poetry's dev group, or development requirements.
Beartype is a runtime dependency: use `uv add beartype` or equivalent and verify
production imports without development dependencies.

Run `prek install`, verify changed behavior and the full hook suite, and report
changes and unresolved findings.

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

- Copy `assets/agents.red-green-tdd.md` to `.claude/`.
- Use [coding-conventions](../coding-conventions/SKILL.md) to establish or update
  the project's canonical conventions for approved advisory categories. Its
  linked references own the design guidance; load only the relevant topics.
  Link project conventions and architecture/quality docs from
  `CLAUDE.md` or `AGENTS.md`. No Hookify installation is required.
