---
name: no-junk-drawers
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: (^|[/\\])(utils|helpers|misc|common|shared|general)\.py$
action: warn
---

You're creating or editing a module with a generic name. Name it after its purpose so readers can tell where to find code.

Instead of `utils.py`, name the module after what it actually does:

- `billing/compute.py` not `billing/utils.py`
- `auth/tokens.py` not `auth/helpers.py`
- `parsing/csv_reader.py` not `common/misc.py`

Put shared code in a package named for its purpose, and keep its invariants there instead of duplicating helpers across domains. Functions used by only one module belong in that module.
