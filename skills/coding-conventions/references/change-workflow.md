# Change workflow

## Reproduce bugs before fixing them

For a behavior bug, capture the reported symptom in a focused failing test or
another repeatable check. Confirm that it fails for the expected reason before
changing production code, then verify the fix and relevant regressions. Assert
observable behavior rather than the implementation's shape.

Trivial text edits do not need a test suite. If no practical automated
reproduction exists, explain the limit and use the closest meaningful check.

## Check consumers before adding compatibility code

Before introducing a legacy wrapper, alias, or fallback, identify its consumers.
Remove unused interfaces and update callers directly when they are within the
requested migration. Public APIs with external consumers may need compatibility;
state the concrete contract and why the compatibility path remains necessary.

Do not infer dead code from names or ban re-exports that form an intentional
public API. Follow the project's API and compatibility policy.

## Put gotchas beside the code they describe

Document verified, non-obvious behavior at its owner: a code comment explaining
the reason, a docstring for callers, or module documentation for a broader
invariant. Use an existing operational skill or runbook for deployment procedures.

Keep top-level agent instructions focused on project entry points. Do not add
a session hook or permanent rule for every surprising detail encountered.
