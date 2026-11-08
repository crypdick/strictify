# Strictify

[ARCHITECTURE.md](ARCHITECTURE.md) maps the repo and its invariants.
Read [architecture.toml](architecture.toml) before adding Python units or changing
imports; it owns registration, public modules, dependencies, and loader exceptions.
Keep declarations current; never weaken policy to hide debt.

Keep the four hooks standalone and stdlib-only. The architecture toolkit is one
stdlib-only package exposing `api`; copy the complete directory. Test public
functions or the CLI, not implementation helpers.

Run `uvx prek run --all-files` before committing. Install local hooks with
`uvx prek install`.
