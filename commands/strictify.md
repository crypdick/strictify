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
- prek.toml exists: !`test -f prek.toml && echo "YES" || echo "NO"`
- prek.toml contents: !`cat prek.toml 2>/dev/null || echo "No prek.toml"`
- Legacy hook config requiring migration: !`if test -f .pre-commit-config.yaml || test -f .pre-commit-config.yml; then echo "YES"; else echo "NO"; fi`
- AGENTS.md exists: !`test -f AGENTS.md && echo "YES" || echo "NO"`
- AGENTS.md contents: !`cat AGENTS.md 2>/dev/null || echo "No AGENTS.md"`
- Package manager detection: !`test -f uv.lock && echo "uv" || (test -f poetry.lock && echo "poetry" || (test -f requirements.txt && echo "pip" || echo "unknown"))`
- Package layout: !`find . -maxdepth 3 -name "__init__.py" -not -path "./.venv/*" 2>/dev/null | head -10`

## Your task

Invoke the strictify skill. Use this context for its analyze, propose, and apply workflow.
