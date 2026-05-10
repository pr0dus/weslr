import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.standalone_runtime_status import (
    find_repo_root,
    get_standalone_runtime_status,
    scan_runtime_openclaw_coupling,
)


class TestStandaloneRuntimeStatusV1(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(ROOT)

    def test_find_repo_root_resolves_current_repo(self):
        resolved = find_repo_root(self.repo_root / "weslr" / "tests")
        self.assertEqual(resolved, self.repo_root)

    def test_status_reports_expected_runtime_mode_and_read_only(self):
        status = get_standalone_runtime_status(self.repo_root)
        self.assertEqual(status["runtime_mode"], "standalone_candidate")
        self.assertTrue(status["read_only"])
        self.assertTrue(status["repo_root_detected"])

    def test_status_reports_openclaw_not_required(self):
        status = get_standalone_runtime_status(self.repo_root)
        self.assertFalse(status["openclaw_runtime_required"])

    def test_status_includes_expected_subsystems(self):
        status = get_standalone_runtime_status(self.repo_root)
        subsystems = status["subsystems"]
        for name in (
            "interpretation",
            "file_router",
            "eval_harness",
            "state_checkpoint",
            "governance_health",
            "public_demo_chat",
        ):
            self.assertIn(name, subsystems)
            self.assertIn("available", subsystems[name])
            self.assertIn("path", subsystems[name])

    def test_openclaw_path_in_repo_path_does_not_make_runtime_required(self):
        with tempfile.TemporaryDirectory(prefix="fake-.openclaw-") as td:
            nested = Path(td) / "repo" / "weslr"
            nested.mkdir(parents=True)
            (Path(td) / "repo" / "main.py").write_text("# stub\n", encoding="utf-8")
            status = get_standalone_runtime_status(Path(td) / "repo")
            self.assertFalse(status["openclaw_runtime_required"])
            self.assertTrue(status["openclaw_runtime_detected"])

    def test_coupling_scanner_checks_only_runnable_runtime_files(self):
        scan = scan_runtime_openclaw_coupling(self.repo_root)
        self.assertEqual(
            scan["checked_files"],
            [
                "main.py",
                "run.sh",
                "weslr_main.py",
                "weslr-test-deployment/api_server.py",
                "deploy/staging/weslr_demo_server.py",
            ],
        )

    def test_coupling_scanner_reports_clean_for_current_runtime_files(self):
        scan = scan_runtime_openclaw_coupling(self.repo_root)
        self.assertTrue(scan["clean"])
        self.assertEqual(scan["hardcoded_openclaw_paths"], [])

    def test_status_has_recommendations_and_blockers_fields(self):
        status = get_standalone_runtime_status(self.repo_root)
        self.assertIn("recommendations", status)
        self.assertIn("standalone_blockers", status)
        self.assertIsInstance(status["recommendations"], list)
        self.assertIsInstance(status["standalone_blockers"], list)

    def test_module_does_not_mutate_files(self):
        target = self.repo_root / "weslr-test-deployment" / "api_server.py"
        before = target.read_bytes()
        before_mtime = target.stat().st_mtime_ns
        _ = get_standalone_runtime_status(self.repo_root)
        after = target.read_bytes()
        after_mtime = target.stat().st_mtime_ns
        self.assertEqual(before, after)
        self.assertEqual(before_mtime, after_mtime)


if __name__ == "__main__":
    unittest.main()
