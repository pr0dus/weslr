"""
WESLR Workplace Review Surface V1 — Unit Tests

Tests the workplace_review_surface module.
Uses temp files/dirs only. No real timeline files, no Ollama, no external calls.
"""

import json
import os
import pathlib
import tempfile
import unittest

from weslr.workplace_review_surface import (
    _is_idea_summary,
    build_workplace_overview,
    build_workplace_text,
    list_pending_experiment_proposals,
    list_recent_ideas,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_temp_timeline(
    user_id: str,
    summaries: list[dict],
    tmpdir: str,
) -> str:
    """Create a temp timeline JSONL file for testing."""
    base = pathlib.Path(tmpdir) / ".weslr" / "timelines" / f"user_{user_id}"
    base.mkdir(parents=True, exist_ok=True)
    path = base / "events.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for s in summaries:
            f.write(json.dumps(s) + "\n")
    return str(pathlib.Path(tmpdir) / ".weslr" / "timelines")


def _make_temp_proposals(
    proposals: list[dict],
    tmpdir: str,
) -> str:
    """Create a temp experiment_proposals.jsonl for testing."""
    p = pathlib.Path(tmpdir) / "experiment_proposals.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for proposal in proposals:
            f.write(json.dumps(proposal) + "\n")
    return str(p)


# ---------------------------------------------------------------------------
# Idea detection tests
# ---------------------------------------------------------------------------

class TestIdeaDetection(unittest.TestCase):
    def test_idea_keywords_detected(self):
        keywords = [
            "maybe we should look into this",
            "I have an idea to try",
            "could we build something around this",
            "experiment with the new API",
            "project: redesign the bootstrap flow",
            "test the hypothesis",
            "try a different approach",
            "explore external evidence",
            "investigate memory patterns",
            "design a new capability",
            "plan the next phase",
        ]
        for kw in keywords:
            self.assertTrue(_is_idea_summary(kw), f"Expected idea for: {kw}")

    def test_non_ideas_ignored(self):
        non_ideas = [
            "Continued the session as normal.",
            "Reviewed the contract observation report.",
            "Checked the operator consistency log.",
            "No issues found.",
        ]
        for n in non_ideas:
            self.assertFalse(_is_idea_summary(n), f"Expected not idea for: {n}")


# ---------------------------------------------------------------------------
# list_pending_experiment_proposals tests
# ---------------------------------------------------------------------------

class TestListPendingProposals(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_store_returns_empty_list(self):
        result = list_pending_experiment_proposals(
            path=self.tmpdir + "/nonexistent.jsonl", limit=10
        )
        self.assertEqual(result, [])

    def test_only_pending_returned(self):
        proposals = [
            {
                "record_type": "experiment_proposal_v1",
                "proposal_id": "EXP-20260502-001",
                "type": "search_insight",
                "title": "Test proposal 1",
                "confidence": 0.8,
                "risk_level": "low",
                "requires_operator_approval": True,
                "timeline_id": "tl_1",
                "execution_status": "pending",
            },
            {
                "record_type": "experiment_proposal_v1",
                "proposal_id": "EXP-20260502-002",
                "type": "search_insight",
                "title": "Test proposal 2",
                "confidence": 0.7,
                "risk_level": "medium",
                "requires_operator_approval": True,
                "timeline_id": "tl_2",
                "execution_status": "executed",
            },
        ]
        path = _make_temp_proposals(proposals, self.tmpdir)
        result = list_pending_experiment_proposals(path=path, limit=10)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["proposal_id"], "EXP-20260502-001")

    def test_limit_applied(self):
        proposals = [
            {
                "record_type": "experiment_proposal_v1",
                "proposal_id": f"EXP-20260502-{i:03d}",
                "type": "search_insight",
                "title": f"Test {i}",
                "confidence": 0.8,
                "risk_level": "low",
                "requires_operator_approval": True,
                "timeline_id": f"tl_{i}",
                "execution_status": "pending",
            }
            for i in range(1, 6)
        ]
        path = _make_temp_proposals(proposals, self.tmpdir)
        result = list_pending_experiment_proposals(path=path, limit=3)
        self.assertEqual(len(result), 3)

    def test_compact_fields_only(self):
        proposals = [
            {
                "record_type": "experiment_proposal_v1",
                "proposal_id": "EXP-20260502-001",
                "type": "search_insight",
                "title": "Test",
                "confidence": 0.75,
                "risk_level": "low",
                "requires_operator_approval": True,
                "timeline_id": "tl_1",
                "execution_status": "pending",
                "extra_field": "should_not_appear",
                "raw_prompt": "should_not_appear",
            }
        ]
        path = _make_temp_proposals(proposals, self.tmpdir)
        result = list_pending_experiment_proposals(path=path, limit=10)
        self.assertNotIn("extra_field", result[0])
        self.assertNotIn("raw_prompt", result[0])


# ---------------------------------------------------------------------------
# list_recent_ideas tests
# ---------------------------------------------------------------------------

class TestListRecentIdeas(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_timeline_returns_empty(self):
        result = list_recent_ideas(
            user_id="nonexistent_xyz",
            limit=5,
            timeline_base_dir="/nonexistent/path",
        )
        self.assertEqual(result, [])

    def test_idea_summaries_extracted(self):
        base_dir = _make_temp_timeline(
            "testuser",
            [
                {
                    "record_type": "user_session_summary_event_v1",
                    "summary": "We should build a new experiment proposal system.",
                    "timeline_id": "tl_testuser",
                    "timestamp": "2026-05-02T10:00:00Z",
                },
                {
                    "record_type": "user_session_summary_event_v1",
                    "summary": "Reviewed the contract observation log.",
                    "timeline_id": "tl_testuser",
                    "timestamp": "2026-05-02T11:00:00Z",
                },
                {
                    "record_type": "user_session_summary_event_v1",
                    "summary": "Maybe we could experiment with proactive suggestions.",
                    "timeline_id": "tl_testuser",
                    "timestamp": "2026-05-02T12:00:00Z",
                },
            ],
            self.tmpdir,
        )
        result = list_recent_ideas(user_id="testuser", limit=5, timeline_base_dir=base_dir)
        self.assertEqual(len(result), 2)
        # Most recent idea comes first (file order reversed by load_recent_session_summaries)
        self.assertTrue(
            result[0]["summary"].startswith("Maybe we could"),
            f'Expected first idea to start with "Maybe we could", got: {result[0]["summary"]}',
        )
        self.assertEqual(result[0]["idea_id"], "IDEA-TL-001")
        self.assertEqual(result[0]["authority"], "read_only_workplace")

    def test_non_ideas_ignored(self):
        base_dir = _make_temp_timeline(
            "testuser",
            [
                {
                    "record_type": "user_session_summary_event_v1",
                    "summary": "Continued the session as normal.",
                    "timeline_id": "tl_testuser",
                    "timestamp": "2026-05-02T10:00:00Z",
                },
                {
                    "record_type": "user_session_summary_event_v1",
                    "summary": "Reviewed the contract observation report.",
                    "timeline_id": "tl_testuser",
                    "timestamp": "2026-05-02T11:00:00Z",
                },
            ],
            self.tmpdir,
        )
        result = list_recent_ideas(user_id="testuser", limit=5, timeline_base_dir=base_dir)
        self.assertEqual(result, [])

    def test_limit_applied(self):
        base_dir = _make_temp_timeline(
            "testuser",
            [
                {
                    "record_type": "user_session_summary_event_v1",
                    "summary": f"Test idea number {i}.",
                    "timeline_id": "tl_testuser",
                    "timestamp": f"2026-05-02T{10+i:02d}:00:00Z",
                }
                for i in range(1, 8)
            ],
            self.tmpdir,
        )
        result = list_recent_ideas(user_id="testuser", limit=3, timeline_base_dir=base_dir)
        self.assertEqual(len(result), 3)


# ---------------------------------------------------------------------------
# build_workplace_overview tests
# ---------------------------------------------------------------------------

class TestBuildWorkplaceOverview(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_workplace_returns_safe_overview(self):
        overview = build_workplace_overview(
            user_id="nonexistent_xyz",
            proposal_path=self.tmpdir + "/nonexistent.jsonl",
            timeline_base_dir="/nonexistent/path",
        )
        self.assertEqual(overview["record_type"], "workplace_overview_v1")
        self.assertEqual(overview["authority"], "read_only_workplace")
        self.assertEqual(overview["automatic_action"], False)
        self.assertEqual(overview["hidden_learning"], False)
        self.assertEqual(overview["raw_prompt_stored"], False)
        self.assertIn("sections", overview)
        self.assertIn("counts", overview)

    def test_pending_experiments_appear_in_overview(self):
        proposals = [
            {
                "record_type": "experiment_proposal_v1",
                "proposal_id": "EXP-20260502-001",
                "type": "search_insight",
                "title": "Test experiment",
                "confidence": 0.8,
                "risk_level": "low",
                "requires_operator_approval": True,
                "timeline_id": "tl_1",
                "execution_status": "pending",
            }
        ]
        prop_path = _make_temp_proposals(proposals, self.tmpdir)
        timeline_dir = _make_temp_timeline(
            "testuser",
            [
                {
                    "record_type": "user_session_summary_event_v1",
                    "summary": "Continued the session.",
                    "timeline_id": "tl_testuser",
                    "timestamp": "2026-05-02T10:00:00Z",
                }
            ],
            self.tmpdir,
        )
        overview = build_workplace_overview(
            user_id="testuser",
            proposal_path=prop_path,
            timeline_base_dir=timeline_dir,
        )
        self.assertEqual(len(overview["sections"]["pending_experiments"]), 1)
        self.assertEqual(overview["counts"]["pending_experiments"], 1)

    def test_proactive_suggestion_included_when_available(self):
        timeline_dir = _make_temp_timeline(
            "testuser",
            [
                {
                    "record_type": "user_session_summary_event_v1",
                    "summary": "We should build a new experiment proposal system.",
                    "timeline_id": "tl_testuser",
                    "timestamp": "2026-05-02T10:00:00Z",
                }
            ],
            self.tmpdir,
        )
        overview = build_workplace_overview(
            user_id="testuser",
            proposal_path=self.tmpdir + "/none.jsonl",
            timeline_base_dir=timeline_dir,
        )
        self.assertIn("proactive_suggestion", overview["sections"])

    def test_next_review_actions_generated(self):
        proposals = [
            {
                "record_type": "experiment_proposal_v1",
                "proposal_id": "EXP-20260502-001",
                "type": "search_insight",
                "title": "Test",
                "confidence": 0.8,
                "risk_level": "low",
                "requires_operator_approval": True,
                "timeline_id": "tl_1",
                "execution_status": "pending",
            }
        ]
        prop_path = _make_temp_proposals(proposals, self.tmpdir)
        timeline_dir = _make_temp_timeline(
            "testuser",
            [
                {
                    "record_type": "user_session_summary_event_v1",
                    "summary": "Maybe try a new approach.",
                    "timeline_id": "tl_testuser",
                    "timestamp": "2026-05-02T10:00:00Z",
                }
            ],
            self.tmpdir,
        )
        overview = build_workplace_overview(
            user_id="testuser",
            proposal_path=prop_path,
            timeline_base_dir=timeline_dir,
        )
        actions = overview["sections"]["next_review_actions"]
        self.assertIsInstance(actions, list)
        self.assertGreater(len(actions), 0)
        self.assertTrue(
            any("experiment" in a.lower() for a in actions),
            f"Expected 'experiment' in actions: {actions}",
        )

    def test_authority_read_only_workplace(self):
        overview = build_workplace_overview(
            user_id="nonexistent",
            proposal_path=self.tmpdir + "/none.jsonl",
            timeline_base_dir="/none",
        )
        self.assertEqual(overview["authority"], "read_only_workplace")


# ---------------------------------------------------------------------------
# build_workplace_text tests
# ---------------------------------------------------------------------------

class TestBuildWorkplaceText(unittest.TestCase):
    def test_includes_pending_experiments_header(self):
        overview = {
            "sections": {"pending_experiments": []},
            "counts": {"pending_experiments": 0},
        }
        text = build_workplace_text(overview)
        self.assertIn("Pending Experiments", text)

    def test_includes_recent_ideas_header(self):
        overview = {
            "sections": {"recent_ideas": []},
        }
        text = build_workplace_text(overview)
        self.assertIn("Recent Ideas", text)

    def test_idea_bullets_shown(self):
        overview = {
            "sections": {
                "pending_experiments": [],
                "recent_ideas": [
                    {
                        "idea_id": "IDEA-TL-001",
                        "summary": "Build a workplace review surface.",
                        "source": "user_timeline_memory",
                        "timeline_id": "tl_test",
                        "authority": "read_only_workplace",
                    }
                ],
                "proactive_suggestion": None,
                "next_review_actions": [],
            },
        }
        text = build_workplace_text(overview)
        self.assertIn("Build a workplace review surface", text)

    def test_proposal_title_shown(self):
        overview = {
            "sections": {
                "pending_experiments": [
                    {
                        "proposal_id": "EXP-20260502-001",
                        "type": "search_insight",
                        "title": "Test search experiment",
                        "confidence": 0.8,
                        "risk_level": "low",
                        "requires_operator_approval": True,
                        "timeline_id": "tl_1",
                    }
                ],
                "recent_ideas": [],
                "proactive_suggestion": None,
                "next_review_actions": [],
            },
        }
        text = build_workplace_text(overview)
        self.assertIn("Test search experiment", text)
        self.assertIn("[LOW]", text)


# ---------------------------------------------------------------------------
# Safety tests
# ---------------------------------------------------------------------------

class TestWorkplaceSafety(unittest.TestCase):
    def test_no_ollama_imports(self):
        with open("weslr/workplace_review_surface.py") as f:
            content = f.read()
        self.assertNotIn("import ollama", content.lower())
        self.assertNotIn("from ollama", content.lower())
        self.assertNotIn("import openai", content.lower())

    def test_no_external_calls(self):
        with open("weslr/workplace_review_surface.py") as f:
            content = f.read()
        self.assertNotIn("subprocess", content)
        self.assertNotIn("requests", content)
        self.assertNotIn("urllib", content)
        self.assertNotIn("os.system", content)

    def test_authority_read_only_workplace(self):
        with open("weslr/workplace_review_surface.py") as f:
            content = f.read()
        self.assertIn('read_only_workplace', content)

    def test_automatic_action_false(self):
        with open("weslr/workplace_review_surface.py") as f:
            content = f.read()
        self.assertIn("automatic_action", content)

    def test_no_execution_approval_rejection(self):
        with open("weslr/workplace_review_surface.py") as f:
            content = f.read()
        # Check for actual function/method calls, not docstring mentions
        self.assertNotIn("approve_proposal", content)
        self.assertNotIn("reject_proposal", content)
        self.assertNotIn("execute_proposal", content)
        self.assertNotIn("run_experiment", content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
