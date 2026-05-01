"""
Tests for Staging Demo Server Evidence Bridge Integration V1
Read-only. No live web calls. No Ollama. No JSONL writes.
"""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
STAGING_SERVER = REPO_ROOT / "deploy" / "staging" / "weslr_demo_server.py"


class TestStagingDemoEvidenceBridgeIntegration(unittest.TestCase):

    def test_server_file_exists(self):
        self.assertTrue(STAGING_SERVER.exists(), "weslr_demo_server.py not found")

    def test_server_imports_evidence_chat_bridge(self):
        """Evidence chat bridge is imported in staging server."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        self.assertIn("from weslr.evidence_chat_bridge import maybe_answer_with_evidence", content)

    def test_bridge_called_inside_post_chat_handler(self):
        """Evidence bridge is called inside the POST /chat handler."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        # Confirm integration is inside POST handler (after response built)
        # The comment "─── Evidence Chat Bridge" and call to maybe_answer_with_evidence
        # should appear after the response = weslr_chat(message) call
        post_handler_idx = content.find("def do_POST(self):")
        self.assertGreater(post_handler_idx, -1, "do_POST handler not found")
        bridge_idx = content.find("maybe_answer_with_evidence")
        self.assertGreater(bridge_idx, -1, "maybe_answer_with_evidence not called")
        # Bridge call must come after do_POST starts
        self.assertGreater(bridge_idx, post_handler_idx, "Bridge call must be inside do_POST")

    def test_bridge_result_overrides_message_field(self):
        """When bridge activates, response.reply is overridden."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        # Verify the override pattern: response["reply"] = _bridge_result["message"]
        self.assertIn('response["reply"] = _bridge_result["message"]', content)
        self.assertIn('response["path"] = _bridge_result["path"]', content)
        self.assertIn('response["response_contract"] = _bridge_result.get("response_contract")', content)
        self.assertIn('response["_evidence_metadata"] = _bridge_result["evidence_metadata"]', content)

    def test_bridge_exception_guarded(self):
        """Bridge failure is wrapped in try/except — never crashes request."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        # The evidence bridge section must have its own try/except
        bridge_section_start = content.find("# ── Evidence Chat Bridge")
        self.assertGreater(bridge_section_start, -1)
        # Find the section that contains the bridge call
        bridge_section = content[bridge_section_start:bridge_section_start + 1000]
        self.assertIn("try:", bridge_section)
        # Look for "except" keyword in the bridge section (catches bare except variants)
        self.assertTrue(
            "except" in bridge_section,
            "No except block found in bridge section",
        )
        self.assertIn("pass", bridge_section)  # silent failure

    def test_bridge_called_with_message_and_reply(self):
        """Bridge is called with (message, response.get('reply'))."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        self.assertIn("maybe_answer_with_evidence(\n                message,\n                response.get(\"reply\"),\n            )", content)

    def test_response_structure_updated(self):
        """Confirmed: reply, path, response_contract, _evidence_metadata are all set."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        fields_updated = [
            'response["reply"]',
            'response["path"]',
            'response["response_contract"]',
            'response["_evidence_metadata"]',
        ]
        for field in fields_updated:
            self.assertIn(field, content)

    def test_no_ollama_import_in_staging_server(self):
        """Staging server does not import Ollama."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        self.assertNotIn("from ollama", content)
        self.assertNotIn("import ollama", content)

    def test_no_jsonl_writes_in_staging_server(self):
        """Staging server does not write JSONL files."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        self.assertNotIn(".jsonl", content.lower())

    def test_original_chat_behavior_unchanged_comment(self):
        """Comment confirms original behavior is preserved."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        # The signal capture comment still says original behavior unchanged
        self.assertIn("# ── Return original response unchanged", content)

    def test_evidence_bridge_comment_describes_guards(self):
        """Bridge comment documents the activation guards."""
        with open(STAGING_SERVER) as f:
            content = f.read()
        comment = "# Only activates when: search enabled, evidence_needed=true,"
        self.assertIn(comment, content)


class TestNoSideEffects(unittest.TestCase):

    def test_workspace_accessible(self):
        self.assertTrue(REPO_ROOT.exists())

    def test_no_jsonl_writes_in_test(self):
        weslr_dir = REPO_ROOT / "weslr"
        if not weslr_dir.exists():
            return
        before = {}
        for p in weslr_dir.rglob("*.jsonl"):
            before[str(p)] = p.stat().st_mtime
        # No actual server running — just verify file content
        self.assertTrue(STAGING_SERVER.exists())
        for p in weslr_dir.rglob("*.jsonl"):
            self.assertEqual(p.stat().st_mtime, before.get(str(p)))


if __name__ == "__main__":
    unittest.main()