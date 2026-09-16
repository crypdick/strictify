# Architecture

Strictify ships Python enforcement instructions and assets for Claude Code and
Codex. Both hosts use `.claude-plugin` metadata and `skills/strictify/SKILL.md`.
The agent analyzes a target repo, proposes changes, and applies approved categories.
Claude Code also uses the hookify rules.

## Codemap

### `.claude-plugin/`

`plugin.json` declares the plugin; `marketplace.json` makes it installable.
Their names and versions must match.

### `.github/workflows/` and `tools/`

`checks.yml` runs the full gate on pushes and pull requests. After a successful
push to `main`, `tools/prepare_plugin_release.py` preserves a deliberate version
increase or bumps both manifests' patch version. CI commits the release.
Source-commit metadata supports retries; stale runs cannot overwrite newer pushes.
`tools/check_category_count.py` checks documented counts against the skill's list.

### `commands/strictify.md`

The `/strictify` entry point gathers repo context through shell substitutions and
invokes the skill.

### `skills/strictify/`

- `SKILL.md`: 22 categories and the analyze/propose/apply workflow.
- `references/`: tool configs, Beartype integration, conditional releases,
  architecture contracts, and toolkit setup/schema.
- `scripts/`: four standalone hooks plus the `architecture/` package. Its public
  `api.py` exposes the CLI/API; implementation modules remain private.
- `assets/`: starter architecture policy, hookify rules, TDD directive, and the
  conventions template. Hookify rules and the directive go in `.claude/`.
  Adapt `CONVENTIONS.md-EXAMPLE` into root `CONVENTIONS.md` and link it from agent
  instructions. It holds principles that require code review to apply.

## Invariants

- The plugin has no application runtime or install dependencies. Agents copy
  assets into target repos, where the configured tools enforce policy.
- The four single-file hooks remain standalone and stdlib-only. Copy the toolkit
  as a complete directory, including its MIT license.
- Hooks accept filenames, emit `{file}:{line}: {message} -- {remediation}`, and
  exit nonzero on violations. Exemptions use `# allow: {hook-name}` on the relevant
  line, or in the first five lines for file length. Ruff reports syntax and
  encoding errors. See [hook contracts](skills/strictify/SKILL.md#scripts-and-assets).
- Merge target config without weakening user settings. For a legacy YAML hook
  migration, preserve behavior, verify native `prek.toml`, then remove the old file.
- The skill, README, and both manifests must agree on the category count.
  Both manifests must also agree on versions, including manual bumps.

## Repository boundary enforcement

[architecture.toml](architecture.toml) uses the shipped
[toolkit CLI](skills/strictify/scripts/architecture/api.py) as the sole architecture
checker. It owns registration, exact public modules, and dependency directions.

Hooks and repository tools are exact single-module units. The toolkit is one
package exposing only `api`; tests form a separate unit. This repo needs no
application layers, composition roots, inbound budgets, or debt baseline.

All scanned sources are stdlib-only. Exact standalone declarations also prohibit
first-party imports for independent scripts and designated test harnesses. The
loader exception permits the public-hook harness only; unused exceptions fail.
Tests exercise single-file hooks with isolated import paths and the complete
copied toolkit through its public CLI in fixture repos.

Git supplies tracked and non-ignored untracked Python files across the repository
root. Unowned modules, source symlinks, and stale declarations fail. Git commands
clear inherited `GIT_*` context so fixture and `--root` scans use the intended repo.
The [toolkit guide](skills/strictify/references/architecture-toolkit.md) owns the
schema, installation, baseline format, and AST limitations.

`prek.toml` invokes `python -m skills.strictify.scripts.architecture.api` over the
whole tree. CI runs the same hook suite. Use `uvx prek install` locally and
`uvx prek run --all-files` to verify. Checks require Python 3.11+ and Git.

## Non-goals

Strictify targets Python repos. This plugin repo has no `pyproject.toml` or
application package, so its gate covers hygiene, Ruff, mypy, architecture, category
counts, and unittest regressions rather than every target-repo category.

Review this map twice yearly or when categories or invariants change.
