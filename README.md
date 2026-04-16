# strictify

A [Claude Code plugin](https://docs.claude.com/en/docs/claude-code-plugins) that applies opinionated Python code quality enforcement to any repo.

Run `/strictify-repo` in any Python project. It analyzes what's already in place, proposes strictness additions across 21 categories, and applies approved changes — including self-reinforcing [hookify](https://github.com/anthropics/claude-code-plugins/tree/main/hookify) rules that capture your taste preferences as you work.

## Install

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

## What it does

`/strictify-repo` runs a three-phase workflow:

1. **Analyze** — scans pyproject.toml, pre-commit config, package layout, Python version, package manager, test setup, beartype, domain structure
2. **Propose** — presents 21 categories grouped into 6 areas, showing current state vs. proposed change for each. You veto what you don't want.
3. **Apply** — merges configs, copies scripts, installs hooks, adds dev dependencies

### Categories

| Group | Categories |
|-------|-----------|
| **Static Analysis & Type Safety** | Pre-commit framework, Ruff, mypy strict, Beartype, Semantic typing (NewType), Parse-don't-validate |
| **Code Health** | Vulture (dead code), Xenon (complexity), Pyupgrade + Flynt, Structured logging |
| **Testing & Coverage** | Coverage `fail_under=100`, Fast tests (xdist, timeouts, --failed-first) |
| **Architecture & Organization** | File length limits, Architectural layers, Quality scorecard |
| **Environment & Infrastructure** | Ephemeral environments, Per-worktree isolation |
| **Ongoing Enforcement** | Custom hooks, Hygiene hooks, Doc gardening, Taste enforcer |

### Hookify rules

Four rules are installed into your project's `.claude/` directory:

- **taste-enforcer** — when you express a coding preference ("don't use X", "always prefer Y"), Claude codifies it as a pre-commit hook, hookify rule, or pyproject.toml setting
- **no-junk-drawers** — warns on `utils.py`, `helpers.py`, `misc.py` — name modules after what they do
- **parse-dont-validate** — nudges toward boundary parsing with constrained types instead of scattered validation
- **semantic-types** — catches bare `str`/`int` for domain concepts like `user_id`, nudges toward `NewType`

### Custom pre-commit hooks

Five scripts are adapted to your repo and installed in `scripts/pre_commit_hooks/`:

| Hook | What it catches |
|------|----------------|
| `check_exception_handling.py` | Bare `except:`, swallowed exceptions, `except Exception: pass` |
| `check_print_statements.py` | `print()` in production code, unstructured logging (f-strings/concat in logger calls) |
| `check_file_length.py` | Files over 400 logical lines |
| `check_timeless_comments.py` | Temporal language in comments ("legacy", "old", "deprecated") |
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
