import os
import sys
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TestStandaloneRuntimeIndependenceV1(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(ROOT)
        self.api_server = self.repo_root / "weslr-test-deployment" / "api_server.py"
        self.staging_server = self.repo_root / "deploy" / "staging" / "weslr_demo_server.py"
        self.run_sh = self.repo_root / "run.sh"
        self.weslr_main = self.repo_root / "weslr_main.py"

    def test_api_server_no_longer_contains_openclaw_workspace_path(self):
        text = self.api_server.read_text(encoding="utf-8")
        self.assertNotIn(".openclaw/workspace", text)
        self.assertNotIn("/data/data/com.termux/files/home/.openclaw/workspace", text)

    def test_api_server_uses_dynamic_repo_root_detection(self):
        text = self.api_server.read_text(encoding="utf-8")
        self.assertIn("from pathlib import Path", text)
        self.assertIn("def _find_repo_root", text)
        self.assertIn("Path(__file__).resolve()", text)
        self.assertIn('(candidate / "main.py").is_file()', text)
        self.assertIn('(candidate / "weslr").is_dir()', text)
        self.assertIn("sys.path.insert(0, str(REPO_ROOT))", text)

    def test_repo_root_detection_logic_resolves_current_repo(self):
        namespace = {}
        source = self.api_server.read_text(encoding="utf-8")
        prefix = source.split("REPO_ROOT =", 1)[0]
        exec(prefix, namespace)
        finder = namespace["_find_repo_root"]
        resolved = finder(self.api_server.resolve().parent)
        self.assertEqual(resolved, self.repo_root)

    def test_runnable_deployment_files_do_not_require_openclaw_runtime_dependency(self):
        runtime_files = [
            self.api_server,
            self.staging_server,
            self.run_sh,
            self.weslr_main,
        ]
        for path in runtime_files:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("/data/data/com.termux/files/home/.openclaw/workspace", text, msg=str(path))
            self.assertNotIn("sys.path.insert(0, '/data/data/com.termux/files/home/.openclaw/workspace')", text, msg=str(path))
            self.assertNotIn('sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")', text, msg=str(path))


if __name__ == "__main__":
    unittest.main()
