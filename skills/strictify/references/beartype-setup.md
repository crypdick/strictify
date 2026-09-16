# Beartype integration

Beartype checks annotations at runtime. Default checks are constant-time,
not exhaustive container validation. Profile hot paths before exempting them.

## Install and activate

Add a runtime dependency with `uv add beartype`, `poetry add beartype`, or the
project's pip requirements workflow. In root `__init__.py`, after its docstring
and future imports but before submodule imports, add:

```python
from beartype import BeartypeConf
from beartype.claw import beartype_this_package

beartype_this_package(conf=BeartypeConf(claw_is_pep526=False))
```

The hook instruments subsequent package imports, not already imported modules or
this executing `__init__.py`. Do not repeat it in subpackages or a separate test
package. `claw_is_pep526=False` disables variable-assignment checks; parameter and
return checks remain enabled. See the [import-hook reference](https://beartype.readthedocs.io/en/v0.21.0/api_claw/).

## Verify coverage of runtime checks

Test a production import without development dependencies. Run the suite and
exercise valid/invalid arguments on representative functions, including decorators
and generated methods where used.

Keep decoration-failure warnings visible: affected callables may be unchecked.
Investigate the callable and decorator order before filtering warnings. To make
failures stop imports, set `warning_cls_on_decorator_exception=None` and verify
against the installed version and application startup.

## Performance exemptions

For measured hot paths, use the documented no-check strategy:

```python
from beartype import BeartypeConf, BeartypeStrategy, beartype

@beartype(conf=BeartypeConf(strategy=BeartypeStrategy.O0))
def identity(value: object) -> object:
    return value
```

Keep accurate annotations for static checking. See the
[decorator and strategy reference](https://beartype.readthedocs.io/en/latest/api_decor/).
