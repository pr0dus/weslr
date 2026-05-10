import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestStandaloneRuntimeStatusCliV1(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(ROOT)
        self.cli = self.repo_root / "weslr_main.py"
        self.api_server = self.repo_root / "weslr-test-deployment" / "api_server.py"

    def _run_cli(self):
        return subprocess.run(
            [sys.executable, str(self.cli), "standalone-status", "--json"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )

    def test_cli_command_exists_and_returns_json(self):
        result = self._run_cli()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, dict)

    def test_cli_json_contains_expected_runtime_fields(self):
        result = self._run_cli()
        payload = json.loads(result.stdout)
        self.assertEqual(payload["runtime_mode"], "standalone_candidate")
        self.assertFalse(payload["openclaw_runtime_required"])
        self.assertIn("subsystems", payload)

    def test_cli_exits_zero_when_no_blockers(self):
        result = self._run_cli()
        payload = json.loads(result.stdout)
        self.assertEqual(payload["standalone_blockers"], [])
        self.assertEqual(result.returncode, 0)

    def test_existing_status_surface_still_passes_through_cli(self):
        result = self._run_cli()
        payload = json.loads(result.stdout)
        self.assertTrue(payload["read_only"])
        self.assertTrue(payload["repo_root_detected"])

    def test_no_endpoint_added_in_this_step(self):
        text = self.api_server.read_text(encoding="utf-8")
        self.assertNotIn('/api/status', text)
        self.assertNotIn('standalone_runtime_status', text)


if __name__ == "__main__":
    unittest.main()
