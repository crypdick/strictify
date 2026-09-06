"""Exercise shipped policy through tool and script command-line boundaries."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/strictify"


class ShippedPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        reference = (SKILL / "references/pyproject-strict.md").read_text()
        blocks = re.findall(r"```toml\n(.*?)```", reference, re.DOTALL)
        config = "\n".join(blocks)
        tomllib.loads(config)
        (self.root / "pyproject.toml").write_text(config)

    def run_ruff(self, filename: str, source: bytes) -> subprocess.CompletedProcess[str]:
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source)
        result = subprocess.run(  # noqa: S603 -- fixed interpreter and repository-controlled fixtures
            [sys.executable, "-m", "ruff", "check", "--no-fix", "--output-format", "json", filename],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(path.read_bytes(), source)
        return result

    def test_print_exemptions_and_production_rejection(self) -> None:
        for filename in (
            "cli.py",
            "pkg/__main__.py",
            "tests/test_app.py",
            "tools/report.py",
            "_tools/report.py",
            "scripts/report.py",
        ):
            with self.subTest(filename=filename):
                result = self.run_ruff(filename, b'print("hello")\n')
                self.assertNotIn("T201", result.stdout)
                self.assertNotIn("No module named ruff", result.stderr)
        result = self.run_ruff("app.py", b'print("hello")\n')
        self.assertIn("T201", result.stdout)
        result = self.run_ruff("app.py", b'print("hello")  # noqa: T201\n')
        self.assertNotIn("T201", result.stdout)

    def test_logging_detection_respects_receiver(self) -> None:
        result = self.run_ruff("app.py", b'widget.info(f"Hello {name}")\n')
        self.assertNotIn("G004", result.stdout)
        result = self.run_ruff("app.py", b'import logging\nlogging.info(f"Hello {name}")\n')
        self.assertIn("G004", result.stdout)

    def test_future_import_policy_preserves_source(self) -> None:
        for source in (
            b'EXAMPLE = """\nfrom __future__ import annotations\n"""\n',
            b'# Copyright holder\n"""Public docs."""\nfrom __future__ import annotations\n',
            b'r"""Public docs."""\nfrom __future__ import annotations\n',
            b"import os\r\nfrom __future__ import annotations\r\n",
        ):
            with self.subTest(source=source):
                result = self.run_ruff("app.py", source)
                if source.startswith(b"import os"):
                    self.assertIn("F404", result.stdout)
        template = (SKILL / "references/prek-config.md").read_text()
        self.assertNotIn('id = "fix-future-annotations"', template)
        self.assertNotIn('id = "check-print-statements"', template)

    def test_flat_module_private_import_is_rejected(self) -> None:
        for directory in (self.root, self.root / "src"):
            with self.subTest(directory=directory):
                directory.mkdir(exist_ok=True)
                module = directory / "app.py"
                module.write_text("_secret = 1\n")
                test = self.root / "test_app.py"
                test.write_text("from app import _secret\n")
                result = subprocess.run(  # noqa: S603 -- fixed interpreter and repository-controlled fixtures
                    [sys.executable, str(SKILL / "scripts/check_private_test_imports.py"), test.name],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("private '_secret'", result.stdout)
                module.unlink()

    def test_beartype_is_not_in_dev_install(self) -> None:
        skill = (SKILL / "SKILL.md").read_text()
        commands = re.findall(r"`(uv add --dev [^`]+)`", skill)
        self.assertTrue(commands)
        for command in commands:
            self.assertNotIn("beartype", command.split())
        self.assertIn("`uv add beartype`", skill)

    def test_documented_boundary_rejects_invalid_input(self) -> None:
        document = (SKILL / "assets/CONVENTIONS.md-EXAMPLE").read_text()
        section = document.split("## Parse, don't validate", 1)[1]
        example = re.findall(r"```python\n(.*?)```", section, re.DOTALL)[0]
        path = self.root / "boundary.py"
        path.write_text(
            example
            + """
assert parse_user_request({"user_id": "alice"}).user_id == "alice"
for value in ({}, {"user_id": 123}, {"user_id": ""}, None, []):
    try:
        parse_user_request(value)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError(f"Accepted invalid input: {value!r}")
"""
        )
        result = subprocess.run(  # noqa: S603 -- fixed interpreter and repository-controlled fixtures
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
