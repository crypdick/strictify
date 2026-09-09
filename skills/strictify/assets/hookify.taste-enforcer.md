---
name: taste-enforcer
enabled: true
event: prompt
pattern: don.?t use|always prefer|avoid|never do|instead of|I hate when|stop using|should always|should never|prefer .+ over|ban |forbid
action: warn
---

The prompt matched a keyword that may indicate a coding preference.

When the user expresses a coding preference that should apply to future work, determine whether it can be enforced with:

1. **A prek hook script** — if it's about code patterns that can be detected statically (e.g., "don't use bare except", "avoid print statements"). Create or update a script in `scripts/prek_hooks/` and wire it into `prek.toml`.

2. **A hookify rule** — if it's about Claude's behavior during sessions (e.g., "don't create utils.py files", "always use NewType for IDs"). Create a `.claude/hookify.{name}.md` rule.

3. **A pyproject.toml setting** — if it maps to an existing tool's configuration (e.g., "ban star imports" → ruff rule).

If an existing hook or rule missed the issue, check its pattern, event type, and edge cases, then propose a fix.

Check earlier messages in this conversation for preferences this hook missed, and write hooks for those too.
