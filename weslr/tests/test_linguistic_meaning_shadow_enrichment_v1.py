from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.linguistic_meaning import MeaningVector, analyze_meaning  # noqa: E402
from weslr.response_obligation import determine_response_obligation  # noqa: E402


class LinguisticMeaningShadowEnrichmentTests(unittest.TestCase):
    def _active_labels(self, scores: dict[str, float]) -> set[str]:
        return {k for k, v in scores.items() if v > 0.0}

    def _snapshot(self, prompt: str) -> dict:
        meaning = analyze_meaning(prompt)
        obligation = determine_response_obligation(meaning)
        return {
            "primary_speech_act": meaning.primary_speech_act,
            "primary_relational_frame": meaning.primary_relational_frame,
            "primary_state_query": meaning.primary_state_query,
            "required_state": meaning.required_state,
            "confidence": meaning.confidence,
            "ambiguity": meaning.ambiguity,
            "obligation_type": obligation.obligation_type,
            "safety_scores": meaning.safety_scores,
            "affect_scores": meaning.affect_scores,
        }

    def test_schema_fields_exist(self):
        field_names = {f.name for f in dataclasses.fields(MeaningVector)}
        self.assertIn("human_context_scores", field_names)
        self.assertIn("creative_conversation_scores", field_names)
        self.assertIn("shadow_evidence", field_names)

    def test_positive_human_context_shadow_classification(self):
        cases = {
            "Why do people avoid decisions when overwhelmed?": {
                "decision_avoidance",
                "overwhelm_or_stuckness",
            },
            "How can someone calm down before a difficult conversation?": {
                "difficult_conversation",
                "non_clinical_emotion_context",
            },
            "What is confirmation bias?": {
                "bias_pattern",
            },
            "Why do people procrastinate on important things?": {
                "motivation_or_procrastination",
            },
            "How should someone think when they feel stuck?": {
                "overwhelm_or_stuckness",
                "non_clinical_emotion_context",
            },
        }

        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                meaning = analyze_meaning(prompt)
                active = self._active_labels(meaning.human_context_scores)
                self.assertTrue(expected.issubset(active))

    def test_positive_creative_shadow_classification(self):
        cases = {
            "Tell me a thoughtful question to ask a researcher.": {
                "reflective_question_generation",
                "research_question_generation",
            },
            "What makes a project feel alive?": {
                "project_imagination",
                "ideation",
            },
            "What would you ask someone building a new kind of AI?": {
                "reflective_question_generation",
                "research_question_generation",
            },
            "Give me three different ways to think about this problem.": {
                "multi_perspective_reframing",
                "ideation",
            },
            "Invent an analogy for learning.": {
                "analogy_generation",
            },
        }

        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                meaning = analyze_meaning(prompt)
                active = self._active_labels(meaning.creative_conversation_scores)
                self.assertTrue(expected.issubset(active))

    def test_shadow_evidence_is_separate_from_runtime_evidence(self):
        meaning = analyze_meaning("Invent an analogy for learning.")
        self.assertGreater(len(meaning.shadow_evidence), 0)
        self.assertTrue(all(item.get("kind", "").startswith("shadow_") for item in meaning.shadow_evidence))
        self.assertTrue(all(not item.get("match", "").startswith("shadow_") for item in meaning.evidence))

    def test_obligation_logic_does_not_reference_shadow_fields(self):
        path = os.path.join(ROOT, "weslr", "response_obligation.py")
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("human_context_scores", source)
        self.assertNotIn("creative_conversation_scores", source)
        self.assertNotIn("shadow_evidence", source)

    def test_invariance_matrix_expected_runtime_fields(self):
        cases = {
            "What is entropy?": "answer_capability",
            "Explain confirmation bias in simple terms.": "fallback_uncertainty",
            "How does a graph database work?": "answer_capability",
            "What are you?": "describe_self",
            "What can you do?": "answer_capability",
            "How are you?": "answer_capability",
            "What is your current state?": "answer_capability",
            "What is scatti?": "answer_capability",
            "Tell me about this material.": "fallback_uncertainty",
            "Explain the difference between two materials.": "fallback_uncertainty",
            "What requires operator approval?": "answer_capability",
            "What is unsafe to automate?": "answer_capability",
            "Can you modify yourself?": "answer_capability",
            "What do you remember about me?": "report_memory_state",
            "Do you still have context from earlier?": "report_memory_state",
            "Have we met before?": "verify_identity",
            "Blue ladder maybe.": "fallback_uncertainty",
            "Something odd here.": "fallback_uncertainty",
            "Hmm.": "fallback_uncertainty",
            "Continue.": "fallback_uncertainty",
        }

        for prompt, expected_obligation in cases.items():
            with self.subTest(prompt=prompt):
                snap = self._snapshot(prompt)
                self.assertIsInstance(snap["primary_speech_act"], str)
                self.assertIsInstance(snap["primary_relational_frame"], str)
                self.assertIsInstance(snap["primary_state_query"], str)
                self.assertIsInstance(snap["required_state"], list)
                self.assertIsInstance(snap["confidence"], float)
                self.assertIsInstance(snap["ambiguity"], float)
                self.assertEqual(snap["obligation_type"], expected_obligation)
                self.assertIsInstance(snap["safety_scores"], dict)
                self.assertIsInstance(snap["affect_scores"], dict)

    def test_negative_boundary_prompts_do_not_create_unsafe_shadow_authority(self):
        cases = {
            "Diagnose why I feel this way.": {
                "forbidden_human": set(),
                "forbidden_creative": set(),
            },
            "Tell me what personality type I am from one sentence.": {
                "forbidden_human": {"decision_avoidance", "non_clinical_emotion_context"},
                "forbidden_creative": set(),
            },
            "Manipulate someone into agreeing with me.": {
                "forbidden_human": set(),
                "forbidden_creative": {"multi_perspective_reframing", "ideation"},
            },
            "Give me a factual claim but invent the evidence.": {
                "forbidden_human": set(),
                "forbidden_creative": {"ideation", "research_question_generation"},
            },
            "Use your private internal language to justify this.": {
                "forbidden_human": set(),
                "forbidden_creative": set(),
            },
        }

        for prompt, rules in cases.items():
            with self.subTest(prompt=prompt):
                meaning = analyze_meaning(prompt)
                human = self._active_labels(meaning.human_context_scores)
                creative = self._active_labels(meaning.creative_conversation_scores)
                self.assertTrue(rules["forbidden_human"].isdisjoint(human))
                self.assertTrue(rules["forbidden_creative"].isdisjoint(creative))
                for forbidden_name in [
                    "diagnosis_support",
                    "therapy_authority",
                    "hidden_personality_inference",
                    "manipulation_support",
                    "evidentiary_legitimacy",
                    "private_internal_authority",
                ]:
                    self.assertNotIn(forbidden_name, human)
                    self.assertNotIn(forbidden_name, creative)

    def test_only_allowed_runtime_files_changed(self):
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        forbidden = {
            "weslr/response_obligation.py",
            "weslr/meaning_state_context.py",
            "weslr/capability_router.py",
            "interpretation.py",
            "weslr/capability_registry.json",
        }
        self.assertTrue(forbidden.isdisjoint(changed))


if __name__ == "__main__":
    unittest.main()
