"""Regression tests for strictify's shipped hook scripts and guidance."""

from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "strictify" / "scripts"


class TimelessCommentsModule(Protocol):
    """Typed surface used from the dynamically loaded hook module."""

    @staticmethod
    def check_timeless_comments(file_path: Path) -> list[tuple[int, str, str]]:
        """Return timeless-comment violations."""
        ...


class FileLengthModule(Protocol):
    """Typed surface used from the dynamically loaded hook module."""

    @staticmethod
    def main(filenames: list[str] | None = None) -> int:
        """Run the file-length hook."""
        ...


def load_hook_module(name: str) -> ModuleType:
    """Load one shipped hook script as a module."""
    script_path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    if spec is None or spec.loader is None:
        msg = f"Unable to load hook module: {script_path}"
        raise RuntimeError(msg)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TIMELESS_COMMENTS = cast("TimelessCommentsModule", load_hook_module("check_timeless_comments"))
FILE_LENGTH = cast("FileLengthModule", load_hook_module("check_file_length"))


class HookScriptTests(unittest.TestCase):
    """Protect the behavior and remediation text shipped to target repos."""

    def write_source(self, source: str) -> Path:
        """Write a temporary Python source file and return its path."""
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "sample.py"
        path.write_text(source, encoding="utf-8")
        return path

    def test_timeless_comments_ignores_strings_and_fixture_delimiters(self) -> None:
        """Triple-quoted fixtures and string contents are not comments."""
        path = self.write_source(
            '''FIXTURE = """
# fallback data from an external system
"""
old = "# previous value"
'''
        )

        self.assertEqual(TIMELESS_COMMENTS.check_timeless_comments(path), [])

    def test_timeless_comments_checks_real_docstrings_and_comments(self) -> None:
        """Real docstrings and tokenized comments remain enforced."""
        path = self.write_source(
            '''"""Legacy adapter."""

def load() -> str:
    """Fallback loader."""
    value = "# old value"
    return value  # previous behavior
'''
        )

        violations = TIMELESS_COMMENTS.check_timeless_comments(path)

        self.assertEqual([line for line, _text, _keyword in violations], [1, 4, 6])

    def test_timeless_comments_honors_exemption_markers(self) -> None:
        """Explicit exemptions and task markers remain allowed."""
        path = self.write_source(
            """# fallback provider  # temporal-ok
# TODO: replace provider
"""
        )

        self.assertEqual(TIMELESS_COMMENTS.check_timeless_comments(path), [])

    def test_file_length_advice_avoids_junk_drawers_and_inheritance(self) -> None:
        """Remediation must agree with strictify's design principles."""
        path = self.write_source("first = 1\nsecond = 2\n")
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = FILE_LENGTH.main([str(path), "--max-lines", "1"])

        advice = output.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("domain-focused module", advice)
        self.assertIn("composed collaborators", advice)
        self.assertNotIn("utils module", advice)
        self.assertNotIn("mixins", advice)
        self.assertNotIn("sub-classes", advice)

    def test_skill_uses_stdlib_compatible_structured_logging(self) -> None:
        """The skill must not recommend unsupported logging keyword arguments."""
        skill = (REPO_ROOT / "skills" / "strictify" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn('logger.info("message", extra={"key": value})', skill)
        self.assertNotIn('logger.info("message", key=value)', skill)
