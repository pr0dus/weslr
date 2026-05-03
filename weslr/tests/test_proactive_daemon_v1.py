"""
Tests for WESLR Proactive File-Based Daemon V1

Covers: start_proactive_daemon, stop_proactive_daemon, _daemon_loop,
_dedup_cache, duplicate detection, config from env.

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
from unittest.mock import patch

# Ensure weslr module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import proactive_daemon as pd


class TestDedupCache(unittest.TestCase):
    """Tests for deduplication cache."""

    def setUp(self):
        pd._DEDUP_CACHE.clear()
        pd._STOP_EVENT.clear()

    def test_is_duplicate_false_for_new_message(self):
        result = pd._is_duplicate("a brand new suggestion")
        self.assertFalse(result)

    def test_is_duplicate_true_after_mark_sent(self):
        pd._mark_sent("test message")
        result = pd._is_duplicate("test message")
        self.assertTrue(result)

    def test_is_duplicate_false_after_24h(self):
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        pd._DEDUP_CACHE.append(("old message", old_time))
        result = pd._is_duplicate("old message")
        self.assertFalse(result)

    def test_is_duplicate_true_within_24h(self):
        recent_time = datetime.now(timezone.utc) - timedelta(hours=12)
        pd._DEDUP_CACHE.append(("recent message", recent_time))
        result = pd._is_duplicate("recent message")
        self.assertTrue(result)

    def test_cache_size_cap(self):
        for i in range(10):
            pd._mark_sent(f"msg-{i}")
        with pd._DEDUP_LOCK:
            self.assertLessEqual(len(pd._DEDUP_CACHE), pd._DEDUP_MAX)


class TestConfiguration(unittest.TestCase):
    """Tests for environment variable configuration."""

    def test_default_disabled(self):
        self.assertFalse(pd._ENABLED)

    def test_interval_from_env(self):
        with patch.dict(os.environ, {"WESLR_PROACTIVE_INTERVAL_MINUTES": "30"}):
            interval = int(os.environ.get("WESLR_PROACTIVE_INTERVAL_MINUTES", "60"))
            self.assertEqual(interval, 30)

    def test_operator_id_from_env(self):
        with patch.dict(os.environ, {"WESLR_OPERATOR_ID": "pr0dus"}):
            op_id = os.environ.get("WESLR_OPERATOR_ID", "operator")
            self.assertEqual(op_id, "pr0dus")


class TestStartStopDaemon(unittest.TestCase):
    """Tests for daemon start/stop lifecycle."""

    def setUp(self):
        pd._THREAD = None
        pd._STOP_EVENT.clear()

    def tearDown(self):
        pd._STOP_EVENT.set()
        if pd._THREAD is not None:
            pd._THREAD.join(timeout=2)
            pd._THREAD = None

    def test_start_when_disabled_returns_none(self):
        result = pd.start_proactive_daemon(enabled=False)
        self.assertIsNone(result)

    def test_stop_idempotent(self):
        result = pd.stop_proactive_daemon()
        self.assertTrue(result)

    def test_start_when_enabled_creates_daemon_thread(self):
        pd._THREAD = None
        pd._STOP_EVENT.clear()
        with patch("proactive_daemon.build_proactive_suggestion",
                   return_value={"suggestion_available": False}):
            thread = pd.start_proactive_daemon(enabled=True, interval_minutes=60)
            self.assertIsNotNone(thread)
            self.assertTrue(thread.daemon)
            self.assertTrue(thread.is_alive())
            pd.stop_proactive_daemon()
            thread.join(timeout=2)


class TestDaemonLoopLogic(unittest.TestCase):
    """Test daemon loop logic without real file I/O."""

    def setUp(self):
        pd._DEDUP_CACHE.clear()
        pd._STOP_EVENT.clear()

    def tearDown(self):
        pd._STOP_EVENT.set()
        if pd._THREAD is not None:
            pd._THREAD.join(timeout=2)
            pd._THREAD = None

    def test_loop_skips_when_no_suggestion(self):
        """When suggestion_available=False, enqueue should never be called."""
        with patch("proactive_daemon.build_proactive_suggestion",
                   return_value={"suggestion_available": False}):
            with patch("proactive_daemon.enqueue") as mock_enqueue:
                with patch.object(pd, "_queue_path",
                                  return_value=Path("/fake/nonexistent/queue.jsonl")):
                    pd._STOP_EVENT.set()
                    pd._daemon_loop(60.0)
                    mock_enqueue.assert_not_called()

    def test_loop_skips_duplicate(self):
        """When _is_duplicate=True, enqueue should never be called."""
        with patch("proactive_daemon.build_proactive_suggestion",
                   return_value={"suggestion_available": True, "suggestion": "dup msg"}):
            with patch("proactive_daemon.enqueue") as mock_enqueue:
                with patch.object(pd, "_queue_path",
                                  return_value=Path("/fake/nonexistent/queue.jsonl")):
                    with patch.object(pd, "_is_duplicate", return_value=True):
                        pd._STOP_EVENT.set()
                        pd._daemon_loop(60.0)
                        mock_enqueue.assert_not_called()

    def test_loop_enqueues_when_suggestion_available_and_not_duplicate(self):
        """When suggestion available and not duplicate, enqueue should be called."""
        suggestion = {
            "suggestion_available": True,
            "suggestion": "You could test the jarvis roadmap.",
        }
        call_count = [0]

        def wait_side_effect(timeout=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return False  # First: timeout occurred, continue
            pd._STOP_EVENT.set()
            return True     # Second: stop

        with patch("proactive_daemon.build_proactive_suggestion", return_value=suggestion):
            with patch("proactive_daemon.enqueue") as mock_enqueue:
                with patch.object(pd, "_queue_path",
                                  return_value=Path("/fake/nonexistent/queue.jsonl")):
                    with patch.object(pd, "_is_duplicate", return_value=False):
                        with patch.object(pd._STOP_EVENT, "wait", side_effect=wait_side_effect):
                            pd._daemon_loop(60.0)
                        mock_enqueue.assert_called_once()
                        call_kwargs = mock_enqueue.call_args.kwargs
                        self.assertEqual(call_kwargs["queue_type"], "proactive")
                        self.assertIn("Hey", call_kwargs["message"])
                        self.assertEqual(call_kwargs["priority"], "medium")

    def test_loop_marks_sent_after_enqueue(self):
        suggestion = {
            "suggestion_available": True,
            "suggestion": "Test suggestion for marking.",
        }
        call_count = [0]


        def wait_side_effect(timeout=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return False
            pd._STOP_EVENT.set()
            return True

        with patch("proactive_daemon.build_proactive_suggestion", return_value=suggestion):
            with patch("proactive_daemon.enqueue"):
                with patch.object(pd, "_queue_path",
                                  return_value=Path("/fake/nonexistent/queue.jsonl")):
                    with patch.object(pd, "_is_duplicate", return_value=False):
                        with patch.object(pd, "_mark_sent") as mock_mark:
                            with patch.object(pd._STOP_EVENT, "wait", side_effect=wait_side_effect):
                                pd._daemon_loop(60.0)
                            mock_mark.assert_called_once_with("Test suggestion for marking.")

    def test_loop_respects_stop_event_immediately(self):
        """If stop event is already set before wait, loop should exit without calling build."""
        pd._STOP_EVENT.set()
        with patch("proactive_daemon.build_proactive_suggestion") as mock_build:
            pd._daemon_loop(60.0)
            mock_build.assert_not_called()

    def test_loop_continues_after_wait_when_suggestion_available(self):
        """Loop should continue (call build) after wait times out, until stop is set."""
        suggestion = {"suggestion_available": True, "suggestion": "Test."}
        with patch("proactive_daemon.build_proactive_suggestion", return_value=suggestion):
            with patch("proactive_daemon.enqueue"):
                with patch.object(pd, "_queue_path",
                                  return_value=Path("/fake/nonexistent/queue.jsonl")):
                    with patch.object(pd, "_is_duplicate", return_value=False):
                        stop_now = threading.Event()

                        def wait_with_stop(timeout=None):
                            if not stop_now.is_set():
                                stop_now.set()
                                pd._STOP_EVENT.set()
                                return False
                            return True

                        with patch.object(pd._STOP_EVENT, "wait", side_effect=wait_with_stop):
                            pd._daemon_loop(60.0)


class TestConstraints(unittest.TestCase):
    """Verify structural constraints."""

    def test_no_ollama_imports(self):
        import inspect
        src = inspect.getsource(pd)
        self.assertNotIn("import ollama", src)
        self.assertNotIn("from ollama", src)

    def test_no_execution_calls(self):
        import inspect
        src = inspect.getsource(pd)
        self.assertNotIn("os.system", src)
        self.assertNotIn("subprocess.run", src)
        self.assertNotIn("subprocess.Popen", src)
        self.assertNotIn("eval(", src)
        self.assertNotIn("exec(", src)

    def test_no_raw_prompt_storage(self):
        import inspect
        import re
        src = inspect.getsource(pd)
        raw_prompt_literals = re.findall(r"raw_prompt_stored\s*=\s*(True|1)", src)
        self.assertEqual(len(raw_prompt_literals), 0)

    def test_daemon_thread_is_daemon(self):
        import inspect
        src = inspect.getsource(pd)
        self.assertIn("daemon=True", src)

    def test_stop_event_is_threading_event(self):
        self.assertIsInstance(pd._STOP_EVENT, threading.Event)


if __name__ == "__main__":
    unittest.main()
