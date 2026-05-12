from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    PropositionCandidate,
    classify_choice_target_role,
    classify_premise_context_type,
    classify_question_target_type,
    create_reasoning_context_binding_candidate_from_structures,
    summarize_reasoning_context_binding_diagnostics,
)


class Record:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


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
    "weslr/tests/test_reasoning_context_binding_schema_v1.py",
    "weslr/tests/test_reasoning_context_binding_helpers_v1.py",
}


def premise_prop(pid: str = "premise:1", relation: str = "if then") -> PropositionCandidate:
    return PropositionCandidate(
        proposition_id=pid,
        proposition_role="premise",
        relation=relation,
        relation_canonical_hint=relation,
        human_translation="redacted premise",
    )


def choice_prop(pid: str = "choice:1", relation: str = "supports") -> PropositionCandidate:
    return PropositionCandidate(
        proposition_id=pid,
        proposition_role="choice_claim",
        relation=relation,
        relation_canonical_hint=relation,
        human_translation="redacted candidate conclusion",
    )


class ReasoningContextBindingHelpersV1Tests(unittest.TestCase):
    def test_classifier_detects_must_be_true(self):
        self.assertEqual("must_be_true", classify_question_target_type(Record(normalized_text="must be true")))

    def test_classifier_detects_must_be_false(self):
        self.assertEqual("must_be_false", classify_question_target_type(Record(normalized_text="must be false")))

    def test_classifier_detects_follows(self):
        self.assertEqual("follows", classify_question_target_type(Record(normalized_text="what follows")))

    def test_classifier_detects_does_not_follow(self):
        self.assertEqual("does_not_follow", classify_question_target_type(Record(normalized_text="does not follow")))

    def test_classifier_detects_valid_argument(self):
        self.assertEqual("valid_argument", classify_question_target_type(Record(normalized_text="valid argument")))

    def test_classifier_detects_counterexample(self):
        self.assertEqual("counterexample", classify_question_target_type(Record(normalized_text="identify counterexample")))

    def test_classifier_detects_invalid_argument(self):
        self.assertEqual("invalid_argument", classify_question_target_type(Record(normalized_text="invalid argument")))

    def test_classifier_detects_completion(self):
        self.assertEqual("completion", classify_question_target_type(Record(normalized_text="complete the template")))

    def test_premise_classifier_detects_conditional_rule(self):
        self.assertEqual("conditional_rule", classify_premise_context_type([premise_prop(relation="if then")]))

    def test_premise_classifier_detects_quantified_rule(self):
        self.assertEqual("quantified_rule", classify_premise_context_type([premise_prop(relation="all")]))

    def test_premise_classifier_detects_exclusion_rule(self):
        self.assertEqual("exclusion_rule", classify_premise_context_type([premise_prop(relation="not")]))

    def test_premise_classifier_detects_mixed_context(self):
        self.assertEqual("mixed_context", classify_premise_context_type([premise_prop(relation="if then"), premise_prop(pid="premise:2", relation="all")]))

    def test_premise_classifier_detects_definition_like_context(self):
        self.assertEqual("definition_like", classify_premise_context_type([premise_prop(relation="defines")]))

    def test_premise_classifier_detects_given_fact_context(self):
        self.assertEqual("given_fact", classify_premise_context_type([premise_prop(relation="supports")]))

    def test_context_binding_preserves_statement_ref_when_premise_proposition_id_missing(self):
        candidate = create_reasoning_context_binding_candidate_from_structures(
            binding_id="ctx:statement-ref",
            premise_propositions=[Record(statement_id="stmt:p1", normalized_text="if p then q")],
            question_instruction_records=[Record(statement_id="question:provided", normalized_text="what follows")],
            choice_propositions=[choice_prop(pid="choice:provided")],
        )
        self.assertIn("premise_statement:stmt:p1", candidate.source_premise_proposition_ids)

    def test_choice_classifier_detects_candidate_conclusion(self):
        self.assertEqual("candidate_conclusion", classify_choice_target_role(choice_prop()))

    def test_choice_classifier_detects_candidate_counterexample(self):
        self.assertEqual(
            "candidate_counterexample",
            classify_choice_target_role(choice_prop(relation="lacks"), Record(normalized_text="counterexample")),
        )

    def test_context_binding_candidate_preserves_premise_ids(self):
        candidate = self._candidate()
        self.assertEqual(["premise:1"], candidate.source_premise_proposition_ids)

    def test_context_binding_candidate_preserves_question_ids(self):
        candidate = self._candidate()
        self.assertEqual(["question:1"], candidate.source_question_instruction_ids)

    def test_context_binding_candidate_preserves_choice_ids(self):
        candidate = self._candidate()
        self.assertEqual(["choice:1"], candidate.source_choice_proposition_ids)

    def test_context_binding_keeps_unsupported_gaps_visible(self):
        candidate = create_reasoning_context_binding_candidate_from_structures(binding_id="ctx:gap")
        self.assertTrue(candidate.unsupported_gaps)
        self.assertFalse(candidate.legibility.hides_unsupported_assumptions)

    def test_context_binding_does_not_select_answers(self):
        self.assertTrue(self._candidate().anti_gaming.no_answer_selection)

    def test_context_binding_does_not_claim_truth(self):
        candidate = self._candidate()
        self.assertNotIn("truth", candidate.human_explanation.lower())
        self.assertNotIn("true", candidate.human_explanation.lower())

    def test_context_binding_does_not_use_answer_key(self):
        self.assertFalse(self._candidate().anti_gaming.uses_answer_key)

    def test_context_binding_does_not_use_item_id_authority(self):
        self.assertFalse(self._candidate().anti_gaming.uses_item_id_as_authority)

    def test_context_binding_preserves_premise_refs_when_provided(self):
        candidate = create_reasoning_context_binding_candidate_from_structures(
            binding_id="ctx:preserve",
            premise_propositions=[premise_prop(pid="premise:provided")],
            question_instruction_records=[Record(statement_id="question:provided", normalized_text="what follows")],
            choice_propositions=[choice_prop(pid="choice:provided")],
        )
        self.assertIn("premise:provided", candidate.source_premise_proposition_ids)

    def test_context_binding_keeps_gap_when_premise_refs_missing(self):
        candidate = create_reasoning_context_binding_candidate_from_structures(
            binding_id="ctx:missing-premise",
            question_instruction_records=[Record(statement_id="question:provided", normalized_text="what follows")],
            choice_propositions=[choice_prop(pid="choice:provided")],
        )
        self.assertIn("missing_premise_proposition_refs", candidate.unsupported_gaps)

    def test_summary_is_redacted(self):
        summary = summarize_reasoning_context_binding_diagnostics([self._candidate()])
        self.assertEqual(1, summary["context_binding_count"])
        text = str(summary).lower()
        for forbidden in ["answer_key", "correct_answer", "raw_text", "source_premise_proposition_ids"]:
            self.assertNotIn(forbidden, text)

    def test_schema_tests_still_pass(self):
        result = subprocess.run(
            ["python3", "weslr/tests/test_reasoning_context_binding_schema_v1.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_gate_and_check_pass(self):
        gate = subprocess.run(
            ["python3", "weslr/tests/release_gate_v1.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(gate.returncode, 0, gate.stdout + gate.stderr)
        check = subprocess.run(
            ["bash", "scripts/weslr_release_check.sh"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_no_forbidden_files_changed(self):
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only && git ls-files --others --exclude-standard"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")

    def _candidate(self):
        return create_reasoning_context_binding_candidate_from_structures(
            binding_id="ctx:1",
            premise_propositions=[premise_prop()],
            question_instruction_records=[Record(statement_id="question:1", normalized_text="what follows")],
            choice_propositions=[choice_prop()],
        )


if __name__ == "__main__":
    unittest.main()
