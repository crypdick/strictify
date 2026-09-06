# Architecture

Strictify is a Claude Code and Codex plugin, not a runnable program. It is a bundle
of *instructions and assets* that teach an agent how to add opinionated Python
code-quality enforcement to some *other* repo. Both hosts read the same
`.claude-plugin` marketplace metadata and `skills/strictify/SKILL.md`; duplicating
those declarations in a second manifest would create version and description drift.
There is no strictify runtime: the agent reads the skill, follows its three-phase
workflow (analyze → propose → apply), and writes config and scripts into the target
repo. Claude Code also consumes the bundled hookify rules. This document is a map
of where things live, not how each rule works — the rules document themselves.

## Codemap

### `.claude-plugin/`

Cross-host plugin manifest. `plugin.json` declares name, version, and description;
`marketplace.json` lets the repo be installed as a single-plugin marketplace in
Claude Code or Codex. These two files must agree on name and version. No behavior
lives here.

### `commands/strictify.md`

The `/strictify` slash command. Its front-matter gathers context (directory listing,
git status, existing `pyproject.toml` / `prek.toml` / `AGENTS.md`,
package manager, layout) via `!` shell substitutions, then hands off to the skill.
The command is a thin entry point; all logic lives in the skill.

### `skills/strictify/`

The heart of the plugin.

- **`SKILL.md`** — the workflow. Defines the 22 enforcement categories, the
  analyze/propose/apply phases, conflict handling, and pointers to every resource
  below. This is the one file to read to understand what strictify *does*. Category
  numbering here is load-bearing: `SKILL.md`, `README.md`, and the plugin manifests
  all quote "22 categories" and must stay in sync.
- **`references/`** — the config payloads the agent merges into a target repo:
  `pyproject-strict.md` (ruff/mypy/pytest/coverage/vulture/deptry), `prek-config.md`
  (the native `prek.toml` template), and `beartype-setup.md`. Prose-wrapped so
  the agent reads intent before copying.
- **`scripts/`** — custom prek hook scripts copied into the target repo's
  `scripts/prek_hooks/`: `check_exception_handling.py`,
  `check_file_length.py`, `check_timeless_comments.py`, and
  `check_private_test_imports.py`. Ruff owns print/logging and future-import checks.
- **`assets/`** — files copied into the target repo. `hookify.*.md` rules
  (taste-enforcer, no-junk-drawers) and `agents.red-green-tdd.md` go into `.claude/`;
  only mechanical, low-false-positive matches ship as hooks. `CONVENTIONS.md-EXAMPLE`
  is copied to the repo root as `CONVENTIONS.md`, adapted, and referenced from
  `CLAUDE.md`/`AGENTS.md` — it holds the judgment-based principles (composition over
  inheritance, parse-don't-validate, semantic types, code/doc coupling) that were too
  nuanced to enforce with a regex hook.

## Invariants

- **No strictify runtime.** The plugin ships instructions and assets only. Behavior
  is produced by the agent following `SKILL.md`, and by the tools (ruff, mypy,
  prek, …) it installs into the *target* repo. Strictify itself has no
  dependencies to install and nothing to import.
- **Hook scripts are self-contained and stdlib-only.** Every script in `scripts/`
  imports nothing beyond the standard library (`argparse`, `ast`, `io`, `re`,
  `sys`, `tokenize`, `pathlib`) so it can be dropped into any target repo and
  run under prek without adding dependencies. A unittest regression suite exercises hook behavior and the shipped Ruff
  configuration; prek supplies pinned Ruff for these integration checks.
- **Agent-readable output.** Every hook reports violations as
  `{file}:{line}: {message} -- {remediation}`, exits nonzero on failure, and honors
  `# allow: {hook-name}` per-line exemptions. This contract is what lets both humans
  and agents act on findings.
- **Merge, never clobber.** The apply phase only adds or tightens target-repo
  settings, and the user can veto any category. A legacy YAML hook config is the
  one format-migration exception: preserve its behavior in native `prek.toml`,
  validate the replacement, then remove the obsolete file so only one runner owns
  the hook lifecycle.
- **Category count is a shared constant.** The "22 categories" figure appears in the
  skill, the README, and both manifests. Changing the set means updating all four.

## Non-goals

- Strictify does not enforce most categories on *this* repo — there is no Python
  package here and no `pyproject.toml`; its native `prek.toml` only dogfoods the
  repo-agnostic checks and validates the shipped hook payloads.
- It targets Python repos only; the analysis and configs assume a Python toolchain.

Revisit this file a couple of times a year, or whenever a category is added, split,
or removed — not on every edit.
