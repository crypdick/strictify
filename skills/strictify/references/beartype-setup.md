# Beartype integration

Beartype checks annotated values at runtime. Its default strategy performs
constant-time checks; this is not zero overhead or exhaustive validation of every
container element. Profile performance-sensitive code before choosing exemptions.

## Install and activate

Add Beartype as a **runtime dependency** with `uv add beartype`, `poetry add
beartype`, or the project's pip requirements workflow. Production imports must
work without development dependencies.

Place this in the root package's `__init__.py`, after any module docstring and
`from __future__` imports, but before imports of its submodules:

```python
from beartype import BeartypeConf
from beartype.claw import beartype_this_package

beartype_this_package(conf=BeartypeConf(claw_is_pep526=False))
```

This instruments subsequent imports under the package. It does not retroactively
instrument modules already imported, including the executing `__init__.py`.
Do not repeat it in subpackages or activate it in a separate test package.
See the [import-hook documentation](https://beartype.readthedocs.io/en/v0.21.0/api_claw/).

`claw_is_pep526=False` disables checks injected for annotated variable assignments.
Function parameter and return checks remain enabled. Choose whether to enable
assignment checks based on the target's behavior and tests.

## Verify coverage of runtime checks

Run the project's tests and a package-import smoke test in its production
installation. Exercise representative annotated functions with valid and invalid
arguments. Include decorated functions and generated methods if the project uses
frameworks or dataclasses; do not assume every callable is instrumented.

Import hooks can warn when decoration fails, leaving the affected callable
unchecked. Keep those warnings visible during adoption. Investigate the reported
callable and decorator order before adding a narrow warning filter. A framework's
name alone is not evidence that its decorators require suppression.

For projects that need decoration failures to stop imports, explicitly configure
`warning_cls_on_decorator_exception=None`. Verify this against the installed
version and application startup before adopting it.

## Performance exemptions

For a measured hot path that should skip checking, use the documented no-check
strategy:

```python
from beartype import BeartypeConf, BeartypeStrategy, beartype

@beartype(conf=BeartypeConf(strategy=BeartypeStrategy.O0))
def identity(value: object) -> object:
    return value
```

Keep annotations accurate; weakening them to reduce runtime checks also weakens
static analysis. See the [decorator and strategy documentation](https://beartype.readthedocs.io/en/latest/api_decor/).
