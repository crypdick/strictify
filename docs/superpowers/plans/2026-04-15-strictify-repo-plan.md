# strictify-repo Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `strictify-repo` Claude Code plugin — a `/strictify-repo` command that applies opinionated Python code quality enforcement to any repo.

**Architecture:** A Claude Code plugin with a thin command entry point that triggers a skill. The skill drives a three-phase workflow (analyze → propose → apply). Reference configs, custom hook scripts, and hookify rule assets are bundled in the skill directory.

**Tech Stack:** Claude Code plugin system (markdown + YAML frontmatter), Python 3.13 (hook scripts), pre-commit, ruff, mypy, beartype, vulture, xenon, pytest, hookify.

**Spec:** `docs/superpowers/specs/2026-04-15-strictify-repo-design.md`

---

## File Structure

```
strictify-repo/
├── .claude-plugin/
│   └── plugin.json                          # Plugin metadata
├── commands/
│   └── strictify-repo.md                    # /strictify-repo slash command
└── skills/
    └── strictify-repo/
        ├── SKILL.md                         # Core workflow (analyze → propose → apply)
        ├── references/
        │   ├── pyproject-strict.md          # Strict pyproject.toml sections
        │   ├── pre-commit-config.md         # .pre-commit-config.yaml template
        │   └── beartype-setup.md            # Beartype integration guide
        ├── scripts/
        │   ├── check_exception_handling.py  # Adapted from gantt-believe-it
        │   ├── check_print_statements.py    # Adapted + structured logging
        │   ├── check_file_length.py         # Adapted from gantt-believe-it
        │   ├── check_timeless_comments.py   # Adapted from gantt-believe-it
        │   └── fix_future_annotations.py    # Adapted from .cfg repo
        └── assets/
            ├── hookify.taste-enforcer.local.md
            ├── hookify.no-junk-drawers.local.md
            ├── hookify.parse-dont-validate.local.md
            └── hookify.semantic-types.local.md
```

---

### Task 1: Plugin Scaffold

**Files:**
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Create plugin.json**

```json
{
  "name": "strictify-repo",
  "description": "Apply opinionated Python code quality enforcement to any repo. Analyzes existing config, proposes strictness additions across 21 categories, and installs self-reinforcing hookify rules.",
  "author": {
    "name": "decal"
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: add plugin scaffold"
```

---

### Task 2: Hookify Rule Assets

**Files:**
- Create: `skills/strictify-repo/assets/hookify.taste-enforcer.local.md`
- Create: `skills/strictify-repo/assets/hookify.no-junk-drawers.local.md`
- Create: `skills/strictify-repo/assets/hookify.parse-dont-validate.local.md`
- Create: `skills/strictify-repo/assets/hookify.semantic-types.local.md`

- [ ] **Step 1: Create taste-enforcer hookify rule**

Write `skills/strictify-repo/assets/hookify.taste-enforcer.local.md`:

```markdown
---
name: taste-enforcer
enabled: true
event: prompt
pattern: don.?t use|always prefer|avoid|never do|instead of|I hate when|stop using|should always|should never|prefer .+ over|ban |forbid
action: warn
---

Keyword hit. The user might have expressed a coding preference or taste.

Reminder: always do the following when the user expresses a code preference that should be enforced going forward. Determine whether it can be codified as:

1. **A pre-commit hook script** — if it's about code patterns that can be detected statically (e.g., "don't use bare except", "avoid print statements"). Create or update a script in `scripts/pre_commit_hooks/` and wire it into `.pre-commit-config.yaml`.

2. **A hookify rule** — if it's about Claude's behavior during sessions (e.g., "don't create utils.py files", "always use NewType for IDs"). Create a `.claude/hookify.{name}.local.md` rule.

3. **A pyproject.toml setting** — if it maps to an existing tool's configuration (e.g., "ban star imports" → ruff rule).

If the preference is already enforced by an existing hook or rule but the user still had to say something about it, that means the existing enforcement failed to do its job. Identify why it didn't catch the issue (pattern too narrow? wrong event type? missing edge case?) and propose a fix to strengthen the existing hook or rule.

Also: if the user previously expressed a taste in this conversation that this hook missed as a false negative, write a hook for that too.
```

- [ ] **Step 2: Create no-junk-drawers hookify rule**

Write `skills/strictify-repo/assets/hookify.no-junk-drawers.local.md`:

```markdown
---
name: no-junk-drawers
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: (utils|helpers|misc|common|shared|general)\.py$
action: warn
---

You're creating or editing a junk-drawer module. The blog principle "treat directory structure and filenames as an interface" means every file should have a clear, domain-specific purpose.

Instead of `utils.py`, name the module after what it actually does:
- `billing/compute.py` not `billing/utils.py`
- `auth/tokens.py` not `auth/helpers.py`
- `parsing/csv_reader.py` not `common/misc.py`

The problem isn't shared code — it's *anonymous* shared code. If you genuinely need a shared utility, name it after what it does and put it where it belongs. Prefer a well-named shared package with centralized invariants over hand-rolled helpers scattered across domains. But if the functions are only used by one module, they belong in that module.
```

- [ ] **Step 3: Create parse-dont-validate hookify rule**

Write `skills/strictify-repo/assets/hookify.parse-dont-validate.local.md`:

```markdown
---
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
---

Possible validate-then-discard pattern detected. The principle "parse, don't validate" means: coerce unstructured data into constrained types at the boundary of your system, so downstream code never needs to re-validate.

**Instead of validating and discarding the evidence:**
```python
def process(data: dict) -> None:
    if "user_id" not in data:
        raise ValueError("missing user_id")  # checked and discarded
```

**Parse into a constrained type that carries proof:**
```python
@dataclass(frozen=True)
class UserRequest:
    user_id: UserId
    # Construction IS validation. If it exists, it's valid.

def process(request: UserRequest) -> None:
    # No validation needed — the type proves it.
```

Use Pydantic models, frozen dataclasses, or `NewType` to carry proof through the type system. Parse at the boundary, execute with confidence downstream.

If this is internal code operating on already-parsed types, ignore this message.
```

- [ ] **Step 4: Create semantic-types hookify rule**

Write `skills/strictify-repo/assets/hookify.semantic-types.local.md`:

```markdown
---
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
---

Bare primitive type detected for what looks like a domain concept. Semantic types help both humans and AI agents understand the code:

```python
from typing import NewType

UserId = NewType("UserId", str)
Amount = NewType("Amount", int)

def get_user(user_id: UserId) -> User:  # Clear intent
    ...
```

`NewType` is zero-cost at runtime and catches category errors at type-check time (passing an `OrgId` where a `UserId` is expected).

If this is genuinely a raw primitive with no domain meaning, ignore this message.
```

- [ ] **Step 5: Commit**

```bash
git add skills/strictify-repo/assets/
git commit -m "feat: add hookify rule assets (taste-enforcer, junk-drawers, parse-dont-validate, semantic-types)"
```

---

### Task 3: Custom Hook Scripts

Adapt the five hook scripts from gantt-believe-it and .cfg repos. Key changes from originals:
- Remove all project-specific references (gantt-believe-it paths, Textual imports, etc.)
- Update error output format to include remediation guidance: `{file}:{line}: {message} — {remediation}`
- Add structured logging detection to check_print_statements.py
- Make allowed-paths configurable via comments at top of each script

**Files:**
- Create: `skills/strictify-repo/scripts/check_exception_handling.py`
- Create: `skills/strictify-repo/scripts/check_print_statements.py`
- Create: `skills/strictify-repo/scripts/check_file_length.py`
- Create: `skills/strictify-repo/scripts/check_timeless_comments.py`
- Create: `skills/strictify-repo/scripts/fix_future_annotations.py`

- [ ] **Step 1: Create check_exception_handling.py**

Adapt from `/home/decal/src/PERSONAL/gantt-believe-it/scripts/pre_commit_hooks/check_exception_handling.py`. This is the reference implementation — the agent running `/strictify-repo` will read this, understand the pattern, and adapt it for the target repo.

Key changes from original:
- Update violation messages to include remediation: e.g., `"Bare 'except:' clause — catch a specific exception type instead (e.g., except ValueError as e:)"`
- Keep the `ExceptionHandlerVisitor` AST approach
- Keep the `# allow: exception-handling` exemption
- Remove any gantt-believe-it-specific paths

Write the full script (see spec section "Custom Pre-Commit Hook Scripts" for contract details). The script structure is:
1. `#!/usr/bin/env python3` shebang
2. Module docstring explaining what it detects and the philosophy
3. AST visitor class that finds violations
4. `check_file()` function
5. `main(filenames)` function that iterates files, prints violations with remediation, prints summary
6. `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`

- [ ] **Step 2: Create check_print_statements.py**

Adapt from `/home/decal/src/PERSONAL/gantt-believe-it/scripts/pre_commit_hooks/check_print_statements.py`.

Key changes from original:
- Remove `still-gantt-believe-it` from `is_allowed_location()`
- Add structured logging detection: detect `logger.info("user: " + user_id)`, `logger.info("user: %s", user_id)`, `logger.info(f"user: {user_id}")` patterns
- Update violation messages with remediation
- Make the allowed-paths list generic (tests/, scripts/, CLI entry points)

The script should have two AST visitors:
1. `PrintStatementVisitor` — finds print() calls (existing)
2. `UnstructuredLoggingVisitor` — finds string formatting in logger calls (new)

- [ ] **Step 3: Create check_file_length.py**

Adapt from `/home/decal/src/PERSONAL/gantt-believe-it/scripts/pre_commit_hooks/check_file_length.py`.

This one needs minimal changes:
- Update violation message to include remediation
- Keep the `LogicalLineCounter` AST approach
- Keep `--max-lines` argument (default 400)
- Keep `# allow: file-length` exemption

- [ ] **Step 4: Create check_timeless_comments.py**

Adapt from `/home/decal/src/PERSONAL/gantt-believe-it/scripts/pre_commit_hooks/check_timeless_comments.py`.

Key changes:
- Update violation messages with remediation
- Remove the self-skip for `check_timeless_comments.py` filename (the agent will handle that when adapting)
- Keep the temporal keywords list, docstring handling, and exemption support

- [ ] **Step 5: Create fix_future_annotations.py**

Adapt from `/home/decal/.cfg/scripts/fix_future_annotations.py`.

Key changes:
- Update output messages with remediation
- Keep the insertion-point logic (shebang → encoding → uv metadata → docstring → import)
- Keep CRLF/LF detection
- Keep the fixer behavior (modify files, exit 1 if changes were made)

- [ ] **Step 6: Commit**

```bash
git add skills/strictify-repo/scripts/
git commit -m "feat: add custom pre-commit hook scripts (exception handling, print/logging, file length, timeless comments, future annotations)"
```

---

### Task 4: Reference Documents

**Files:**
- Create: `skills/strictify-repo/references/pyproject-strict.md`
- Create: `skills/strictify-repo/references/pre-commit-config.md`
- Create: `skills/strictify-repo/references/beartype-setup.md`

- [ ] **Step 1: Create pyproject-strict.md**

This is the reference for all strict `pyproject.toml` tool sections. The agent reads this when applying strictness and merges relevant sections into the target repo's pyproject.toml.

Include complete TOML blocks for each tool. Derive from the gantt-believe-it and .cfg repo configs, removing project-specific settings. Include:

**[tool.ruff]:**
```toml
[tool.ruff]
line-length = 110
preview = true

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "C4", "SIM", "RUF"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"

[tool.ruff.lint.mccabe]
max-complexity = 15

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["F841", "C901", "PLR0912", "PLR0913", "PLR0915"]
"scripts/**/*.py" = ["C901", "PLR0912", "PLR0913", "PLR0915"]
```

**[tool.mypy]:**
```toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
show_error_codes = true
pretty = true

# Pragmatic exceptions — agent should adjust based on target project's frameworks
disable_error_code = ["no-untyped-call", "no-untyped-def"]

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_untyped_calls = false
check_untyped_defs = false
ignore_errors = true
```

**[tool.pytest.ini_options]:**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
addopts = "--no-header -n auto -q --durations=5 --durations-min=1.0 --cov-report=term-missing --cov-report=html --failed-first"
timeout = 20
timeout_method = "thread"
```

**[tool.coverage]:**
```toml
[tool.coverage.run]
fail_under = 100
skip_empty = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
    "@abc.abstractmethod",
]
```

**[tool.vulture]:**
```toml
[tool.vulture]
min_confidence = 80
exclude = [".venv/"]
```

Include commentary above each section explaining what it does and when the agent should adjust settings for the target project.

- [ ] **Step 2: Create pre-commit-config.md**

Complete `.pre-commit-config.yaml` template. Include every hook from the spec's 21 categories. Use the gantt-believe-it config as the structural reference, removing all project-specific hooks (Textual, test conventions, defensive get, polymorphic dict, markup safety, polling, terraform).

Template should include:
1. `pre-commit/pre-commit-hooks` (standard hygiene)
2. `astral-sh/ruff-pre-commit` (ruff-check + ruff-format)
3. `jendrikseipp/vulture` (dead code)
4. `asottile/pyupgrade` (modernize syntax)
5. `ikamensh/flynt` (f-strings)
6. `rubik/xenon` (complexity — `repo: https://github.com/rubik/xenon`)
7. Local hooks:
   - mypy (via `uv run mypy {package_name}/`)
   - check-exception-handling
   - check-print-statements
   - check-timeless-comments
   - check-file-length
   - fix-future-annotations
   - pytest (last, always_run)

Include `{package_name}` and `{python_version}` as placeholders with comments explaining the agent should substitute them.

- [ ] **Step 3: Create beartype-setup.md**

Reference for beartype integration. Include:

1. The `__init__.py` snippet:
```python
import warnings
from beartype import BeartypeConf
from beartype.claw import beartype_this_package
from beartype.roar import BeartypeClawDecorWarning

warnings.filterwarnings("ignore", category=BeartypeClawDecorWarning)

beartype_this_package(
    conf=BeartypeConf(
        claw_is_pep526=False,
        warning_cls_on_decorator_exception=BeartypeClawDecorWarning,
    )
)
```

2. What each `BeartypeConf` option does
3. When to suppress `BeartypeClawDecorWarning` (frameworks with decorators beartype can't handle)
4. How to add as a dependency:
   - `uv add beartype`
   - `pip install beartype`
   - `poetry add beartype`
5. Common issues and fixes (click decorators, Pydantic models, etc.)

- [ ] **Step 4: Commit**

```bash
git add skills/strictify-repo/references/
git commit -m "feat: add reference configs (pyproject-strict, pre-commit-config, beartype-setup)"
```

---

### Task 5: SKILL.md — Core Workflow

**Files:**
- Create: `skills/strictify-repo/SKILL.md`

This is the most important file — it drives the entire three-phase workflow. The SKILL.md body should be ~2000 words, with detailed content pushed to references.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: strictify-repo
description: This skill should be used when the user asks to "strictify a repo", "add code quality enforcement", "make this repo strict", "add pre-commit hooks", "add type checking", "enforce code quality", "set up linting", or runs the /strictify-repo command.
---
```

**Body structure:**

1. **Overview** — what this skill does (enforce taste programmatically across 21 categories)
2. **Philosophy** — enforce taste not arbitrary strictness; bias strict but check in; self-reinforcing
3. **Phase 1: Analyze** — checklist of what to detect:
   - `pyproject.toml` existence and current tool configs
   - `.pre-commit-config.yaml` existence and current hooks
   - Package layout (`src/` vs flat), package name
   - Python version (from `pyproject.toml`, `.python-version`, or runtime)
   - Package manager (uv lockfile? poetry.lock? requirements.txt?)
   - beartype already present?
   - Test infrastructure (pytest config, test directory, coverage config)
   - Existing `__init__.py` contents
4. **Phase 2: Propose** — present findings grouped by category (reference the 21 categories in the spec). For each: current state → proposed change. Ask user to veto any.
5. **Phase 3: Apply** — for each approved category, what to do:
   - Merge into `pyproject.toml` — read `references/pyproject-strict.md` for configs
   - Merge into `.pre-commit-config.yaml` — read `references/pre-commit-config.md` for template
   - Copy/adapt scripts from `scripts/` directory — read each, adapt paths/package names, write to target
   - Beartype — read `references/beartype-setup.md`, modify `__init__.py`
   - Hookify rules — copy from `assets/` to target's `.claude/`
   - Dev dependencies — add via detected package manager
   - Run `pre-commit install`
   - Architecture analysis — analyze domain structure, propose layers, create lint rules
   - Quality scorecard — create `docs/QUALITY.md` with initial grades
   - Doc gardening — assess project maturity, set up appropriate infrastructure
   - Per-worktree isolation — analyze and configure
6. **Conflict handling** — merge-up, never remove, present diff, user veto
7. **Resource pointers** — where to find reference configs, scripts, and assets

Keep SKILL.md lean. Point to references for detailed configs. The skill tells the agent *what to do* and *where to find the details*.

- [ ] **Step 2: Commit**

```bash
git add skills/strictify-repo/SKILL.md
git commit -m "feat: add SKILL.md core workflow (analyze → propose → apply)"
```

---

### Task 6: Command Entry Point

**Files:**
- Create: `commands/strictify-repo.md`

- [ ] **Step 1: Write command file**

```markdown
---
description: Apply opinionated Python code quality enforcement to this repo
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, AskUserQuestion
---

## Context

- Current directory listing: !`ls -la`
- Git status: !`git status --short`
- Python version: !`python3 --version 2>/dev/null || echo "Python not found"`
- pyproject.toml exists: !`test -f pyproject.toml && echo "YES" || echo "NO"`
- pyproject.toml contents: !`cat pyproject.toml 2>/dev/null || echo "No pyproject.toml"`
- .pre-commit-config.yaml exists: !`test -f .pre-commit-config.yaml && echo "YES" || echo "NO"`
- .pre-commit-config.yaml contents: !`cat .pre-commit-config.yaml 2>/dev/null || echo "No .pre-commit-config.yaml"`
- Package manager detection: !`test -f uv.lock && echo "uv" || (test -f poetry.lock && echo "poetry" || (test -f requirements.txt && echo "pip" || echo "unknown"))`
- Package layout: !`find . -maxdepth 3 -name "__init__.py" -not -path "./.venv/*" 2>/dev/null | head -10`

## Your task

Use the strictify-repo skill to apply opinionated Python code quality enforcement to this repository.

The skill drives a three-phase workflow:
1. **Analyze** — use the context above plus additional exploration to understand the repo's current state
2. **Propose** — present the user with a summary of 21 strictness categories, showing current state → proposed change for each
3. **Apply** — for each approved category, merge configs, copy scripts, install hooks

Invoke the skill and follow its workflow.
```

- [ ] **Step 2: Commit**

```bash
git add commands/strictify-repo.md
git commit -m "feat: add /strictify-repo command entry point"
```

---

### Task 7: Validation and Final Commit

- [ ] **Step 1: Verify directory structure**

```bash
find . -not -path './.git/*' -type f | sort
```

Expected output:
```
./.claude-plugin/plugin.json
./commands/strictify-repo.md
./docs/superpowers/plans/2026-04-15-strictify-repo-plan.md
./docs/superpowers/specs/2026-04-15-strictify-repo-design.md
./skills/strictify-repo/SKILL.md
./skills/strictify-repo/assets/hookify.no-junk-drawers.local.md
./skills/strictify-repo/assets/hookify.parse-dont-validate.local.md
./skills/strictify-repo/assets/hookify.semantic-types.local.md
./skills/strictify-repo/assets/hookify.taste-enforcer.local.md
./skills/strictify-repo/references/beartype-setup.md
./skills/strictify-repo/references/pre-commit-config.md
./skills/strictify-repo/references/pyproject-strict.md
./skills/strictify-repo/scripts/check_exception_handling.py
./skills/strictify-repo/scripts/check_file_length.py
./skills/strictify-repo/scripts/check_print_statements.py
./skills/strictify-repo/scripts/check_timeless_comments.py
./skills/strictify-repo/scripts/fix_future_annotations.py
```

- [ ] **Step 2: Verify plugin.json is valid JSON**

```bash
python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"
```

- [ ] **Step 3: Verify SKILL.md has valid frontmatter**

```bash
head -5 skills/strictify-repo/SKILL.md
```

Expected: YAML frontmatter with `name` and `description` fields.

- [ ] **Step 4: Verify all hookify rules have valid frontmatter**

```bash
for f in skills/strictify-repo/assets/hookify.*.local.md; do echo "=== $f ==="; head -10 "$f"; echo; done
```

Expected: each file has YAML frontmatter with `name`, `enabled`, `event`, and either `pattern` or `conditions`.

- [ ] **Step 5: Verify all scripts are syntactically valid Python**

```bash
for f in skills/strictify-repo/scripts/*.py; do python3 -c "import ast; ast.parse(open('$f').read()); print('OK: $f')"; done
```

- [ ] **Step 6: Verify command file has valid frontmatter**

```bash
head -5 commands/strictify-repo.md
```

Expected: YAML frontmatter with `description` and `allowed-tools` fields.

- [ ] **Step 7: Count SKILL.md word count**

```bash
wc -w skills/strictify-repo/SKILL.md
```

Expected: ~1500-2500 words (lean but comprehensive).
