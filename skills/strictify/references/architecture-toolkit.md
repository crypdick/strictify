# Install the bundled architecture toolkit

Use when existing tools cannot enforce the [boundary contracts](architecture-boundaries.md).
Requires Python 3.11+ and Git; no third-party runtime dependencies. Adapted from
Pynchy's MIT-licensed checker.

## Setup on a new repository

1. Copy the entire `scripts/architecture/` directory, including `LICENSE`, to
   `scripts/prek_hooks/architecture/`. No editable install or `PYTHONPATH` change
   is needed.
2. Copy `assets/architecture.toml` to root `architecture.toml` and adapt its roles
   and imports. Its example uses
   `src/app/{__init__,cli}.py`, `src/app/core/{__init__,api}.py`, and `tests/__init__.py`.
   Do not create layers to fit the example.
3. Register intended roots, including tools, tests, and separate runtimes. Use
   `path = ".", module = ""` for flat layouts and the importable package prefix
   for packages under `src/`. Exclude nested roots from their enclosing root;
   document intentional scope exclusions.
4. From the repo root, run:

   ```bash
   uv run --no-project python -m scripts.prek_hooks.architecture.api
   ```

   `--root` selects the repo; the copied package must remain importable from the
   invocation directory. `--policy` and `--baseline` accept absolute paths or paths
   relative to `--root`. Exit codes: 0 success, 1 violations, 2 invalid config.
5. Fix classification errors, then review exact debt exceptions using the baseline
   format below. No baseline means zero allowed debt; no regeneration command exists.
   Once passing, merge this hook into prek:

   ```toml
   [[repos]]
   repo = "local"
   hooks = [
     {id = "architecture", name = "Architecture boundaries", entry = "python -m scripts.prek_hooks.architecture.api", language = "python", pass_filenames = false, always_run = true},
   ]
   ```

6. Run the same full-hook command in CI and `uvx prek install` locally. Link policy
   from the architecture map and agent instructions. Verify the installed CLI
   against the [contract cases](architecture-boundaries.md#integration-and-observable-verification)
   and run behavior tests for migrated code.

## Policy schema (version 2)

Unknown fields, malformed types, duplicate lists, and stale declarations fail.
This is Strictify's schema: do not copy another checker's version-2 policy or
baseline verbatim. In particular, baseline records include both role identities,
and inbound-budget exemptions require reasons.

- `version`: integer `2`.
- `source_roots`: nonempty array of `{path, module, exclude?}`. Paths are exact,
  repository-relative directories. `module` is an exact dotted prefix, or `""`
  for a flat root. Each root must discover at least one source. `exclude` contains
  exact relative paths or directory subtrees ending `/**`, not general globs.
  Git supplies tracked and non-ignored untracked Python files; ignored untracked
  build output is not scanned. Symlinked source is rejected. Inherited `GIT_*`
  context cannot redirect discovery into another repository.
- `roles`: nonempty table. Each role has `allowed_dependencies`, an exact list of
  role names, and optional `violation_guidance`. Cross-package same-role imports
  require explicit self-role permission. Cycles between distinct roles fail.
- `packages`: array of `{name, root, role, public_modules, include_descendants?}`.
  Names identify unique units; roots are unique exact modules. The deepest root
  owns descendants unless `include_descendants = false`. Every discovered module
  needs an owner. Exact public modules must exist and belong to that unit. Prefer
  `<package>.api` for multi-module units; explicit established API alternatives
  remain legal to preserve compatibility. An empty list means private-only.
- `package_families`: optional array of `{name, root_pattern, role, public_modules}`.
  The sole wildcard form is a one-level `namespace.*`, expanding actual package
  directories with `__init__.py`. Public templates may use `{root}`. Empty families,
  overlapping roots, recursive wildcards, and missing public surfaces fail.
- `composition_roots`: optional exact module list. Only these modules bypass both
  visibility and direction gates, not ownership, budgets, or package-cycle checks.
  Stale names fail; sibling modules receive no exemption.
- `check_package_cycles`: optional boolean, default false. Reject actual package
  dependency cycles, including type-checking and composition-root edges. Independent
  from the always-enforced role graph check.
- `default_violation_guidance`: optional remediation text for direction findings.
- `root_module_max_inbound_importers`: optional positive integer. Counts distinct
  importing modules for each non-package `.py` directly inside a source root,
  even when that module belongs to a larger architectural package. Repeated imports
  by one module count once. Omitting the field disables the budget.
- `file_overrides`: optional exact repository-relative source-path table. Each
  entry must contain `allow_unbounded_inbound_imports = true` and a nonempty
  `reason`. Only root modules with an enabled budget may be exempted. Exemptions
  never relax outbound visibility or direction.
- `standalone_modules`: optional exact module list. These may import only stdlib
  modules, not first-party siblings or third-party dependencies. Local module
  names conservatively protect against shadowing stdlib imports.
- `stdlib_only`: optional boolean, default false. All scanned modules may import
  stdlib or first-party modules only; first-party imports still obey both gates.
- `dynamic_loading`: optional exact module-to-reason table. Allows recognized
  loader calls under standalone/stdlib-only constraints. Scope this to intentional
  test harnesses or plugin loaders; it does not bypass static-import restrictions
  or first-party dependency gates. Unused exceptions fail.

## Reviewed baseline

Record each gate independently; a single import violating both gates needs two
records. `imports` is an exact multiset: repeat a target for repeated occurrences.
No line numbers or wildcards. New targets, growth, and stale/reduced entries fail.
Changing either role cannot silently reuse the exception.

```toml
version = 2

[[violations]]
importer = "app.adapter.api"
importer_role = "adapter"
target_role = "core"
rule = "visibility" # or "direction"
kind = "runtime-import" # or "type-checking-import"
count = 1
imports = ["app.core.implementation"]
reason = "Move this caller to the core facade with its package migration."

[[root_module_inbound_imports]]
path = "src/app/shared.py"
count = 12
reason = "Move shared consumers into their owning packages."
```

The inbound count must exactly match an over-budget current module. Growth fails;
improvement requires shrinking the record; reaching the policy limit requires
removing it. Schema and ownership problems cannot be baseline exemptions. Review
policy/baseline edits in code review: a current-tree checker cannot prohibit someone
from expanding the policy and baseline in the same commit.

## Scope and limitations

The AST checker follows static imports, relative imports, re-exports, and
`TYPE_CHECKING` blocks without executing source. It checks exact module surfaces,
not exported symbol names or runtime attribute access. Recognized dynamic forms
are absolute string-literal `__import__(...)`, `importlib.import_module(...)`, and
imported/aliased `import_module(...)`. Relative/computed dynamic targets,
`builtins.__import__`, reassigned callables, arbitrary reflection, subprocesses,
and data-file access are not a complete dependency graph. Standalone mode also
rejects recognized direct import loaders (including common aliases), but is not
a sandbox. Keep behavior tests for copied scripts and actual runtime boundaries.

Source roots define scan scope; they need not include every Python file. Empty/missing roots and duplicate discovered module names fail; code
outside configured roots does not. Deliberately scope generated or vendored code.

## Strictify as the worked example

Strictify uses this package through `python -m skills.strictify.scripts.architecture.api`.
Its [architecture map](https://github.com/crypdick/strictify/blob/main/ARCHITECTURE.md#repository-boundary-enforcement)
explains the repo policy, standalone constraints, and tests.
