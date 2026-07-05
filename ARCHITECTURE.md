# Architecture

Strictify is a [Claude Code plugin](https://docs.claude.com/en/docs/claude-code-plugins),
not a runnable program. It is a bundle of *instructions and assets* that teach an
agent how to add opinionated Python code-quality enforcement to some *other* repo.
There is no strictify runtime: the agent reads the skill, follows its three-phase
workflow (analyze → propose → apply), and writes config, scripts, and hookify rules
into the target repo. This document is a map of where things live, not how each rule
works — the rules document themselves.

## Codemap

### `.claude-plugin/`

Plugin manifest. `plugin.json` declares name, version, and description;
`marketplace.json` lets the repo be installed as a single-plugin marketplace. These
two files must agree on name and version. No behavior lives here.

### `commands/strictify.md`

The `/strictify` slash command. Its front-matter gathers context (directory listing,
git status, existing `pyproject.toml` / `.pre-commit-config.yaml` / `AGENTS.md`,
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
  `pyproject-strict.md` (ruff/mypy/pytest/coverage/vulture), `pre-commit-config.md`
  (the `.pre-commit-config.yaml` template), and `beartype-setup.md`. Prose-wrapped so
  the agent reads intent before copying.
- **`scripts/`** — custom pre-commit hook scripts copied into the target repo's
  `scripts/pre_commit_hooks/`: `check_exception_handling.py`,
  `check_print_statements.py`, `check_file_length.py`, `check_timeless_comments.py`,
  `check_private_test_imports.py`, and the `fix_future_annotations.py` fixer.
- **`assets/`** — files copied verbatim into the target repo's `.claude/`:
  `hookify.*.md` rules (taste-enforcer, no-junk-drawers, parse-dont-validate,
  semantic-types, doc-code-coupling) and the `agents.red-green-tdd.md` directive.

## Invariants

- **No strictify runtime.** The plugin ships instructions and assets only. Behavior
  is produced by the agent following `SKILL.md`, and by the tools (ruff, mypy,
  pre-commit, …) it installs into the *target* repo. Strictify itself has no
  dependencies to install and nothing to import.
- **Hook scripts are self-contained and stdlib-only.** Every script in `scripts/`
  imports nothing beyond the standard library (`argparse`, `ast`, `re`, `sys`,
  `pathlib`) so it can be dropped into any target repo and run under pre-commit
  without adding dependencies.
- **Agent-readable output.** Every hook reports violations as
  `{file}:{line}: {message} -- {remediation}`, exits nonzero on failure, and honors
  `# allow: {hook-name}` per-line exemptions. This contract is what lets both humans
  and agents act on findings.
- **Merge, never clobber.** The apply phase only adds or tightens target-repo
  settings; it never removes existing user config, and the user can veto any category.
- **Category count is a shared constant.** The "22 categories" figure appears in the
  skill, the README, and both manifests. Changing the set means updating all four.

## Non-goals

- Strictify does not enforce anything on *this* repo — there is no Python package
  here, no `pyproject.toml`, and the hook scripts are payloads, not this repo's own
  pre-commit config.
- It targets Python repos only; the analysis and configs assume a Python toolchain.

Revisit this file a couple of times a year, or whenever a category is added, split,
or removed — not on every edit.
