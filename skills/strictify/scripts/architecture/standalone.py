"""Optional standalone-script and stdlib-only import constraints."""

from __future__ import annotations

import ast
import sys

from .policy import Diagnostic, Policy, SourceModule

_LOADERS = frozenset(
    {
        "__import__",
        "builtins.__import__",
        "importlib.import_module",
        "importlib.util.spec_from_file_location",
        "importlib.machinery.SourceFileLoader",
        "importlib.machinery.SourcelessFileLoader",
        "importlib.machinery.ExtensionFileLoader",
    }
)


def _name(node: ast.expr, bindings: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return bindings.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return f"{_name(node.value, bindings)}.{node.attr}"
    return ""


def _imports(tree: ast.AST) -> tuple[list[tuple[int, str]], dict[str, str]]:
    imports: list[tuple[int, str]] = []
    bindings: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name))
                bindings[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.append((node.lineno, module))
            for alias in node.names:
                bindings[alias.asname or alias.name] = f"{module}.{alias.name}"
    return imports, bindings


def _inspect(module: SourceModule, local_names: set[str], first_party: set[str], policy: Policy) -> list[str]:
    path = module.path
    name = path.as_posix()
    standalone = module.name in policy.standalone_modules
    allow_dynamic = module.name in policy.dynamic_loading
    if path.is_symlink():
        return [f"{name}: architecture-source: symlinked Python source -- keep source in this repo"]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=name)
    except (SyntaxError, UnicodeError, ValueError) as exc:
        return [f"{name}: architecture-parse: {exc} -- repair source before checking boundaries"]
    imports, bindings = _imports(tree)
    diagnostics = []
    for line, target in imports:
        top = target.split(".")[0]
        if (standalone and (top not in sys.stdlib_module_names or top in local_names)) or (
            policy.stdlib_only
            and not target.startswith(".")
            and top not in sys.stdlib_module_names
            and top not in first_party
        ):
            diagnostics.append(
                f"{name}:{line}: architecture-import: {target!r} is not an independent stdlib import "
                "-- keep scripts standalone; test public entry points through the CLI or approved loader"
            )
    loads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _name(node.func, bindings) in _LOADERS
    ]
    if not allow_dynamic and (standalone or policy.stdlib_only):
        diagnostics.extend(
            f"{name}:{node.lineno}: architecture-dynamic: {_name(node.func, bindings)} loads code "
            "-- use static stdlib imports; only registered test harnesses may load scripts"
            for node in loads
        )
    elif allow_dynamic and not loads:
        diagnostics.append(
            f"architecture.toml: architecture-stale: {name!r} no longer loads scripts "
            "-- remove its dynamic_loading exception"
        )
    return diagnostics


def check_scripts(modules: dict[str, SourceModule], policy: Policy) -> list[Diagnostic]:
    local_names = {name.split(".")[0] for name in modules} | {module.path.stem for module in modules.values()}
    diagnostics: list[Diagnostic] = []
    for name, module in modules.items():
        if (
            name not in policy.standalone_modules
            and not policy.stdlib_only
            and name not in policy.dynamic_loading
        ):
            continue
        messages = _inspect(module, local_names, {name.split(".")[0] for name in modules}, policy)
        diagnostics.extend(
            Diagnostic(module.path.as_posix(), 0, "architecture-script", message) for message in messages
        )
    return diagnostics
