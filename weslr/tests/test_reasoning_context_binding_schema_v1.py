from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    SAFE_REASONING_CONTEXT_CANDIDATE_SUPPORT_ROLES,
    SAFE_REASONING_CONTEXT_CHOICE_TARGET_ROLES,
    SAFE_REASONING_CONTEXT_EXPECTED_RELATIONS,
    SAFE_REASONING_CONTEXT_PREMISE_CONTEXT_TYPES,
    SAFE_REASONING_CONTEXT_QUESTION_TARGET_TYPES,
    ReasoningContextBindingCandidate,
    create_empty_reasoning_context_binding_candidate,
    reasoning_context_binding_candidate_from_dict,
    reasoning_context_binding_candidate_to_dict,
    summarize_reasoning_context_binding_candidate,
    validate_reasoning_context_binding_candidate,
)

FORBIDDEN_CHANGED = {
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/tests/test_logic_teaching_spine_schema_v1.py",
    "weslr/tests/test_reasoning_context_binding_schema_v1.py",
}


class ReasoningContextBindingSchemaV1Tests(unittest.TestCase):
    def valid_candidate(self) -> ReasoningContextBindingCandidate:
        candidate = create_empty_reasoning_context_binding_candidate(binding_id="ctx:1")
        candidate.human_explanation = "Redacted structural context binding only."
        return candidate

    def test_schema_imports(self):
        self.assertIsNotNone(ReasoningContextBindingCandidate)

    def test_empty_candidate_instantiates(self):
        candidate = create_empty_reasoning_context_binding_candidate()
        self.assertEqual("1.0", candidate.schema_version)
        self.assertEqual("unknown", candidate.question_target_type)

    def test_safe_anti_gaming_defaults(self):
        candidate = create_empty_reasoning_context_binding_candidate()
        self.assertFalse(candidate.anti_gaming.uses_answer_key)
        self.assertFalse(candidate.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(candidate.anti_gaming.uses_answer_position_bias)
        self.assertFalse(candidate.anti_gaming.claims_official_score)
        self.assertFalse(candidate.anti_gaming.benchmark_specific_tuning)
        self.assertTrue(candidate.anti_gaming.no_answer_selection)

    def test_safe_legibility_defaults(self):
        candidate = create_empty_reasoning_context_binding_candidate()
        self.assertTrue(candidate.legibility.redacted_summary_only)
        self.assertFalse(candidate.legibility.stores_raw_benchmark_text)
        self.assertFalse(candidate.legibility.hides_unsupported_assumptions)
        self.assertFalse(candidate.legibility.private_symbolic_authority)

    def test_all_allowed_question_target_types_validate(self):
        for value in SAFE_REASONING_CONTEXT_QUESTION_TARGET_TYPES:
            candidate = self.valid_candidate()
            candidate.question_target_type = value
            self.assertNotIn("invalid question target type", validate_reasoning_context_binding_candidate(candidate))

    def test_all_allowed_premise_context_types_validate(self):
        for value in SAFE_REASONING_CONTEXT_PREMISE_CONTEXT_TYPES:
            candidate = self.valid_candidate()
            candidate.premise_context_type = value
            self.assertNotIn("invalid premise context type", validate_reasoning_context_binding_candidate(candidate))

    def test_all_allowed_choice_target_roles_validate(self):
        for value in SAFE_REASONING_CONTEXT_CHOICE_TARGET_ROLES:
            candidate = self.valid_candidate()
            candidate.choice_target_role = value
            self.assertNotIn("invalid choice target role", validate_reasoning_context_binding_candidate(candidate))

    def test_all_allowed_expected_reasoning_relations_validate(self):
        for value in SAFE_REASONING_CONTEXT_EXPECTED_RELATIONS:
            candidate = self.valid_candidate()
            candidate.expected_reasoning_relation = value
            self.assertNotIn("invalid expected reasoning relation", validate_reasoning_context_binding_candidate(candidate))

    def test_invalid_question_target_type_fails(self):
        candidate = self.valid_candidate()
        candidate.question_target_type = "correct_answer"
        self.assertIn("invalid question target type", validate_reasoning_context_binding_candidate(candidate))

    def test_invalid_premise_context_type_fails(self):
        candidate = self.valid_candidate()
        candidate.premise_context_type = "benchmark_context"
        self.assertIn("invalid premise context type", validate_reasoning_context_binding_candidate(candidate))

    def test_invalid_choice_target_role_fails(self):
        candidate = self.valid_candidate()
        candidate.choice_target_role = "selected_answer"
        self.assertIn("invalid choice target role", validate_reasoning_context_binding_candidate(candidate))

    def test_invalid_expected_reasoning_relation_fails(self):
        candidate = self.valid_candidate()
        candidate.expected_reasoning_relation = "proves_correct_answer"
        self.assertIn("invalid expected reasoning relation", validate_reasoning_context_binding_candidate(candidate))

    def test_invalid_candidate_support_role_fails(self):
        candidate = self.valid_candidate()
        candidate.candidate_support_role = "wins"
        self.assertIn("invalid candidate support role", validate_reasoning_context_binding_candidate(candidate))

    def test_invalid_confidence_fails(self):
        candidate = self.valid_candidate()
        candidate.confidence = "certain"
        self.assertIn("invalid confidence", validate_reasoning_context_binding_candidate(candidate))

    def test_missing_binding_id_fails(self):
        self.assertIn("missing binding id", validate_reasoning_context_binding_candidate(create_empty_reasoning_context_binding_candidate()))

    def test_high_confidence_missing_source_ids_fails(self):
        candidate = self.valid_candidate()
        candidate.confidence = "high"
        findings = validate_reasoning_context_binding_candidate(candidate)
        self.assertIn("missing premise source ids for high-confidence context binding", findings)
        self.assertIn("missing question instruction source ids for high-confidence context binding", findings)
        self.assertIn("missing choice source ids for high-confidence context binding", findings)

    def test_high_confidence_missing_explanation_fails(self):
        candidate = create_empty_reasoning_context_binding_candidate(
            binding_id="ctx:1",
            source_premise_proposition_ids=["prop:p"],
            source_question_instruction_ids=["stmt:q"],
            source_choice_proposition_ids=["prop:c"],
        )
        candidate.confidence = "high"
        self.assertIn("missing human explanation for high-confidence context binding", validate_reasoning_context_binding_candidate(candidate))

    def test_answer_key_use_fails(self):
        candidate = self.valid_candidate()
        candidate.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_reasoning_context_binding_candidate(candidate))

    def test_item_id_authority_fails(self):
        candidate = self.valid_candidate()
        candidate.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_reasoning_context_binding_candidate(candidate))

    def test_answer_position_bias_fails(self):
        candidate = self.valid_candidate()
        candidate.anti_gaming.uses_answer_position_bias = True
        self.assertIn("answer-position bias is forbidden", validate_reasoning_context_binding_candidate(candidate))

    def test_raw_benchmark_storage_fails(self):
        candidate = self.valid_candidate()
        candidate.legibility.stores_raw_benchmark_text = True
        self.assertIn("raw benchmark storage by default is forbidden", validate_reasoning_context_binding_candidate(candidate))

    def test_benchmark_specific_tuning_fails(self):
        candidate = self.valid_candidate()
        candidate.anti_gaming.benchmark_specific_tuning = True
        self.assertIn("benchmark-specific tuning is forbidden", validate_reasoning_context_binding_candidate(candidate))

    def test_answer_selection_enabled_fails(self):
        candidate = self.valid_candidate()
        candidate.anti_gaming.no_answer_selection = False
        self.assertIn("answer selection must remain disabled", validate_reasoning_context_binding_candidate(candidate))

    def test_official_score_claim_fails(self):
        candidate = self.valid_candidate()
        candidate.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_reasoning_context_binding_candidate(candidate))

    def test_private_symbolic_authority_fails(self):
        candidate = self.valid_candidate()
        candidate.legibility.private_symbolic_authority = True
        self.assertIn("private symbolic authority is forbidden", validate_reasoning_context_binding_candidate(candidate))

    def test_hidden_unsupported_assumptions_fail(self):
        candidate = self.valid_candidate()
        candidate.legibility.hides_unsupported_assumptions = True
        self.assertIn("unsupported assumptions must remain visible", validate_reasoning_context_binding_candidate(candidate))

    def test_to_from_dict_roundtrip_works(self):
        candidate = create_empty_reasoning_context_binding_candidate(
            binding_id="ctx:1",
            source_premise_proposition_ids=["prop:p"],
            source_question_instruction_ids=["stmt:q"],
            source_choice_proposition_ids=["prop:c"],
            question_target_type="must_be_true",
            premise_context_type="conditional_rule",
            choice_target_role="candidate_conclusion",
            expected_reasoning_relation="apply_condition",
            candidate_support_role="supports_target",
        )
        candidate.human_explanation = "Redacted context binding."
        data = reasoning_context_binding_candidate_to_dict(candidate)
        restored = reasoning_context_binding_candidate_from_dict(data)
        self.assertEqual(data, reasoning_context_binding_candidate_to_dict(restored))

    def test_summary_is_redacted(self):
        candidate = self.valid_candidate()
        candidate.source_premise_proposition_ids = ["premise_secret"]
        candidate.source_question_instruction_ids = ["question_secret"]
        candidate.source_choice_proposition_ids = ["choice_secret"]
        summary = summarize_reasoning_context_binding_candidate(candidate)
        self.assertEqual(1, summary["premise_source_count"])
        self.assertNotIn("source_premise_proposition_ids", summary)
        self.assertNotIn("source_question_instruction_ids", summary)
        self.assertNotIn("source_choice_proposition_ids", summary)

    def test_summary_does_not_contain_raw_question_choice_answer_key_correct_answer_raw_text(self):
        summary_text = str(summarize_reasoning_context_binding_candidate(self.valid_candidate())).lower()
        for forbidden in ["raw_question", "raw_choice", "answer_key", "correct_answer", "raw_text"]:
            self.assertNotIn(forbidden, summary_text)

    def test_existing_teaching_spine_schema_test_file_exists(self):
        self.assertTrue((ROOT / "weslr/tests/test_logic_teaching_spine_schema_v1.py").exists())

    def test_context_binding_design_test_file_exists(self):
        self.assertTrue((ROOT / "weslr/tests/test_premise_question_choice_context_binding_design_v1.py").exists())

    def test_no_forbidden_files_changed(self):
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        changed = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
