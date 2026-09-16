"""Regression tests through the standalone scripts' public CLI."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/strictify/scripts"


class HookCliTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def run_hook(
        self, hook: str, source: str | bytes, *args: str, filename: str = "sample.py"
    ) -> subprocess.CompletedProcess[str]:
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        expected = source.encode("utf-8") if isinstance(source, str) else source
        path.write_bytes(expected)
        result = subprocess.run(  # noqa: S603 -- repository scripts and isolated fixtures
            [sys.executable, str(SCRIPTS / f"check_{hook}.py"), *args, filename],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(path.read_bytes(), expected)
        return result

    def test_broad_exception_forms_are_rejected(self) -> None:
        for exception in ("Exception", "BaseException", "builtins.Exception", "(ValueError, Exception)"):
            with self.subTest(exception=exception):
                result = self.run_hook(
                    "exception_handling", f"try:\n    work()\nexcept {exception}:\n    pass\n"
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn("sample.py:3:", result.stdout)

    def test_each_hook_runs_as_a_single_copied_file(self) -> None:
        for script in sorted(SCRIPTS.glob("*.py")):
            with self.subTest(script=script.name):
                copied = self.root / "standalone.py"
                copied.write_bytes(script.read_bytes())
                fixture = self.root / "test_example.py"
                fixture.write_text("value = 1\n", encoding="utf-8")
                result = subprocess.run(  # noqa: S603 -- copied hook and isolated fixture
                    [sys.executable, "-I", str(copied), str(fixture)],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(fixture.read_text(encoding="utf-8"), "value = 1\n")

    def test_exception_logging_requires_a_logger_receiver(self) -> None:
        for receiver, expected in (("logger", 0), ("logging", 0), ("audit_logger", 0), ("widget", 1)):
            with self.subTest(receiver=receiver):
                result = self.run_hook(
                    "exception_handling",
                    f"try:\n    work()\nexcept Exception:\n    {receiver}.error('failed')\n",
                )
                self.assertEqual(result.returncode, expected)

    def test_narrow_and_reraising_handlers_are_allowed(self) -> None:
        for clause in ("except ValueError:\n    pass", "except Exception:\n    raise"):
            with self.subTest(clause=clause):
                self.assertEqual(
                    self.run_hook("exception_handling", f"try:\n    work()\n{clause}\n").returncode, 0
                )

    def test_exception_exemption_must_be_an_exact_comment(self) -> None:
        for body, expected in (
            ("pass  # allow: exception-handling", 0),
            ('report("# allow: exception-handling")', 1),
            ("pass  # allow: exception-handling-extra", 1),
        ):
            with self.subTest(body=body):
                result = self.run_hook("exception_handling", f"try: work()\nexcept Exception: {body}\n")
                self.assertEqual(result.returncode, expected)

    def test_private_imports_only_check_test_paths(self) -> None:
        for filename, expected in (
            ("contest.py", 0),
            ("contests/report.py", 0),
            ("tests/report.py", 1),
            ("test/report.py", 1),
            ("app_test.py", 1),
        ):
            with self.subTest(filename=filename):
                result = self.run_hook(
                    "private_test_imports", "from app import _secret\n", "--package", "app", filename=filename
                )
                self.assertEqual(result.returncode, expected)

    def test_relative_test_helpers_are_not_absolute_first_party_imports(self) -> None:
        result = self.run_hook(
            "private_test_imports",
            "from .app import _fixture\n",
            "--package",
            "app",
            filename="tests/test_app.py",
        )
        self.assertEqual(result.returncode, 0)

    def test_private_import_exemptions_apply_per_name(self) -> None:
        source = "from app import (\n    _one,  # allow: private-test-imports\n    _two,\n)\n"
        result = self.run_hook(
            "private_test_imports", source, "--package", "app", filename="tests/test_app.py"
        )
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("private '_one'", result.stdout)
        self.assertIn("private '_two'", result.stdout)

    def test_private_import_exemption_cannot_be_a_string(self) -> None:
        result = self.run_hook(
            "private_test_imports",
            'from app import _one; reason = "# allow: private-test-imports"\n',
            "--package",
            "app",
            filename="test_app.py",
        )
        self.assertEqual(result.returncode, 1)

    def test_file_length_counts_code_sharing_a_docstring_line(self) -> None:
        result = self.run_hook(
            "file_length", '"""Module docs."""; first = 1\nsecond = 2\n', "--max-lines", "1"
        )
        self.assertEqual(result.returncode, 1)

    def test_file_length_exemption_cannot_be_a_string(self) -> None:
        result = self.run_hook(
            "file_length", 'MARKER = "# allow: file-length"\nfirst = 1\n', "--max-lines", "1"
        )
        self.assertEqual(result.returncode, 1)

    def test_file_length_ignores_comments_and_standalone_strings(self) -> None:
        source = '# heading\n"""Module\ndocs.\n"""\n\nfirst = 1  # inline\n'
        self.assertEqual(self.run_hook("file_length", source, "--max-lines", "1").returncode, 0)

    def test_timeless_comments_do_not_scan_code_next_to_docstrings(self) -> None:
        self.assertEqual(self.run_hook("timeless_comments", '"""Module docs."""; old = 1\n').returncode, 0)

    def test_timeless_exemption_cannot_be_a_code_string(self) -> None:
        result = self.run_hook(
            "timeless_comments", 'MARKER = "# allow: timeless-comments"  # legacy behavior\n'
        )
        self.assertEqual(result.returncode, 1)

    def test_timeless_task_markers_are_words(self) -> None:
        self.assertEqual(self.run_hook("timeless_comments", "# old todoscope\n").returncode, 1)

    def test_missing_files_are_ignored(self) -> None:
        for hook in ("exception_handling", "file_length", "private_test_imports", "timeless_comments"):
            with self.subTest(hook=hook):
                result = subprocess.run(  # noqa: S603 -- fixed scripts and nonexistent fixture
                    [sys.executable, str(SCRIPTS / f"check_{hook}.py"), "test_deleted.py"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_source_is_left_to_ruff(self) -> None:
        for hook in ("exception_handling", "file_length", "private_test_imports", "timeless_comments"):
            for source in (b"value = \xff\n", b"def incomplete("):
                with self.subTest(hook=hook, source=source):
                    args = ("--package", "app") if hook == "private_test_imports" else ()
                    result = self.run_hook(hook, source, *args, filename="test_app.py")
                    self.assertEqual(result.returncode, 0)

    def test_file_length_handles_unicode_and_multiline_literals(self) -> None:
        for source in (
            '"""Résumé."""; first = 1\nsecond = 2\n',
            'DATA = """first\n# literal data\n"""\n',
        ):
            with self.subTest(source=source):
                self.assertEqual(self.run_hook("file_length", source, "--max-lines", "1").returncode, 1)

    def test_file_length_exemption_is_limited_to_first_five_lines(self) -> None:
        for padding, expected in ((4, 0), (5, 1)):
            with self.subTest(padding=padding):
                source = "\n" * padding + "# allow: file-length\nfirst = 1\nsecond = 2\n"
                self.assertEqual(
                    self.run_hook("file_length", source, "--max-lines", "1").returncode, expected
                )
