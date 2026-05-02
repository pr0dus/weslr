"""
WESLR Experiment Proposal Generator V1 — Unit Tests

Tests the experiment_proposal_generator module.
Uses temp files for all JSONL operations.
No Ollama, no external calls, no real timeline files in tests.
"""

import json
import os
import pathlib
import tempfile
import unittest

from weslr.experiment_proposal_generator import (
    build_search_insight_proposal_from_timeline,
    build_self_improvement_proposal,
    generate_experiment_proposals,
    VALID_SI_RULES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_temp_timeline(user_id: str, summaries: list, tmpdir: str) -> str:
    """Create a temp timeline JSONL file for testing."""
    base = pathlib.Path(tmpdir) / ".weslr" / "timelines" / f"user_{user_id}"
    base.mkdir(parents=True, exist_ok=True)
    path = base / "events.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for s in summaries:
            f.write(json.dumps(s) + "\n")
    return str(base.parent.parent)


# ---------------------------------------------------------------------------
# Self-improvement proposal tests
# ---------------------------------------------------------------------------

class TestSelfImprovementProposals(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "proposals.jsonl")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_all_si_rules_valid(self):
        for rule in VALID_SI_RULES:
            result = build_self_improvement_proposal(rule_id=rule, dry_run=True)
            self.assertIsNotNone(result["proposal"])
            self.assertEqual(result["status"], "dry_run")
            self.assertEqual(result["proposal"]["type"], "self_improvement_suggestion")

    def test_si1_proposal_structure(self):
        result = build_self_improvement_proposal(rule_id="SI-1", dry_run=True)
        p = result["proposal"]
        self.assertEqual(p["type"], "self_improvement_suggestion")
        self.assertEqual(p["risk_level"], "low")
        self.assertEqual(p["requires_operator_approval"], True)
        self.assertEqual(p["automatic_execution"], False)
        self.assertEqual(p["hidden_learning"], False)
        self.assertEqual(p["raw_prompt_stored"], False)
        self.assertIn("SI-1", p["params"]["rule_id"])

    def test_si4_proposal_approval_required(self):
        result = build_self_improvement_proposal(rule_id="SI-4", dry_run=True)
        p = result["proposal"]
        self.assertEqual(p["type"], "self_improvement_suggestion")
        self.assertEqual(p["requires_operator_approval"], True)
        self.assertEqual(p["operator_approval_required"], True)

    def test_invalid_rule_returns_error(self):
        result = build_self_improvement_proposal(rule_id="SI-X", dry_run=True)
        self.assertIsNone(result["proposal"])
        self.assertEqual(result["status"], "invalid_rule_id")
        self.assertIn("errors", result)

    def test_self_improvement_writes_when_dry_run_false(self):
        result = build_self_improvement_proposal(
            rule_id="SI-1",
            path=self.tmpfile,
            dry_run=False,
        )
        self.assertEqual(result["status"], "appended")
        self.assertTrue(os.path.exists(self.tmpfile))
        with open(self.tmpfile) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["type"], "self_improvement_suggestion")

    def test_self_improvement_duplicate_skipped(self):
        r1 = build_self_improvement_proposal(rule_id="SI-1", path=self.tmpfile, dry_run=False)
        self.assertEqual(r1["status"], "appended")
        r2 = build_self_improvement_proposal(rule_id="SI-1", path=self.tmpfile, dry_run=False)
        self.assertEqual(r2["status"], "skipped_duplicate")


# ---------------------------------------------------------------------------
# Timeline search insight tests
# ---------------------------------------------------------------------------

class TestSearchInsightFromTimeline(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "proposals.jsonl")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_timeline_returns_no_proposal(self):
        # Use a path with no timeline at all
        result = build_search_insight_proposal_from_timeline(
            user_id="nonexistent_user_xyz",
            base_dir="/nonexistent/path",
            path=self.tmpfile,
            dry_run=True,
        )
        self.assertIsNone(result["proposal"])
        self.assertEqual(result["status"], "no_proposal")

    def test_evidence_theme_generates_proposal(self):
        tmpdir = tempfile.mkdtemp()
        try:
            base = pathlib.Path(tmpdir) / ".weslr" / "timelines" / "user_testuser"
            base.mkdir(parents=True, exist_ok=True)
            path = base / "events.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "record_type": "user_session_summary_event_v1",
                    "summary": "We looked at evidence for the new governance framework.",
                    "timestamp": "2026-05-02T10:00:00Z",
                }) + "\n")

            result = build_search_insight_proposal_from_timeline(
                user_id="testuser",
                base_dir=str(pathlib.Path(tmpdir) / ".weslr" / "timelines"),
                path=self.tmpfile,
                dry_run=True,
            )
            self.assertIsNotNone(result["proposal"])
            self.assertEqual(result["proposal"]["type"], "search_insight")
            self.assertEqual(result["proposal"]["risk_level"], "low")
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_continuity_theme_generates_proposal(self):
        tmpdir = tempfile.mkdtemp()
        try:
            base = pathlib.Path(tmpdir) / ".weslr" / "timelines" / "user_testuser"
            base.mkdir(parents=True, exist_ok=True)
            path = base / "events.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "record_type": "user_session_summary_event_v1",
                    "summary": "We worked on continuity and memory for the agent system.",
                    "timestamp": "2026-05-02T10:00:00Z",
                }) + "\n")

            result = build_search_insight_proposal_from_timeline(
                user_id="testuser",
                base_dir=str(pathlib.Path(tmpdir) / ".weslr" / "timelines"),
                path=self.tmpfile,
                dry_run=True,
            )
            self.assertIsNotNone(result["proposal"])
            self.assertEqual(result["proposal"]["type"], "search_insight")
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_dry_run_does_not_create_jsonl(self):
        tmpdir = tempfile.mkdtemp()
        try:
            base = pathlib.Path(tmpdir) / ".weslr" / "timelines" / "user_testuser"
            base.mkdir(parents=True, exist_ok=True)
            path = base / "events.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "record_type": "user_session_summary_event_v1",
                    "summary": "We tested new evidence search functionality.",
                    "timestamp": "2026-05-02T10:00:00Z",
                }) + "\n")

            result = build_search_insight_proposal_from_timeline(
                user_id="testuser",
                base_dir=str(pathlib.Path(tmpdir) / ".weslr" / "timelines"),
                path=self.tmpfile,
                dry_run=True,
            )
            self.assertFalse(os.path.exists(self.tmpfile))
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_dry_run_false_appends_to_temp(self):
        tmpdir = tempfile.mkdtemp()
        try:
            base = pathlib.Path(tmpdir) / ".weslr" / "timelines" / "user_testuser"
            base.mkdir(parents=True, exist_ok=True)
            path = base / "events.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "record_type": "user_session_summary_event_v1",
                    "summary": "We reviewed capability discovery and planning.",
                    "timestamp": "2026-05-02T10:00:00Z",
                }) + "\n")

            result = build_search_insight_proposal_from_timeline(
                user_id="testuser",
                base_dir=str(pathlib.Path(tmpdir) / ".weslr" / "timelines"),
                path=self.tmpfile,
                dry_run=False,
            )
            self.assertTrue(os.path.exists(self.tmpfile))
            self.assertEqual(result["status"], "appended")
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Generator top-level tests
# ---------------------------------------------------------------------------

class TestGenerateExperimentProposals(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir, "proposals.jsonl")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_returns_dict_with_generated_list(self):
        result = generate_experiment_proposals(
            user_id="nonexistent_xyz",
            dry_run=True,
            path=self.tmpfile,
        )
        self.assertIn("generated", result)
        self.assertIn("total_count", result)
        self.assertIn("statuses", result)
        self.assertIn("dry_run", result)

    def test_generate_never_produces_physical_action(self):
        """V1 generator must not generate physical_action proposals."""
        tmpdir = tempfile.mkdtemp()
        try:
            base = pathlib.Path(tmpdir) / ".weslr" / "timelines" / "user_testuser"
            base.mkdir(parents=True, exist_ok=True)
            path = base / "events.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                for i in range(5):
                    f.write(json.dumps({
                        "record_type": "user_session_summary_event_v1",
                        "summary": f"Test session {i}",
                        "timestamp": f"2026-05-02T{10+i:02d}:00:00Z",
                    }) + "\n")

            result = generate_experiment_proposals(
                user_id="testuser",
                dry_run=True,
                path=self.tmpfile,
            )
            for p in result["generated"]:
                self.assertNotEqual(p["type"], "physical_action")
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Safety tests
# ---------------------------------------------------------------------------

class TestGeneratorSafety(unittest.TestCase):
    def test_no_ollama_imports(self):
        with open("weslr/experiment_proposal_generator.py") as f:
            content = f.read()
        self.assertNotIn("import ollama", content.lower())
        self.assertNotIn("from ollama", content.lower())
        self.assertNotIn("import openai", content.lower())
        self.assertNotIn("import requests", content.lower())
        self.assertNotIn("import urllib", content.lower())

    def test_no_external_calls_in_code(self):
        with open("weslr/experiment_proposal_generator.py") as f:
            content = f.read()
        self.assertNotIn("subprocess", content)
        self.assertNotIn("os.system", content)

    def test_all_proposals_have_safety_flags(self):
        """Every proposal type must have safety flags set correctly."""
        result = build_self_improvement_proposal(rule_id="SI-1", dry_run=True)
        p = result["proposal"]
        self.assertEqual(p["automatic_execution"], False)
        self.assertEqual(p["hidden_learning"], False)
        self.assertEqual(p["raw_prompt_stored"], False)

    def test_no_raw_prompt_storage(self):
        result = build_self_improvement_proposal(rule_id="SI-1", dry_run=True)
        p = result["proposal"]
        self.assertNotIn("raw_prompt", p)
        self.assertNotIn("transcript", p)
        self.assertNotIn("full_conversation", p)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
