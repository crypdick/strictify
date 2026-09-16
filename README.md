# strictify

A Claude Code and Codex plugin for Python code quality enforcement. Run `/strictify`
in Claude Code or ask Codex to "strictify this repo." It inspects your setup,
proposes changes across 22 categories, and applies approved changes.

## Install

### Claude Code

```shell
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

```shell
codex plugin marketplace add crypdick/strictify
codex plugin add strictify@strictify
```

## Releases

After checks pass on `main`, CI preserves a deliberate version increase or bumps
both plugin manifests' patch version. Retries reuse the release commit; stale runs
stop. See [release implementation](ARCHITECTURE.md#githubworkflows-and-tools).

## What it does

Strictify proposes current state → change for each category, then merges configs,
copies scripts, and installs approved tools. Rules depend on the repo: dependency
checks need reliable metadata, package checks need a publishable distribution,
and service isolation needs shared state.

Hook enforcement uses `prek` exclusively. Strictify migrates legacy YAML config
to `prek.toml`, verifies the replacement, then removes the obsolete config.
Ruff uses curated rules without `ALL`, global preview, or unsafe fixes.

### Categories

The [skill](skills/strictify/SKILL.md) defines the full policy:

| Group | Categories |
|---|---|
| Static analysis and type safety | Prek, Ruff, mypy, Beartype, semantic typing, boundary parsing |
| Code health | Vulture, dependency/package integrity, Pyupgrade + Flynt, structured logging |
| Testing and coverage | Branch coverage targeting 100%, parallel tests and timeouts, red/green test-driven development directive |
| Architecture and organization | File length, architecture map, package boundaries, quality scorecard |
| Environment and infrastructure | Worktree setup and service isolation |
| Ongoing enforcement | Custom hooks, hygiene checks, doc gardening, preference enforcement |

Boundary checks use existing tools or the bundled
[architecture toolkit](skills/strictify/references/architecture-toolkit.md) and
[starter policy](skills/strictify/assets/architecture.toml). Automatic releases
are optional for uv-managed distributions published from GitHub.

### Hookify rules

For Claude Code, two [hookify](https://github.com/anthropics/claude-code-plugins/tree/main/hookify)
rules in `.claude/` capture coding preferences as enforcement and warn on generic
module names such as `utils.py` and `helpers.py`.

### Design conventions doc

An adapted `CONVENTIONS.md`, linked from agent instructions, covers composition,
boundary parsing, semantic types, and code/doc coupling. These require judgment
when reading code.

### Custom prek hooks

Four standalone scripts go in `scripts/prek_hooks/`:

| Hook | Check |
|---|---|
| `check_exception_handling.py` | Bare `except:` and broad handlers without a direct raise or logging call |
| `check_file_length.py` | More than 400 logical lines |
| `check_timeless_comments.py` | Temporal wording in comments/docstrings |
| `check_private_test_imports.py` | Private first-party imports in tests |

See [hook behavior and exemptions](skills/strictify/SKILL.md#scripts-and-assets).
Ruff owns print/logging and syntax diagnostics.

## Philosophy

Choose checks that prevent concrete problems, adapt them to the repo, and let users
veto them. Inspired by [AI Is Forcing Us to Write Good Code](https://bits.logic.inc/p/ai-is-forcing-us-to-write-good-code)
and [Harness Engineering](https://openai.com/index/harness-engineering/).

## Development

Repository checks require Python 3.11+ and Git:

```shell
uvx prek install
uvx prek run --all-files
```

CI runs the same checks. To run only the regression suite with pinned Ruff:

```shell
uv run --no-project --with ruff==0.15.20 python -m unittest discover -s tests
```

See [architecture enforcement](ARCHITECTURE.md#repository-boundary-enforcement)
for source ownership, standalone constraints, and tests.

## License

MIT
