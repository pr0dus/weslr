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
    PropositionAntiGamingRecord,
    PropositionLegibilityRecord,
    create_teaching_explanation_from_proof_step,
    proof_step_from_dict,
    proof_step_to_dict,
    summarize_teaching_explanation,
    summarize_teaching_explanation_generation_diagnostics,
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
    "weslr/tests/test_teaching_explanation_helpers_v1.py",
    "weslr/tests/test_synthetic_proof_step_helpers_v1.py",
    "weslr/tests/test_teaching_explanation_fallacy_mapping_helpers_v1.py",
}


class TeachingExplanationFallacyMappingHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only && git ls-files --others --exclude-standard"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def proof_step(self, *, form_label: str = "affirming_consequent", fallacy_shaped: bool = True, support_assessment: str = "fallacy_shaped", **kwargs) -> ProofStep:
        data = {
            "proof_step_id": "proof_step:fallacy",
            "source_candidate_id": "candidate:fallacy",
            "source_context_binding_ids": ["ctx:fallacy"],
            "source_premise_proposition_ids": ["premise:conditional", "premise:asserted"],
            "source_choice_proposition_ids": ["choice:target"],
            "reasoning_relation": "apply_condition",
            "inference_pattern": form_label,
            "support_status": "unsupported" if fallacy_shaped else "rule_application_supported",
            "source_proposition_ids": ["premise:conditional", "premise:asserted"],
            "target_proposition_id": "choice:target",
            "inference_pattern_id": form_label,
            "warrant": "Helper-only structural warrant; not answer selection and not a benchmark truth claim.",
            "validity_status": "unknown",
            "conditional_form_mapping": {
                "origin": "pipeline_derived_mapping",
                "form_label": form_label,
                "support_assessment": support_assessment,
                "fallacy_shaped": fallacy_shaped,
                "supported_form": not fallacy_shaped,
                "unsupported_gaps": [],
            },
            "conditional_form_mapping_origin": "pipeline_derived_mapping",
            "confidence": "low",
            "human_explanation": "Redacted structural proof step only.",
            "unsupported_gaps": ["recognized_fallacy_shaped_pattern"] if fallacy_shaped else [],
            "unsupported_assumptions": ["recognized_fallacy_shaped_pattern"] if fallacy_shaped else [],
        }
        data.update(kwargs)
        return ProofStep(**data)

    def explanation_text(self, explanation) -> str:
        return " ".join(
            [
                explanation.core_claim,
                explanation.why_it_follows_or_fails,
                explanation.uncertainty_note,
                " ".join(explanation.step_by_step_explanation),
                str(summarize_teaching_explanation(explanation)),
            ]
        ).lower()

    def test_affirming_consequent_mapping_populates_fallacy_name_after_dict_round_trip(self):
        restored = proof_step_from_dict(proof_step_to_dict(self.proof_step(form_label="affirming_consequent")))
        explanation = create_teaching_explanation_from_proof_step(restored, teaching_mode="academic")
        self.assertEqual("affirming the consequent", explanation.fallacy_name)
        self.assertIn("This has the structure of affirming the consequent.", explanation.step_by_step_explanation)

    def test_denying_antecedent_mapping_populates_fallacy_name_after_dict_round_trip(self):
        restored = proof_step_from_dict(proof_step_to_dict(self.proof_step(form_label="denying_antecedent")))
        explanation = create_teaching_explanation_from_proof_step(restored, teaching_mode="academic")
        self.assertEqual("denying the antecedent", explanation.fallacy_name)
        self.assertIn("This has the structure of denying the antecedent.", explanation.step_by_step_explanation)

    def test_fallacy_explanation_without_answer_selection_truth_soundness_or_score_claim(self):
        explanation = create_teaching_explanation_from_proof_step(self.proof_step(), teaching_mode="beginner")
        summary = summarize_teaching_explanation_generation_diagnostics([explanation])
        text = self.explanation_text(explanation)
        self.assertFalse(summary["answer_selection_enabled"])
        self.assertFalse(summary["truth_claim_made"])
        self.assertFalse(summary["official_score_claimed"])
        self.assertNotIn("correct", text)
        self.assertNotIn("incorrect", text)
        self.assertNotIn("sound", text)
        self.assertNotIn("official score", text)

    def test_unsupported_gaps_remain_visible(self):
        explanation = create_teaching_explanation_from_proof_step(self.proof_step(), teaching_mode="technical")
        self.assertIn("recognized_fallacy_shaped_pattern", explanation.unsupported_gaps)
        self.assertIn("Unsupported or ambiguous gaps remain visible.", explanation.step_by_step_explanation)

    def test_non_fallacy_supported_form_does_not_get_fallacy_name(self):
        explanation = create_teaching_explanation_from_proof_step(
            self.proof_step(
                form_label="modus_ponens",
                fallacy_shaped=False,
                support_assessment="supported_form",
                support_status="rule_application_supported",
                unsupported_gaps=[],
                unsupported_assumptions=[],
            ),
            teaching_mode="technical",
        )
        self.assertEqual("", explanation.fallacy_name)
        self.assertEqual("", explanation.common_fallacy)

    def test_counterexample_explanation_still_works(self):
        explanation = create_teaching_explanation_from_proof_step(
            self.proof_step(
                form_label="modus_tollens",
                fallacy_shaped=False,
                support_assessment="supported_form",
                support_status="counterexample_supported",
                requires_counterexample=True,
            ),
            teaching_mode="technical",
        )
        self.assertTrue(explanation.counterexample_note)


    def test_source_safety_flags_are_not_laundered(self):
        step = self.proof_step()
        step.anti_gaming = PropositionAntiGamingRecord(uses_answer_key=True, no_answer_selection=False)
        step.legibility = PropositionLegibilityRecord(stores_raw_benchmark_text=True, redacted_summary_only=False)
        explanation = create_teaching_explanation_from_proof_step(step, teaching_mode="technical")
        summary = summarize_teaching_explanation_generation_diagnostics([explanation])
        self.assertTrue(explanation.anti_gaming.uses_answer_key)
        self.assertFalse(explanation.anti_gaming.no_answer_selection)
        self.assertTrue(explanation.legibility.stores_raw_benchmark_text)
        self.assertFalse(summary["anti_gaming_safe"])
        self.assertFalse(summary["legibility_safe"])

    def test_fallacy_and_unsupported_confidence_is_conservative(self):
        explanation = create_teaching_explanation_from_proof_step(self.proof_step(confidence="high"), teaching_mode="technical")
        self.assertEqual("low", explanation.confidence)

    def test_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
