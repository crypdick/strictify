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

Combine focused components when feature variants multiply subclasses or boolean
flags. For example, let a report render sections rather than encoding every
combination in subclasses:

```python
from typing import Protocol

class Renderable(Protocol):
    def render(self) -> str: ...

class Report:
    def __init__(self, sections: list[Renderable]):
        self.sections = sections

    def render(self) -> str:
        return "\n\n".join(section.render() for section in self.sections)
```

Inject a strategy for behavior that varies. Inheritance still fits framework base
classes, `Enum`, `Exception`, and is-a relationships without combinatorial variants.
