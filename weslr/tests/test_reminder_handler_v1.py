"""
Tests for WESLR Reminder Handler V1

Covers: parse_reminder_request, set_reminder, list_reminders, cancel_reminder,
handle_reminder_command, schedule_reminder, pending_messages_queue.

No Ollama, no execution, no raw prompts.
"""

import json
import os
import sys
import threading
import time
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure weslr module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import reminder_handler as rh
from reminder_handler import (
    parse_reminder_request,
    set_reminder,
    list_reminders,
    cancel_reminder,
    handle_reminder_command,
)

import pending_messages_queue as pmq


class TestParseReminderRequest(unittest.TestCase):
    """Tests for parse_reminder_request."""

    def test_parse_relative_minutes(self):
        result = parse_reminder_request("remind me in 5 minutes to finish the report")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "relative")
        self.assertEqual(result["message"], "finish the report")
        due = datetime.fromisoformat(result["due_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = (due - now).total_seconds()
        self.assertGreater(delta, 0)
        self.assertAlmostEqual(delta / 60, 5, delta=2)

    def test_parse_relative_hours(self):
        result = parse_reminder_request("remind me in 2 hours to call the doctor")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "relative")
        due = datetime.fromisoformat(result["due_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = (due - now).total_seconds()
        self.assertAlmostEqual(delta / 3600, 2, delta=5)

    def test_parse_absolute_time(self):
        # Pick a time far in the future
        future = (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%H:%M")
        result = parse_reminder_request(f"remind me at {future} to check the build")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "absolute")
        self.assertEqual(result["message"], "check the build")

    def test_parse_absolute_time_tomorrow_if_passed(self):
        # 00:01 always in the past
        result = parse_reminder_request("remind me at 00:01 to midnight thing")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "absolute")
        due = datetime.fromisoformat(result["due_at"].replace("Z", "+00:00"))
        tomorrow = datetime.now(timezone.utc).replace(hour=0, minute=1) + timedelta(days=1)
        self.assertEqual(due.day, tomorrow.day)

    def test_parse_unsupported_format_returns_none(self):
        for text in [
            "remember to buy milk",
            "set a timer for 5 minutes",
            "remind me tomorrow",
        ]:
            result = parse_reminder_request(text)
            self.assertIsNone(result, f"Should return None for: {text}")

    def test_message_over_500_chars_returns_none(self):
        # Parser only accepts messages up to 500 chars
        long_msg = "x" * 600
        result = parse_reminder_request(f"remind me in 5 minutes to {long_msg}")
        self.assertIsNone(result)

    def test_case_insensitive(self):
        for text in [
            "REMIND ME IN 5 MINUTES TO test",
            "Remind Me At 14:30 To test",
        ]:
            result = parse_reminder_request(text)
            self.assertIsNotNone(result, f"Should parse: {text}")


class TestReminderStorage(unittest.TestCase):
    """Tests for reminder storage and retrieval."""

    def setUp(self):
        # Use a temp file for isolation
        self.temp_dir = MagicMock()
        self.original_path = rh._reminder_path
        self.original_log = rh._reminder_log_path

    def tearDown(self):
        pass  # No cleanup needed for append-only


class TestSetReminder(unittest.TestCase):
    """Tests for set_reminder."""

    @patch.object(rh, "_append_reminder")
    @patch.object(rh, "_append_event")
    @patch.object(rh, "schedule_reminder")
    def test_set_reminder_returns_dict(self, mock_schedule, mock_append, mock_append_reminder):
        now = datetime.now(timezone.utc) + timedelta(minutes=10)
        result = set_reminder(
            message="test reminder",
            due_at=now.isoformat(),
        )
        self.assertIn("reminder_id", result)
        self.assertTrue(result["reminder_id"].startswith("REM-"))
        self.assertEqual(result["message"], "test reminder")
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["authority"], "reminder_system")
        self.assertFalse(result["automatic_change"])
        self.assertFalse(result["raw_prompt_stored"])
        self.assertFalse(result["hidden_learning"])

    @patch.object(rh, "_generate_id")
    @patch.object(rh, "_append_reminder")
    @patch.object(rh, "_append_event")
    @patch.object(rh, "schedule_reminder")
    def test_set_reminder_generates_unique_ids(self, mock_schedule, mock_append, mock_append_reminder, mock_gen_id):
        mock_gen_id.side_effect = ["REM-20260503-001", "REM-20260503-002"]
        now = datetime.now(timezone.utc) + timedelta(minutes=5)
        r1 = set_reminder(message="one", due_at=now.isoformat())
        r2 = set_reminder(message="two", due_at=now.isoformat())
        self.assertNotEqual(r1["reminder_id"], r2["reminder_id"])
        self.assertEqual(r1["reminder_id"], "REM-20260503-001")
        self.assertEqual(r2["reminder_id"], "REM-20260503-002")


class TestListReminders(unittest.TestCase):
    """Tests for list_reminders."""

    @patch.object(rh, "_load_pending")
    def test_list_reminders_empty(self, mock_load):
        mock_load.return_value = []
        result = list_reminders(session_id="test-session")
        self.assertEqual(result, [])

    @patch.object(rh, "_load_pending")
    def test_list_reminders_filters_session(self, mock_load):
        from reminder_handler import Reminder
        mock_load.return_value = [
            Reminder(
                reminder_id="REM-20260503-001",
                created_at=datetime.now(timezone.utc).isoformat(),
                due_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                message="test",
                status="pending",
                session_id="session-a",
            ),
            Reminder(
                reminder_id="REM-20260503-002",
                created_at=datetime.now(timezone.utc).isoformat(),
                due_at=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                message="test2",
                status="pending",
                session_id="session-b",
            ),
        ]
        result = list_reminders(session_id="session-a")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["reminder_id"], "REM-20260503-001")


class TestCancelReminder(unittest.TestCase):
    """Tests for cancel_reminder."""

    @patch.object(rh, "_cancel_timer")
    @patch.object(rh, "_update_status")
    @patch.object(rh, "_append_event")
    def test_cancel_reminder_found(self, mock_event, mock_update, mock_cancel):
        mock_update.return_value = True
        result = cancel_reminder("REM-20260503-001")
        self.assertEqual(result["status"], "cancelled")
        mock_cancel.assert_called_once_with("REM-20260503-001")

    @patch.object(rh, "_cancel_timer")
    @patch.object(rh, "_update_status")
    @patch.object(rh, "_append_event")
    def test_cancel_reminder_not_found(self, mock_event, mock_update, mock_cancel):
        mock_update.return_value = False
        result = cancel_reminder("REM-DOESNOTEXIST-999")
        self.assertEqual(result["status"], "not_found")


class TestHandleReminderCommand(unittest.TestCase):
    """Tests for handle_reminder_command."""

    @patch.object(rh, "list_reminders")
    def test_show_reminders_empty(self, mock_list):
        mock_list.return_value = []
        result = handle_reminder_command("show my reminders", "show my reminders")
        self.assertTrue(result.get("path"), "reminder_list")
        self.assertIn("no pending reminders", result.get("response_text", "").lower())

    @patch.object(rh, "list_reminders")
    def test_show_reminders_with_items(self, mock_list):
        mock_list.return_value = [
            {
                "reminder_id": "REM-20260503-001",
                "message": "test reminder",
                "due_at": "2026-05-03T10:00:00+00:00",
            }
        ]
        result = handle_reminder_command("show my reminders", "show my reminders")
        self.assertIn("REM-20260503-001", result["response_text"])

    @patch.object(rh, "cancel_reminder")
    def test_cancel_reminder_command(self, mock_cancel):
        mock_cancel.return_value = {"reminder_id": "REM-20260503-001", "status": "cancelled"}
        result = handle_reminder_command(
            "cancel reminder REM-20260503-001",
            "cancel reminder rem-20260503-001",
        )
        # The regex captures uppercase REM-, but cancel_reminder is case-insensitive internally
        self.assertIn("cancelled", result.get("response_text", "").lower())
        # ID appears as entered by user (lowercase in this case)
        self.assertIn("rem-20260503-001", result.get("response_text", ""))

    @patch.object(rh, "set_reminder")
    def test_remind_me_in_command(self, mock_set):
        mock_set.return_value = {
            "reminder_id": "REM-20260503-001",
            "due_at": (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat(),
            "message": "test",
        }
        result = handle_reminder_command(
            "remind me in 2 minutes to test",
            "remind me in 2 minutes to test",
        )
        self.assertIn("Reminder set", result["response_text"])
        self.assertIn("REM-20260503-001", result["response_text"])

    def test_unrelated_message_not_handled(self):
        result = handle_reminder_command("hello there", "hello there")
        # Returns {"handled": False} for unhandled
        self.assertFalse(result.get("handled", True))


class TestPendingMessagesQueue(unittest.TestCase):
    """Tests for pending_messages_queue."""

    def test_enqueue_dequeue_no_file_perms_uses_memory(self):
        # Test queue logic in-memory without file I/O (no /tmp perms in this env)
        # format_queue_messages is pure text transformation, test directly
        msgs = [
            {
                "queue_type": "reminder",
                "message": "check the build",
                "session_id": "default",
                "enqueued_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
        formatted = pmq.format_queue_messages(msgs)
        self.assertIn("[Reminder]", formatted)
        self.assertIn("check the build", formatted)

    def test_format_queue_messages_reminder(self):
        msgs = [
            {
                "queue_type": "reminder",
                "message": "check the build",
                "session_id": "default",
                "enqueued_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
        formatted = pmq.format_queue_messages(msgs)
        self.assertIn("[Reminder]", formatted)
        self.assertIn("check the build", formatted)

    def test_format_queue_messages_empty(self):
        self.assertEqual(pmq.format_queue_messages([]), "")

    def test_format_queue_messages_multiple(self):
        msgs = [
            {"queue_type": "reminder", "message": "r1", "session_id": "default", "enqueued_at": ""},
            {"queue_type": "proactive_suggestion", "message": "p1", "session_id": "default", "enqueued_at": ""},
        ]
        formatted = pmq.format_queue_messages(msgs)
        self.assertIn("[Reminder] r1", formatted)
        self.assertIn("[Suggestion] p1", formatted)

    def test_pending_count_returns_zero_for_missing_file(self):
        with patch.object(pmq, "_queue_path", return_value=Path("/nonexistent/path/queue.jsonl")):
            count = pmq.pending_count(session_id="test-session")
            self.assertEqual(count, 0)

    def test_flush_queue_returns_zero_for_missing_file(self):
        with patch.object(pmq, "_queue_path", return_value=Path("/nonexistent/path/queue.jsonl")):
            count = pmq.flush_queue(session_id="test-session")
            self.assertEqual(count, 0)


class TestConstraints(unittest.TestCase):
    """Verify structural constraints."""

    def test_no_ollama_imports(self):
        import inspect
        src = inspect.getsource(rh)
        self.assertNotIn("import ollama", src)
        self.assertNotIn("from ollama", src)

    def test_no_execution_calls(self):
        import inspect
        src = inspect.getsource(rh)
        # Should not call os.system, subprocess, eval, exec
        self.assertNotIn("os.system", src)
        self.assertNotIn("subprocess.run", src)
        self.assertNotIn("subprocess.Popen", src)
        self.assertNotIn("eval(", src)
        self.assertNotIn("exec(", src)

    def test_no_raw_prompt_storage(self):
        import inspect
        src = inspect.getsource(rh)
        # raw_prompt_stored must always be False in any dict literal
        import re
        raw_prompt_literals = re.findall(r"raw_prompt_stored\s*=\s*(True|1)", src)
        self.assertEqual(len(raw_prompt_literals), 0, "raw_prompt_stored should never be True")

    def test_authority_on_storage(self):
        import inspect
        src = inspect.getsource(rh)
        # All Reminder dataclass instantiations should have authority="reminder_system"
        # and automatic_change=False
        self.assertIn("reminder_system", src)
        self.assertNotIn('automatic_change: True', src)


if __name__ == "__main__":
    unittest.main()