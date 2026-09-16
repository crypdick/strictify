"""Release preparation tests through the repository tool's CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "prepare_plugin_release.py"
GIT = Path(shutil.which("git") or "")
if not GIT.is_file():
    raise RuntimeError("Git is required")


class PreparePluginReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.git("init", "--quiet", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        (self.root / ".claude-plugin").mkdir()
        shutil.copy2(SCRIPT, self.root / "prepare_plugin_release.py")

    def git(self, *args: str) -> str:
        result = subprocess.run(  # noqa: S603 -- fixed Git binary and test-controlled arguments.
            [GIT, *args],
            cwd=self.root,
            env=self.git_env,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def write_versions(self, plugin: str, marketplace: str | None = None) -> None:
        marketplace = plugin if marketplace is None else marketplace
        (self.root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "strictify", "version": plugin}, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.root / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps({"plugins": [{"name": "strictify", "version": marketplace}]}, indent=2) + "\n",
            encoding="utf-8",
        )

    def commit(self, message: str) -> str:
        self.git("add", ".")
        self.git("commit", "--no-verify", "--quiet", "-m", message)
        return self.git("rev-parse", "HEAD")

    def run_tool(self, source: str) -> subprocess.CompletedProcess[str]:
        output = self.root / "github-output"
        output.unlink(missing_ok=True)
        return subprocess.run(  # noqa: S603 -- repository tool and test-controlled SHA.
            [sys.executable, "prepare_plugin_release.py", "--source", source],
            cwd=self.root,
            env={**os.environ, "GITHUB_OUTPUT": str(output)},
            capture_output=True,
            text=True,
            check=False,
        )

    def versions(self) -> tuple[str, str]:
        plugin = json.loads((self.root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))[
            "version"
        ]
        marketplace = json.loads(
            (self.root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )["plugins"][0]["version"]
        return plugin, marketplace

    def output(self) -> str:
        return (self.root / "github-output").read_text(encoding="utf-8")

    def test_unchanged_version_gets_patch_bump(self) -> None:
        self.write_versions("0.8.0")
        self.commit("base")
        (self.root / "feature.txt").write_text("change\n", encoding="utf-8")
        source = self.commit("feature")

        result = self.run_tool(source)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.versions(), ("0.8.1", "0.8.1"))
        self.assertEqual(self.output(), "state=new\nversion=0.8.1\n")

    def test_manual_version_bump_is_preserved(self) -> None:
        self.write_versions("0.8.0")
        self.commit("base")
        self.write_versions("0.9.0")
        source = self.commit("feature with release version")

        result = self.run_tool(source)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.versions(), ("0.9.0", "0.9.0"))
        self.assertEqual(self.output(), "state=new\nversion=0.9.0\n")

    def test_manifest_versions_must_agree(self) -> None:
        self.write_versions("0.8.0")
        self.commit("base")
        self.write_versions("0.8.0", "0.8.1")
        source = self.commit("mismatched versions")

        result = self.run_tool(source)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("plugin manifests disagree", result.stderr)

    def test_version_cannot_decrease(self) -> None:
        self.write_versions("0.8.0")
        self.commit("base")
        self.write_versions("0.7.0")
        source = self.commit("regressed version")

        result = self.run_tool(source)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("plugin version decreased from 0.8.0 to 0.7.0", result.stderr)

    def test_retry_reuses_existing_release_commit(self) -> None:
        self.write_versions("0.8.0")
        self.commit("base")
        (self.root / "feature.txt").write_text("change\n", encoding="utf-8")
        source = self.commit("feature")
        self.assertEqual(self.run_tool(source).returncode, 0)
        self.commit(f"Release 0.8.1\n\nSource-Commit: {source}")

        result = self.run_tool(source)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.versions(), ("0.8.1", "0.8.1"))
        self.assertEqual(self.output(), "state=retry\nversion=0.8.1\n")

    def test_overtaken_run_does_not_change_versions(self) -> None:
        self.write_versions("0.8.0")
        source = self.commit("source")
        (self.root / "newer.txt").write_text("newer\n", encoding="utf-8")
        self.commit("newer source")

        result = self.run_tool(source)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.versions(), ("0.8.0", "0.8.0"))
        self.assertEqual(self.output(), "state=stale\nversion=0.8.0\n")


if __name__ == "__main__":
    unittest.main()
