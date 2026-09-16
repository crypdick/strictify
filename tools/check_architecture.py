#!/usr/bin/env python3
"""Enforce Strictify's source registry and standalone, stdlib-only scripts."""

from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path

import tomllib

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


def _string_table(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) or not isinstance(item, str) for key, item in value.items()
    ):
        msg = "expected a table of source paths and string values"
        raise ValueError(msg)
    return {str(key): str(item) for key, item in value.items()}


def _load_policy(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    with (root / "architecture.toml").open("rb") as handle:
        raw = tomllib.load(handle)
    if not isinstance(raw.get("version"), int) or isinstance(raw.get("version"), bool) or raw["version"] != 1:
        msg = "version must be integer 1"
        raise ValueError(msg)
    if set(raw) - {"version", "sources", "dynamic_loading"}:
        msg = "unknown policy fields; expected version, sources, and optional dynamic_loading"
        raise ValueError(msg)
    sources = _string_table(raw.get("sources"))
    if not sources:
        msg = "sources must register at least one Python file"
        raise ValueError(msg)
    for name, role in sources.items():
        path = Path(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != name
            or path.suffix != ".py"
            or any(character in name for character in "*?[]\\")
            or role not in {"hook", "tool", "test"}
        ):
            msg = f"invalid source {name!r}: use an exact relative Python path and hook/tool/test role"
            raise ValueError(msg)
    dynamic = _string_table(raw.get("dynamic_loading", {}))
    for name, reason in dynamic.items():
        if sources.get(name) != "test" or not reason.strip():
            msg = f"dynamic loading exception {name!r} needs a registered test source and a reason"
            raise ValueError(msg)
    return sources, dynamic


def _source_files(root: Path) -> set[str]:
    # Git hooks export their repository location; --root must select this scan's repo.
    env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "*.py"],  # noqa: S607 -- Git is required on PATH
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return {name for name in result.stdout.split("\0") if name and (root / name).exists()}


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


def _inspect(root: Path, name: str, local_names: set[str], *, allow_dynamic: bool) -> list[str]:
    path = root / name
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
        if top not in sys.stdlib_module_names or top in local_names:
            diagnostics.append(
                f"{name}:{line}: architecture-import: {target!r} is not an independent stdlib import "
                "-- keep scripts standalone; test public entry points through the CLI or approved loader"
            )
    loads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _name(node.func, bindings) in _LOADERS
    ]
    if not allow_dynamic:
        diagnostics.extend(
            f"{name}:{node.lineno}: architecture-dynamic: {_name(node.func, bindings)} loads code "
            "-- use static stdlib imports; only registered test harnesses may load scripts"
            for node in loads
        )
    elif not loads:
        diagnostics.append(
            f"architecture.toml: architecture-stale: {name!r} no longer loads scripts "
            "-- remove its dynamic_loading exception"
        )
    return diagnostics


def check_architecture(root: Path) -> list[str]:
    """Check every tracked or non-ignored Python source, including untracked files."""
    sources, dynamic = _load_policy(root)
    files = _source_files(root)
    diagnostics = [
        f"{name}: architecture-ownership: unregistered Python source -- assign its role in architecture.toml"
        for name in sorted(files - sources.keys())
    ]
    diagnostics.extend(
        f"architecture.toml: architecture-stale: {name!r} is not source -- remove its registration"
        for name in sorted(sources.keys() - files)
    )
    # Both direct script imports and imports through namespace parents break independence.
    local_names = {Path(name).stem for name in files} | {
        Path(name).parts[0] for name in files if len(Path(name).parts) > 1
    }
    for name in sorted(files):
        diagnostics.extend(_inspect(root, name, local_names, allow_dynamic=name in dynamic))
    return diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        diagnostics = check_architecture(args.root.resolve())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"architecture.toml: architecture-policy: {exc} -- fix policy or repository access")
        return 1
    for diagnostic in diagnostics:
        print(diagnostic)
    return int(bool(diagnostics))


if __name__ == "__main__":
    sys.exit(main())
