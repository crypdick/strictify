# strictify-repo Plugin Design

## Overview

`strictify-repo` is a Claude Code plugin that applies opinionated Python code quality enforcement to any repository. It analyzes what's already in place, proposes strictness additions across 21 categories, checks in with the user before applying, and installs self-reinforcing hookify rules that capture ongoing taste preferences.

### Philosophy

Inspired by [AI Is Forcing Us to Write Good Code](https://bits.logic.inc/p/ai-is-forcing-us-to-write-good-code) and [Harness Engineering](https://openai.com/index/harness-engineering/): AI agents amplify whatever quality level your codebase has. The only guardrails are the ones you set and enforce. This plugin exists to enforce taste programmatically — not strictness for its own sake, but practices that make code better for both humans and AI agents to work with.

From OpenAI's harness engineering experience: "building software still demands discipline, but the discipline shows up more in the scaffolding rather than the code." The tooling, abstractions, and feedback loops that keep the codebase coherent are the primary leverage point. Agent legibility — making code, docs, and architecture navigable by AI — is a first-class goal alongside human readability.

### Core Principles

1. **Enforce taste, not arbitrary strictness** — every rule exists because it improves code quality, not because a linter supports it
2. **Detect and fill gaps** — works on both new and existing projects, merging strictness into whatever's already there
3. **Bias for strict, but check in** — proposes aggressive defaults, lets the user veto what doesn't fit
4. **Self-reinforcing** — hookify rules capture new taste preferences as the user expresses them during normal work

## Target

- **Language**: Python only
- **Projects**: Both existing projects (adding strictness on top) and new/near-empty projects (bootstrapping from scratch)
- **Package managers**: Detects uv, pip, poetry — adapts commands accordingly

## Plugin Structure

```
strictify-repo/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── strictify-repo.md              # /strictify-repo slash command entry point
└── skills/
    └── strictify-repo/
        ├── SKILL.md                    # Core three-phase workflow
        ├── references/
        │   ├── pyproject-strict.md     # Strict tool configs (ruff, mypy, coverage, vulture, xenon, pytest)
        │   ├── pre-commit-config.md    # Full .pre-commit-config.yaml template
        │   └── beartype-setup.md       # Beartype integration patterns
        ├── scripts/
        │   ├── check_exception_handling.py
        │   ├── check_print_statements.py
        │   ├── check_file_length.py
        │   ├── check_timeless_comments.py
        │   └── fix_future_annotations.py
        └── assets/
            ├── hookify.taste-enforcer.local.md
            ├── hookify.no-junk-drawers.local.md
            ├── hookify.parse-dont-validate.local.md
            └── hookify.semantic-types.local.md
```

## Workflow

### Phase 1: Analyze

Scan the target repo to understand its current state:

- Does `pyproject.toml` exist? What tools are already configured?
- Does `.pre-commit-config.yaml` exist? Which hooks are present?
- Is there a `src/` or flat layout? What's the package name?
- What Python version does the project target?
- Does it use `uv`, `pip`, or `poetry`?
- Is beartype already a dependency?
- What's the current test setup (if any)?

### Phase 2: Propose

Present the user with a summary of what's already in place and what would be added/tightened. For each category, show: **current state → proposed change**. The user can veto any category before application.

#### Categories

**Static Analysis & Type Safety**

1. **Pre-commit framework** — install if missing, add missing hooks
2. **Ruff** — lint rules (`E`, `W`, `F`, `I`, `B`, `UP`, `C4`, `SIM`, `RUF`) and format config
3. **mypy** — `strict = true` with pragmatic exceptions for the project's frameworks
4. **Beartype** — add dependency, insert `beartype_this_package()` in package `__init__.py`
5. **Semantic typing guidance** `[blog]` — hookify rule nudging toward `NewType`/`TypeAlias` for domain concepts
6. **Parse-don't-validate discipline** `[blog]` `[harness]` — hookify rule encouraging boundary parsing with constrained types (Pydantic models, frozen dataclasses, `NewType`) instead of scattered validation. "Don't probe data YOLO-style — validate boundaries or rely on typed SDKs."

**Code Health**

7. **Vulture** — dead code detection with sensible ignore list
8. **Xenon** — cyclomatic complexity ceiling (max-average C)
9. **Pyupgrade + flynt** — modernize syntax to target Python version
10. **Structured logging** `[harness]` — `check_print_statements.py` also detects unstructured logging patterns (string concatenation/%-formatting in log calls) and nudges toward structured `logger.info("message", key=value)` style

**Testing & Coverage**

11. **Coverage enforcement** `[blog]` — `fail_under = 100`, coverage report as explicit todo list, curated `exclude_lines` for `TYPE_CHECKING`, `@abstractmethod`, `__repr__`, etc.
12. **Fast test infrastructure** `[blog]` — pytest-xdist parallel execution, test timeouts, `--failed-first` for fast feedback

**Architecture & Organization**

13. **Filesystem discipline** `[blog]` — file length limits (400 lines), hookify rule warning on `utils.py`/`helpers.py`/`misc.py` creation. The problem isn't shared code, it's *anonymous* shared code — if you need a shared utility, name it after what it does.
14. **Architectural layer enforcement** `[harness]` — analyze the project's domain structure and propose dependency direction linting. For a Django project, this might be models → services → views → urls. For a CLI tool: parsing → domain → output. For a data pipeline: extract → transform → load. The agent figures out the appropriate layers for the target project, creates custom lint rules enforcing valid dependency edges, and documents the architecture. Constraints may be lightweight for small projects and more rigid for larger ones.
15. **Quality grades per domain** `[harness]` — create a quality scorecard (`docs/QUALITY.md` or similar) grading each module/domain on coverage, type safety, complexity, and test health. This becomes a living document tracking gaps over time. The agent assesses the current state and produces initial grades, with guidance on how to maintain and update them.

**Environment & Infrastructure**

16. **Ephemeral environment setup** `[blog]` — if uv detected, ensure `uv run` works as single-command entry; add bootstrap script or documentation
17. **Per-worktree app booting** `[harness]` — ensure the app can run in isolation, one instance per git worktree or branch. The agent analyzes what this means for the specific project (configurable ports? separate DB names? isolated caches?) and sets up or documents the necessary configuration. For simple projects this may just be confirming `uv run` works from any worktree; for complex ones it may involve environment variable templating or a dev setup script.

**Ongoing Enforcement**

18. **Custom hooks** — exception handling, print/logging bans, timeless comments, future annotations
19. **Hygiene hooks** — trailing whitespace, large files, merge conflicts, debug statements, private key detection
20. **Doc gardening** `[harness]` — set up infrastructure for detecting stale documentation that doesn't reflect actual code behavior. This may be a pre-commit hook that checks doc freshness, a CI job, or guidance for a recurring agent task that scans for drift between docs and code and opens fix-up PRs. The agent assesses what level of doc gardening infrastructure fits the project's maturity.
21. **Taste enforcer** — hookify rule that captures ongoing user preferences

Items marked `[blog]` originate from the "AI Is Forcing Us to Write Good Code" blog post. Items marked `[harness]` originate from OpenAI's "Harness Engineering" post. All others come from battle-tested practices in the gantt-believe-it and cfg repos.

### Phase 3: Apply

For each approved category:

- Merge new settings into existing `pyproject.toml` (or create it)
- Merge new hooks into existing `.pre-commit-config.yaml` (or create it)
- Copy and adapt custom hook scripts to `scripts/pre_commit_hooks/`
- Modify the package `__init__.py` for beartype (if approved)
- Install hookify rules into `.claude/`
- Run `pre-commit install` if not already set up
- Run `uv add --dev` (or `pip install`) for new dev dependencies
- Analyze project domain structure and create architectural layer documentation and lint rules (if approved)
- Create initial quality scorecard in `docs/QUALITY.md` (if approved)
- Set up doc gardening infrastructure appropriate to the project's maturity (if approved)
- Configure per-worktree isolation if applicable (if approved)

## Hookify Rules

Four hookify rules are installed into the target project's `.claude/` directory.

### Rule 1: `hookify.taste-enforcer.local.md`

```yaml
name: taste-enforcer
enabled: true
event: prompt
pattern: don.?t use|always prefer|avoid|never do|instead of|I hate when|stop using|should always|should never|prefer .+ over|ban |forbid
action: warn
```

**Message body:**

> Keyword hit. The user might have expressed a coding preference or taste.
>
> Reminder: always do the following when the user expresses a code preference that should be enforced going forward. Determine whether it can be codified as:
>
> 1. **A pre-commit hook script** — if it's about code patterns that can be detected statically (e.g., "don't use bare except", "avoid print statements"). Create or update a script in `scripts/pre_commit_hooks/` and wire it into `.pre-commit-config.yaml`.
>
> 2. **A hookify rule** — if it's about Claude's behavior during sessions (e.g., "don't create utils.py files", "always use NewType for IDs"). Create a `.claude/hookify.{name}.local.md` rule.
>
> 3. **A pyproject.toml setting** — if it maps to an existing tool's configuration (e.g., "ban star imports" → ruff rule).
>
> If the preference is already enforced by an existing hook or rule but the user still had to say something about it, that means the existing enforcement failed to do its job. Identify why it didn't catch the issue (pattern too narrow? wrong event type? missing edge case?) and propose a fix to strengthen the existing hook or rule.
>
> Also: if the user previously expressed a taste in this conversation that this hook missed as a false negative, write a hook for that too.

### Rule 2: `hookify.no-junk-drawers.local.md`

```yaml
name: no-junk-drawers
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: (utils|helpers|misc|common|shared|general)\.py$
action: warn
```

**Message body:**

> You're creating or editing a junk-drawer module. The blog principle "treat directory structure and filenames as an interface" means every file should have a clear, domain-specific purpose.
>
> Instead of `utils.py`, name the module after what it actually does:
> - `billing/compute.py` not `billing/utils.py`
> - `auth/tokens.py` not `auth/helpers.py`
> - `parsing/csv_reader.py` not `common/misc.py`
>
> The problem isn't shared code — it's *anonymous* shared code. If you genuinely need a shared utility, name it after what it does and put it where it belongs. Prefer a well-named shared package with centralized invariants over hand-rolled helpers scattered across domains. But if the functions are only used by one module, they belong in that module.

### Rule 3: `hookify.parse-dont-validate.local.md`

```yaml
name: parse-dont-validate
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: (isinstance\(.*,\s*(str|int|dict|list)\)|def \w+\(.*:\s*dict\b|-> None.*\n.*raise|\.get\(|if .+ is not None)
action: warn
```

**Message body:**

> Possible validate-then-discard pattern detected. The principle "parse, don't validate" means: coerce unstructured data into constrained types at the boundary of your system, so downstream code never needs to re-validate.
>
> **Instead of validating and discarding the evidence:**
> ```python
> def process(data: dict) -> None:
>     if "user_id" not in data:
>         raise ValueError("missing user_id")  # checked and discarded
> ```
>
> **Parse into a constrained type that carries proof:**
> ```python
> @dataclass(frozen=True)
> class UserRequest:
>     user_id: UserId
>     # Construction IS validation. If it exists, it's valid.
>
> def process(request: UserRequest) -> None:
>     # No validation needed — the type proves it.
> ```
>
> Use Pydantic models, frozen dataclasses, or `NewType` to carry proof through the type system. Parse at the boundary, execute with confidence downstream.
>
> If this is internal code operating on already-parsed types, ignore this message.

### Rule 4: `hookify.semantic-types.local.md`

```yaml
name: semantic-types
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: (user_id|account_id|org_id|slug|token|amount|price|email|url|path)\s*:\s*(str|int|float)\b
action: warn
```

**Message body:**

> Bare primitive type detected for what looks like a domain concept. Semantic types help both humans and AI agents understand the code:
>
> ```python
> from typing import NewType
>
> UserId = NewType("UserId", str)
> Amount = NewType("Amount", int)
>
> def get_user(user_id: UserId) -> User:  # Clear intent
>     ...
> ```
>
> `NewType` is zero-cost at runtime and catches category errors at type-check time (passing an `OrgId` where a `UserId` is expected).
>
> If this is genuinely a raw primitive with no domain meaning, ignore this message.

## Custom Pre-Commit Hook Scripts

Five Python scripts are copied into the target repo's `scripts/pre_commit_hooks/` directory. The agent reads each script from the plugin's `skills/strictify-repo/scripts/` directory, adapts it to the target repo (adjusting paths, package names, allowed directories), and writes the adapted version.

All scripts follow the same contract:
- Accept filenames as arguments (from pre-commit `pass_filenames`)
- Report violations as `{file}:{line}: {message} — {remediation}` where remediation is agent-readable guidance on how to fix the issue (not just what's wrong, but how to make it right). This makes error output useful for both humans and AI agents working on the codebase. `[harness]`
- Exit nonzero on failure
- Support per-line exemption via `# allow: {hook-name}` comments

### `check_exception_handling.py`

Detects:
- Bare `except:` clauses
- `except Exception:` without logging or re-raising
- Exception handlers with only `pass`

Philosophy: fail fast, fix root cause rather than masking errors.

### `check_print_statements.py`

Bans `print()` in production code. Allowed in `tests/`, `scripts/`, and CLI entry points (agent adapts the allowed-paths list per repo). Enforces use of a proper logger (loguru, logging, structlog — whatever the project uses).

Also detects unstructured logging anti-patterns `[harness]`:
- String concatenation in log calls: `logger.info("user: " + user_id)`
- %-formatting in log calls: `logger.info("user: %s", user_id)`
- f-string formatting in log calls: `logger.info(f"user: {user_id}")`

Nudges toward structured logging: `logger.info("user logged in", user_id=user_id)` (for structlog/loguru) or at minimum `logger.info("user logged in", extra={"user_id": user_id})` (for stdlib logging).

### `check_file_length.py`

Enforces max 400 logical lines per file. Supports `# allow: file-length` exemption on the first line. Agent may adjust the limit if the project has a good reason.

### `check_timeless_comments.py`

Detects temporal keywords in comments: "legacy", "new", "old", "previous", "deprecated", "refactor", "TODO", "FIXME", "HACK", "temporary". Comments should describe what and why, not history. Supports `# allow: timeless-comments` exemption.

### `fix_future_annotations.py`

Ensures `from __future__ import annotations` is placed correctly — after shebangs, encoding declarations, PEP-723 metadata blocks, and module docstrings. Runs as a fixer: modifies files in-place and fails the commit if changes were needed.

## Reference Configs

### `references/pyproject-strict.md`

Contains strict configuration sections for:

- **Ruff**: `select = ["E", "W", "F", "I", "B", "UP", "C4", "SIM", "RUF"]`, `line-length = 110`, `preview = true`, per-file ignores for tests/scripts
- **mypy**: `strict = true`, `warn_return_any = true`, `show_error_codes = true`, `pretty = true`, pragmatic `disable_error_code` list, overrides for test files and common frameworks
- **pytest**: `asyncio_mode = "auto"`, `addopts = "--no-header -n auto -q --durations=5 --durations-min=1.0 --cov-report=term-missing --cov-report=html --failed-first"`, `timeout = 20`
- **coverage**: `fail_under = 100`, curated `exclude_lines` (`pragma: no cover`, `TYPE_CHECKING`, `@abstractmethod`, `__repr__`, `raise NotImplementedError`, `if __name__`)
- **vulture**: `min_confidence = 80`, curated `ignore_decorators` and `ignore_names`

### `references/pre-commit-config.md`

Contains a full `.pre-commit-config.yaml` template with:

- Standard hooks (trailing-whitespace, end-of-file-fixer, check-yaml/json/toml, merge conflicts, debug statements, detect-private-key, large files)
- Ruff (check + format)
- Pyupgrade (target Python version)
- Flynt (f-string conversion)
- Xenon (complexity: max-average C, max-modules C, max-absolute C)
- Vulture (dead code, min-confidence 80)
- Local hooks for all five custom scripts
- mypy (via `uv run mypy`)
- pytest (via `uv run pytest`, runs last)

### `references/beartype-setup.md`

Contains:
- The `beartype_this_package()` snippet for `__init__.py`
- `BeartypeConf` options and what they do
- Common issues (suppressing warnings for frameworks that beartype can't decorate)
- How to add beartype as a dev/runtime dependency via uv/pip/poetry

## Command: `commands/strictify-repo.md`

Thin entry point that:
- Gathers repo context via `!`-backtick commands (directory listing, pyproject.toml contents if present, .pre-commit-config.yaml if present, git status, Python version)
- Triggers the strictify-repo skill
- Restricts tools to: Read, Write, Edit, Bash, Glob, Grep, Skill, AskUserQuestion

## Conflict Handling

When existing config already exists:
- **Merge-up**: read existing config, add missing strict settings, tighten existing ones
- **Never remove** user settings — only add or tighten
- **Present diff**: show current state → proposed change for every modification
- **User veto**: the user can reject any category before application
- **Bias strict**: default is to apply everything; the user opts *out*, not in
