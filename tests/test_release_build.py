# SPDX-License-Identifier: GPL-2.0-or-later
"""Distribution checks must prevent publishing unverified archives."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_plugin
from release_checks import check_reports


class ReleaseBuildTests(unittest.TestCase):
    def test_findings_and_incomplete_reports_fail_even_with_success_exit(self):
        clean = ({"results": [], "errors": []}, {"results": {}},
                 "=== dry_run mode | Start Logs ===\n")
        check_reports(*clean)
        cases = [({"results": ["finding"]}, clean[1], clean[2]),
                 ({"results": [], "errors": ["unreadable"]}, clean[1], clean[2]),
                 ({}, clean[1], clean[2]),
                 (clean[0], {"results": {"file": ["finding"]}}, clean[2]),
                 (clean[0], {}, clean[2]),
                 (clean[0], clean[1], clean[2] + "Replace Qt enum\n"),
                 (clean[0], clean[1], "")]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(RuntimeError):
                check_reports(*case)

    def build(self, directory, scanner):
        with patch.object(sys, "argv", ["build_plugin.py", "--release", "--output-dir", directory]), \
                patch.object(build_plugin, "scan", scanner), contextlib.redirect_stdout(io.StringIO()):
            build_plugin.main()

    def test_failed_check_leaves_no_distribution(self):
        with tempfile.TemporaryDirectory() as directory:
            def fail(*args):
                raise RuntimeError("missing tool or finding")
            with self.assertRaises(RuntimeError):
                self.build(directory, fail)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_success_scans_extracted_zip_and_records_matching_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            def passed(package, reports, *args):
                self.assertTrue((package / "metadata.txt").is_file())
                self.assertFalse((package / "settings.json").exists())
                reports.mkdir()
                return {"checks": ["test double"]}
            self.build(directory, passed)
            archive, = Path(directory).glob("*.zip")
            summary = json.loads((archive.with_suffix(".checks") / "summary.json").read_text())
            self.assertEqual(summary["zip_sha256"], build_plugin.hashlib.sha256(archive.read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):
                self.build(directory, passed)

    def test_mutating_checker_cannot_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            def mutate(package, reports, *args):
                (package / "plugin.py").write_text("changed", encoding="utf-8")
                reports.mkdir()
                return {}
            with self.assertRaisesRegex(RuntimeError, "modified"):
                self.build(directory, mutate)
            self.assertEqual(list(Path(directory).iterdir()), [])
