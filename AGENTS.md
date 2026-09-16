# Strictify

Read [ARCHITECTURE.md](ARCHITECTURE.md) for the codemap and repository invariants.
[architecture.toml](architecture.toml) owns package registration, public modules,
dependency directions, and exact test-loader exceptions. Read it before adding
Python files or changing imports.

The four single-file hooks must remain standalone and stdlib-only. The reusable
architecture toolkit is one stdlib-only package exposing its `api` module; copy it
as a complete directory. Test public functions or the CLI; implementation helpers
remain private. Register new units, remove stale registrations and exceptions,
and never weaken policy to hide debt. This repository uses the same shipped
checker and schema demonstrated in the toolkit setup guide.

Run `uvx prek run --all-files` before committing. It includes architecture checks,
Ruff, mypy, and the unittest suite. Install local enforcement with `uvx prek install`.
