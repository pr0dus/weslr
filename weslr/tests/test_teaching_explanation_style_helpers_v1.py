from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    ProofStep,
    create_teaching_explanation_from_proof_step,
    summarize_teaching_explanation_generation_diagnostics,
    validate_teaching_explanation,
)
from weslr.synthetic_logic_curriculum import load_synthetic_logic_curriculum_v1  # noqa: E402


TEACHING_MODES = ["beginner", "technical", "academic", "spock", "operator_audit"]
FORBIDDEN_EXPLANATION_PATTERNS = [
    r"\b(?:in)?correct(?:ness)?\b",
    r"\b(?:right|wrong)\b",
    r"\b(?:dis)?proves?\b",
    r"\b(?:un)?sound(?:ness)?\b",
    r"\bbest\s+answer\b",
    r"\bofficial\s+scores?\b",
    r"\bground\s+truth\b",
    r"\bcloser\s+to\s+correct\b",
    r"\bWESLR\s+knows\b",
    r"\bguaranteed\b",
    r"\b(?:passes|fails)\b",
    r"\bselect(?:s|ed|ing)?\s+an?\s+answer\b",
    r"\banswer\s+selection\b",
    r"\bthe\s+answer\s+is\b",
    r"\banswer\s+key\b",
]
UNSUPPORTED_BOUNDARY_RE = re.compile(
    r"trace does not yet establish|connection remains unestablished|support is incomplete",
    re.IGNORECASE,
)
FALLACY_BOUNDARY_RE = re.compile(r"has the structure of", re.IGNORECASE)


def explanation_text(explanation) -> str:
    fields = [
        explanation.core_claim,
        explanation.why_it_follows_or_fails,
        explanation.counterexample_note,
        explanation.uncertainty_note,
        *explanation.step_by_step_explanation,
        explanation.human_explanation,
    ]
    return "\n".join(str(field) for field in fields if str(field).strip())


def make_proof_step(pattern: str = "modus_ponens", *, support_status: str = "supported", gaps: list[str] | None = None) -> ProofStep:
    mapping = {}
    if pattern in {"affirming_consequent", "denying_antecedent"}:
        mapping = {"form_label": pattern, "support_assessment": "fallacy_shaped", "fallacy_shaped": True}
        support_status = "unsupported"
        gaps = list(gaps or ["recognized_fallacy_shaped_pattern"])
    return ProofStep(
        proof_step_id=f"proof_step:{pattern}:{support_status}",
        source_context_binding_ids=["ctx:synthetic"],
        source_premise_proposition_ids=["premise:1", "premise:2"],
        source_choice_proposition_ids=["choice:1"],
        reasoning_relation="synthetic_relation",
        inference_pattern=pattern,
        inference_pattern_id=pattern,
        support_status=support_status,
        source_proposition_ids=["premise:1", "premise:2", "choice:1"],
        target_proposition_id="choice:1",
        conditional_form_mapping=mapping,
        confidence="medium",
        unsupported_gaps=list(gaps or []),
        human_explanation="Redacted synthetic proof-step structure only.",
    )


def proof_step_from_fixture(fixture) -> ProofStep:
    pattern = fixture.expected_structural_pattern
    support_status = "rule_application_supported"
    mapping = {}
    requires_counterexample = False
    gaps = list(fixture.unsupported_gaps_allowed)
    if pattern in {"affirming_consequent", "denying_antecedent"}:
        support_status = "unsupported"
        mapping = {"form_label": pattern, "support_assessment": "fallacy_shaped", "fallacy_shaped": True}
        gaps = ["recognized_fallacy_shaped_pattern", *gaps]
    elif pattern == "counterexample":
        support_status = "counterexample_supported"
        requires_counterexample = True
    elif pattern in {"invalid_argument_identification", "irrelevant_choice"}:
        support_status = "unsupported"
    return ProofStep(
        proof_step_id=f"proof_step:{fixture.example_id}",
        source_context_binding_ids=[f"ctx:{fixture.example_id}"],
        source_premise_proposition_ids=[f"premise:{fixture.example_id}:1"],
        source_choice_proposition_ids=[f"choice:{fixture.example_id}:1"],
        reasoning_relation=fixture.expected_context_binding_type,
        inference_pattern=pattern,
        inference_pattern_id=pattern,
        support_status=support_status,
        source_proposition_ids=[f"premise:{fixture.example_id}:1", f"choice:{fixture.example_id}:1"],
        target_proposition_id=f"choice:{fixture.example_id}:1",
        conditional_form_mapping=mapping,
        confidence="medium",
        unsupported_gaps=gaps,
        requires_counterexample=requires_counterexample,
        human_explanation="Redacted synthetic curriculum structure only.",
    )


class TeachingExplanationStyleHelpersV1Tests(unittest.TestCase):
    def explanation_for(self, mode: str, **kwargs):
        return create_teaching_explanation_from_proof_step(make_proof_step(**kwargs), teaching_mode=mode)

    def assert_no_forbidden_phrases(self, text: str) -> None:
        for pattern in FORBIDDEN_EXPLANATION_PATTERNS:
            self.assertIsNone(re.search(pattern, text, re.IGNORECASE), f"forbidden phrase matched {pattern!r} in {text!r}")

    def test_beginner_mode_produces_beginner_style_text(self):
        text = explanation_text(self.explanation_for("beginner"))
        self.assertIn("Plain structural teaching note", text)
        self.assertIn("Observed pattern", text)
        self.assertIn("Why it matters", text)

    def test_technical_mode_produces_technical_style_text(self):
        text = explanation_text(self.explanation_for("technical"))
        self.assertIn("Technical structural note", text)
        self.assertIn("Pattern field", text)
        self.assertIn("Gap constraint", text)

    def test_academic_mode_produces_academic_style_text(self):
        text = explanation_text(self.explanation_for("academic"))
        self.assertIn("Reviewer-style", text)
        self.assertIn("Claim:", text)
        self.assertIn("Warrant:", text)
        self.assertIn("Limitation:", text)

    def test_spock_mode_produces_concise_neutral_text(self):
        explanation = self.explanation_for("spock")
        text = explanation_text(explanation)
        self.assertIn("Non-conclusive", text)
        self.assertIn("Observed:", text)
        self.assertLessEqual(len(explanation.step_by_step_explanation), 4)

    def test_operator_audit_mode_produces_traceability_text(self):
        text = explanation_text(self.explanation_for("operator_audit", gaps=["slot_binding_incomplete"]))
        self.assertIn("OBSERVED", text)
        self.assertIn("INFERRED", text)
        self.assertIn("NOT_ESTABLISHED", text)
        self.assertIn("TRACE_LIMITATION", text)

    def test_same_proof_step_and_mode_is_deterministic(self):
        step = make_proof_step(gaps=["slot_binding_incomplete"])
        first = create_teaching_explanation_from_proof_step(step, teaching_mode="technical")
        second = create_teaching_explanation_from_proof_step(step, teaching_mode="technical")
        self.assertEqual(first, second)

    def test_different_modes_produce_distinct_text(self):
        step = make_proof_step(gaps=["slot_binding_incomplete"])
        texts = {
            mode: explanation_text(create_teaching_explanation_from_proof_step(step, teaching_mode=mode))
            for mode in TEACHING_MODES
        }
        self.assertEqual(len(TEACHING_MODES), len(set(texts.values())))

    def test_fallacy_shaped_explanation_uses_bounded_structure_wording(self):
        text = explanation_text(self.explanation_for("academic", pattern="affirming_consequent"))
        self.assertRegex(text, FALLACY_BOUNDARY_RE)
        self.assertIn("introduces a structural risk", text)
        self.assertIn("does not by itself establish the target relation", text)

    def test_fallacy_shaped_explanation_avoids_verdict_wording(self):
        text = explanation_text(self.explanation_for("technical", pattern="denying_antecedent"))
        self.assert_no_forbidden_phrases(text)

    def test_unsupported_gap_explanation_uses_trace_limit_wording(self):
        text = explanation_text(self.explanation_for("beginner", support_status="ambiguous", gaps=["slot_binding_incomplete"]))
        self.assertRegex(text, UNSUPPORTED_BOUNDARY_RE)

    def test_unsupported_gap_explanation_avoids_system_failure_wording(self):
        text = explanation_text(self.explanation_for("operator_audit", support_status="unsupported", gaps=["slot_binding_incomplete"]))
        for forbidden in ["broken", "failed", "cannot reason", "impossible"]:
            self.assertNotIn(forbidden, text.lower())

    def test_forbidden_phrase_list_is_absent_from_generated_text(self):
        for mode in TEACHING_MODES:
            with self.subTest(mode=mode):
                text = explanation_text(self.explanation_for(mode, support_status="ambiguous", gaps=["slot_binding_incomplete"]))
                self.assert_no_forbidden_phrases(text)

    def test_no_answer_selection(self):
        explanations = [self.explanation_for(mode) for mode in TEACHING_MODES]
        summary = summarize_teaching_explanation_generation_diagnostics(explanations)
        self.assertFalse(summary["answer_selection_enabled"])
        for explanation in explanations:
            self.assertTrue(explanation.anti_gaming.no_answer_selection)
            self.assert_no_forbidden_phrases(explanation_text(explanation))

    def test_no_truth_or_soundness_claim(self):
        explanations = [self.explanation_for(mode) for mode in TEACHING_MODES]
        summary = summarize_teaching_explanation_generation_diagnostics(explanations)
        self.assertFalse(summary["truth_claim_made"])
        for explanation in explanations:
            self.assert_no_forbidden_phrases(explanation_text(explanation))

    def test_no_official_score(self):
        explanations = [self.explanation_for(mode) for mode in TEACHING_MODES]
        summary = summarize_teaching_explanation_generation_diagnostics(explanations)
        self.assertFalse(summary["official_score_claimed"])
        for explanation in explanations:
            self.assertFalse(explanation.anti_gaming.claims_official_score)
            self.assert_no_forbidden_phrases(explanation_text(explanation))

    def test_all_70_synthetic_style_explanations_are_covered_and_safe(self):
        fixtures = load_synthetic_logic_curriculum_v1()
        explanations = []
        for fixture in fixtures:
            step = proof_step_from_fixture(fixture)
            for mode in TEACHING_MODES:
                explanations.append(create_teaching_explanation_from_proof_step(step, teaching_mode=mode))
        self.assertEqual(14, len(fixtures))
        self.assertEqual(70, len(explanations))
        summary = summarize_teaching_explanation_generation_diagnostics(explanations)
        self.assertEqual(70, summary["teaching_explanation_count"])
        self.assertEqual({mode: 14 for mode in TEACHING_MODES}, {mode: summary["teaching_mode_counts"][mode] for mode in TEACHING_MODES})
        self.assertFalse(summary["answer_selection_enabled"])
        self.assertFalse(summary["truth_claim_made"])
        self.assertFalse(summary["official_score_claimed"])
        self.assertTrue(summary["anti_gaming_safe"])
        self.assertTrue(summary["legibility_safe"])
        for explanation in explanations:
            self.assertEqual([], validate_teaching_explanation(explanation))
            self.assertTrue(explanation_text(explanation).strip())
            self.assert_no_forbidden_phrases(explanation_text(explanation))

    def test_all_70_synthetic_style_explanations_are_deterministic(self):
        fixtures = load_synthetic_logic_curriculum_v1()
        first = []
        second = []
        for fixture in fixtures:
            step = proof_step_from_fixture(fixture)
            for mode in TEACHING_MODES:
                first.append(create_teaching_explanation_from_proof_step(step, teaching_mode=mode))
                second.append(create_teaching_explanation_from_proof_step(step, teaching_mode=mode))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
