"""
WESLR Arbiter Context Builder V1 — Unit Tests
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from weslr.arbiter_context_builder import (
    build_arbiter_context,
    _load_pending_experiment_proposals,
    _load_workplace_overview_text,
)


class TestLoadPendingExperimentProposals(unittest.TestCase):
    """Test reading pending experiment proposals from JSONL."""

    def test_missing_file_returns_empty(self):
        result = _load_pending_experiment_proposals(path="/nonexistent/file.jsonl")
        self.assertEqual(result, [])

    def test_filters_non_pending(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(json.dumps({"execution_status": "pending", "title": "A"}) + "\n")
            f.write(json.dumps({"execution_status": "approved", "title": "B"}) + "\n")
            f.write(json.dumps({"execution_status": "pending", "title": "C"}) + "\n")
            temp_path = f.name

        try:
            result = _load_pending_experiment_proposals(path=temp_path)
            self.assertEqual(len(result), 2)
            titles = [r["title"] for r in result]
            self.assertIn("A", titles)
            self.assertIn("C", titles)
            self.assertNotIn("B", titles)
        finally:
            os.unlink(temp_path)

    def test_limit(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            for i in range(20):
                f.write(json.dumps({"execution_status": "pending", "title": f"P{i}"}) + "\n")
            temp_path = f.name

        try:
            result = _load_pending_experiment_proposals(path=temp_path, limit=5)
            self.assertEqual(len(result), 5)
        finally:
            os.unlink(temp_path)

    def test_malformed_lines_skipped(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(json.dumps({"execution_status": "pending", "title": "Good"}) + "\n")
            f.write("not valid json\n")
            f.write(json.dumps({"execution_status": "pending", "title": "AlsoGood"}) + "\n")
            temp_path = f.name

        try:
            result = _load_pending_experiment_proposals(path=temp_path)
            self.assertEqual(len(result), 2)
        finally:
            os.unlink(temp_path)


class TestLoadWorkplaceOverviewText(unittest.TestCase):
    """Test reading workplace overview from a text file."""

    def test_missing_file_returns_none(self):
        result = _load_workplace_overview_text(path="/nonexistent/file.txt")
        self.assertIsNone(result)

    def test_reads_file_content(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("WESLR workplace: 2 ideas, 1 pending experiment.")
            temp_path = f.name

        try:
            result = _load_workplace_overview_text(path=temp_path)
            self.assertEqual(
                result,
                "WESLR workplace: 2 ideas, 1 pending experiment."
            )
        finally:
            os.unlink(temp_path)


class TestBuildArbiterContext(unittest.TestCase):
    """Test the full context builder."""

    def test_returns_all_keys(self):
        ctx = build_arbiter_context(user_id="test_user")
        self.assertIn("user_id", ctx)
        self.assertIn("recent_timeline_events", ctx)
        self.assertIn("workplace_overview", ctx)
        self.assertIn("pending_experiment_proposals", ctx)
        self.assertIn("session_turn_history", ctx)
        self.assertIn("authority", ctx)
        self.assertEqual(ctx["authority"], "read_only_context")
        self.assertFalse(ctx["automatic_action"])

    def test_user_id_passed_through(self):
        ctx = build_arbiter_context(user_id="pr0dus")
        self.assertEqual(ctx["user_id"], "pr0dus")

    def test_session_turn_history_passed_through(self):
        history = [{"turn_kind": "continuity"}, {"turn_kind": "evidence"}]
        ctx = build_arbiter_context(session_turn_history=history)
        self.assertEqual(ctx["session_turn_history"], history)

    @patch(
        "weslr.arbiter_context_builder._load_workplace_overview_text",
        return_value="Test workplace overview",
    )
    @patch(
        "weslr.arbiter_context_builder._load_pending_experiment_proposals",
        return_value=[{"title": "Test proposal"}],
    )
    @patch(
        "weslr.user_timeline_memory.load_recent_session_summaries",
        return_value=[
            {"summary": "worked on Jarvis gap", "timestamp": "2026-05-01T10:00:00Z", "source": "chat", "tags": []}
        ],
    )
    def test_all_sources_integrated(
        self, mock_timeline, mock_proposals, mock_workplace
    ):
        ctx = build_arbiter_context(user_id="arthur")

        self.assertEqual(ctx["workplace_overview"], "Test workplace overview")
        self.assertEqual(len(ctx["pending_experiment_proposals"]), 1)
        self.assertEqual(ctx["pending_experiment_proposals"][0]["title"], "Test proposal")
        self.assertEqual(len(ctx["recent_timeline_events"]), 1)
        self.assertEqual(
            ctx["recent_timeline_events"][0]["summary"],
            "worked on Jarvis gap",
        )


if __name__ == "__main__":
    unittest.main()
