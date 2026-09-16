---
name: taste-enforcer
enabled: true
event: prompt
pattern: don.?t use|always prefer|avoid|never do|instead of|I hate when|stop using|should always|should never|prefer .+ over|ban |forbid
action: warn
---

If this prompt expresses a durable coding preference, codify it with an existing
`pyproject.toml` tool setting, a static check in `scripts/prek_hooks/` wired into
`prek.toml`, or a `.claude/hookify.{name}.md` rule for session behavior.

If enforcement missed it, inspect the pattern, event, and edge cases and propose
repair. Check earlier messages for missed preferences and enforce those too.
