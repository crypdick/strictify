# Beartype Integration Reference

beartype provides zero-cost runtime type checking for Python. When configured at the
package level with `beartype_this_package()`, it automatically instruments every function
in the package with runtime type checks -- no individual `@beartype` decorators needed.

---

## 1. The `__init__.py` Snippet

This snippet must be placed at the **top** of the package's root `__init__.py` file,
**before any other imports from the package**. beartype's import hook (`beartype_this_package`)
works by intercepting subsequent imports, so it must be activated before those imports occur.

```python
import warnings
from beartype import BeartypeConf
from beartype.claw import beartype_this_package
from beartype.roar import BeartypeClawDecorWarning

warnings.filterwarnings("ignore", category=BeartypeClawDecorWarning)

beartype_this_package(
    conf=BeartypeConf(
        claw_is_pep526=False,
        warning_cls_on_decorator_exception=BeartypeClawDecorWarning,
    )
)
```

### Placement

```
my_package/
    __init__.py      <-- snippet goes HERE, at the very top
    module_a.py
    module_b.py
    subpackage/
        __init__.py  <-- do NOT repeat the snippet in sub-packages
        ...
```

The snippet goes only in the top-level package `__init__.py`. `beartype_this_package()`
automatically applies to all submodules and subpackages -- there is no need to repeat it
in nested `__init__.py` files.

---

## 2. Configuration Options Explained

### `claw_is_pep526=False`

Controls whether beartype checks PEP 526 variable annotations (e.g., `x: int = "oops"`).

- **`False` (recommended):** Only function signatures (parameters and return types) are
  checked at runtime. Variable annotations are treated as documentation only.
- **`True`:** Every annotated variable assignment is also checked. This is significantly
  more expensive and produces many false positives with Pydantic models, dataclasses, and
  other frameworks that use annotations for metadata rather than runtime types.

Set to `False` unless the project has no Pydantic, dataclasses, attrs, or similar
annotation-driven frameworks.

### `warning_cls_on_decorator_exception=BeartypeClawDecorWarning`

Controls what happens when beartype fails to instrument a function (usually because the
function has a decorator beartype cannot introspect).

- **With this setting:** beartype emits a `BeartypeClawDecorWarning` instead of raising
  an exception. The function is left uninstrumented but the program continues.
- **Without this setting:** beartype raises an exception and the import fails entirely.

This is essential for any project using frameworks with complex decorators (click, typer,
FastAPI, pytest, Textual, etc.).

---

## 3. When to Suppress `BeartypeClawDecorWarning`

The `warnings.filterwarnings("ignore", category=BeartypeClawDecorWarning)` line silences
warnings about functions beartype cannot instrument. This is appropriate when:

- The project uses **click** or **typer** decorators (`@click.command()`, `@click.group()`,
  `@app.command()`). These produce complex wrapper objects that beartype cannot introspect.
- The project uses **pytest fixtures** (`@pytest.fixture`). The fixture decorator's
  signature manipulation confuses beartype.
- The project uses **FastAPI** route decorators (`@app.get()`, `@router.post()`). The
  dependency injection system creates wrapper signatures beartype cannot follow.
- The project uses **Textual** message handlers, watchers, or validators that are
  discovered by name convention rather than explicit decoration.

If you want to see which functions beartype skips (useful during initial setup), temporarily
change the filter to:

```python
warnings.filterwarnings("once", category=BeartypeClawDecorWarning)
```

This will print each warning exactly once, helping you audit what beartype cannot cover.

---

## 4. Installation

### uv (recommended)

```bash
uv add beartype
```

### pip

```bash
pip install beartype
```

### poetry

```bash
poetry add beartype
```

beartype has zero dependencies and is pure Python, so it adds no transitive dependency
weight to the project.

---

## 5. Common Issues and Fixes

### click / typer decorators

**Symptom:** `BeartypeClawDecorWarning` for every `@click.command()` or `@app.command()`
decorated function.

**Fix:** The `warning_cls_on_decorator_exception` setting handles this automatically.
The click-decorated functions will not have runtime type checking, but all other functions
in the package will. This is acceptable because click performs its own argument validation
via its type system.

### Pydantic models

**Symptom:** `BeartypeClawDecorWarning` for Pydantic validators, or unexpected runtime
errors when constructing models.

**Fix:** Ensure `claw_is_pep526=False`. Pydantic uses variable annotations extensively
for field definitions, and beartype's PEP 526 checking conflicts with Pydantic's own
annotation processing. With `claw_is_pep526=False`, beartype only checks function
signatures and leaves Pydantic's field annotations alone.

If Pydantic validators (decorated with `@field_validator` or `@model_validator`) still
trigger warnings, the `warning_cls_on_decorator_exception` setting will degrade them to
suppressed warnings.

### pytest fixtures

**Symptom:** `BeartypeClawDecorWarning` for functions decorated with `@pytest.fixture`.

**Fix:** The warning suppression handles this. pytest fixtures are discovered and called
by the pytest framework, which handles its own argument injection. beartype cannot
instrument them, but this is harmless -- the fixtures' type annotations are still
valuable as documentation and for mypy/pyright static checking.

Note: beartype should generally NOT be activated in test packages. The
`beartype_this_package()` call in the main package's `__init__.py` does not affect the
`tests/` directory (which is a separate top-level package). This is the desired behavior.

### dataclass fields

**Symptom:** Runtime type errors when instantiating dataclasses with `claw_is_pep526=True`.

**Fix:** Set `claw_is_pep526=False`. Dataclass field annotations define constructor
parameters and instance attributes, not runtime type guards. With `claw_is_pep526=False`,
beartype still checks the `__init__` and `__post_init__` signatures (which dataclasses
generate from the field annotations), providing type safety without conflicting with the
dataclass machinery.

### Circular imports

**Symptom:** `ImportError` or `AttributeError` during startup after adding beartype.

**Fix:** Because `beartype_this_package()` uses import hooks, it can interact poorly with
circular imports that were previously benign. The fix is to resolve the circular imports
(which is good practice regardless). Common strategies:
- Move shared types to a dedicated `types.py` or `protocols.py` module.
- Use `TYPE_CHECKING` guards for annotation-only imports.
- Use string-form annotations (`def foo(x: "MyClass")`) to break cycles.

### Performance

beartype's overhead is near-zero for typical function signatures. However, deeply nested
generic types (e.g., `dict[str, list[tuple[int, ...]]]`) incur proportionally more
checking. If profiling shows beartype as a hotspot:
- Add `@beartype.beartype(conf=BeartypeConf(is_check_time=False))` to specific hot
  functions to disable their runtime checks.
- Or narrow the type annotation to something simpler on the hot path.

---

## 6. How It Works

`beartype_this_package()` installs a Python import hook (PEP 302 / PEP 451) that
intercepts all subsequent imports within the package. For each imported module, beartype
automatically wraps every function and method with a thin type-checking decorator --
equivalent to manually applying `@beartype.beartype` to every function, but without
modifying any source files.

This means:
- **No `@beartype` decorators needed on individual functions.** The import hook handles it.
- **All functions in the package are covered**, including private functions, nested
  functions, and methods on classes.
- **Subpackages are included automatically.** A single `beartype_this_package()` call in
  the root `__init__.py` covers the entire package tree.
- **External packages are not affected.** Only the package calling
  `beartype_this_package()` is instrumented.

---

## 7. Summary Checklist for the Agent

1. Add `beartype` as a dependency (`uv add beartype`).
2. Place the snippet at the top of `{package_name}/__init__.py`, before other intra-package
   imports.
3. Ensure `claw_is_pep526=False` unless the project has no annotation-driven frameworks.
4. Keep the warning suppression line -- remove it only for debugging.
5. Do NOT add `beartype_this_package()` to sub-package `__init__.py` files.
6. Do NOT add `beartype_this_package()` to the test package.
7. Verify the project still starts correctly after adding beartype. If import errors occur,
   resolve circular imports first.
