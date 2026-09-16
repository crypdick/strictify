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
  repo-selected checker. `architecture-toolkit.md` documents the bundled checker's
  installation, schema, and starter template. Each reference explains when and how
  to adapt its policy.
- **`scripts/`** — custom prek hook scripts copied into the target repo's
  `scripts/prek_hooks/`: `check_exception_handling.py`,
  `check_file_length.py`, `check_timeless_comments.py`, and
  `check_private_test_imports.py`. The `architecture/` subdirectory is a reusable
  stdlib-only package: its `api.py` is the public CLI/API; policy/schema, discovery,
  imports, baseline, budgets, cycles, and standalone constraints remain internal.
  Copy the full directory including its MIT license. Ruff owns print/logging and
  future-import checks.
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
- **Hook scripts are self-contained and stdlib-only.** The four single-file hooks in `scripts/`
  import nothing beyond the standard library (`argparse`, `ast`, `io`, `re`,
  `sys`, `tokenize`, `pathlib`) so it can be dropped into any target repo and
  run under prek without adding dependencies. A unittest regression suite exercises hook behavior and the shipped Ruff
  configuration; prek supplies pinned Ruff for these integration checks.
- **Agent-readable output.** The single-file hooks report violations as
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

[architecture.toml](architecture.toml) is a worked instance of the same executable
schema shipped to target repositories. [The public toolkit CLI](skills/strictify/scripts/architecture/api.py)
checks ownership, exact public modules, independent visibility/direction gates,
policy cycles, and optional package cycles. It replaces the repository-only source
registry checker; there is no second architecture implementation.

The four single-file hooks and repository tool are exact single-module units.
The toolkit is one multi-module package exposing only its `api` module. Tests form
one owned package. Strictify needs no application layers, composition roots,
inbound-importer budget, or adoption baseline. Its graph is currently independent
units, with internal toolkit imports. The reusable toolkit's layered behavior,
composition roots, optional budgets, and ratchet are exercised in temporary fixture
repositories through a copied package's public CLI.

The repository enables `stdlib_only` across all scanned sources and exact
`standalone_modules` for the independent scripts and existing test harnesses.
The exact loader exception permits the public-hook test harness, not static
third-party imports or other loader callers. Unused exceptions fail. Tests also
run each single-file hook with isolated Python import paths. The toolkit is copied
and tested as a package, preserving its distinct distribution contract.

Git supplies tracked and non-ignored untracked Python files under the configured
roots. Strictify uses the whole repository root, so new root modules cannot evade
ownership. Source symlinks and stale declarations fail. Git subprocesses clear
inherited `GIT_*` context to protect fixture initialization and `--root` scans.
The [toolkit guide](skills/strictify/references/architecture-toolkit.md) owns the
complete schema, copied-install procedure, baseline rules, and AST limitations.
The [starter policy](skills/strictify/assets/architecture.toml) demonstrates a
small application and test layout without imposing those roles on Strictify.

`prek.toml` runs `python -m skills.strictify.scripts.architecture.api` over the
whole tree. [.github/workflows/checks.yml](.github/workflows/checks.yml) runs the
same hook suite on pushes and pull requests. Use `uvx prek install` locally and
`uvx prek run --all-files` for verification. The checker requires Python 3.11+
and Git, with no external Python dependencies.

## Non-goals

- Strictify does not enforce most categories on *this* repo — there is no Python
  package here and no `pyproject.toml`; its native `prek.toml` runs the
  repo-agnostic checks, shared-toolkit architecture policy, and bundled hook
  regression tests.
- It targets Python repos only; the analysis and configs assume a Python toolchain.

Revisit this file a couple of times a year, or whenever a category is added, split,
or removed — not on every edit.
