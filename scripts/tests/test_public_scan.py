"""Regression coverage for publishing the index, rather than trusting the working tree."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("public_scan", Path(__file__).resolve().parents[1] / "check_public_repo.py")
scanner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scanner)


class PublicScanTests(unittest.TestCase):
    def test_secret_findings_hide_matched_values(self):
        fake_key = "sk-" + "x" * 48
        with patch.object(scanner, "working_files", return_value=iter([("example.txt", fake_key.encode())])), patch("sys.argv", ["scan"]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = scanner.main()
        self.assertEqual(result, 1)
        self.assertIn("provider-key", output.getvalue())
        self.assertNotIn(fake_key, output.getvalue())

    def test_staged_scan_detects_a_secret_removed_only_from_working_tree(self):
        with tempfile.TemporaryDirectory(prefix="ailf-scan-") as directory:
            root = Path(directory).resolve()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            file = root / "example.txt"
            file.write_text("sk-" + "x" * 48, encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "example.txt"], check=True)
            file.write_text("safe working copy", encoding="utf-8")
            with patch.object(scanner, "ROOT", root):
                staged = list(scanner.working_files(True))
                working = list(scanner.working_files(False))
            self.assertEqual(scanner.scan_text(*staged[0])[0][2], "provider-key")
            self.assertEqual(scanner.scan_text(*working[0]), [])

    def test_private_files_are_rejected_but_templates_are_allowed(self):
        for name in (".env", "backend/.env.production", "backup.sql", "service-account.json", "adapter.safetensors"):
            with self.subTest(name=name):
                self.assertTrue(scanner.forbidden_path(name))
        self.assertFalse(scanner.forbidden_path("backend/.env.example"))

    def test_public_fixture_identifiers_are_allowed(self):
        self.assertEqual(scanner.scan_text("example.json", b'{"id":"DEMO-0001","phone":"00000000000","email":"user@example.com"}'), [])


if __name__ == "__main__":
    unittest.main()
