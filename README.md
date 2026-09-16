# strictify

A Claude Code and Codex plugin that applies opinionated Python code quality
enforcement to any repo.

Run `/strictify` in Claude Code, or ask Codex to “strictify this repo,” from any
Python project. It checks the existing setup, proposes changes
across 22 categories, and applies the changes you approve. It also installs
[hookify](https://github.com/anthropics/claude-code-plugins/tree/main/hookify) rules
for Claude Code that capture your taste preferences as you work.

## Install

### Claude Code

```
claude plugins add github:crypdick/strictify
```

Or add to `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "strictify": {
      "source": { "source": "github", "repo": "crypdick/strictify" }
    }
  },
  "enabledPlugins": {
    "strictify@strictify": true
  }
}
```

### Codex

```
codex plugin marketplace add crypdick/strictify
codex plugin add strictify@strictify
```

Codex reads the same marketplace and skill metadata; a second, duplicated plugin
manifest is not required.

## Releases

Every successful push to `main` creates a plugin release commit. CI preserves a
deliberate version increase already present in both plugin manifests; otherwise it
increments the patch version. Superseded runs stop without overwriting newer work,
and retries reuse an existing release commit.

## What it does

Strictify includes reusable configs and instructions for changes that depend on your repo:

- Ruff, mypy, pytest, and coverage settings; a native `prek.toml` template; and self-contained hook scripts.
- A reusable [architecture toolkit and setup guide](skills/strictify/references/architecture-toolkit.md), with [starter architecture.toml](skills/strictify/assets/architecture.toml), exact public APIs, independent dependency gates, and a shrinking reviewed baseline.
- Instructions to set up services and isolate worktrees based on your repo's needs.

`/strictify` runs a three-phase workflow:

1. **Analyze** — scans pyproject.toml, `prek.toml`, package layout, Python version, package manager, test setup, beartype, domain structure
2. **Propose** — presents 22 categories grouped into 6 areas, showing current state vs. proposed change for each. You veto what you don't want.
3. **Apply** — merges configs, copies scripts, installs hooks, adds dev dependencies

Hook enforcement uses `prek` exclusively. Strictify migrates legacy YAML hook
configuration to native `prek.toml` and removes the old config rather than keeping
two runners in parallel.

Dependency and package checks are fitted to the target: `deptry` is enabled only
when dependency metadata is trustworthy, `pyproject.toml` schema validation is
used only while its third-party schemas cover the selected tools, and `check-sdist`
is reserved for publishable distributions. For uv-managed packages published from
GitHub, Strictify can optionally set up an automatic main-branch release that keeps
`pyproject.toml` and `uv.lock` synchronized before trusted publishing.

Ruff remains a curated policy: Strictify does not enable `ALL`, top-level preview mode,
or unsafe fixes. Preview lint rules are opted into by exact code so broader rule-family
selections cannot silently acquire new preview checks.

### Categories

| Group | Categories |
|-------|-----------|
| **Static Analysis & Type Safety** | Prek hook framework, Ruff anti-slop rules, mypy strict, Beartype, Semantic typing (NewType), Parse-don't-validate |
| **Code Health** | Vulture (dead code), Dependency/package integrity, Pyupgrade + Flynt, Structured logging |
| **Testing & Coverage** | Branch coverage with `fail_under=100`, Fast tests (xdist, timeouts, --failed-first), Red/green TDD agent directive |
| **Architecture & Organization** | File length limits, Architecture codemap (ARCHITECTURE.md), Architecture boundaries, Quality scorecard |
| **Environment & Infrastructure** | Ephemeral environments, Per-worktree isolation |
| **Ongoing Enforcement** | Custom hooks, Hygiene hooks, Doc gardening, Taste enforcer |

### Hookify rules

Two rules are installed into your project's `.claude/` directory. They match prompt keywords and filenames:

- **taste-enforcer** — when you express a coding preference ("don't use X", "always prefer Y"), Claude codifies it as a prek hook, hookify rule, or pyproject.toml setting
- **no-junk-drawers** — warns on `utils.py`, `helpers.py`, `misc.py` — name modules after what they do

### Design conventions doc

Some design decisions require reading the code: whether a `str` represents a domain concept, for example, or whether inheritance fits. Strictify records these principles in a `CONVENTIONS.md` adapted to your repo and references it from `CLAUDE.md`/`AGENTS.md`:

- **Composition over inheritance** — combine focused components and inject strategies to avoid multiplying subclasses or configuration flags
- **Parse, don't validate** — coerce to constrained types at the boundary; carry proof through types (with the Pydantic-validator caveat)
- **Semantic types** — `NewType` for domain concepts like `user_id`, `amount`, `slug`
- **Code/doc coupling** — leave `NOTE:` back-pointers where a value is also documented in prose

### Custom prek hooks

Four scripts are adapted to your repo and installed in `scripts/prek_hooks/`:

| Hook | What it catches |
|------|----------------|
| `check_exception_handling.py` | Bare `except:` and broad handlers without a direct raise or logging call |
| `check_file_length.py` | Files over 400 logical lines |
| `check_timeless_comments.py` | Temporal language in comments ("legacy", "old", "deprecated") |
| `check_private_test_imports.py` | Tests importing private (`_foo`) first-party symbols instead of driving public behaviour |

Ruff owns print/logging checks and misplaced future-import diagnostics. Print
exemptions live in Ruff configuration or `# noqa: T201`.

Exception logging detection recognizes `logging`, `log`, `logger`, and names ending
in `_logger`; it does not resolve imports or prove control flow. Private-import
checks cover absolute `from` imports in `test/`, `tests/`, `test_*.py`, and
`*_test.py`; relative test-helper imports are excluded. File-length checks count
physical lines containing code, including continuation lines, and accept a
file-wide exemption comment in the first five lines. Ruff must run alongside
these hooks to report syntax and encoding errors.

All hooks output `{file}:{line}: {message} — {remediation}` so both humans and AI agents can act on violations.

## Philosophy

Inspired by [AI Is Forcing Us to Write Good Code](https://bits.logic.inc/p/ai-is-forcing-us-to-write-good-code) and [Harness Engineering](https://openai.com/index/harness-engineering/):

- Choose rules for the problems they prevent.
- Propose strict defaults and let the user veto what doesn't fit.
- Capture coding preferences as enforceable rules during normal work.
- Parse input at system boundaries and use types to preserve the resulting guarantees.
- Organize code so people and agents can find what they need.

## Development

Run the regression suite with its pinned Ruff dependency:

```sh
uv run --no-project --with ruff==0.15.20 python -m unittest discover -s tests
```

Run all repository checks with `uvx prek run --all-files`; enable commit checks
with `uvx prek install`. CI runs the same suite. The repository's
[architecture policy](architecture.toml) uses the same shipped toolkit as target
repositories, and keeps single-file hooks independent and stdlib-only. See [architecture enforcement](ARCHITECTURE.md#repository-boundary-enforcement)
for scope, exceptions, and tests. Repository checks require Python 3.11 or newer
and Git.

## License

MIT
