"""Exercise repository architecture policy through its public CLI."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[1] / "tools/check_architecture.py"


class ArchitectureTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        subprocess.run(  # noqa: S603 -- isolated fixture repository
            ["git", "init", "--quiet", str(self.root)],  # noqa: S607 -- Git is required on PATH
            check=True,
            capture_output=True,
        )
        self.write("hook.py", "import ast\nfrom pathlib import Path\n")
        self.write("tools/check.py", "import sys\n")
        self.write("tests/test_hook.py", "import unittest\n")
        self.policy = """version = 1
[sources]
"hook.py" = "hook"
"tools/check.py" = "tool"
"tests/test_hook.py" = "test"
"""

    def write(self, filename: str, source: str) -> None:
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    def run_check(self) -> subprocess.CompletedProcess[str]:
        self.write("architecture.toml", self.policy)
        return subprocess.run(  # noqa: S603 -- fixed checker and isolated fixture
            [sys.executable, str(CHECKER), "--root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )

    def assert_rejected(self, code: str) -> None:
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(code, result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_registered_stdlib_sources_pass(self) -> None:
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dependencies_cannot_enter_standalone_scripts(self) -> None:
        for source in (
            "import requests\n",
            "import tools.check\n",
            "from hook import main\n",
            "from . import helper\n",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import requests\n",
        ):
            with self.subTest(source=source):
                self.write("hook.py", source)
                self.assert_rejected("architecture-import")

    def test_all_roles_obey_import_boundary(self) -> None:
        for filename in ("hook.py", "tools/check.py", "tests/test_hook.py"):
            with self.subTest(filename=filename):
                self.write(filename, "import requests\n")
                self.assert_rejected(f"{filename}:1: architecture-import")
                self.write(filename, "import sys\n")

    def test_unregistered_sources_and_stale_ownership_fail(self) -> None:
        self.write("new_package/internal.py", "")
        self.assert_rejected("architecture-ownership")
        (self.root / "new_package/internal.py").unlink()
        (self.root / "hook.py").unlink()
        self.assert_rejected("architecture-stale")

    def test_ignored_generated_files_are_outside_source_scope(self) -> None:
        self.write(".gitignore", "generated/\n")
        self.write("generated/output.py", "import unavailable\n")
        self.assertEqual(self.run_check().returncode, 0)

    def test_local_module_cannot_impersonate_stdlib(self) -> None:
        self.write("json.py", "")
        self.policy += '"json.py" = "hook"\n'
        self.write("hook.py", "import json\n")
        self.assert_rejected("architecture-import")

    def test_dynamic_loading_requires_exact_test_exception(self) -> None:
        for source in (
            'import importlib\nimportlib.import_module("requests")\n',
            'from importlib import import_module as load\nload("requests")\n',
            'import builtins as b\nb.__import__("requests")\n',
            '__import__("requests")\n',
            'import importlib.util as loader\nloader.spec_from_file_location("hook", path)\n',
        ):
            with self.subTest(source=source):
                self.write("hook.py", source)
                self.assert_rejected("architecture-dynamic")
        self.write("hook.py", "import ast\n")
        self.write("tests/test_hook.py", source)
        self.assert_rejected("architecture-dynamic")
        self.policy += '\n[dynamic_loading]\n"tests/test_hook.py" = "Load public hook entry points."\n'
        self.assertEqual(self.run_check().returncode, 0)
        self.write("tests/test_other.py", source)
        self.policy = self.policy.replace("[sources]", '[sources]\n"tests/test_other.py" = "test"')
        self.assert_rejected("tests/test_other.py:2: architecture-dynamic")

    def test_exception_does_not_allow_static_third_party_imports(self) -> None:
        self.policy += '\n[dynamic_loading]\n"tests/test_hook.py" = "Load hook entry points."\n'
        self.write("tests/test_hook.py", 'import requests\n__import__("hook")\n')
        self.assert_rejected("architecture-import")

    def test_unused_dynamic_exception_fails(self) -> None:
        self.policy += '\n[dynamic_loading]\n"tests/test_hook.py" = "Load public hook entry points."\n'
        self.assert_rejected("architecture-stale")

    def test_invalid_policy_fails_without_traceback(self) -> None:
        valid = self.policy
        for policy in (
            "version = 1\n",
            valid.replace('"hook.py" = "hook"', '"hook.py" = "unknown"'),
            valid.replace("version = 1", "version = 2"),
            valid.replace("version = 1", "version = true"),
            valid.replace("version = 1", "version = 1.0"),
            valid + '\n[dynamic_loading]\n"hook.py" = "Let a payload load anything."\n',
            valid + '\n[dynamic_loading]\n"tests/test_hook.py" = ""\n',
            valid + '\n[dynamic_loading]\n"missing.py" = "Missing source."\n',
            valid.replace('"hook.py"', '"../outside.py"'),
            valid.replace('"hook.py"', '"*.py"'),
            valid + "\n[unknown]\nvalue = true\n",
            "not valid TOML",
        ):
            with self.subTest(policy=policy):
                self.policy = policy
                self.assert_rejected("architecture-policy")

    def test_source_parse_failure_is_not_a_clean_scan(self) -> None:
        self.write("hook.py", "def broken(\n")
        self.assert_rejected("architecture-parse")


if __name__ == "__main__":
    unittest.main()
