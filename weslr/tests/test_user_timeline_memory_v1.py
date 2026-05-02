"""
weslr/tests/test_user_timeline_memory_v1.py
============================================
Tests for user_timeline_memory V1.

Uses temporary directories only — no writes to real .weslr/timelines.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from weslr.user_timeline_memory import (
    MAX_SUMMARY_LENGTH,
    append_session_summary,
    build_continuity_note,
    build_session_summary_event,
    get_user_timeline_path,
    load_recent_session_summaries,
    normalize_user_id,
)


class TestNormalizeUserId(unittest.TestCase):
    def test_lowercase(self):
        self.assertEqual(normalize_user_id("Pr0dUs"), "pr0dus")

    def test_safe_chars_only(self):
        self.assertEqual(normalize_user_id("user@domain.com"), "userdomaincom")
        self.assertEqual(normalize_user_id("user name"), "username")

    def test_collapse_dashes(self):
        self.assertEqual(normalize_user_id("user---name"), "user-name")

    def test_strip_leading_trailing_dashes(self):
        self.assertEqual(normalize_user_id("-user-"), "user")

    def test_empty_defaults_to_default_user(self):
        self.assertEqual(normalize_user_id(""), "default_user")
        self.assertEqual(normalize_user_id(None), "default_user")
        self.assertEqual(normalize_user_id("   "), "default_user")


class TestGetUserTimelinePath(unittest.TestCase):
    def test_path_format(self):
        path = get_user_timeline_path("pr0dus", base_dir=".weslr/timelines")
        expected = Path(".weslr/timelines/user_pr0dus/events.jsonl")
        self.assertEqual(path, expected)

    def test_normalizes_user(self):
        path = get_user_timeline_path("Pr0dUs", base_dir=".weslr/timelines")
        self.assertTrue(str(path).endswith("user_pr0dus/events.jsonl"))


class TestBuildSessionSummaryEvent(unittest.TestCase):
    def test_required_fields_present(self):
        event = build_session_summary_event("pr0dus", "Test summary", source="manual")
        self.assertEqual(event["record_type"], "user_session_summary_event_v1")
        self.assertEqual(event["user_id"], "pr0dus")
        self.assertEqual(event["summary"], "Test summary")
        self.assertEqual(event["source"], "manual")
        self.assertIn("timestamp", event)

    def test_raw_prompt_stored_false(self):
        event = build_session_summary_event("pr0dus", "Test", source="manual")
        self.assertFalse(event["raw_prompt_stored"])

    def test_hidden_learning_false(self):
        event = build_session_summary_event("pr0dus", "Test", source="manual")
        self.assertFalse(event["hidden_learning"])

    def test_automatic_action_false(self):
        event = build_session_summary_event("pr0dus", "Test", source="manual")
        self.assertFalse(event["automatic_action"])

    def test_authority_is_user_timeline_memory(self):
        event = build_session_summary_event("pr0dus", "Test", source="manual")
        self.assertEqual(event["authority"], "user_timeline_memory")

    def test_tags_default_empty_list(self):
        event = build_session_summary_event("pr0dus", "Test", source="manual")
        self.assertEqual(event["tags"], [])

    def test_tags_custom(self):
        event = build_session_summary_event(
            "pr0dus", "Test", source="manual", tags=["python", "weslr"]
        )
        self.assertEqual(event["tags"], ["python", "weslr"])

    def test_valid_sources(self):
        for source in ["manual", "voice", "chat", "operator"]:
            event = build_session_summary_event("pr0dus", "Test", source=source)
            self.assertEqual(event["source"], source)

    def test_invalid_source_raises(self):
        with self.assertRaises(ValueError):
            build_session_summary_event("pr0dus", "Test", source="invalid")

    def test_empty_summary_raises(self):
        with self.assertRaises(ValueError):
            build_session_summary_event("pr0dus", "", source="manual")

    def test_whitespace_only_summary_raises(self):
        # After strip, whitespace becomes empty → catches on `if not summary`
        with self.assertRaises(ValueError) as ctx:
            build_session_summary_event("pr0dus", "   ", source="manual")
        # Must fail on empty check, not on length
        self.assertIn("non-empty", str(ctx.exception))

    def test_summary_length_capped_rejected(self):
        long_summary = "x" * (MAX_SUMMARY_LENGTH + 1)
        with self.assertRaises(ValueError) as ctx:
            build_session_summary_event("pr0dus", long_summary, source="manual")
        self.assertIn(str(MAX_SUMMARY_LENGTH), str(ctx.exception))


class TestAppendSessionSummary(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_append_returns_event_and_path(self):
        result = append_session_summary(
            "testuser", "Test summary", source="manual", base_dir=self.tmpdir
        )
        self.assertIn("event", result)
        self.assertIn("path", result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "appended")

    def test_append_writes_one_jsonl_line(self):
        path = get_user_timeline_path("testuser", base_dir=self.tmpdir)
        append_session_summary("testuser", "Test summary", source="manual", base_dir=self.tmpdir)
        with open(path, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        self.assertEqual(parsed["summary"], "Test summary")

    def test_multiple_appends_increment_file(self):
        path = get_user_timeline_path("testuser", base_dir=self.tmpdir)
        for i in range(3):
            append_session_summary(f"testuser", f"Summary {i}", source="manual", base_dir=self.tmpdir)
        with open(path, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        self.assertEqual(len(lines), 3)


class TestLoadRecentSessionSummaries(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_when_no_file(self):
        result = load_recent_session_summaries("nonexistent", base_dir=self.tmpdir)
        self.assertEqual(result, [])

    def test_returns_latest_events(self):
        # Use append_session_summary to create the parent dir
        for i in range(5):
            append_session_summary("testuser", f"Summary {i}", source="manual", base_dir=self.tmpdir)
        result = load_recent_session_summaries("testuser", limit=3, base_dir=self.tmpdir)
        self.assertEqual(len(result), 3)
        # Most recent first (last appended = Summary 4)
        self.assertEqual(result[0]["summary"], "Summary 4")

    def test_malformed_jsonl_line_ignored(self):
        # Append via append_session_summary, then manually add malformed line
        path = get_user_timeline_path("testuser", base_dir=self.tmpdir)
        append_session_summary("testuser", "Good", source="manual", base_dir=self.tmpdir)
        # Append malformed line
        with open(path, "a") as f:
            f.write("this is not json\n")
        append_session_summary("testuser", "Also good", source="manual", base_dir=self.tmpdir)
        result = load_recent_session_summaries("testuser", limit=5, base_dir=self.tmpdir)
        self.assertEqual(len(result), 2)

    def test_limit_zero_returns_all(self):
        for i in range(3):
            append_session_summary("testuser", f"Summary {i}", source="manual", base_dir=self.tmpdir)
        result = load_recent_session_summaries("testuser", limit=0, base_dir=self.tmpdir)
        self.assertEqual(len(result), 3)


class TestBuildContinuityNote(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_history_safe_message(self):
        result = build_continuity_note("newuser", limit=3, base_dir=self.tmpdir)
        self.assertEqual(result["message"], "I do not have prior timeline notes yet.")
        self.assertEqual(result["events_used"], 0)
        self.assertFalse(result["automatic_action"])
        self.assertFalse(result["hidden_learning"])

    def test_uses_stored_summary(self):
        # Append some events
        append_session_summary("testuser", "Working on Weslr entity graph", source="manual", base_dir=self.tmpdir)
        result = build_continuity_note("testuser", limit=3, base_dir=self.tmpdir)
        self.assertIn("Weslr entity graph", result["message"])
        self.assertEqual(result["events_used"], 1)

    def test_multiple_events_combined(self):
        append_session_summary("testuser", "Phase 1 complete", source="manual", base_dir=self.tmpdir)
        append_session_summary("testuser", "Phase 2 started", source="manual", base_dir=self.tmpdir)
        result = build_continuity_note("testuser", limit=3, base_dir=self.tmpdir)
        self.assertIn("Phase 1 complete", result["message"])
        self.assertIn("Phase 2 started", result["message"])
        self.assertEqual(result["events_used"], 2)


class TestNoExternalCalls(unittest.TestCase):
    def test_no_ollama_import(self):
        import ast
        with open("weslr/user_timeline_memory.py", "r") as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("ollama", alias.name.lower())
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn("ollama", (node.module or "").lower())

    def test_no_http_requests(self):
        with open("weslr/user_timeline_memory.py", "r") as f:
            source = f.read()
        # No requests, urllib, httpx, aiohttp
        for keyword in ["requests.", "urllib", "httpx", "aiohttp"]:
            self.assertNotIn(keyword, source)


if __name__ == "__main__":
    unittest.main()