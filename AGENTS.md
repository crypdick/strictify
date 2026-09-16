# Strictify

Read [ARCHITECTURE.md](ARCHITECTURE.md) for the codemap and repository invariants.
[architecture.toml](architecture.toml) owns Python source registration and exact
test-loader exceptions. Read it before adding Python files or changing imports.

Each shipped hook must remain a single stdlib-only script. Test public functions
or the CLI; implementation helpers remain private. Register new source files,
remove stale registrations and exceptions, and never weaken policy to hide debt.
The architecture guide explains which category-15 rules fit this repository.

Run `uvx prek run --all-files` before committing. It includes architecture checks,
Ruff, mypy, and the unittest suite. Install local enforcement with `uvx prek install`.
