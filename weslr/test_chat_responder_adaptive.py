"""Integration tests for adaptive explanation in chat_responder."""

import unittest

from weslr.chat_responder import compose_reply


class TestChatResponderAdaptive(unittest.TestCase):
    def test_be_shorter_changes_output(self):
        resp = compose_reply(
            messages=[],
            summary="Coverage missing in module A",
            explanation_overrides={"be shorter": True},
            explanation_signals={"confidence": 0.7},
        )
        self.assertIn("Finding:", resp.content)

    def test_be_more_technical_changes_output(self):
        resp = compose_reply(
            messages=[],
            summary="Coverage missing in module A",
            explanation_overrides={"be more technical": True},
            explanation_signals={"confidence": 0.7},
        )
        self.assertIn("signal:", resp.content)

    def test_explain_simply_changes_output(self):
        resp = compose_reply(
            messages=[],
            summary="Coverage missing in module A",
            explanation_overrides={"explain simply": True},
            explanation_signals={"confidence": 0.7},
        )
        self.assertIn("part", resp.content)  # low technicality swaps module->part

    def test_persona_defaults_affect_output(self):
        tech_resp = compose_reply(
            messages=[],
            summary="Coverage missing in module A",
            explanation_signals={"confidence": 0.7},
            persona="technical operator",
            domain="technical",
        )
        teach_resp = compose_reply(
            messages=[],
            summary="Coverage missing in module A",
            explanation_signals={"confidence": 0.7},
            persona="teacher",
            domain="educational",
        )
        self.assertNotEqual(tech_resp.content, teach_resp.content)

    def test_explicit_override_still_wins(self):
        teach_resp = compose_reply(
            messages=[],
            summary="Coverage missing in module A",
            explanation_overrides={"be more technical": True},
            explanation_signals={"confidence": 0.7},
            persona="teacher",
            domain="educational",
        )
        self.assertIn("signal:", teach_resp.content)  # override forces technical wording

    def test_session_preference_persists(self):
        compose_reply(
            messages=[],
            summary="Coverage missing in module A",
            explanation_overrides={"be more direct": True},
            explanation_signals={"confidence": 0.7},
        )
        resp2 = compose_reply(
            messages=[],
            summary="Coverage missing in module A",
            explanation_signals={"confidence": 0.7},
        )
        self.assertIn("Finding:", resp2.content)

    def test_truth_and_governance_preserved(self):
        resp = compose_reply(
            messages=[],
            summary="Coverage missing in module A",
            explanation_signals={"confidence": 0.7},
        )
        self.assertIn("Coverage missing in module A", resp.content)


if __name__ == "__main__":
    unittest.main()
