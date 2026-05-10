from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DOC_PATH = os.path.join(
    ROOT,
    "docs",
    "WESLR_SHADOW_SIGNAL_RESPONSE_OBLIGATION_WIRING_V1.md",
)


class ShadowSignalResponseObligationWiringDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DOC_PATH, "r", encoding="utf-8") as f:
            cls.doc = f.read()

    def test_document_exists(self):
        self.assertTrue(os.path.exists(DOC_PATH))

    def test_document_contains_current_state(self):
        for phrase in [
            "taxonomy entries exist",
            "shadow meaning labels exist",
            "response_obligation.py does not consume shadow scores",
            "runtime invariance is currently preserved",
        ]:
            self.assertIn(phrase, self.doc)

    def test_document_contains_candidate_obligations(self):
        for phrase in [
            "support_human_context",
            "support_creative_conversation",
            "refuse_manipulative_or_diagnostic_request",
            "clarify_evidence_vs_ideation",
        ]:
            self.assertIn(phrase, self.doc)

    def test_document_contains_boundary_first_routing(self):
        self.assertIn("Boundary-first routing", self.doc)
        self.assertIn("unsafe boundary path wins", self.doc)

    def test_document_contains_all_unsafe_boundaries(self):
        for phrase in [
            "diagnosis request",
            "therapy replacement",
            "hidden personality inference",
            "emotional manipulation",
            "unsafe persuasion",
            "invented evidence",
            "private/internal authority",
        ]:
            self.assertIn(phrase, self.doc)

    def test_document_states_no_runtime_behavior_is_implemented(self):
        self.assertIn("No runtime behavior is implemented by this document.", self.doc)
        self.assertIn("design only", self.doc)

    def test_document_states_response_obligation_not_changed_or_authorized(self):
        self.assertIn("does not authorize edits to `weslr/response_obligation.py` in this step", self.doc)
        self.assertIn("no `weslr/response_obligation.py` changes authorized by this document", self.doc)

    def test_document_references_cognitive_legibility_boundary(self):
        self.assertIn("Cognitive Legibility Boundary", self.doc)

    def test_document_rejects_fake_claims(self):
        for phrase in [
            '"WESLR can diagnose users"',
            '"WESLR can manipulate emotions"',
            '"WESLR has passed official psychology benchmarks"',
        ]:
            self.assertIn(phrase, self.doc)


if __name__ == "__main__":
    unittest.main()
