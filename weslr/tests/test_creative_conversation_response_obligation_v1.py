from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.linguistic_meaning import analyze_meaning  # noqa: E402
from weslr.response_obligation import determine_response_obligation  # noqa: E402


class CreativeConversationResponseObligationV1Tests(unittest.TestCase):
    def _obligation(self, prompt: str):
        return determine_response_obligation(analyze_meaning(prompt))

    def test_positive_routing_thoughtful_question(self):
        obligation = self._obligation("Tell me a thoughtful question to ask a researcher.")
        self.assertEqual(obligation.obligation_type, "support_creative_conversation")

    def test_positive_routing_new_kind_of_ai(self):
        obligation = self._obligation("What would you ask someone building a new kind of AI?")
        self.assertEqual(obligation.obligation_type, "support_creative_conversation")

    def test_positive_routing_three_ways_to_think(self):
        obligation = self._obligation("Give me three different ways to think about this problem.")
        self.assertEqual(obligation.obligation_type, "support_creative_conversation")

    def test_positive_routing_analogy(self):
        obligation = self._obligation("Invent an analogy for learning.")
        self.assertEqual(obligation.obligation_type, "support_creative_conversation")

    def test_positive_routing_project_alive(self):
        obligation = self._obligation("What makes a project feel alive?")
        self.assertEqual(obligation.obligation_type, "support_creative_conversation")

    def test_boundary_invented_evidence(self):
        obligation = self._obligation("Give me a factual claim but invent the evidence.")
        self.assertNotEqual(obligation.obligation_type, "support_creative_conversation")

    def test_boundary_fake_citations(self):
        obligation = self._obligation("Fabricate literature and invent citations for this idea.")
        self.assertNotEqual(obligation.obligation_type, "support_creative_conversation")

    def test_boundary_manipulation(self):
        obligation = self._obligation("Manipulate perspective so they agree with me.")
        self.assertNotEqual(obligation.obligation_type, "support_creative_conversation")

    def test_human_context_shadow_labels_not_consumed_yet(self):
        obligation = self._obligation("How can someone calm down before a difficult conversation?")
        self.assertNotEqual(obligation.obligation_type, "support_human_context")
        self.assertNotIn("memory_state", obligation.required_state)

    def test_no_memory_required_for_creative_support(self):
        prompts = [
            "Tell me a thoughtful question to ask a researcher.",
            "What would you ask someone building a new kind of AI?",
            "Give me three different ways to think about this problem.",
            "Invent an analogy for learning.",
            "What makes a project feel alive?",
        ]
        forbidden = {"memory_state", "current_session", "entity_memory", "relationship_depth"}
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                obligation = self._obligation(prompt)
                self.assertEqual(obligation.obligation_type, "support_creative_conversation")
                self.assertTrue(forbidden.isdisjoint(obligation.required_state))
                self.assertFalse(obligation.memory_evidence_required)

    def test_existing_invariance_cases(self):
        cases = {
            "What are you?": "describe_self",
            "What do you remember about me?": "report_memory_state",
            "Can you modify yourself?": "answer_capability",
            "What can you do?": "answer_capability",
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                obligation = self._obligation(prompt)
                self.assertEqual(obligation.obligation_type, expected)

    def test_source_level_guards(self):
        response_path = os.path.join(ROOT, "weslr", "response_obligation.py")
        with open(response_path, "r", encoding="utf-8") as f:
            response_source = f.read()
        self.assertNotIn("human_context_scores", response_source)

        state_context_path = os.path.join(ROOT, "weslr", "meaning_state_context.py")
        with open(state_context_path, "r", encoding="utf-8") as f:
            state_context_source = f.read()
        self.assertNotIn("creative_conversation_scores", state_context_source)
        self.assertNotIn("human_context_scores", state_context_source)


if __name__ == "__main__":
    unittest.main()
