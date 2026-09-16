# Architecture

Strictify is a Claude Code and Codex plugin containing instructions and assets for
adding Python code-quality enforcement to a target repo. Both hosts read the same
`.claude-plugin` marketplace metadata and `skills/strictify/SKILL.md`. The agent
follows the skill's analyze → propose → apply workflow and writes config and scripts
into the target repo. Claude Code also reads the bundled hookify rules.

## Codemap

### `.claude-plugin/`

`plugin.json` declares name, version, and description;
`marketplace.json` lets the repo be installed as a single-plugin marketplace in
Claude Code or Codex. These two files must agree on name and version. No behavior
lives here.

### `commands/strictify.md`

The `/strictify` slash command. Its front-matter gathers context (directory listing,
git status, existing `pyproject.toml` / `prek.toml` / `AGENTS.md`,
package manager, layout) via `!` shell substitutions, then hands off to the skill.
The command is a thin entry point; all logic lives in the skill.

### `skills/strictify/`

- **`SKILL.md`** — the workflow. Defines the 22 enforcement categories, the
  analyze/propose/apply phases, conflict handling, and pointers to every resource
  below. Start here to understand what strictify does. `SKILL.md`, `README.md`, and
  the plugin manifests all quote "22 categories" and must stay in sync.
- **`references/`** — the configs the agent merges into a target repo:
  `pyproject-strict.md` (ruff/mypy/pytest/coverage/vulture/deptry), `prek-config.md`
  (the native `prek.toml` template), and `beartype-setup.md`. The
  `architecture-boundaries.md` reference specifies package ownership, independent
  visibility/direction gates, composition roots, and shrinking baselines for a
  repo-selected checker. Each reference explains when and how to adapt its policy.
- **`scripts/`** — custom prek hook scripts copied into the target repo's
  `scripts/prek_hooks/`: `check_exception_handling.py`,
  `check_file_length.py`, `check_timeless_comments.py`, and
  `check_private_test_imports.py`. Ruff owns print/logging and future-import checks.
- **`assets/`** — files copied into the target repo. `hookify.*.md` rules
  (taste-enforcer, no-junk-drawers) and `agents.red-green-tdd.md` go into `.claude/`;
  only mechanical, low-false-positive matches ship as hooks. `CONVENTIONS.md-EXAMPLE`
  is copied to the repo root as `CONVENTIONS.md`, adapted, and referenced from
  `CLAUDE.md`/`AGENTS.md` — it holds the judgment-based principles (composition over
  inheritance, parse-don't-validate, semantic types, code/doc coupling) that require
  reading the code to apply.

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
  `# allow: {hook-name}` exemptions on the relevant line (or in the first five
  lines for file length). Ruff owns syntax and encoding diagnostics. This contract
  lets both humans and agents act on findings.
- **Merge, never clobber.** The apply phase only adds or tightens target-repo
  settings, and the user can veto any category. A legacy YAML hook config is the
  one format-migration exception: preserve its behavior in native `prek.toml`,
  validate the replacement, then remove the obsolete file so only one runner owns
  the hook lifecycle.
- **Category count is a shared constant.** The "22 categories" figure appears in the
  skill, the README, and both manifests. Changing the set means updating all four.

## Repository boundary enforcement

[architecture.toml](architecture.toml) registers every Python source as a shipped
hook, repository tool, or test. [tools/check_architecture.py](tools/check_architecture.py)
checks that registry and permits only static standard-library imports. A local
module with a standard-library name cannot bypass this restriction. New Python
files require registration; deleted files require removing their registrations.
Git supplies the whole source list: tracked and non-ignored untracked `.py` files,
including root modules. Ignored, untracked build artifacts are outside this scope.

Each hook and tool is a single-module unit whose public surface is its CLI and
public functions. There are no cross-unit static imports, so role layers, `api.py`
facades, cycle checks, and inbound-importer budgets add no constraint here. No debt
baseline is needed. If the repository gains a shared multi-module package, apply
the [category-15 guidance](skills/strictify/references/architecture-boundaries.md)
before changing this policy.

The exact test-loader exception in `architecture.toml` lets that harness load
standalone hooks by source path to test public functions. It does not permit static
third-party imports or grant loader access to other files. Removing the last loader
call makes the exception stale and fails the check. CLI tests also run each hook
as a copied file with isolated Python import paths; Ruff checks private attribute
access in tests.

The checker scans relative imports, re-exports, and type-checking blocks. It
recognizes direct calls to common import loaders, including import aliases, and
rejects them outside the registered harness. It does not trace reassigned callables,
arbitrary reflection, subprocess behavior, or data-file access. This is a static
dependency check; the copied-hook tests verify actual standalone execution.

This repo needs source registration and a stdlib allowlist rather than a package
dependency graph. Import Linter's [package contracts](https://import-linter.readthedocs.io/en/v2.11/get_started/configure/)
do not supply those two checks; the small repo-local checker covers this policy
without adding a dependency or changing the distributed scripts' layout.

`prek.toml` runs the architecture check over the whole tree on every invocation.
[.github/workflows/checks.yml](.github/workflows/checks.yml) runs the same hook suite
on pushes and pull requests. Use `uvx prek install` to enable local commit checks,
and `uvx prek run --all-files` for a full run. The repository checks require
Python 3.11 or newer and Git. Boundary regression tests use temporary repositories
through the checker's CLI.

## Non-goals

- Strictify does not enforce most categories on *this* repo — there is no Python
  package here and no `pyproject.toml`; its native `prek.toml` runs the
  repo-agnostic checks, standalone-script architecture policy, and bundled hook
  regression tests.
- It targets Python repos only; the analysis and configs assume a Python toolchain.

Revisit this file a couple of times a year, or whenever a category is added, split,
or removed — not on every edit.
