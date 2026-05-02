"""
WESLR Workplace Chat Bridge V1 — Tests

Tests:
  - is_workplace_query: detection of trigger/ignore patterns
  - maybe_answer_with_workplace: returns None for non-workplace queries
  - maybe_answer_with_workplace: returns correct shape for workplace queries
  - Generated suggestions section: included when proposals exist
  - Generated suggestions section: omitted when no proposals exist
  - include_generated_suggestions=False suppresses generated section
  - _build_generated_suggestions_section: empty string when none
  - _build_generated_suggestions_section: format when proposals exist
  - Metadata contains generated_suggestions count

Authority: read_only_workplace — no writes, no execution, no external calls.
"""

import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

# ─── Import the module under test ─────────────────────────────────────────────
from weslr.workplace_chat_bridge import (
    is_workplace_query,
    maybe_answer_with_workplace,
    _build_generated_suggestions_section,
)


class TestIsWorkplaceQuery(unittest.TestCase):
    def test_triggers(self):
        triggers = [
            "what are we working on",
            "show my workplace",
            "workplace overview",
            "what ideas are pending",
            "what experiments are pending",
            "pending ideas",
            "pending experiments",
            "what should we continue",
            "/workplace",
            "/ideas",
            "/experiments",
        ]
        for msg in triggers:
            self.assertTrue(is_workplace_query(msg), f"Should match: {msg}")

    def test_ignored(self):
        ignored = [
            "what is entropy",
            "what is weslr",
            "what can you do",
            "do you remember what we worked on",
            "/evidence",
            "/state",
            "continuity",
        ]
        for msg in ignored:
            self.assertFalse(is_workplace_query(msg), f"Should ignore: {msg}")

    def test_case_insensitive(self):
        self.assertTrue(is_workplace_query("WHAT EXPERIMENTS ARE PENDING"))
        self.assertTrue(is_workplace_query("/Workplace"))


class TestMaybeAnswerWithWorkplace(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Create a minimal user timeline so user_timeline_memory doesn't fail
        user_dir = pathlib.Path(self.tmpdir) / "tl_user_arthur"
        user_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_non_workplace_returns_none(self):
        result = maybe_answer_with_workplace(
            "What is the weather?",
            user_id="arthur",
            timeline_base_dir=self.tmpdir,
        )
        self.assertIsNone(result)

    def test_workplace_query_returns_correct_shape(self):
        with patch(
            "weslr.workplace_chat_bridge._build_generated_suggestions_section",
            return_value="",
        ):
            result = maybe_answer_with_workplace(
                "what experiments are pending?",
                user_id="arthur",
                timeline_base_dir=self.tmpdir,
                include_generated_suggestions=False,
            )
        self.assertIsNotNone(result)
        self.assertEqual(result["path"], "workplace_overview")
        self.assertEqual(result["response_contract"], "system_answer")
        self.assertIn("reply", result)
        self.assertIn("_workplace_metadata", result)
        meta = result["_workplace_metadata"]
        self.assertEqual(meta["authority"], "read_only_workplace")
        self.assertFalse(meta["automatic_action"])
        self.assertFalse(meta["hidden_learning"])
        self.assertFalse(meta["raw_prompt_stored"])
        self.assertIn("pending_experiments", meta)
        self.assertIn("recent_ideas", meta)

    def test_generated_suggestions_included_when_proposals_exist(self):
        with patch(
            "weslr.workplace_chat_bridge._build_generated_suggestions_section",
            return_value=(
                "Generated experiment suggestions (based on your recent work)\n"
                "(Not yet approved or queued — review before acting)\n"
                "----------------------------------------------------\n"
                "  • Search for evidence about robotic arm calibration\n"
                "    Look up how similar systems handle calibration.\n"
                "    [confidence: 78%]\n"
            ),
        ):
            result = maybe_answer_with_workplace(
                "what experiments are pending?",
                user_id="arthur",
                timeline_base_dir=self.tmpdir,
                include_generated_suggestions=True,
            )
        self.assertIsNotNone(result)
        self.assertIn("Generated experiment suggestions", result["reply"])
        self.assertIn("Not yet approved or queued", result["reply"])

    def test_generated_suggestions_omitted_when_no_proposals(self):
        with patch(
            "weslr.workplace_chat_bridge._build_generated_suggestions_section",
            return_value="",
        ):
            result = maybe_answer_with_workplace(
                "what experiments are pending?",
                user_id="arthur",
                timeline_base_dir=self.tmpdir,
                include_generated_suggestions=True,
            )
        self.assertIsNotNone(result)
        self.assertNotIn("Generated experiment suggestions", result["reply"])

    def test_include_generated_suggestions_false(self):
        with patch(
            "weslr.workplace_chat_bridge._build_generated_suggestions_section",
            return_value="SHOULD NOT APPEAR",
        ):
            result = maybe_answer_with_workplace(
                "what experiments are pending?",
                user_id="arthur",
                timeline_base_dir=self.tmpdir,
                include_generated_suggestions=False,
            )
        self.assertIsNotNone(result)
        self.assertNotIn("SHOULD NOT APPEAR", result["reply"])

    def test_metadata_generated_suggestions_count(self):
        with patch(
            "weslr.experiment_proposal_generator.generate_experiment_proposals",
            return_value={"generated": [], "total_count": 0, "statuses": {}},
        ):
            result = maybe_answer_with_workplace(
                "what experiments are pending?",
                user_id="arthur",
                timeline_base_dir=self.tmpdir,
                include_generated_suggestions=True,
            )
        self.assertIsNotNone(result)
        self.assertEqual(result["_workplace_metadata"]["generated_suggestions"], 0)


class TestBuildGeneratedSuggestionsSection(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_string_when_no_proposals(self):
        with patch(
            "weslr.experiment_proposal_generator.generate_experiment_proposals",
            return_value={"generated": [], "total_count": 0, "statuses": {}},
        ):
            section = _build_generated_suggestions_section(
                user_id="arthur",
                timeline_base_dir=self.tmpdir,
            )
        self.assertEqual(section, "")

    def test_format_when_proposals_exist(self):
        mock_proposals = [
            {
                "title": "Search for evidence on topic X",
                "description": "A short description of the proposal.",
                "confidence": 0.75,
            },
            {
                "title": "Another proposal",
                "description": "",
                "confidence": 0.60,
            },
        ]
        with patch(
            "weslr.experiment_proposal_generator.generate_experiment_proposals",
            return_value={
                "generated": mock_proposals,
                "total_count": 2,
                "statuses": {"dry_run": 2},
            },
        ):
            section = _build_generated_suggestions_section(
                user_id="arthur",
                timeline_base_dir=self.tmpdir,
                limit=3,
            )
        self.assertIn("Generated experiment suggestions", section)
        self.assertIn("Not yet approved or queued", section)
        self.assertIn("Search for evidence on topic X", section)
        self.assertIn("A short description of the proposal.", section)
        self.assertIn("75%", section)
        self.assertIn("Another proposal", section)
        self.assertIn("60%", section)

    def test_limit_applied(self):
        mock_proposals = [
            {"title": f"Proposal {i}", "description": "", "confidence": 0.7}
            for i in range(5)
        ]
        with patch(
            "weslr.experiment_proposal_generator.generate_experiment_proposals",
            return_value={
                "generated": mock_proposals,
                "total_count": 5,
                "statuses": {},
            },
        ):
            section = _build_generated_suggestions_section(
                user_id="arthur",
                timeline_base_dir=self.tmpdir,
                limit=2,
            )
        self.assertIn("Proposal 0", section)
        self.assertIn("Proposal 1", section)
        self.assertNotIn("Proposal 2", section)

    def test_truncates_long_description(self):
        long_desc = "x" * 200
        mock_proposals = [
            {"title": "Test", "description": long_desc, "confidence": 0.7},
        ]
        with patch(
            "weslr.experiment_proposal_generator.generate_experiment_proposals",
            return_value={"generated": mock_proposals, "total_count": 1, "statuses": {}},
        ):
            section = _build_generated_suggestions_section(
                user_id="arthur",
                timeline_base_dir=self.tmpdir,
            )
        # Description should be truncated to ~120 chars + "..."
        self.assertLess(len(section), 500)


if __name__ == "__main__":
    unittest.main()