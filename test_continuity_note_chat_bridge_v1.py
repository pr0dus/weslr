"""
test_continuity_note_chat_bridge_v1.py
======================================
Tests for continuity_note_chat_bridge V1.

Uses temporary directories only — no writes to real .weslr/timelines.
"""

import json
import tempfile
import unittest
from pathlib import Path

from weslr.continuity_note_chat_bridge import (
    is_continuity_query,
    maybe_answer_with_continuity_note,
)
from weslr.user_timeline_memory import append_session_summary


class TestIsContinuityQuery(unittest.TestCase):
    def _check(self, msg: str) -> bool:
        return is_continuity_query(msg)

    def test_do_you_remember_what_we_worked_on(self):
        self.assertTrue(self._check("do you remember what we worked on?"))

    def test_remember_what_we_worked_on(self):
        self.assertTrue(self._check("remember what we worked on"))

    def test_continue_from_last_time(self):
        self.assertTrue(self._check("continue from last time"))

    def test_what_did_we_do_last_time(self):
        self.assertTrue(self._check("What did we do last time?"))

    def test_what_were_we_working_on(self):
        self.assertTrue(self._check("What were we working on?"))

    def test_what_did_we_work_on_yesterday(self):
        self.assertTrue(self._check("what did we work on yesterday"))

    def test_what_did_we_discuss_last_time(self):
        self.assertTrue(self._check("what did we discuss last time"))

    def test_case_insensitive(self):
        self.assertTrue(self._check("DO YOU REMEMBER WHAT WE WORKED ON?"))
        self.assertTrue(self._check("What Did We Do Last Time?"))

    def test_whitespace_tolerant(self):
        self.assertTrue(self._check("  do   you   remember   what   we   worked   on  "))

    def test_not_continuity_what_is_entropy(self):
        self.assertFalse(self._check("what is entropy?"))

    def test_not_continuity_what_is_weslr(self):
        self.assertFalse(self._check("what is WESLR"))

    def test_not_continuity_what_can_you_do(self):
        self.assertFalse(self._check("what can you do?"))

    def test_not_continuity_empty_slash(self):
        self.assertFalse(self._check("/"))

    def test_not_continuity_evidence(self):
        self.assertFalse(self._check("/evidence what is entropy"))

    def test_not_continuity_whitespace_only(self):
        self.assertFalse(self._check("   "))

    def test_not_continuity_none(self):
        self.assertFalse(self._check(None))


class TestMaybeAnswerWithContinuityNote(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_returns_none_for_non_continuity(self):
        result = maybe_answer_with_continuity_note(
            "what is entropy?",
            user_id="testuser",
            base_dir=self.tmpdir,
        )
        self.assertIsNone(result)

    def test_returns_continuity_note_for_query(self):
        append_session_summary(
            "testuser",
            "Completed Jarvis gap assessment",
            source="manual",
            base_dir=self.tmpdir,
        )
        result = maybe_answer_with_continuity_note(
            "what did we work on last time?",
            user_id="testuser",
            base_dir=self.tmpdir,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["path"], "continuity_note")
        self.assertEqual(result["response_contract"], "system_answer")
        self.assertIn("Completed Jarvis gap assessment", result["reply"])

    def test_response_includes_stored_summary(self):
        append_session_summary(
            "testuser",
            "First session summary test",
            source="manual",
            tags=["test"],
            base_dir=self.tmpdir,
        )
        result = maybe_answer_with_continuity_note(
            "do you remember what we worked on?",
            user_id="testuser",
            base_dir=self.tmpdir,
        )
        self.assertIn("First session summary test", result["reply"])

    def test_no_history_returns_safe_message(self):
        result = maybe_answer_with_continuity_note(
            "what did we do last time?",
            user_id="brandnewuser",
            base_dir=self.tmpdir,
        )
        self.assertIsNotNone(result)
        self.assertIn("do not have prior timeline notes", result["reply"])

    def test_continuity_metadata_fields(self):
        append_session_summary(
            "testuser",
            "Test summary",
            source="manual",
            base_dir=self.tmpdir,
        )
        result = maybe_answer_with_continuity_note(
            "continue from last time",
            user_id="testuser",
            base_dir=self.tmpdir,
        )
        meta = result["_continuity_metadata"]
        self.assertTrue(meta["continuity_used"])
        self.assertEqual(meta["authority"], "user_timeline_memory")
        self.assertFalse(meta["automatic_action"])
        self.assertFalse(meta["hidden_learning"])
        self.assertFalse(meta["raw_prompt_stored"])
        self.assertEqual(meta["events_used"], 1)

    def test_uses_temp_dir_only(self):
        result = maybe_answer_with_continuity_note(
            "what were we working on?",
            user_id="sandboxuser",
            base_dir=self.tmpdir,
        )
        # Should not crash and should return safe no-history note
        self.assertIsNotNone(result)
        self.assertIn("do not have prior timeline notes", result["reply"])


class TestNoExternalCalls(unittest.TestCase):
    def test_no_ollama_import_in_bridge(self):
        import ast
        with open("weslr/continuity_note_chat_bridge.py", "r") as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("ollama", alias.name.lower())
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn("ollama", (node.module or "").lower())

    def test_no_http_requests(self):
        with open("weslr/continuity_note_chat_bridge.py", "r") as f:
            source = f.read()
        for keyword in ["requests.", "urllib", "httpx", "aiohttp"]:
            self.assertNotIn(keyword, source)


class TestStagingServerIntegration(unittest.TestCase):
    def test_continuity_bridge_before_capability_welcome_in_staging(self):
        with open("deploy/staging/weslr_demo_server.py", "r") as f:
            source = f.read()
        # Find positions of continuity_note_chat_bridge and capability_welcome_chat_bridge
        cont_pos = source.find("continuity_note_chat_bridge")
        cap_pos = source.find("capability_welcome_chat_bridge")
        self.assertGreater(cont_pos, 0, "continuity_note_chat_bridge not found in staging server")
        self.assertGreater(cap_pos, 0, "capability_welcome_chat_bridge not found in staging server")
        self.assertLess(cont_pos, cap_pos, "continuity bridge must appear BEFORE capability welcome in do_POST")

    def test_continuity_bridge_before_evidence_bridge_in_staging(self):
        with open("deploy/staging/weslr_demo_server.py", "r") as f:
            source = f.read()
        cont_pos = source.find("continuity_note_chat_bridge")
        evid_pos = source.find("evidence_chat_bridge")
        self.assertGreater(cont_pos, 0, "continuity_note_chat_bridge not found in staging server")
        self.assertGreater(evid_pos, 0, "evidence_chat_bridge not found in staging server")
        self.assertLess(cont_pos, evid_pos, "continuity bridge must appear BEFORE evidence bridge in do_POST")


if __name__ == "__main__":
    unittest.main()