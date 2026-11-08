---
name: coding-conventions
description: Review or apply coding conventions for module structure, types and parsing, change workflow, and durable preferences. Use for code design or conventions reviews and documenting project coding preferences; use strictify for tool and hook setup.
---

# Coding conventions

Apply advisory design guidance to the requested code or project conventions.
Read existing project guidance and the affected callers before proposing changes.
Load only the references relevant to the current concern:

- Module names, shared ownership, or composition:
  [module structure](references/structure.md).
- Domain primitives, parsing, or validation:
  [types and boundaries](references/types-and-boundaries.md).
- Bug reproduction, compatibility decisions, or discovered gotchas:
  [change workflow](references/change-workflow.md).
- Retaining coding preferences or keeping docs aligned with code:
  [preferences and documentation](references/preferences-and-documentation.md).

Fit recommendations to actual domain errors and maintenance costs; a matching
name or syntax is not proof of a design problem.

## Review or edit code

- Stay within the requested scope. Explain a concrete consequence for each
  finding, such as confused identifiers, repeated validation, or unclear ownership.
- Use domain-specific module names, types that preserve useful distinctions,
  and boundary parsers that return validated values. Preserve established APIs
  and framework conventions unless their migration is part of the request.
- Reuse existing types and helpers. Do not add wrappers, validation frameworks,
  or abstractions solely to satisfy a convention.
- When editing behavior, use the project's tests. When reviewing, report
  actionable findings without changing code unless edits were requested.

## Establish or update conventions

When asked to document conventions or retain a durable preference, adapt the
relevant guidance into the project's existing canonical conventions document,
or root `CONVENTIONS.md` if none exists. Preserve local decisions and use domain
examples. Keep temporary task instructions out of permanent guidance.

Link the document from the agent instructions used by the project when that
edit is authorized. A skill is selected for relevant tasks; its presence does
not guarantee that every coding turn reads these conventions. Linked project
guidance provides the persistent entry point.

For mechanically checkable preferences, prefer an existing tool setting or
repair an existing check. Use Strictify when setup of executable enforcement is
requested. These conventions do not install hooks or turn advice into blockers.
