"""
WESLR Arbiter Integration Tests V1

Integration tests for arbiter → /chat pipeline.
Verifies that the hybrid turn arbiter correctly routes messages through the staging server.

Tests run against the arbiter directly (not the HTTP server) to stay unit-testable.
"""

import unittest
from unittest.mock import patch, MagicMock

# Import the modules under test
from weslr.hybrid_turn_arbiter import analyze_turn
from weslr.arbiter_context_builder import build_arbiter_context


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ctx(
    user_id=None,
    recent_timeline_events=None,
    workplace_overview=None,
    session_turn_history=None,
):
    """Build a minimal context dict."""
    c = {}
    if user_id is not None:
        c["user_id"] = user_id
    if recent_timeline_events is not None:
        c["recent_timeline_events"] = recent_timeline_events
    if workplace_overview is not None:
        c["workplace_overview"] = workplace_overview
    if session_turn_history is not None:
        c["session_turn_history"] = session_turn_history
    return c if c else None


# ──────────────────────────────────────────────────────────────────────────────
# Integration tests — arbiter routing decisions
# ──────────────────────────────────────────────────────────────────────────────

class TestArbiterRoutingIntegration(unittest.TestCase):
    """Test that arbiter routes the 6 required cases correctly."""

    # ── 1. Zero-context bare question → clarification ────────────────────

    def test_what_can_we_do_no_context_returns_clarification(self):
        """What can we do? with no prior context → clarification"""
        result = analyze_turn("What can we do?", context=None)
        self.assertEqual(result["selected_layer"], "clarification")
        self.assertEqual(result["ambiguity"], "high")
        self.assertIsNotNone(result["clarification_question"])
        self.assertTrue(
            "haven't worked together" in result["clarification_question"]
            or "not sure" in result["clarification_question"].lower()
        )

    def test_what_can_we_do_no_context_uses_correct_question(self):
        result = analyze_turn("What can we do?", context=None)
        self.assertEqual(
            result["clarification_question"],
            "We haven't worked together before. What would you like to do? "
            "I can explain what WESLR is, help with a project, "
            "search for information, or something else."
        )

    # ── 2. Zero-context with explicit external topic → evidence ──────────

    def test_climate_change_routes_to_evidence(self):
        """What can we do about climate change? → evidence"""
        result = analyze_turn("What can we do about climate change?", context=None)
        self.assertEqual(result["selected_layer"], "evidence")
        self.assertTrue(result["requires_evidence"])
        self.assertEqual(result["ambiguity"], "none")

    # ── 3. Continuity scope → continuity ────────────────────────────────

    def test_last_time_routes_to_continuity(self):
        """What did we work on last time? → continuity"""
        result = analyze_turn("What did we work on last time?", context=None)
        self.assertEqual(result["selected_layer"], "continuity")
        self.assertTrue(result["requires_memory"])

    # ── 4. WESLR self → capability_welcome ────────────────────────────

    def test_what_is_weslr_routes_to_capability_welcome(self):
        """What is WESLR? → capability_welcome"""
        result = analyze_turn("What is WESLR?", context=None)
        self.assertEqual(result["selected_layer"], "capability_welcome")
        self.assertEqual(result["turn_kind"], "system_identity")

    def test_what_can_you_do_routes_to_capability_welcome(self):
        """What can you do? → capability_welcome"""
        result = analyze_turn("What can you do?", context=None)
        self.assertEqual(result["selected_layer"], "capability_welcome")
        self.assertEqual(result["turn_kind"], "capability_help")

    # ── 5. Workplace scope → workplace ─────────────────────────────────

    @patch("weslr.arbiter_context_builder._load_workplace_overview_text")
    @patch("weslr.arbiter_context_builder._load_pending_experiment_proposals")
    @patch("weslr.user_timeline_memory.load_recent_session_summaries")
    def test_what_experiments_pending_with_context_routes_to_workplace(
        self, mock_timeline, mock_proposals, mock_workplace
    ):
        """What experiments are pending? with context → workplace"""
        mock_workplace.return_value = "WESLR workplace: 1 pending experiment."
        mock_proposals.return_value = [{"title": "Test experiment", "execution_status": "pending"}]
        mock_timeline.return_value = []

        ctx = build_arbiter_context(user_id="arthur")
        result = analyze_turn("What experiments are pending?", context=ctx)

        self.assertEqual(result["selected_layer"], "workplace")
        self.assertEqual(result["turn_kind"], "workplace")

    # ── 6. Action candidate ─────────────────────────────────────────────

    def test_should_we_run_robotic_arm_action_candidate(self):
        """Should we run the robotic arm? → action_candidate"""
        result = analyze_turn("Should we run the robotic arm?", context=None)
        self.assertEqual(result["turn_kind"], "action_candidate")
        self.assertTrue(result["requires_action"])
        self.assertFalse(result["automatic_action"])
        self.assertEqual(result["selected_layer"], "capability_welcome")


# ──────────────────────────────────────────────────────────────────────────────
# Context builder integration tests
# ──────────────────────────────────────────────────────────────────────────────

class TestArbiterContextBuilderIntegration(unittest.TestCase):
    """Test that context builder correctly assembles all sources."""

    @patch("weslr.arbiter_context_builder._load_workplace_overview_text")
    @patch("weslr.arbiter_context_builder._load_pending_experiment_proposals")
    @patch("weslr.user_timeline_memory.load_recent_session_summaries")
    def test_context_contains_all_sources(
        self, mock_timeline, mock_proposals, mock_workplace
    ):
        mock_workplace.return_value = "WESLR workplace overview text."
        mock_proposals.return_value = [
            {"proposal_id": "EP-001", "title": "Test proposal", "execution_status": "pending"}
        ]
        mock_timeline.return_value = [
            {"summary": "worked on Jarvis gap", "timestamp": "2026-05-01T10:00:00Z", "source": "chat", "tags": ["jarvis"]}
        ]

        ctx = build_arbiter_context(user_id="arthur")

        self.assertEqual(ctx["user_id"], "arthur")
        self.assertEqual(ctx["workplace_overview"], "WESLR workplace overview text.")
        self.assertEqual(len(ctx["pending_experiment_proposals"]), 1)
        self.assertEqual(ctx["pending_experiment_proposals"][0]["title"], "Test proposal")
        self.assertEqual(len(ctx["recent_timeline_events"]), 1)
        self.assertEqual(ctx["recent_timeline_events"][0]["summary"], "worked on Jarvis gap")
        self.assertFalse(ctx["automatic_action"])
        self.assertEqual(ctx["authority"], "read_only_context")

    def test_context_with_no_sources(self):
        """Context builds even when no sources exist."""
        ctx = build_arbiter_context(user_id="new_user")
        self.assertEqual(ctx["user_id"], "new_user")
        self.assertEqual(ctx["recent_timeline_events"], [])
        self.assertEqual(ctx["pending_experiment_proposals"], [])


# ──────────────────────────────────────────────────────────────────────────────
# Arbiter decision logging tests
# ──────────────────────────────────────────────────────────────────────────────

class TestArbiterDecisionLogging(unittest.TestCase):
    """Test that arbiter decision logging writes correctly."""

    def test_log_entry_shape(self):
        """Verify log entry has all required fields."""
        import time
        import json

        # Simulate a log entry
        analysis = analyze_turn("What is entropy?", context=None)
        log_entry = {
            "timestamp": time.time(),
            "user_id": "arthur",
            "session_id": "test-session",
            "message": "What is entropy?",
            "selected_layer": analysis["selected_layer"],
            "turn_kind": analysis["turn_kind"],
            "target_scope": analysis["target_scope"],
            "requires_evidence": analysis["requires_evidence"],
            "requires_memory": analysis["requires_memory"],
            "requires_action": analysis["requires_action"],
            "confidence": analysis["confidence"],
            "ambiguity": analysis["ambiguity"],
            "candidate_capabilities": analysis["candidate_capabilities"],
            "external_topic": analysis["external_topic"],
            "clarification_question": analysis["clarification_question"],
            "authority": analysis["authority"],
            "automatic_action": analysis["automatic_action"],
        }

        # Verify it's valid JSON
        encoded = json.dumps(log_entry, ensure_ascii=False)
        decoded = json.loads(encoded)

        self.assertEqual(decoded["selected_layer"], "evidence")
        self.assertTrue(decoded["requires_evidence"])
        self.assertFalse(decoded["automatic_action"])
        self.assertEqual(decoded["authority"], "routing_analysis_only")

    def test_no_automatic_action_on_any_path(self):
        """Sanity: automatic_action must always be False on all paths."""
        messages = [
            "What can we do?",
            "What can we do about climate change?",
            "What can you do?",
            "What is WESLR?",
            "What is entropy?",
            "What did we work on last time?",
            "Should we run the robotic arm?",
            "What?",
        ]
        for msg in messages:
            result = analyze_turn(msg, context=None)
            self.assertFalse(
                result["automatic_action"],
                f"automatic_action=True for message: {msg}"
            )


# ──────────────────────────────────────────────────────────────────────────────
# Backward compatibility tests
# ──────────────────────────────────────────────────────────────────────────────

class TestBackwardCompatibility(unittest.TestCase):
    """Test that existing bridges still return correct shapes when called directly."""

    def test_continuity_bridge_returns_correct_shape(self):
        from weslr.continuity_note_chat_bridge import maybe_answer_with_continuity_note
        result = maybe_answer_with_continuity_note("What did we work on last time?")
        # Returns None when no actual timeline data exists (which is fine for unit test)
        # But should not raise
        self.assertIsInstance(result, (dict, type(None)))

    def test_capability_welcome_bridge_returns_correct_shape(self):
        from weslr.capability_welcome_chat_bridge import maybe_answer_with_capability_welcome
        result = maybe_answer_with_capability_welcome("What can you do?")
        self.assertIsInstance(result, (dict, type(None)))

    def test_workplace_bridge_returns_correct_shape(self):
        from weslr.workplace_chat_bridge import maybe_answer_with_workplace
        result = maybe_answer_with_workplace("What are we working on?")
        self.assertIsInstance(result, (dict, type(None)))


if __name__ == "__main__":
    unittest.main()
