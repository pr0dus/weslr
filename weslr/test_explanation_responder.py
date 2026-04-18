"""Tests for ExplanationSession integration (Human-Adaptive Explanation v1).
Updated to verify formatting variations.
"""

import unittest
from weslr.explanation_responder import ExplanationSession


class TestExplanationSession(unittest.TestCase):
    def test_override_changes_future_responses(self):
        sess = ExplanationSession()
        sess.apply_user_overrides({"be more technical": True})
        resp1 = sess.render("Coverage missing in module A", signals={"confidence": 0.7})
        resp2 = sess.render("Coverage missing in module A", signals={"confidence": 0.7})
        self.assertIn("signal:", resp2.content)
        self.assertTrue(resp2.metadata["truth_preserved"])

    def test_session_preference_persists(self):
        sess = ExplanationSession()
        sess.apply_user_overrides({"be more direct": True})
        resp = sess.render("Coverage missing in module A")
        resp2 = sess.render("Coverage missing in module A")
        self.assertIn("Finding:", resp2.content)

    def test_conflict_resolution_ambiguity_keeps_uncertainty_plain(self):
        sess = ExplanationSession(persona="engineer")
        sess.apply_user_overrides({"be shorter": True})
        resp = sess.render("Coverage missing in module A", signals={"ambiguity": 0.8, "confidence": 0.6})
        self.assertIn("confidence", resp.content.lower())

    def test_truth_and_governance_preserved(self):
        sess = ExplanationSession()
        resp = sess.render("Coverage missing in module A")
        self.assertIn("Coverage missing in module A", resp.content)
        self.assertFalse(resp.metadata.get("governance_changed"))

    def test_format_variations(self):
        sess = ExplanationSession()
        short_resp = sess.render("Coverage missing in module A", overrides={"be shorter": True}, signals={"confidence": 0.7})
        detail_resp = sess.render("Coverage missing in module A", overrides={"more detail": True}, signals={"confidence": 0.7})
        simple_resp = sess.render("Coverage missing in module A", overrides={"explain simply": True}, signals={"confidence": 0.7})
        self.assertNotEqual(short_resp.content, detail_resp.content)
        self.assertNotEqual(simple_resp.content, detail_resp.content)


if __name__ == "__main__":
    unittest.main()
