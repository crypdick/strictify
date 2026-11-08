# Module structure

## Name modules for their purpose

Treat directory structure and filenames as an interface. Prefer names such as
`auth/tokens.py` or `parsing/csv_reader.py` over anonymous `utils.py`, `helpers.py`,
or `misc.py` modules. Keep shared code and its invariants in the owning package;
functions used by one module usually belong there.

A filename alone does not establish a problem. Keep established public names
and framework conventions when renaming would break callers. Do not scatter
shared invariants or create unnecessary modules merely to avoid a generic name.

## Composition over inheritance

Prefer focused collaborators when inheritance creates combinatorial variants.
Use inheritance where the relationship or framework calls for it; introduce a
strategy only for behavior that actually varies.
