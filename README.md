# strictify

Strictify turns Python coding standards into automated checks, giving AI coding
agents concrete feedback when they break the rules. It works as a Claude Code
and Codex plugin: it inspects your repo, proposes checks that fit, and applies
only changes you approve.

Inspired by [AI Is Forcing Us to Write Good Code](https://bits.logic.inc/p/ai-is-forcing-us-to-write-good-code)
and [Harness Engineering](https://openai.com/index/harness-engineering/).

## Install

### Claude Code

```shell
claude plugins add github:crypdick/strictify
```

Run `/strictify` in your repo.

### Codex

```shell
codex plugin marketplace add crypdick/strictify
codex plugin add strictify@strictify
```

Ask Codex to "strictify this repo."

## What it does

The [skill](skills/strictify/SKILL.md) covers 22 categories: linting and types,
dead code and dependencies, tests and coverage, architecture boundaries,
worktree isolation, and ongoing enforcement. It merges existing settings and
installs approved tools and configures hooks through `prek`.

The plugin also ships [coding-conventions](skills/coding-conventions/SKILL.md)
for advisory reviews of module naming, semantic types, boundary parsing, and
durable preferences. Ask it to review code or establish project conventions.
For guidance across ordinary coding tasks, keep conventions linked from project
agent instructions. Neither skill requires Hookify. See
[advisory migration](skills/strictify/references/advisory-migration.md) when
replacing existing reminders.

## Releases

After checks pass for a push to `main`, CI increments the plugin's patch version,
synchronizes `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`,
checks the release, and pushes a `Release X.Y.Z` commit. To choose a release
version, increase `.claude-plugin/plugin.json` in your commit; CI preserves a
version higher than the branch version before the whole push. Decreased versions
fail preparation. Retries reuse the release commit; superseded runs skip release.
Feature branches and pull requests only run checks. Branch rules must allow the
GitHub Actions bot to push release commits using `GITHUB_TOKEN`.

## License

MIT
