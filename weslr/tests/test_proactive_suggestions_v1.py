"""
weslr/tests/test_proactive_suggestions_v1.py
============================================
Tests for proactive_suggestions V1.

Uses temporary directories only — no writes to real .weslr/timelines.
"""

import tempfile
import unittest

from weslr.proactive_suggestions import (
    build_proactive_suggestion,
    build_suggestion_from_theme,
    classify_timeline_theme,
)
from weslr.user_timeline_memory import append_session_summary


class TestClassifyTimelineTheme(unittest.TestCase):
    def _classify(self, text):
        return classify_timeline_theme(text)

    def test_continuity_theme(self):
        result = self._classify("We worked on Jarvis-like memory and continuity experiments")
        self.assertEqual(result["theme"], "continuity")
        self.assertGreater(result["confidence"], 0.0)

    def test_evidence_theme(self):
        result = self._classify("I was doing evidence search and source research today")
        self.assertEqual(result["theme"], "evidence")

    def test_capability_discovery_theme(self):
        result = self._classify("Exploring WESLR capabilities and what commands are available")
        self.assertEqual(result["theme"], "capability_discovery")

    def test_experiment_theme(self):
        result = self._classify("Running tests and validating the new experiment implementation")
        self.assertEqual(result["theme"], "experiment")

    def test_governance_theme(self):
        result = self._classify("Reviewing governance boundaries and operator approval requirements")
        self.assertEqual(result["theme"], "governance")

    def test_unknown_theme(self):
        result = self._classify("Random unrelated session about cooking dinner")
        self.assertEqual(result["theme"], "unknown")

    def test_empty_input(self):
        result = self._classify("")
        self.assertEqual(result["theme"], "unknown")

    def test_none_input(self):
        result = self._classify(None)
        self.assertEqual(result["theme"], "unknown")

    def test_matched_terms_returned(self):
        result = self._classify("we worked on memory and continuity today")
        self.assertIn("memory", result["matched_terms"])
        self.assertIn("continuity", result["matched_terms"])

    def test_confidence_increases_with_hits(self):
        weak = self._classify("memory")
        strong = self._classify("memory continuity recall remember timeline")
        self.assertGreater(strong["confidence"], weak["confidence"])


class TestBuildSuggestionFromTheme(unittest.TestCase):
    def test_continuity_suggestion(self):
        result = build_suggestion_from_theme("continuity")
        self.assertIsNotNone(result)
        self.assertIn("You could", result["suggestion"])
        self.assertIn("continuity", result["suggestion"].lower())

    def test_evidence_suggestion(self):
        result = build_suggestion_from_theme("evidence")
        self.assertIsNotNone(result)
        self.assertIn("source", result["suggestion"].lower())

    def test_capability_discovery_suggestion(self):
        result = build_suggestion_from_theme("capability_discovery")
        self.assertIsNotNone(result)

    def test_experiment_suggestion(self):
        result = build_suggestion_from_theme("experiment")
        self.assertIsNotNone(result)

    def test_governance_approval_required(self):
        result = build_suggestion_from_theme("governance")
        self.assertIsNotNone(result)
        self.assertTrue(result["operator_approval_required"])

    def test_unknown_theme_returns_none(self):
        result = build_suggestion_from_theme("unknown")
        self.assertIsNone(result)

    def test_invalid_theme_returns_none(self):
        result = build_suggestion_from_theme("not_a_theme")
        self.assertIsNone(result)


class TestBuildProactiveSuggestion(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_summaries_returns_suggestion_unavailable(self):
        result = build_proactive_suggestion("brandnew", base_dir=self.tmpdir)
        self.assertFalse(result["suggestion_available"])
        self.assertIsNone(result["suggestion"])

    def test_continuity_summary_creates_continuity_suggestion(self):
        append_session_summary(
            "testuser",
            "We worked on memory and continuity experiments for Jarvis",
            source="manual",
            base_dir=self.tmpdir,
        )
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertTrue(result["suggestion_available"])
        self.assertIn("continuity", result["suggestion"].lower())

    def test_evidence_summary_creates_evidence_suggestion(self):
        append_session_summary(
            "testuser",
            "Researching evidence sources and citation quality for the project",
            source="manual",
            base_dir=self.tmpdir,
        )
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertTrue(result["suggestion_available"])
        self.assertIn("evidence", result["related_capability"])

    def test_capability_summary_creates_capability_suggestion(self):
        append_session_summary(
            "testuser",
            "Exploring WESLR capabilities and command structure",
            source="manual",
            base_dir=self.tmpdir,
        )
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertTrue(result["suggestion_available"])
        self.assertTrue(len(result["suggestion"]) > 10)

    def test_experiment_summary_creates_experiment_suggestion(self):
        append_session_summary(
            "testuser",
            "Running validation tests on the new experiment setup",
            source="manual",
            base_dir=self.tmpdir,
        )
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertTrue(result["suggestion_available"])
        self.assertIn("experiment", result["suggestion"].lower())

    def test_governance_summary_sets_approval_required(self):
        append_session_summary(
            "testuser",
            "Reviewing governance rules and safety boundaries for the system",
            source="manual",
            base_dir=self.tmpdir,
        )
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertTrue(result["suggestion_available"])
        self.assertTrue(result["operator_approval_required"])

    def test_unknown_summary_returns_suggestion_unavailable(self):
        append_session_summary(
            "testuser",
            "Cooking pasta and relaxing",
            source="manual",
            base_dir=self.tmpdir,
        )
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertFalse(result["suggestion_available"])

    def test_suggestion_optional_wording(self):
        append_session_summary(
            "testuser",
            "We worked on memory continuity",
            source="manual",
            base_dir=self.tmpdir,
        )
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        # Must be phrased as optional, not command
        self.assertTrue(
            result["suggestion"].startswith("You could")
            or result["suggestion"].startswith("Would you like")
            or "could" in result["suggestion"].lower()
        )

    def test_metadata_automatic_action_false(self):
        append_session_summary("testuser", "memory experiment", source="manual", base_dir=self.tmpdir)
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertFalse(result["automatic_action"])

    def test_metadata_hidden_learning_false(self):
        append_session_summary("testuser", "memory experiment", source="manual", base_dir=self.tmpdir)
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertFalse(result["hidden_learning"])

    def test_metadata_raw_prompt_stored_false(self):
        append_session_summary("testuser", "memory experiment", source="manual", base_dir=self.tmpdir)
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertFalse(result["raw_prompt_stored"])

    def test_authority_is_suggestion_only(self):
        append_session_summary("testuser", "memory experiment", source="manual", base_dir=self.tmpdir)
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertEqual(result["authority"], "suggestion_only")

    def test_source_is_user_timeline_memory(self):
        append_session_summary("testuser", "memory experiment", source="manual", base_dir=self.tmpdir)
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertEqual(result["source"], "user_timeline_memory")

    def test_record_type_proactive_suggestion_v1(self):
        append_session_summary("testuser", "memory experiment", source="manual", base_dir=self.tmpdir)
        result = build_proactive_suggestion("testuser", base_dir=self.tmpdir)
        self.assertEqual(result["record_type"], "proactive_suggestion_v1")


class TestNoExternalCalls(unittest.TestCase):
    def test_no_ollama_import(self):
        import ast
        with open("weslr/proactive_suggestions.py", "r") as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("ollama", alias.name.lower())
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn("ollama", (node.module or "").lower())

    def test_no_http_requests(self):
        with open("weslr/proactive_suggestions.py", "r") as f:
            source = f.read()
        for keyword in ["requests.", "urllib", "httpx", "aiohttp"]:
            self.assertNotIn(keyword, source)

    def test_no_jsonl_writes(self):
        with open("weslr/proactive_suggestions.py", "r") as f:
            source = f.read()
        # No open() calls that write, no json.dump calls
        # Read-only module — check for write-mode file operations
        for line in source.split("\n"):
            stripped = line.strip()
            self.assertFalse(
                stripped.startswith('open(') and "'w'" in line,
                f"Write-mode open found: {line}"
            )


if __name__ == "__main__":
    unittest.main()