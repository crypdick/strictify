"""Contract tests through a copied toolkit's public CLI in an unrelated repo."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLKIT = Path(__file__).resolve().parents[1] / "skills/strictify/scripts/architecture"


class ArchitectureTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git_env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
        subprocess.run(  # noqa: S603 -- isolated fixture repository
            ["git", "init", "--quiet", str(self.root)],  # noqa: S607 -- Git is required on PATH
            check=True,
            capture_output=True,
            env=self.git_env,
        )
        shutil.copytree(TOOLKIT, self.root / "architecture", ignore=shutil.ignore_patterns("__pycache__"))
        for filename in (
            "__init__",
            "entry",
            "sibling",
            "domain/__init__",
            "domain/api",
            "domain/internal",
            "adapter/__init__",
            "adapter/api",
            "adapter/internal",
        ):
            self.write(f"src/acme/{filename}.py", "")
        self.policy = """version = 2
source_roots = [{path = "src/acme", module = "acme"}]
[roles.domain]
allowed_dependencies = []
[roles.adapter]
allowed_dependencies = ["domain"]
[[packages]]
name = "root"
root = "acme"
role = "adapter"
public_modules = []
include_descendants = false
[[packages]]
name = "entry"
root = "acme.entry"
role = "adapter"
public_modules = []
[[packages]]
name = "sibling"
root = "acme.sibling"
role = "adapter"
public_modules = []
[[packages]]
name = "domain"
root = "acme.domain"
role = "domain"
public_modules = ["acme.domain.api"]
[[packages]]
name = "adapter"
root = "acme.adapter"
role = "adapter"
public_modules = ["acme.adapter.api"]
"""

    def write(self, filename: str, source: str) -> None:
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    def run_check(self) -> subprocess.CompletedProcess[str]:
        self.write("architecture.toml", self.policy)
        return subprocess.run(  # noqa: S603 -- copied toolkit in an isolated fixture repository
            [sys.executable, "-m", "architecture.api", "--root", str(self.root)],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def assert_passes(self) -> None:
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_rejected(self, *codes: str) -> str:
        result = self.run_check()
        self.assertIn(result.returncode, (1, 2), result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        for code in codes:
            self.assertIn(code, result.stdout)
        return result.stdout

    def test_allowed_public_and_internal_imports_pass(self) -> None:
        self.write(
            "src/acme/adapter/api.py", "from acme.domain.api import Contract\nfrom . import internal\n"
        )
        self.assert_passes()

    def test_visibility_and_direction_are_independent(self) -> None:
        self.write("src/acme/adapter/api.py", "import acme.domain.internal\n")
        self.assertNotIn("architecture-direction", self.assert_rejected("architecture-visibility"))
        self.write("src/acme/adapter/api.py", "")
        self.write("src/acme/domain/api.py", "import acme.adapter.api\n")
        self.assertNotIn("architecture-visibility", self.assert_rejected("architecture-direction"))
        self.write("src/acme/domain/api.py", "import acme.adapter.internal\n")
        self.assert_rejected("architecture-direction", "architecture-visibility")

    def test_import_forms_cannot_bypass_visibility(self) -> None:
        for source in (
            "from ..domain import internal\n",
            "from acme.domain import internal\n",
            "from acme.domain.api import *\nimport acme.domain.internal\n",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import acme.domain.internal\n",
            'import importlib as loader\nloader.import_module("acme.domain.internal")\n',
            'from importlib import import_module as load\nload("acme.domain.internal")\n',
            '__import__("acme.domain.internal")\n',
        ):
            with self.subTest(source=source):
                self.write("src/acme/adapter/api.py", source)
                self.assert_rejected("architecture-visibility")

    def test_mixed_from_import_retains_parent_dependency(self) -> None:
        self.write("src/acme/adapter/api.py", "from acme.domain import api, SECRET\n")
        self.assert_rejected("architecture-visibility", "'acme.domain'")

    def test_composition_exception_is_exact_and_stale_checked(self) -> None:
        self.policy = self.policy.replace("version = 2", 'version = 2\ncomposition_roots = ["acme.entry"]')
        self.write("src/acme/entry.py", "import acme.adapter.internal\n")
        self.assert_passes()
        self.write("src/acme/sibling.py", "import acme.adapter.internal\n")
        self.assert_rejected("architecture-visibility", "architecture-direction")
        self.policy = self.policy.replace('["acme.entry"]', '["acme.absent"]')
        self.assert_rejected("stale exact module")

    def test_added_units_require_ownership_but_internal_modules_stay_private(self) -> None:
        self.write("src/acme/unowned.py", "")
        self.assert_rejected("unclassified")
        (self.root / "src/acme/unowned.py").unlink()
        self.write("src/acme/domain/implementation.py", "")
        self.assert_passes()
        self.write("src/acme/adapter/api.py", "import acme.domain.implementation\n")
        self.assert_rejected("architecture-visibility")

    def test_invalid_policy_fails_closed(self) -> None:
        valid = self.policy
        for policy in (
            valid.replace("version = 2", "version = true"),
            valid.replace("version = 2", "version = 2.0"),
            valid.replace("version = 2", "version = 2\nunknown = true"),
            valid.replace('module = "acme"', 'module = "acme.*"'),
            valid.replace('path = "src/acme"', 'path = "../outside"'),
            valid.replace('path = "src/acme"', 'path = "absent"'),
            valid.replace('role = "domain"', 'role = "unknown"'),
            valid.replace("allowed_dependencies = []", 'allowed_dependencies = ["unknown"]'),
            valid.replace('public_modules = ["acme.domain.api"]', 'public_modules = ["acme.domain.absent"]'),
            valid.replace("include_descendants = false", 'include_descendants = "false"'),
            valid.replace('name = "domain"', 'name = "adapter"'),
            "not valid TOML",
        ):
            with self.subTest(policy=policy):
                self.policy = policy
                self.assert_rejected("architecture")

    def test_public_api_must_belong_to_declared_owner(self) -> None:
        self.policy += (
            '\n[[packages]]\nname="nested"\nroot="acme.domain.api"\nrole="domain"\npublic_modules=[]\n'
        )
        self.assert_rejected("owned by another package")

    def test_unknown_imports_and_parse_errors_fail(self) -> None:
        self.write("src/acme/domain/api.py", "import acme.domain.absent\n")
        self.assert_rejected("architecture-import")
        self.write("src/acme/domain/api.py", "def broken(\n")
        self.assert_rejected("architecture-parse")

    def test_role_and_package_cycles_are_separate(self) -> None:
        self.policy = self.policy.replace("allowed_dependencies = []", 'allowed_dependencies = ["adapter"]')
        self.assert_rejected("architecture-cycle")
        self.policy = self.policy.replace(
            'allowed_dependencies = ["adapter"]', 'allowed_dependencies = ["domain"]'
        )
        self.policy = self.policy.replace('role = "adapter"', 'role = "domain"')
        self.write("src/acme/domain/api.py", "import acme.adapter.api\n")
        self.write("src/acme/adapter/api.py", "import acme.domain.api\n")
        self.assert_passes()
        self.policy = self.policy.replace("version = 2", "version = 2\ncheck_package_cycles = true")
        self.assert_rejected("architecture-package-cycle")

    def test_baseline_is_exact_reviewed_and_shrinks(self) -> None:
        source = "import acme.domain.internal\n"
        self.write("src/acme/adapter/api.py", source)
        baseline = """version = 2
[[violations]]
importer = "acme.adapter.api"
importer_role = "adapter"
target_role = "domain"
rule = "visibility"
kind = "runtime-import"
count = 1
imports = ["acme.domain.internal"]
reason = "Migrate caller with domain facade."
"""
        self.write("architecture-baseline.toml", baseline)
        self.assert_passes()
        self.write("src/acme/adapter/api.py", source * 2)
        self.assert_rejected("architecture-visibility")
        self.write("src/acme/adapter/api.py", "import acme.domain\n")
        self.assert_rejected("architecture-visibility", "architecture-baseline-stale")
        self.write("src/acme/adapter/api.py", "")
        self.assert_rejected("architecture-baseline-stale")
        self.write("src/acme/adapter/api.py", source)
        self.write(
            "architecture-baseline.toml",
            baseline.replace('importer_role = "adapter"', 'importer_role = "domain"'),
        )
        self.assert_rejected("architecture-visibility", "architecture-baseline-stale")
        for invalid in (
            baseline.replace('reason = "Migrate caller with domain facade."', 'reason = ""'),
            baseline.replace("count = 1", "count = true"),
            baseline + baseline[baseline.index("[[violations]]") :],
        ):
            self.write("architecture-baseline.toml", invalid)
            self.assert_rejected("architecture")

    def test_standalone_and_stdlib_constraints_with_exact_loader_exception(self) -> None:
        self.policy = self.policy.replace(
            "version = 2", 'version = 2\nstdlib_only = true\nstandalone_modules = ["acme.entry"]'
        )
        for source in (
            "import requests\n",
            "import acme.domain.api\n",
            "from . import domain\n",
            '__import__("requests")\n',
        ):
            self.write("src/acme/entry.py", source)
            self.assert_rejected("architecture-script")
        self.write("src/acme/entry.py", "import ast\n")
        self.write("src/acme/adapter/api.py", "from . import internal\n")
        self.assert_passes()
        self.write(
            "src/acme/entry.py",
            'import importlib.util as loader\nloader.spec_from_file_location("hook", path)\n',
        )
        self.assert_rejected("architecture-dynamic")
        self.policy += '\n[dynamic_loading]\n"acme.entry"="Exercise public hook entry points."\n'
        self.assert_passes()
        self.write("src/acme/entry.py", "")
        self.assert_rejected("architecture-stale")

    def test_scan_ignores_generated_untracked_files_but_not_new_sources(self) -> None:
        self.write(".gitignore", "generated/\n")
        self.write("src/acme/generated/output.py", "import absent\n")
        self.assert_passes()
        self.write("src/acme/new.py", "")
        self.assert_rejected("unclassified")

    def test_nested_module_cannot_disguise_external_import_as_first_party(self) -> None:
        self.policy = self.policy.replace("version = 2", "version = 2\nstdlib_only = true")
        self.write("src/acme/domain/requests.py", "")
        self.write("src/acme/adapter/api.py", "import requests\n")
        self.assert_rejected("architecture-script")

    def test_git_hook_context_cannot_redirect_fixture_or_scan(self) -> None:
        for command in (
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "--allow-empty",
                "--quiet",
                "-m",
                "fixture",
            ],
            ["git", "worktree", "add", "--quiet", "--detach", str(self.root / "linked")],
        ):
            subprocess.run(command, cwd=self.root, capture_output=True, check=True, env=self.git_env)  # noqa: S603 -- fixed commands in temporary repository
        config = self.root / ".git/config"
        original = config.read_bytes()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.test_architecture.ArchitectureTests.test_allowed_public_and_internal_imports_pass",
            ],
            cwd=TOOLKIT.parents[3],
            env={**os.environ, "GIT_DIR": str(self.root / ".git/worktrees/linked")},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(config.read_bytes(), original)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_root_budget_counts_modules_not_statements_and_ratchets(self) -> None:
        self.policy = self.policy.replace("version = 2", "version = 2\nroot_module_max_inbound_importers = 1")
        self.policy = self.policy.replace(
            "public_modules = []\ninclude_descendants = false", 'public_modules = ["acme.shared"]'
        )
        self.write("src/acme/shared.py", "")
        # shared is owned by acme, not registered as a separate package.
        self.policy = self.policy.replace(
            'allowed_dependencies = ["domain"]', 'allowed_dependencies = ["domain", "adapter"]'
        )
        self.write("src/acme/entry.py", "import acme.shared\nimport acme.shared\n")
        self.assert_passes()
        self.write("src/acme/sibling.py", "import acme.shared\n")
        self.assert_rejected("architecture-root-module-inbound-importers")
        self.write(
            "architecture-baseline.toml",
            'version=2\n[[root_module_inbound_imports]]\npath="src/acme/shared.py"\ncount=2\nreason="Move consumers inward."\n',
        )
        self.assert_passes()
        self.write("src/acme/sibling.py", "")
        self.assert_rejected("architecture-baseline-stale")
        self.write("architecture-baseline.toml", "version=2\n")
        self.policy += '\n[file_overrides."src/acme/shared.py"]\nallow_unbounded_inbound_imports=true\nreason="Universal identifiers."\n'
        self.write("src/acme/shared.py", "import acme.domain.internal\n")
        self.assert_rejected("architecture-visibility")

    def test_one_level_families_do_not_expose_internal_descendants(self) -> None:
        self.policy += '\n[[package_families]]\nname="plugins"\nroot_pattern="acme.plugins.*"\nrole="adapter"\npublic_modules=["{root}.api"]\n'
        for filename in ("__init__", "api", "internal", "nested/__init__"):
            self.write(f"src/acme/plugins/example/{filename}.py", "")
        self.assert_passes()
        self.write("src/acme/plugins/example/api.py", "from acme.domain.api import Contract\n")
        self.assert_passes()
        self.write("src/acme/entry.py", "import acme.plugins.example.internal\n")
        self.assert_rejected("architecture-visibility")
        self.policy = self.policy.replace('root_pattern="acme.plugins.*"', 'root_pattern="acme.plugins.**"')
        self.assert_rejected("architecture configuration")

    def test_documented_starter_runs_with_copied_package(self) -> None:
        shutil.copytree(
            TOOLKIT,
            self.root / "scripts/prek_hooks/architecture",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        for filename in (
            "src/app/__init__.py",
            "src/app/cli.py",
            "src/app/core/__init__.py",
            "src/app/core/api.py",
            "src/app/core/internal.py",
            "tests/__init__.py",
        ):
            self.write(filename, "")
        self.policy = (TOOLKIT.parents[1] / "assets/architecture.toml").read_text(encoding="utf-8")
        self.write("architecture.toml", self.policy)
        command = [sys.executable, "-m", "scripts.prek_hooks.architecture.api"]
        allowed = subprocess.run(command, cwd=self.root, capture_output=True, text=True, check=False)  # noqa: S603 -- documented copied-toolkit command
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
        self.write("tests/test_contract.py", "import app.core.internal\n")
        rejected = subprocess.run(command, cwd=self.root, capture_output=True, text=True, check=False)  # noqa: S603 -- same command with violating fixture
        self.assertEqual(rejected.returncode, 1, rejected.stdout + rejected.stderr)
        self.assertIn("architecture-visibility", rejected.stdout)


if __name__ == "__main__":
    unittest.main()
