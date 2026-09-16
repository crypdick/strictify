# Architecture boundary enforcement

Use for category 15 when a Python repo has meaningful package boundaries and
cross-package consumers. Choose roles, public API conventions, and strictness from
the repo's actual responsibilities. Small programs may need only a documented
import invariant. This reference specifies enforcement behavior; it does not ship
an architecture checker or prescribe one universal layer hierarchy.

## Choose one executable policy

Read existing architecture docs, agent instructions, import checks, and exceptions.
Trace representative callers through their public APIs to concrete dependencies.
Execution order is not import direction: label an arrow `A imports B` explicitly.

Reuse a checker already in the repo when it can express the required contracts.
Otherwise evaluate an established dependency-boundary tool before writing custom
AST checks. Verify the chosen tool's behavior against the cases below; a banned
import list alone does not establish package ownership or public API visibility.
Add only checks for gaps, with each invariant owned by one checker.

Keep ownership and allowed dependencies in version-controlled executable config.
Use the selected tool's native format; use `architecture.toml` for a custom policy.
Do not maintain two handwritten copies of the same allowlists. Link to this source
of truth from the canonical architecture map and `AGENTS.md`/`CLAUDE.md`.

## Package ownership and public surfaces

For repos adopting explicit ownership, declare source roots, package roots, roles,
and exact public modules. An architectural package is an owned unit, which can
include internal Python subpackages. Specify how nested ownership resolves, and
reject ambiguous or unclassified modules. Include root-level Python modules;
moving shared code outside a package must not evade checks.

Keep a namespace-only parent from silently owning every future sibling package.
New modules inside an owned unit inherit its internal status; new architectural
units need explicit registration. Where plugin namespaces deliberately allow
new peers, a one-level family such as `project.plugins.*` can assign ownership
and an exact `{root}.api` surface. Recursive `**` families must not silently
promote implementation subpackages to peers.

Default to one package-local `<package>.api` for each multi-module unit with
external consumers. A facade consisting entirely of curated re-exports is useful.
Keep implementation modules internal regardless of whether their names start with
an underscore. Single-module units may expose their root module directly; wholly
internal packages need no public surface. Preserve established public APIs when
compatibility matters, recording exact alternatives rather than automatically
renaming a published interface. Do not centralize unrelated facades in one package.

## Two independent import gates

Every cross-package import must satisfy both:

- **Visibility:** its target is an exact declared public module of the owning unit.
- **Direction:** the importer's role or package may depend on that target's role or
  package. A public API is not permission for every caller to use it.

Imports within one owned unit remain internal. Distinct packages sharing a role
gain no implicit permission to import each other; express that permission when
intended. For a layered policy, reject cycles between distinct roles and unknown
role references. If peer imports are allowed, check package cycles separately when
the repo requires an acyclic package graph. Do not confuse these two cycle checks.

List composition roots by exact module name. These modules may select and wire
private concrete implementations across otherwise restricted boundaries. Keep
exceptions confined to assembly; do not exempt a whole application package.
Reject stale composition-root names and document which gates they bypass.

Choose roles by responsibility. For a ports-and-adapters design, distinguish
adapters that invoke use cases from adapters that implement capabilities used by
those use cases. Move stable semantic contracts inward; use a use-case-owned port
when substitution, trust, lifecycle, or transaction ownership needs inversion.
A facade provides encapsulation, not dependency inversion. Avoid adding a port
for every concrete dependency or requiring a dependency-injection framework.

## Shared root-module budgets

When root-level shared modules are becoming dependency hubs, propose a limit on
distinct direct first-party importers per module. Select a threshold from the
repo's size and coupling; do not copy a fixed number from another project. Count
importing modules, not import statements or visualization graph degree.

Allow justified exceptions only for exact source paths, with a reason. An inbound
budget exemption must not relax the module's outbound dependency rules. Existing
over-budget modules may use a shrinking count baseline; growth fails, improvement
requires lowering the recorded count, and reaching the limit removes the entry.

## Adopt and shrink an exact baseline

First distinguish real design debt from a misclassified role or intentional public
API. Fix policy errors before measuring debt. Install checks and preserve current
behavior within the approved scope; a larger package migration is separate work.

If adoption needs exceptions, keep them in the tool's baseline format or
`architecture-baseline.toml`. Bootstrap once from reviewed current violations.
Each exception identifies the importer, imported target, gate, import kind
(runtime or type-checking), occurrence count, and reason. Include role identity
where needed to prevent a role change from silently reusing an exception. Do not
key exceptions by line number, use wildcard ignores, or allow one total count to
hide replacement of a removed violation with a different one.

On every check:

- Fail on any unrecorded violation or growth in a recorded occurrence count.
- Fail on stale entries or reduced counts until the baseline is shrunk.
- Reject duplicate, malformed, or unexplained exceptions.
- Keep policy/schema errors outside the baseline; debt must not hide invalid
  ownership, missing public modules, or invalid role references.

Treat policy and baseline edits as reviewed changes. A current-tree check cannot
prove that someone did not add an exception in the same commit. Never regenerate
the baseline or weaken the policy just to make a failing check pass.

Burn down debt one owned package at a time: verify its role, curate its public API,
migrate all cross-package consumers, update its declared surface, resolve direction
violations, and remove every stale exception in that pass. Preserve compatibility
where required. A pass is complete when its behavior checks and boundary checks
pass without the removed exceptions.

## Integration and observable verification

Run architecture checks over all configured first-party roots, not just changed
files: a facade or policy edit can invalidate untouched consumers. In prek use
`pass_filenames = false` and `always_run = true`. Invoke the same check from CI,
either through the existing full-hook job or directly. Configure the actual
installed command; do not add an entry for a nonexistent bundled script.

Check runtime imports, relative imports, re-exports, and `TYPE_CHECKING` imports.
For repos using dynamic imports, cover literal loader targets where supported.
Document limits for computed module names and alias resolution; AST analysis
does not prove the absence of arbitrary runtime dependencies. Generated code,
tests, and separate runtimes need explicit source scope, not silent omissions.

Use small temporary fixture packages through the selected checker's public CLI
or public API to verify the adopted rules. Establish failing cases before adding
custom enforcement, then run the same cases against the implementation:

- An allowed public import passes; importing an internal module from an otherwise
  allowed role fails visibility; an import of a public module from a forbidden
  role fails direction. Violating both produces both findings.
- Internal imports pass. An exact composition root can wire an adapter, while a
  sibling module cannot borrow its exception.
- Adding an unowned architectural unit fails; adding an internal module does not
  expose it. A declared public target must exist and belong to its declared owner.
- Relative and type-checking forms of a forbidden import remain forbidden.
  Exercise literal dynamic imports if the repo relies on them.
- Invalid roles, stale roots, duplicate ownership, and prohibited cycles fail.
  Test family expansion and root-module budgets only if those features apply.
- A reviewed exact baseline passes. Another target cannot reuse its allowance;
  increased occurrences fail; removing an import requires shrinking or deleting
  its baseline entry.
- If inbound budgets apply, repeated imports by one module count once. An exact
  budget exemption leaves outbound restrictions active.

Diagnostics should identify the source location, importer, target, violated gate,
and permitted surface or direction, with a concrete remediation. Exit nonzero on
violations and malformed policy. Run the full check on the target repo, its normal
behavior tests for any migrated code, and the required hook suite before handoff.
