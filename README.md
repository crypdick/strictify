# strictify

A Claude Code and Codex plugin that applies opinionated Python code quality
enforcement to any repo.

Run `/strictify` in Claude Code, or ask Codex to “strictify this repo,” from any
Python project. It analyzes what's already in place, proposes strictness additions
across 22 categories, and applies approved changes — including self-reinforcing
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

## What it does

Strictify ships two kinds of enforcement, and most categories blend both:

- **Pre-baked opinionated configs and scripts** — ruff/mypy/pytest/coverage settings, a native `prek.toml` template, and self-contained hook scripts that drop into any repo unchanged.
- **Adaptable agent directives** — instructions that direct the agent to apply a *principle* to the specifics of your repo (its layers, its services, its worktree isolation needs) rather than copy a fixed artifact. When the right answer varies case by case, strictify hands the agent the essence and lets it build what fits — it does not hardcode stack-specific instructions (no baked-in OpenAPI/Postgres/Kysely recipes).

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
is reserved for publishable distributions.

Ruff remains a curated policy: Strictify does not enable `ALL`, top-level preview mode,
or unsafe fixes. Preview lint rules are opted into by exact code so broader rule-family
selections cannot silently acquire new preview checks.

### Categories

| Group | Categories |
|-------|-----------|
| **Static Analysis & Type Safety** | Prek hook framework, Ruff anti-slop rules, mypy strict, Beartype, Semantic typing (NewType), Parse-don't-validate |
| **Code Health** | Vulture (dead code), Dependency/package integrity, Pyupgrade + Flynt, Structured logging |
| **Testing & Coverage** | Branch coverage with `fail_under=100`, Fast tests (xdist, timeouts, --failed-first), Red/green TDD agent directive |
| **Architecture & Organization** | File length limits, Architecture codemap (ARCHITECTURE.md), Architectural layers, Quality scorecard |
| **Environment & Infrastructure** | Ephemeral environments, Per-worktree isolation |
| **Ongoing Enforcement** | Custom hooks, Hygiene hooks, Doc gardening, Taste enforcer |

### Hookify rules

Two rules are installed into your project's `.claude/` directory — both mechanical, low-false-positive matches:

- **taste-enforcer** — when you express a coding preference ("don't use X", "always prefer Y"), Claude codifies it as a prek hook, hookify rule, or pyproject.toml setting
- **no-junk-drawers** — warns on `utils.py`, `helpers.py`, `misc.py` — name modules after what they do

### Design conventions doc

Judgment-based design principles don't belong in a regex hook — deciding whether a `str` is "really" a domain concept, or whether some inheritance is the right call, takes reading the code. So strictify installs a `CONVENTIONS.md` (adapted from a template) and references it from your `CLAUDE.md`/`AGENTS.md` so agents read and apply it:

- **Composition over inheritance** — small parts + a combiner, and strategy injection, instead of subclass/config explosions
- **Parse, don't validate** — coerce to constrained types at the boundary; carry proof through types (with the Pydantic-validator caveat)
- **Semantic types** — `NewType` for domain concepts like `user_id`, `amount`, `slug`
- **Code/doc coupling** — leave `NOTE:` back-pointers where a value is also documented in prose

### Custom prek hooks

Six scripts are adapted to your repo and installed in `scripts/prek_hooks/`:

| Hook | What it catches |
|------|----------------|
| `check_exception_handling.py` | Bare `except:`, swallowed exceptions, `except Exception: pass` |
| `check_print_statements.py` | `print()` in production code, unstructured logging (f-strings/concat in logger calls) |
| `check_file_length.py` | Files over 400 logical lines |
| `check_timeless_comments.py` | Temporal language in comments ("legacy", "old", "deprecated") |
| `check_private_test_imports.py` | Tests importing private (`_foo`) first-party symbols instead of driving public behaviour |
| `fix_future_annotations.py` | Misplaced `from __future__ import annotations` |

All hooks output `{file}:{line}: {message} — {remediation}` so both humans and AI agents can act on violations.

## Philosophy

Inspired by [AI Is Forcing Us to Write Good Code](https://bits.logic.inc/p/ai-is-forcing-us-to-write-good-code) and [Harness Engineering](https://openai.com/index/harness-engineering/):

- **Enforce taste, not arbitrary strictness** — every rule exists because it improves code quality
- **Bias strict, but check in** — aggressive defaults, user vetoes what doesn't fit
- **Self-reinforcing** — hookify rules capture new preferences as you express them
- **Parse, don't validate** — coerce at the boundary, carry proof through types
- **Agent legibility** — make code navigable by both humans and AI agents

## License

MIT
