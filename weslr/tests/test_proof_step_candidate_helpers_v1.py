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
    classify_proof_step_candidate_type,
    create_proof_step_candidate_from_context_binding,
    create_proof_step_candidates_from_context_bindings,
    summarize_proof_step_candidate_diagnostics,
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
