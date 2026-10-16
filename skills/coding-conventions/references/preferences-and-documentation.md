# Preferences and documentation

## Durable coding preferences

When the user expresses a preference intended for future work, check existing
conventions and enforcement first. Keep task-specific instructions scoped to the
task; do not turn every preference into a permanent rule.

Record durable guidance in the project's canonical conventions. Prefer an existing
tool setting for mechanically checkable rules, then a focused static check if
needed. Keep contextual design judgments in conventions and code review. If an
existing check missed a real violation, reproduce the miss and repair that check
rather than adding another.
Confirm the chosen enforcement runs in the project's tools and agent harness.

## Keep code and its documentation coupled

Where docs repeat a code value, add a back-pointer at its definition:

```python
# NOTE: Update docs/security.md § Credential Handling if you change this list.
allowed_vars = ["PATH", "HOME", "USER"]
```

Update linked docs with code changes. When editing prose lists or tables, check
whether the corresponding code needs a pointer. Skip this where no published
docs duplicate code values or drift would not mislead readers.
