# Architecture boundary enforcement

Use category 15 for repos with meaningful package boundaries and external
consumers. Derive roles and APIs from actual responsibilities. Small programs may
need only a documented import invariant. The [bundled toolkit](architecture-toolkit.md)
provides a checker when existing tools cannot enforce these contracts.

## Choose one executable policy

Read architecture docs, agent instructions, checks, and exceptions. Trace callers
through public APIs to dependencies. Label arrows `A imports B`; execution order
is not import direction.

Prefer existing enforcement or the bundled toolkit over a new checker.
Assign each invariant to one checker. Keep ownership and dependency rules in its native config
(or `architecture.toml` for custom policy), linked from the architecture map and
agent instructions. Do not duplicate allowlists.

## Package ownership and public surfaces

Declare source roots, owned packages, roles, and exact public modules. Include
root-level modules. Define nested ownership and reject ambiguous or unowned
modules. Internal additions inherit ownership without becoming public; separate
architectural units need registration.

Namespace parents must not silently own future siblings. Deliberate plugin
families may use one-level `project.plugins.*` ownership with `{root}.api` surfaces;
recursive `**` must not promote implementation packages to peers.

Prefer a package-local `<package>.api` for multi-module units with external
consumers; curated re-exports are sufficient. Keep other modules internal
regardless of underscores. Single-module units may expose their root; internal-only
units need no public surface. Preserve established APIs through exact alternatives.

## Two independent import gates

Every cross-package import must satisfy both:

- **Visibility:** The target is an exact public module of its owner.
- **Direction:** The importer's role/package may depend on the target's role/package.

Internal imports stay within one owner. Same-role packages need explicit permission
to import peers. Reject unknown roles and cycles between distinct roles. Check
package cycles separately if peers must also form an acyclic graph.

Name composition roots exactly. Document which gates they bypass for assembly of
private implementations; do not exempt sibling modules or whole applications.
Reject stale names.

For ports-and-adapters designs, distinguish callers of use cases from providers
of capabilities. Move stable contracts inward. Introduce use-case-owned ports
where substitution, trust, lifecycle, or transaction ownership needs inversion.
A facade only encapsulates; it does not invert dependencies. Do not require a port
for every dependency or a dependency-injection framework.

## Shared root-module budgets

Where shared root modules become dependency hubs, limit distinct direct first-party
importers per module. Choose a threshold from repo size and coupling. Count modules,
not import statements or graph degree. Exact path exemptions need reasons and
must leave outbound rules active. Existing excess may use a count baseline that
fails growth and requires updating after improvement or removal at the limit.

## Adopt and shrink an exact baseline

Fix misclassified roles and intentional API declarations before recording debt.
Keep broader migrations outside enforcement setup unless already authorized.

Bootstrap reviewed exceptions once in the tool's format or
`architecture-baseline.toml`. Record importer, target, gate, runtime/type-checking
kind, occurrence count, reason, and role identities where needed. No line-number
keys, wildcard ignores, or aggregate counts that let one violation replace another.

Fail on unrecorded violations, growth, stale/reduced entries, duplicates, malformed
records, and missing reasons. Policy/schema errors cannot enter the baseline.
Never regenerate it or weaken policy to pass checks. Review edits: a current-tree
check cannot prevent someone from expanding exceptions in the same commit.

During migrations, update APIs, consumers, policy, and exceptions together.
Preserve required compatibility and verify behavior and boundaries.

## Integration and observable verification

Check all configured roots, including tests, generated code, and separate runtimes
unless explicitly excluded. Use `pass_filenames = false` and `always_run = true`
in prek, and run the same installed command in CI. Unchanged consumers can break
when policy or facades change.

Cover static, relative, re-export, and `TYPE_CHECKING` imports; literal dynamic
imports where supported. Document computed-name and alias-resolution limits.
AST analysis cannot prove the absence of runtime dependencies.

Verify policy through the public CLI/API with fixtures covering allowed imports,
each enforced gate, invalid declarations, and baseline growth or removal. Exercise
composition roots, package families, and budgets when configured. Check diagnostic
content and exit status, not private implementation details.

Diagnostics must identify location, importer, target, gate, permitted API/direction,
and remediation. Exit nonzero for violations or malformed policy. Run the full
repo check, behavior tests for migrated code, and required hooks before handoff.
