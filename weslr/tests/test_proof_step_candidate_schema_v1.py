from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    ProofStepCandidate,
    create_empty_proof_step_candidate,
    proof_step_candidate_from_dict,
    proof_step_candidate_to_dict,
    summarize_proof_step_candidate,
    validate_proof_step_candidate,
)


ALLOWED_CANDIDATE_TYPES = [
    "support_step_candidate",
    "contradiction_step_candidate",
    "counterexample_step_candidate",
    "rule_application_candidate",
    "invalidity_test_candidate",
    "template_completion_candidate",
    "unsupported_step_candidate",
]
ALLOWED_SUPPORT_STATUSES = [
    "candidate_only",
    "insufficient_support",
    "ambiguous",
    "unsupported",
    "unknown",
]
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
    "weslr/tests/test_logic_teaching_spine_schema_v1.py",
    "weslr/tests/test_proof_step_candidate_schema_v1.py",
}


class ProofStepCandidateSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def test_schema_imports(self):
        self.assertIsNotNone(ProofStepCandidate)
        self.assertTrue(callable(create_empty_proof_step_candidate))

    def test_empty_candidate_instantiates(self):
        candidate = create_empty_proof_step_candidate(candidate_id="proof-step-candidate:1")
        self.assertEqual("proof-step-candidate:1", candidate.candidate_id)
        self.assertEqual("unsupported_step_candidate", candidate.candidate_type)
        self.assertEqual("unknown", candidate.support_status)
        self.assertEqual("low", candidate.confidence)

    def test_safe_anti_gaming_defaults(self):
        candidate = create_empty_proof_step_candidate()
        self.assertFalse(candidate.anti_gaming.uses_answer_key)
        self.assertFalse(candidate.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(candidate.anti_gaming.uses_answer_position_bias)
        self.assertFalse(candidate.anti_gaming.claims_official_score)
        self.assertFalse(candidate.anti_gaming.benchmark_specific_tuning)
        self.assertFalse(candidate.anti_gaming.uses_private_symbolic_authority)
        self.assertTrue(candidate.anti_gaming.no_answer_selection)

    def test_safe_legibility_defaults(self):
        candidate = create_empty_proof_step_candidate()
        self.assertTrue(candidate.legibility.human_translation_available)
        self.assertTrue(candidate.legibility.redacted_summary_only)
        self.assertFalse(candidate.legibility.stores_raw_benchmark_text)
        self.assertFalse(candidate.legibility.hides_unsupported_assumptions)
        self.assertFalse(candidate.legibility.private_symbolic_authority)

    def test_all_allowed_candidate_types_validate(self):
        for candidate_type in ALLOWED_CANDIDATE_TYPES:
            candidate = create_empty_proof_step_candidate(
                candidate_id=f"candidate:{candidate_type}",
                candidate_type=candidate_type,
            )
            self.assertNotIn("invalid candidate type", validate_proof_step_candidate(candidate))

    def test_all_allowed_support_statuses_validate(self):
        for support_status in ALLOWED_SUPPORT_STATUSES:
            candidate = create_empty_proof_step_candidate(
                candidate_id=f"candidate:{support_status}",
                support_status=support_status,
            )
            self.assertNotIn("invalid support status", validate_proof_step_candidate(candidate))

    def test_invalid_candidate_type_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1", candidate_type="proof")
        self.assertIn("invalid candidate type", validate_proof_step_candidate(candidate))

    def test_invalid_support_status_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1", support_status="proven")
        self.assertIn("invalid support status", validate_proof_step_candidate(candidate))

    def test_invalid_confidence_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.confidence = "certain"
        self.assertIn("invalid confidence", validate_proof_step_candidate(candidate))

    def test_missing_candidate_id_fails(self):
        self.assertIn("missing candidate id", validate_proof_step_candidate(create_empty_proof_step_candidate()))

    def test_high_confidence_missing_context_binding_ids_fails(self):
        candidate = create_empty_proof_step_candidate(
            candidate_id="candidate:1",
            source_premise_proposition_ids=["premise:1"],
            source_choice_proposition_ids=["choice:1"],
        )
        candidate.confidence = "high"
        candidate.human_explanation = "Human-legible candidate hypothesis only."
        self.assertIn("missing context binding ids for high-confidence proof step candidate", validate_proof_step_candidate(candidate))

    def test_high_confidence_missing_proposition_ids_fails(self):
        candidate = create_empty_proof_step_candidate(
            candidate_id="candidate:1",
            source_context_binding_ids=["binding:1"],
        )
        candidate.confidence = "high"
        candidate.human_explanation = "Human-legible candidate hypothesis only."
        self.assertIn("missing premise/choice proposition ids for high-confidence proof step candidate", validate_proof_step_candidate(candidate))

    def test_high_confidence_missing_explanation_fails(self):
        candidate = create_empty_proof_step_candidate(
            candidate_id="candidate:1",
            source_context_binding_ids=["binding:1"],
            source_premise_proposition_ids=["premise:1"],
            source_choice_proposition_ids=["choice:1"],
        )
        candidate.confidence = "high"
        self.assertIn("missing human explanation for high-confidence proof step candidate", validate_proof_step_candidate(candidate))

    def test_answer_key_use_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_proof_step_candidate(candidate))

    def test_item_id_authority_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_proof_step_candidate(candidate))

    def test_answer_position_bias_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.anti_gaming.uses_answer_position_bias = True
        self.assertIn("answer-position bias is forbidden", validate_proof_step_candidate(candidate))

    def test_raw_benchmark_storage_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.legibility.stores_raw_benchmark_text = True
        self.assertIn("raw benchmark storage by default is forbidden", validate_proof_step_candidate(candidate))

    def test_benchmark_specific_tuning_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.anti_gaming.benchmark_specific_tuning = True
        self.assertIn("benchmark-specific tuning is forbidden", validate_proof_step_candidate(candidate))

    def test_answer_selection_enabled_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.anti_gaming.no_answer_selection = False
        self.assertIn("answer selection must remain disabled", validate_proof_step_candidate(candidate))

    def test_official_score_claim_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_proof_step_candidate(candidate))

    def test_private_symbolic_authority_fails(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.legibility.private_symbolic_authority = True
        self.assertIn("private symbolic authority is forbidden", validate_proof_step_candidate(candidate))

    def test_hidden_unsupported_assumptions_fail(self):
        candidate = create_empty_proof_step_candidate(candidate_id="candidate:1")
        candidate.legibility.hides_unsupported_assumptions = True
        self.assertIn("unsupported assumptions must remain visible", validate_proof_step_candidate(candidate))

    def test_to_from_dict_roundtrip_works(self):
        candidate = create_empty_proof_step_candidate(
            candidate_id="candidate:1",
            source_context_binding_ids=["binding:1"],
            source_premise_proposition_ids=["premise:1"],
            source_choice_proposition_ids=["choice:1"],
            candidate_type="support_step_candidate",
            expected_reasoning_relation="support",
            inference_pattern_hint="weak structural hint",
            support_status="candidate_only",
        )
        candidate.confidence = "medium"
        candidate.unsupported_gaps = ["gap:1"]
        candidate.human_explanation = "Structured hypothesis only; not proof."
        data = proof_step_candidate_to_dict(candidate)
        restored = proof_step_candidate_from_dict(data)
        self.assertEqual(data, proof_step_candidate_to_dict(restored))

    def test_summary_is_redacted(self):
        candidate = create_empty_proof_step_candidate(
            candidate_id="candidate:1",
            source_context_binding_ids=["binding:secret"],
            source_premise_proposition_ids=["premise:secret"],
            source_choice_proposition_ids=["choice:secret"],
            candidate_type="support_step_candidate",
        )
        candidate.human_explanation = "Hidden raw explanation"
        candidate.unsupported_gaps = ["hidden raw gap"]
        summary = summarize_proof_step_candidate(candidate)
        self.assertEqual("candidate:1", summary["candidate_id"])
        self.assertEqual(1, summary["context_binding_source_count"])
        self.assertEqual(1, summary["premise_proposition_source_count"])
        self.assertEqual(1, summary["target_proposition_source_count"])
        self.assertNotIn("source_context_binding_ids", summary)
        self.assertNotIn("source_premise_proposition_ids", summary)
        self.assertNotIn("source_choice_proposition_ids", summary)
        self.assertNotIn("human_explanation", summary)
        self.assertNotIn("unsupported_gaps", summary)

    def test_summary_does_not_contain_forbidden_raw_fields(self):
        summary_text = str(summarize_proof_step_candidate(create_empty_proof_step_candidate(candidate_id="candidate:1"))).lower()
        for forbidden in ["question", "choice", "answer_key", "correct_answer", "raw_text", "official_score"]:
            self.assertNotIn(forbidden, summary_text)

    def test_design_test_still_passes(self):
        design_doc = ROOT / "docs" / "WESLR_PROOF_STEP_CANDIDATE_DESIGN_V1.md"
        text = design_doc.read_text(encoding="utf-8")
        self.assertIn("WESLR Proof-Step Candidate Design V1", text)
        self.assertIn("design_only", text)
        self.assertIn("APPROVE_PROOF_STEP_CANDIDATE_SCHEMA_ONLY", text)

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
        self.assertTrue(changed.issubset(ALLOWED_CHANGED), f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
