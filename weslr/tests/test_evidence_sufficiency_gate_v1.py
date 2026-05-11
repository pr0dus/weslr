from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.evidence_sufficiency_gate import (  # noqa: E402
    BROADEN_EVAL_BEFORE_CODE,
    DESIGN_FIRST,
    IMPLEMENT_GENERAL_PATTERN,
    INSUFFICIENT_EVIDENCE_STOP,
    STOP_RABBIT_HOLE,
    EvidenceSufficiencyDecision,
    EvidenceSufficiencyInput,
    ImprovementProposalCandidate,
    build_formal_logic_dev5_gate_input,
    create_default_evidence_sufficiency_policy,
    decide_evidence_sufficiency,
    evidence_sufficiency_decision_to_dict,
)

DOC = ROOT / "docs" / "WESLR_EVIDENCE_SUFFICIENCY_GATE_V1.md"
REPORT = Path("/data/data/com.termux/files/home/weslr-local/public_subset_results/mmlu_formal_logic_dev5_v1.term_alignment_diagnosis_v1.json")


class EvidenceSufficiencyGateV1Tests(unittest.TestCase):
    def _base_input(self, **overrides):
        data = dict(
            source_report_id="report-1",
            source_eval="internal_eval",
            domain="formal_logic",
            required_skill="formal_logic_reasoning",
            sample_size=24,
            failure_count=8,
            repeated_failure_count=3,
            distinct_subset_count=2,
            official_score=False,
            internal_eval=True,
            sample_only=False,
            observed_failure_modes=["term_alignment_gap"],
            bottleneck_counts={"term_alignment_possible": 3},
            support_metrics={"total_premises": 24},
            safety_flags={},
            provenance={"source": "test"},
            target_substrate="internal_reasoning_graph",
            new_architecture_required=False,
        )
        data.update(overrides)
        return EvidenceSufficiencyInput(**data)

    def test_default_policy_is_conservative(self):
        policy = create_default_evidence_sufficiency_policy()
        self.assertEqual(policy.min_sample_size_for_code_change, 20)
        self.assertEqual(policy.min_distinct_subsets_for_code_change, 2)
        self.assertTrue(policy.require_repeated_pattern)
        self.assertTrue(policy.block_official_score_claim)
        self.assertTrue(policy.block_answer_key_use)
        self.assertTrue(policy.block_item_id_use)
        self.assertTrue(policy.block_raw_benchmark_storage)
        self.assertTrue(policy.block_benchmark_specific_tuning)
        self.assertTrue(policy.require_operator_review)
        self.assertTrue(policy.require_design_first_for_new_architecture)

    def test_decision_defaults_require_operator_review(self):
        decision = EvidenceSufficiencyDecision()
        self.assertTrue(decision.operator_review_required)

    def test_decision_defaults_execution_allowed_false(self):
        decision = EvidenceSufficiencyDecision()
        self.assertFalse(decision.execution_allowed)

    def test_official_score_true_triggers_stop_rabbit_hole(self):
        decision = decide_evidence_sufficiency(self._base_input(official_score=True))
        self.assertEqual(decision.decision_label, STOP_RABBIT_HOLE)

    def test_answer_key_flag_triggers_stop_rabbit_hole(self):
        decision = decide_evidence_sufficiency(self._base_input(safety_flags={"uses_answer_key": True}))
        self.assertEqual(decision.decision_label, STOP_RABBIT_HOLE)

    def test_item_id_flag_triggers_stop_rabbit_hole(self):
        decision = decide_evidence_sufficiency(self._base_input(safety_flags={"uses_item_id": True}))
        self.assertEqual(decision.decision_label, STOP_RABBIT_HOLE)

    def test_raw_benchmark_storage_flag_triggers_stop_rabbit_hole(self):
        decision = decide_evidence_sufficiency(self._base_input(safety_flags={"stores_raw_benchmark_data": True}))
        self.assertEqual(decision.decision_label, STOP_RABBIT_HOLE)

    def test_benchmark_specific_tuning_flag_triggers_stop_rabbit_hole(self):
        decision = decide_evidence_sufficiency(self._base_input(safety_flags={"benchmark_specific_tuning_detected": True}))
        self.assertEqual(decision.decision_label, STOP_RABBIT_HOLE)

    def test_sample_size_five_triggers_broaden_eval_before_code(self):
        decision = decide_evidence_sufficiency(self._base_input(sample_size=5))
        self.assertEqual(decision.decision_label, BROADEN_EVAL_BEFORE_CODE)

    def test_distinct_subset_count_one_triggers_broaden_eval_before_code(self):
        decision = decide_evidence_sufficiency(self._base_input(distinct_subset_count=1))
        self.assertEqual(decision.decision_label, BROADEN_EVAL_BEFORE_CODE)

    def test_no_repeated_pattern_triggers_insufficient_evidence_stop(self):
        decision = decide_evidence_sufficiency(self._base_input(repeated_failure_count=1))
        self.assertEqual(decision.decision_label, INSUFFICIENT_EVIDENCE_STOP)

    def test_repeated_architecture_gap_triggers_design_first(self):
        decision = decide_evidence_sufficiency(
            self._base_input(new_architecture_required=True, repeated_failure_count=4)
        )
        self.assertEqual(decision.decision_label, DESIGN_FIRST)
        self.assertIsNotNone(decision.proposal_candidate)

    def test_sufficient_repeated_general_pattern_triggers_implement_general_pattern(self):
        decision = decide_evidence_sufficiency(self._base_input())
        self.assertEqual(decision.decision_label, IMPLEMENT_GENERAL_PATTERN)
        self.assertIsNotNone(decision.proposal_candidate)

    def test_formal_logic_dev5_redacted_report_maps_to_broaden_eval_before_code(self):
        self.assertTrue(REPORT.exists())
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        gate_input = build_formal_logic_dev5_gate_input(report)
        decision = decide_evidence_sufficiency(gate_input)
        self.assertEqual(gate_input.sample_size, 5)
        self.assertEqual(gate_input.distinct_subset_count, 1)
        self.assertEqual(decision.decision_label, BROADEN_EVAL_BEFORE_CODE)

    def test_broaden_decision_forbids_code_change_threshold_tuning_benchmark_specific_patch(self):
        decision = decide_evidence_sufficiency(self._base_input(sample_size=5))
        self.assertIn("code_change", decision.forbidden_next_actions)
        self.assertIn("threshold_tuning", decision.forbidden_next_actions)
        self.assertIn("benchmark_specific_patch", decision.forbidden_next_actions)

    def test_proposal_candidate_never_has_execution_allowed_true(self):
        decision = decide_evidence_sufficiency(self._base_input())
        self.assertIsInstance(decision.proposal_candidate, ImprovementProposalCandidate)
        self.assertFalse(decision.proposal_candidate.execution_allowed)

    def test_decision_to_dict_works(self):
        decision = decide_evidence_sufficiency(self._base_input())
        data = evidence_sufficiency_decision_to_dict(decision)
        self.assertEqual(data["decision_label"], IMPLEMENT_GENERAL_PATTERN)
        self.assertIn("proposal_candidate", data)

    def test_docs_exist_and_contain_required_phrases(self):
        self.assertTrue(DOC.exists())
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "BROADEN_EVAL_BEFORE_CODE",
            "STOP_RABBIT_HOLE",
            "operator_review_required",
            "execution_allowed = false",
            "no official-score claim",
            "no answer-key use",
            "no item-id authority",
            "no benchmark-specific tuning",
        ]:
            self.assertIn(needle, text)

    def test_no_runtime_behavior_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("docs/WESLR_EVIDENCE_SUFFICIENCY_GATE_V1.md", changed)
        self.assertIn("weslr/evidence_sufficiency_gate.py", changed)
        self.assertIn("weslr/tests/test_evidence_sufficiency_gate_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
