from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs" / "WESLR_LOGIC_TEACHING_SPINE_CONNECTIVITY_CONTRACT_V1.md"
FORBIDDEN_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/logical_form_normalizer.py",
    "weslr/formal_logic_parser.py",
    "weslr/formal_logic_solver.py",
    "weslr/mcq_answer_formatting.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "docs/WESLR_LOGIC_TEACHING_SPINE_CONNECTIVITY_CONTRACT_V1.md",
    "weslr/tests/test_logic_teaching_spine_connectivity_contract_v1.py",
}


class LogicTeachingSpineConnectivityContractV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_contains_connectivity_contract(self):
        self.assertIn("connectivity_contract", self.text)

    def test_contains_execution_allowed_false(self):
        self.assertIn("execution_allowed = false", self.text)

    def test_contains_official_score_claimed_false(self):
        self.assertIn("official_score_claimed = false", self.text)

    def test_contains_canonical_flow(self):
        self.assertIn("PredicateCandidate\n→ PropositionCandidate\n→ InferencePattern\n→ ProofStep\n→ CounterexampleCandidate\n→ TeachingExplanation", self.text)

    def test_contains_predicatecandidate_feeds_only_propositioncandidate_directly(self):
        self.assertIn("PredicateCandidate feeds only PropositionCandidate directly", self.text)

    def test_contains_source_predicate_ids(self):
        self.assertIn("PropositionCandidate.source_predicate_ids", self.text)

    def test_contains_inferencepattern_reusable_typed_reasoning_template(self):
        self.assertIn("InferencePattern is a reusable typed reasoning template", self.text)

    def test_contains_proofstep_source_proposition_ids(self):
        self.assertIn("ProofStep.source_proposition_ids", self.text)

    def test_contains_proofstep_target_proposition_id(self):
        self.assertIn("ProofStep.target_proposition_id", self.text)

    def test_contains_proofstep_inference_pattern_id(self):
        self.assertIn("ProofStep.inference_pattern_id", self.text)

    def test_contains_challenged_proposition_id(self):
        self.assertIn("challenged_proposition_id", self.text)

    def test_contains_challenged_proof_step_id(self):
        self.assertIn("challenged_proof_step_id", self.text)

    def test_contains_teachingexplanation_as_view_layer(self):
        self.assertIn("TeachingExplanation is a view layer", self.text)

    def test_contains_all_six_design_doctrine_principles(self):
        for line in [
            "Predicates are structural atoms for claims.",
            "Propositions are claim units.",
            "Inference patterns are reusable reasoning forms.",
            "Proof steps are concrete reasoning applications.",
            "Counterexamples are concrete failure witnesses.",
            "Teaching explanations are human-facing summaries.",
        ]:
            self.assertIn(line, self.text)

    def test_forbids_answer_key_use(self):
        self.assertIn("must not use answer keys", self.text)

    def test_forbids_item_id_authority(self):
        self.assertIn("must not use item IDs as authority", self.text)

    def test_forbids_parser_changes(self):
        self.assertIn("no parser changes", self.text)

    def test_forbids_solver_changes(self):
        self.assertIn("no solver changes", self.text)

    def test_forbids_mcq_adapter_changes(self):
        self.assertIn("no MCQ adapter changes", self.text)

    def test_forbids_runtime_changes(self):
        self.assertIn("no runtime changes", self.text)

    def test_forbids_answer_selection(self):
        self.assertIn("no answer selection", self.text)

    def test_contains_predicatecandidate_to_propositioncandidate_helper_diagnostics_only(self):
        self.assertIn("PredicateCandidate → PropositionCandidate helper diagnostics only", self.text)

    def test_contains_operator_decision_approve(self):
        self.assertIn("APPROVE_PROPOSITION_HELPERS_ONLY", self.text)

    def test_no_forbidden_implementation_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertTrue(changed.issubset(ALLOWED_CHANGED))


if __name__ == "__main__":
    unittest.main()
