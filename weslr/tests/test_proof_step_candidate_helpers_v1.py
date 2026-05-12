from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    ProofStep,
    ReasoningContextBindingCandidate,
    classify_conditional_form_mapping,
    classify_proof_step_candidate_type,
    create_proof_step_candidate_from_context_binding,
    create_proof_step_candidates_from_context_bindings,
    create_proof_step_from_candidate,
    create_reasoning_context_binding_candidate_from_structures,
    derive_conditional_form_mapping_from_context_binding,
    summarize_conditional_form_mapping_diagnostics,
    summarize_proof_step_candidate_diagnostics,
    summarize_proof_step_generation_diagnostics,
)


FORBIDDEN_CHANGED = {
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/tests/test_proof_step_candidate_schema_v1.py",
    "weslr/tests/test_proof_step_candidate_helpers_v1.py",
    "weslr/tests/test_logic_teaching_spine_schema_v1.py",
    "weslr/tests/test_synthetic_proof_step_helpers_v1.py",
    "weslr/tests/test_conditional_form_mapping_helpers_v1.py",
    "weslr/tests/test_conditional_slot_provenance_helpers_v1.py",
}


class ProofStepCandidateHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only && git ls-files --others --exclude-standard"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def binding(self, relation: str = "support", **kwargs) -> ReasoningContextBindingCandidate:
        data = {
            "binding_id": "ctx:1",
            "source_premise_proposition_ids": ["premise:1"],
            "source_question_instruction_ids": ["question:1"],
            "source_choice_proposition_ids": ["choice:1"],
            "expected_reasoning_relation": relation,
            "candidate_support_role": "supports_target",
            "choice_target_role": "candidate_conclusion",
            "confidence": "medium",
            "unsupported_gaps": [],
            "human_explanation": "Redacted structural context binding explanation.",
        }
        data.update(kwargs)
        return ReasoningContextBindingCandidate(**data)

    def test_classifies_support_relation_as_support_candidate(self):
        self.assertEqual("support_step_candidate", classify_proof_step_candidate_type(self.binding("support")))

    def test_classifies_contradiction_relation_as_contradiction_candidate(self):
        self.assertEqual("contradiction_step_candidate", classify_proof_step_candidate_type(self.binding("contradict")))

    def test_classifies_counterexample_relation_as_counterexample_candidate(self):
        self.assertEqual("counterexample_step_candidate", classify_proof_step_candidate_type(self.binding("provide_counterexample")))

    def test_classifies_rule_application_relation_as_rule_application_candidate(self):
        self.assertEqual("rule_application_candidate", classify_proof_step_candidate_type(self.binding("apply_condition")))
        self.assertEqual("rule_application_candidate", classify_proof_step_candidate_type(self.binding("instantiate_rule")))

    def test_classifies_validity_test_as_invalidity_test_candidate(self):
        self.assertEqual("invalidity_test_candidate", classify_proof_step_candidate_type(self.binding("test_validity")))

    def test_classifies_template_completion(self):
        self.assertEqual("template_completion_candidate", classify_proof_step_candidate_type(self.binding("complete_template")))

    def test_unknown_relation_becomes_unsupported_step_candidate(self):
        self.assertEqual("unsupported_step_candidate", classify_proof_step_candidate_type(self.binding("unknown")))

    def test_creates_proof_step_candidate_from_context_binding(self):
        candidate = create_proof_step_candidate_from_context_binding(self.binding())
        self.assertEqual("proof_step_candidate:ctx:1", candidate.candidate_id)
        self.assertEqual("support_step_candidate", candidate.candidate_type)

    def test_preserves_context_binding_id(self):
        candidate = create_proof_step_candidate_from_context_binding(self.binding(binding_id="ctx:preserve"))
        self.assertEqual(["ctx:preserve"], candidate.source_context_binding_ids)

    def test_preserves_premise_proposition_ids(self):
        candidate = create_proof_step_candidate_from_context_binding(self.binding(source_premise_proposition_ids=["premise:a", "premise:b"]))
        self.assertEqual(["premise:a", "premise:b"], candidate.source_premise_proposition_ids)

    def test_preserves_choice_proposition_ids(self):
        candidate = create_proof_step_candidate_from_context_binding(self.binding(source_choice_proposition_ids=["choice:a", "choice:b"]))
        self.assertEqual(["choice:a", "choice:b"], candidate.source_choice_proposition_ids)

    def test_preserves_unsupported_gaps(self):
        candidate = create_proof_step_candidate_from_context_binding(self.binding(unsupported_gaps=["gap:visible"]))
        self.assertIn("gap:visible", candidate.unsupported_gaps)

    def test_missing_refs_become_insufficient_support(self):
        candidate = create_proof_step_candidate_from_context_binding(
            self.binding(source_premise_proposition_ids=[], source_choice_proposition_ids=[])
        )
        self.assertEqual("insufficient_support", candidate.support_status)
        self.assertIn("missing_premise_proposition_refs", candidate.unsupported_gaps)
        self.assertIn("missing_choice_proposition_refs", candidate.unsupported_gaps)

    def test_confidence_is_never_high_by_default(self):
        candidates = create_proof_step_candidates_from_context_bindings([
            self.binding("support"),
            self.binding("unknown"),
            self.binding(source_premise_proposition_ids=[]),
        ])
        self.assertNotIn("high", {candidate.confidence for candidate in candidates})

    def test_does_not_generate_actual_proof_step(self):
        candidate = create_proof_step_candidate_from_context_binding(self.binding())
        self.assertNotIsInstance(candidate, ProofStep)
        summary = summarize_proof_step_candidate_diagnostics([candidate])
        self.assertFalse(summary["proof_behavior_generated"])

    def test_does_not_select_answers(self):
        candidate = create_proof_step_candidate_from_context_binding(self.binding())
        self.assertTrue(candidate.anti_gaming.no_answer_selection)
        self.assertFalse(summarize_proof_step_candidate_diagnostics([candidate])["answer_selection_enabled"])

    def test_does_not_claim_truth(self):
        candidate = create_proof_step_candidate_from_context_binding(self.binding(human_explanation="Redacted structural explanation."))
        self.assertNotIn("truth", candidate.human_explanation.lower())
        self.assertNotIn("correct", candidate.human_explanation.lower())

    def test_does_not_use_answer_key(self):
        self.assertFalse(create_proof_step_candidate_from_context_binding(self.binding()).anti_gaming.uses_answer_key)

    def test_does_not_use_item_id_as_authority(self):
        self.assertFalse(create_proof_step_candidate_from_context_binding(self.binding()).anti_gaming.uses_item_id_as_authority)

    def conditional_mapping(self, asserted: str, conclusion: str, **kwargs):
        data = {
            "conditional": "P -> Q",
            "asserted_literal": asserted,
            "conclusion_literal": conclusion,
            "conditional_count": 1,
            "conditional_direction": "P_to_Q",
            "negation_scope_status": "clear",
            "slot_binding_status": "complete",
            "conclusion_binding_count": 1,
            "requires_semantic_bridge": False,
        }
        data.update(kwargs)
        return classify_conditional_form_mapping(**data)

    def test_conditional_mapping_classifies_modus_ponens(self):
        result = self.conditional_mapping("P", "Q")
        self.assertEqual("modus_ponens", result.form_label)
        self.assertEqual("supported_form", result.support_assessment)
        self.assertTrue(result.supported_form)
        self.assertFalse(result.fallacy_shaped)

    def test_conditional_mapping_classifies_modus_tollens(self):
        result = self.conditional_mapping("¬Q", "¬P")
        self.assertEqual("modus_tollens", result.form_label)
        self.assertEqual("supported_form", result.support_assessment)

    def test_conditional_mapping_classifies_affirming_consequent(self):
        result = self.conditional_mapping("Q", "P")
        self.assertEqual("affirming_consequent", result.form_label)
        self.assertEqual("fallacy_shaped", result.support_assessment)
        self.assertTrue(result.fallacy_shaped)

    def test_conditional_mapping_classifies_denying_antecedent(self):
        result = self.conditional_mapping("¬P", "¬Q")
        self.assertEqual("denying_antecedent", result.form_label)
        self.assertEqual("fallacy_shaped", result.support_assessment)

    def test_conditional_mapping_swapped_conclusion_stays_unsupported(self):
        result = self.conditional_mapping("P", "¬Q")
        self.assertEqual("unsupported_form", result.form_label)
        self.assertEqual("insufficient_structure", result.support_assessment)

    def test_conditional_mapping_missing_conclusion_stays_ambiguous(self):
        result = self.conditional_mapping("P", "")
        self.assertEqual("ambiguous_form", result.form_label)
        self.assertIn("conclusion_literal_unbound", result.unsupported_gaps)

    def test_conditional_mapping_unclear_negation_scope_stays_ambiguous(self):
        result = self.conditional_mapping("¬Q", "¬P", negation_scope_status="unclear")
        self.assertEqual("ambiguous_form", result.form_label)
        self.assertIn("negation_scope_unclear", result.unsupported_gaps)

    def test_conditional_mapping_multiple_conditionals_stays_ambiguous(self):
        result = self.conditional_mapping("P", "Q", conditional_count=2)
        self.assertEqual("ambiguous_form", result.form_label)
        self.assertIn("conditional_count_not_one", result.unsupported_gaps)

    def test_conditional_mapping_fallacy_flag_is_derived_not_primary_input(self):
        result = self.conditional_mapping("P", "Q", fallacy_shaped=True)
        self.assertEqual("modus_ponens", result.form_label)
        self.assertEqual("supported_form", result.support_assessment)
        self.assertFalse(result.fallacy_shaped)

    def test_conditional_mapping_summary_preserves_safety_flags(self):
        summary = summarize_conditional_form_mapping_diagnostics([
            self.conditional_mapping("P", "Q"),
            self.conditional_mapping("Q", "P"),
            self.conditional_mapping("P", "¬Q"),
        ])
        self.assertEqual(1, summary["supported_form_count"])
        self.assertEqual(1, summary["fallacy_shaped_count"])
        self.assertEqual(1, summary["unsupported_or_insufficient_structure_count"])
        self.assertFalse(summary["answer_selection_enabled"])
        self.assertFalse(summary["truth_claim_made"])
        self.assertFalse(summary["official_score_claimed"])

    def conditional_binding(self, asserted: str = "P", conclusion: str = "Q", **kwargs):
        data = {
            "binding_id": "ctx:conditional:pipeline",
            "source_premise_proposition_ids": ["premise:conditional", "premise:literal"],
            "source_question_instruction_ids": ["question:structural"],
            "source_choice_proposition_ids": ["choice:conclusion"],
            "expected_reasoning_relation": "apply_condition",
            "candidate_support_role": "supports_target",
            "choice_target_role": "candidate_conclusion",
            "conditional_form_slots": {
                "conditional": "P -> Q",
                "asserted_literal": asserted,
                "conclusion_literal": conclusion,
                "conditional_count": 1,
                "conditional_direction": "P_to_Q",
                "negation_scope_status": "clear",
                "slot_binding_status": "complete",
                "conclusion_binding_count": 1,
                "requires_semantic_bridge": False,
            },
        }
        data.update(kwargs)
        return data

    def test_conditional_fallacy_mapping_is_structural_hint_only(self):
        candidate = create_proof_step_candidate_from_context_binding(
            {
                "binding_id": "ctx:conditional:fallacy",
                "source_premise_proposition_ids": ["premise:conditional", "premise:literal"],
                "source_question_instruction_ids": ["question:invalidity"],
                "source_choice_proposition_ids": ["choice:conclusion"],
                "expected_reasoning_relation": "test_validity",
                "candidate_support_role": "tests_target",
                "choice_target_role": "candidate_invalid_statement",
                "conditional_form_slots": {
                    "conditional": "P -> Q",
                    "asserted_literal": "Q",
                    "conclusion_literal": "P",
                    "conditional_count": 1,
                    "conditional_direction": "P_to_Q",
                    "negation_scope_status": "clear",
                    "slot_binding_status": "complete",
                    "conclusion_binding_count": 1,
                    "requires_semantic_bridge": False,
                },
            }
        )
        self.assertEqual("invalidity_test_candidate", candidate.candidate_type)
        self.assertEqual("affirming_consequent", candidate.inference_pattern_hint)
        self.assertEqual("pipeline_derived_mapping", candidate.conditional_form_mapping_origin)
        self.assertEqual("affirming_consequent", candidate.conditional_form_mapping["form_label"])
        self.assertEqual("unsupported", candidate.support_status)
        self.assertEqual("low", candidate.confidence)
        self.assertIn("recognized_fallacy_shaped_pattern", candidate.unsupported_gaps)
        self.assertFalse(candidate.anti_gaming.uses_answer_key)
        self.assertTrue(candidate.anti_gaming.no_answer_selection)

    def test_actual_structure_pipeline_derives_conditional_mapping(self):
        binding = create_reasoning_context_binding_candidate_from_structures(
            binding_id="ctx:fixture:modus_ponens",
            premise_propositions=[{"proposition_id": "premise:conditional"}, {"proposition_id": "premise:literal"}],
            question_instruction_records=[{"statement_id": "question:structural", "normalized_text": "what follows"}],
            choice_propositions=[{"proposition_id": "choice:conclusion", "proposition_role": "choice_claim"}],
            simple_inference_candidates=[{"expected_structural_pattern": "modus_ponens"}],
        )
        candidate = create_proof_step_candidate_from_context_binding(binding)
        self.assertEqual("pipeline_derived_mapping", candidate.conditional_form_mapping_origin)
        self.assertEqual("modus_ponens", candidate.conditional_form_mapping["form_label"])
        self.assertEqual(["ctx:fixture:modus_ponens"], candidate.conditional_form_mapping["source_context_binding_ids"])

    def test_pipeline_conditional_mapping_preserves_candidate_refs(self):
        candidate = create_proof_step_candidate_from_context_binding(self.conditional_binding("P", "Q"))
        self.assertEqual("pipeline_derived_mapping", candidate.conditional_form_mapping_origin)
        self.assertEqual("modus_ponens", candidate.conditional_form_mapping["form_label"])
        self.assertEqual(["ctx:conditional:pipeline"], candidate.conditional_form_mapping["source_context_binding_ids"])
        self.assertEqual(["premise:conditional", "premise:literal"], candidate.conditional_form_mapping["source_premise_proposition_ids"])
        self.assertEqual(["choice:conclusion"], candidate.conditional_form_mapping["source_choice_proposition_ids"])

    def test_pipeline_conditional_mapping_preserves_proof_step_refs(self):
        step = create_proof_step_from_candidate(create_proof_step_candidate_from_context_binding(self.conditional_binding("P", "Q")))
        self.assertEqual("pipeline_derived_mapping", step.conditional_form_mapping_origin)
        self.assertEqual("modus_ponens", step.conditional_form_mapping["form_label"])
        self.assertTrue(step.conditional_form_mapping["source_context_binding_ids"])
        self.assertTrue(step.warrant)

    def test_ad_hoc_mapping_not_counted_as_pipeline_mapping(self):
        helper_result = classify_conditional_form_mapping(asserted_literal="P", conclusion_literal="Q")
        self.assertEqual("modus_ponens", helper_result.form_label)
        candidate = create_proof_step_candidate_from_context_binding(self.binding("apply_condition"))
        summary = summarize_proof_step_candidate_diagnostics([candidate])
        self.assertEqual(0, summary["pipeline_conditional_form_mapping_count"])
        self.assertEqual(0, summary["ad_hoc_conditional_form_mapping_count"])
        self.assertEqual(1, summary["insufficient_slot_evidence_count"])

    def test_missing_slot_evidence_remains_insufficient(self):
        mapping = derive_conditional_form_mapping_from_context_binding({"binding_id": "ctx:missing"})
        self.assertEqual("insufficient_slot_evidence", mapping["origin"])
        self.assertEqual("ambiguous_form", mapping["form_label"])
        self.assertIn("conditional_slot_evidence_unavailable", mapping["unsupported_gaps"])

    def test_incomplete_pipeline_slots_remain_ambiguous(self):
        candidate = create_proof_step_candidate_from_context_binding(self.conditional_binding("P", ""))
        self.assertEqual("pipeline_derived_mapping", candidate.conditional_form_mapping_origin)
        self.assertEqual("ambiguous_form", candidate.conditional_form_mapping["form_label"])
        self.assertEqual("insufficient_structure", candidate.conditional_form_mapping["support_assessment"])
        self.assertEqual("low", candidate.confidence)
        self.assertIn("conditional_form_mapping_insufficient_structure", candidate.unsupported_gaps)

    def test_conditional_pipeline_mapping_counts_by_type(self):
        candidates = [
            create_proof_step_candidate_from_context_binding(self.conditional_binding("P", "Q")),
            create_proof_step_candidate_from_context_binding(self.conditional_binding("¬Q", "¬P")),
            create_proof_step_candidate_from_context_binding(self.conditional_binding("Q", "P")),
            create_proof_step_candidate_from_context_binding(self.conditional_binding("¬P", "¬Q")),
        ]
        summary = summarize_proof_step_candidate_diagnostics(candidates)
        self.assertEqual(4, summary["pipeline_conditional_form_mapping_count"])
        self.assertEqual(0, summary["ad_hoc_conditional_form_mapping_count"])
        self.assertEqual(1, summary["conditional_form_mapping_counts"]["modus_ponens"])
        self.assertEqual(1, summary["conditional_form_mapping_counts"]["modus_tollens"])
        self.assertEqual(1, summary["conditional_form_mapping_counts"]["affirming_consequent"])
        self.assertEqual(1, summary["conditional_form_mapping_counts"]["denying_antecedent"])
        self.assertEqual(2, summary["fallacy_shaped_count"])
        self.assertEqual(2, summary["supported_form_count"])

    def test_proof_step_conditional_diagnostics_preserve_refs_and_safety(self):
        step = create_proof_step_from_candidate(create_proof_step_candidate_from_context_binding(self.conditional_binding("P", "Q")))
        summary = summarize_proof_step_generation_diagnostics([step])
        self.assertEqual(1, summary["pipeline_conditional_form_mapping_count"])
        self.assertEqual(0, summary["ad_hoc_conditional_form_mapping_count"])
        self.assertEqual(1, summary["conditional_mappings_with_context_refs"])
        self.assertEqual(1, summary["conditional_mappings_with_premise_refs"])
        self.assertEqual(1, summary["conditional_mappings_with_choice_refs"])
        self.assertEqual(1, summary["conditional_mappings_with_visible_warrant"])
        self.assertFalse(summary["answer_selection_enabled"])
        self.assertFalse(summary["truth_claim_made"])
        self.assertFalse(summary["official_score_claimed"])

    def test_summary_is_redacted(self):
        candidate = create_proof_step_candidate_from_context_binding(
            self.binding(
                source_premise_proposition_ids=["premise:secret"],
                source_choice_proposition_ids=["choice:secret"],
                unsupported_gaps=["hidden raw gap"],
            )
        )
        summary = summarize_proof_step_candidate_diagnostics([candidate])
        text = str(summary).lower()
        self.assertEqual(1, summary["proof_step_candidate_count"])
        for forbidden in ["source_premise_proposition_ids", "source_choice_proposition_ids", "answer_key", "correct_answer", "raw_text", "official_score"]:
            self.assertNotIn(forbidden, text)

    def test_schema_tests_still_pass(self):
        proc = subprocess.run(
            ["python3", "weslr/tests/test_proof_step_candidate_schema_v1.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("OK", proc.stdout + proc.stderr)

    def test_release_gate_and_check_pass(self):
        proc = subprocess.run(
            ["bash", "-lc", "python3 weslr/tests/release_gate_v1.py && bash scripts/weslr_release_check.sh"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        output = proc.stdout + proc.stderr
        self.assertIn("WESLR_RELEASE_GATE_V1_OK", output)
        self.assertIn("WESLR_RELEASE_CHECK_OK", output)

    def test_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
