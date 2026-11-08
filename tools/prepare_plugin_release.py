#!/usr/bin/env python3
"""Prepare Strictify's synchronized plugin version for an automatic release."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

PLUGIN = Path(".claude-plugin/plugin.json")
MARKETPLACE = Path(".claude-plugin/marketplace.json")
VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
GIT = Path(shutil.which("git") or "")
if not GIT.is_file():
    raise RuntimeError("Git is required")


def _git(*args: str) -> str:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(  # noqa: S603 -- fixed Git command with validated revisions.
        [GIT, *args], check=True, capture_output=True, text=True, env=environment
    )
    return result.stdout.strip()


def _release_state(source: str) -> str:
    head = _git("rev-parse", "HEAD")
    if head == source:
        return "new"
    parent = _git("rev-parse", "HEAD^")
    message = _git("log", "-1", "--format=%B")
    if (
        parent == source
        and message.startswith("Release ")
        and f"Source-Commit: {source}" in message.splitlines()
    ):
        return "retry"
    return "stale"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def _manifest_versions() -> tuple[dict[str, Any], dict[str, Any], str]:
    plugin = _read_json(PLUGIN)
    marketplace = _read_json(MARKETPLACE)
    plugin_version = plugin.get("version")
    if plugin.get("name") != "strictify" or marketplace.get("name") != "strictify":
        raise ValueError("plugin and marketplace names must both be strictify")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise TypeError(f"{MARKETPLACE} must contain a plugins array")
    registrations = [item for item in plugins if isinstance(item, dict) and item.get("name") == "strictify"]
    if len(registrations) != 1:
        raise ValueError(f"{MARKETPLACE} must register strictify exactly once")
    if not isinstance(plugin_version, str) or VERSION_RE.fullmatch(plugin_version) is None:
        raise ValueError(f"plugin version must be major.minor.patch: {plugin_version!r}")
    return plugin, marketplace, plugin_version


def _version_at(revision: str) -> str:
    data = json.loads(_git("show", f"{revision}:{PLUGIN}"))
    version = data.get("version")
    if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
        raise ValueError(f"plugin version at {revision} must be major.minor.patch")
    return version


def _parts(version: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"plugin version must be major.minor.patch: {version!r}")
    return int(match[1]), int(match[2]), int(match[3])


def _next_version(current: str, previous: str) -> str:
    current_parts = _parts(current)
    previous_parts = _parts(previous)
    if current_parts < previous_parts:
        raise ValueError(f"plugin version decreased from {previous} to {current}")
    if current_parts > previous_parts:
        return current
    return f"{current_parts[0]}.{current_parts[1]}.{current_parts[2] + 1}"


def _write_versions(plugin: dict[str, Any], marketplace: dict[str, Any], version: str) -> None:
    plugin["version"] = version
    plugins = marketplace["plugins"]
    for item in plugins:
        if isinstance(item, dict) and item.get("name") == "strictify":
            item["version"] = version
            break
    PLUGIN.write_text(json.dumps(plugin, indent=2) + "\n", encoding="utf-8")
    MARKETPLACE.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate manifest identity without writing")
    parser.add_argument("--source")
    parser.add_argument("--previous", help="Branch HEAD before this push")
    args = parser.parse_args()
    for name in () if args.check else ("source", "previous"):
        if re.fullmatch(r"[0-9a-f]{40}", getattr(args, name) or "") is None:
            parser.error(f"{name} must be a full Git commit SHA")
    try:
        plugin, marketplace, version = _manifest_versions()
        if args.check:
            return
        state = _release_state(args.source)
        if state == "new":
            version = _next_version(version, _version_at(args.previous))
            _write_versions(plugin, marketplace, version)
    except (KeyError, OSError, subprocess.CalledProcessError, TypeError, ValueError) as error:
        parser.error(str(error))
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"state={state}\nversion={version}\n")


if __name__ == "__main__":
    main()
