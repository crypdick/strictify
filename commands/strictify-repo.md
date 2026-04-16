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
