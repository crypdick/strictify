# Migrate advisory Hookify rules

Strictify uses the sibling [coding-conventions skill](../../coding-conventions/SKILL.md)
for design guidance. It does not install Hookify rules. Executable checks remain
in prek; project-specific conventions live in linked project documentation.

When replacing existing advisory rules as part of an approved migration:

1. Inspect `hookify.no-junk-drawers*`, `hookify.semantic-types*`,
   `hookify.parse-dont-validate*`, `hookify.parse-into-semantic-types*`,
   `hookify.taste-enforcer*`, and `hookify.doc-code-coupling*` in `.claude/`.
   Check conditions, enabled state, action, and repo-specific wording.
2. Preserve applicable custom guidance in the project's canonical conventions.
   Skip disabled guidance unless the user asks to adopt it. Use the
   [types and boundaries reference](../../coding-conventions/references/types-and-boundaries.md)
   to correct claims that `NewType` or a frozen dataclass
   validates input by itself. Avoid turning syntax matches into blanket bans.
3. Link the conventions from the agent instructions used by the project when
   that edit is authorized. A skill alone does not provide an always-on reminder.
4. Remove only the advisory rules whose guidance has been preserved. Keep
   unrelated rules and existing blocking policy. Report blocking rules separately;
   replacing them with advice would weaken enforcement.

Hookify discovers `.claude/hookify.*.local.md`, so files lacking `.local` are not
loaded. The suffix is a discovery requirement, not a prohibition on tracking
the file in Git. Include both naming forms when inspecting existing guidance.

Keep the migrated guidance in topic references rather than loading every rule
in `SKILL.md`:

- `no-junk-drawers` maps to coding-conventions' module structure reference.
- `semantic-types`, `parse-dont-validate`, and `parse-into-semantic-types` map to
  its types and boundaries reference.
- `taste-enforcer` and `doc-code-coupling` map to its preferences and
  documentation reference.
- `tdd-bug-fixes`, `warn-backwards-compat`, and `document-gotchas` map to its
  change-workflow reference, with stricter project policy kept in local skills.
- Deployment reminders belong in the project's existing operations skill.

Do not duplicate the shared skill across repos to replace identical rules.
Ensure the coding-conventions skill is installed for the agent being used
before deleting local advisory copies. Keep genuinely repo-specific guidance
in that repo's conventions or an existing relevant skill.

## i-insist boundary

i-insist runs provider-owned tool checks across harnesses. Its checker protocol
returns JSON `null` to allow or a denial string to block, without an advisory
warning result. Its prompt handler records overrides rather than dispatching
provider checks for coding-preference reminders.

Keep naming advice, semantic typing, boundary parsing, and preference capture
in coding-conventions. A project can explicitly adopt a hard restriction with
a Strictify-owned checker, but that changes policy rather than preserving a
warning. Keep corresponding static enforcement in prek: i-insist does not infer
shell write targets from normalized file changes. This migration installs no
i-insist registrations and changes no global plugin settings.
