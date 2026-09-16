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

Name modules for their purpose: `billing/compute.py`, `auth/tokens.py`, or
`parsing/csv_reader.py`. Put shared code and its invariants in the owning package;
keep functions used by one module there.
