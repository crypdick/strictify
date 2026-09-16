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

## License

MIT
