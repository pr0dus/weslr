from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOC = ROOT / "docs" / "WESLR_UNIFIED_REASONING_TASK_SCHEMA_V1.md"


class UnifiedReasoningTaskSchemaDesignV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_document_exists(self):
        self.assertTrue(DOC.exists())

    def test_contains_canonical_name_reasoning_task(self):
        self.assertIn("`ReasoningTask`", self.text)
        self.assertIn("canonical name", self.lower)

    def test_contains_structured_reasoning_request_as_alternative_term(self):
        self.assertIn("StructuredReasoningRequest", self.text)

    def test_contains_required_top_level_fields(self):
        for needle in [
            "schema_version",
            "task_id",
            "task_family",
            "domain",
            "required_skill",
            "provenance",
            "input",
            "parsed",
            "choice_representations",
            "blackboard",
            "solver_plan",
            "arbitration",
            "legibility",
            "anti_gaming",
            "failure",
        ]:
            self.assertIn(f"`{needle}`", self.text)

    def test_contains_provenance_fields(self):
        for needle in [
            "source_eval",
            "dataset_name",
            "subset_name",
            "official_score",
            "internal_eval",
            "sample_only",
            "item_fingerprint",
            "adapter_version",
            "prompt_format_version",
        ]:
            self.assertIn(f"`{needle}`", self.text)

    def test_contains_parsed_fields(self):
        for needle in [
            "task_type",
            "question_intent",
            "premises",
            "conclusion_candidates",
            "constraints",
            "assumptions",
            "entities",
            "relations",
        ]:
            self.assertIn(f"`{needle}`", self.text)

    def test_contains_blackboard_fields(self):
        for needle in [
            "hypotheses",
            "inferences",
            "conflicts",
            "solver_outputs",
        ]:
            self.assertIn(f"`{needle}`", self.text)

    def test_contains_solver_plan_fields(self):
        for needle in [
            "candidate_solvers",
            "selected_solvers",
            "blocked_solvers",
        ]:
            self.assertIn(f"`{needle}`", self.text)

    def test_contains_arbitration_fields(self):
        for needle in [
            "selected_answer",
            "confidence",
            "uncertainty",
            "conflict_status",
            "why_selected",
            "why_rejected",
        ]:
            self.assertIn(f"`{needle}`", self.text)

    def test_contains_legibility_fields(self):
        for needle in [
            "human_explanation",
            "reasoning_trace_summary",
            "symbolic_forms_translated",
            "private_authority_used",
        ]:
            self.assertIn(f"`{needle}`", self.text)

    def test_contains_anti_gaming_fields(self):
        for needle in [
            "uses_item_id",
            "uses_answer_key",
            "uses_answer_position_bias",
            "stores_raw_question_by_default",
            "official_score_claimed",
        ]:
            self.assertIn(f"`{needle}`", self.text)

    def test_contains_failure_fields(self):
        for needle in [
            "failure_mode",
            "missing_skill",
            "target_substrate",
            "enrichment_record_allowed",
        ]:
            self.assertIn(f"`{needle}`", self.text)

    def test_contains_formal_logic_mapping(self):
        for needle in [
            "formal logic mapping",
            "valid/invalid inference",
            "contradiction",
            "consistency",
            "symbolic translation",
        ]:
            self.assertIn(needle, self.lower)

    def test_contains_ethics_tradeoff_mapping(self):
        for needle in [
            "ethics/tradeoff mapping",
            "stakeholders become `entities`",
            "duties/rights/governance become `constraints`",
            "values/tradeoffs become `relations`",
            "option impacts become `choice_representations`",
        ]:
            self.assertIn(needle.lower(), self.lower)

    def test_contains_existing_substrate_mapping(self):
        for needle in [
            "internal_reasoning_graph",
            "concept_graph",
            "capability_registry",
            "eval_scorecard",
            "meaning/response-obligation",
            "MCQ adapter = input/output shell, not reasoning core",
        ]:
            self.assertIn(needle.lower(), self.lower)

    def test_states_subject_scorers_are_helpers_not_central_intelligence(self):
        self.assertIn("subject scorers are helpers, not central intelligence", self.lower)

    def test_contains_future_implementation_phases(self):
        for needle in [
            "A. schema dataclasses only",
            "B. ReasoningTrace schema",
            "C. solver registry",
            "D. arbitrator/conflict detector",
            "E. formal logic solver as first real solver",
            "F. ethics/tradeoff solver migration",
            "G. MCQ adapter calls reasoning engine",
            "H. failure bridge records solver-level failures",
            "I. scorecard compares before/after",
            "J. no official claim",
        ]:
            self.assertIn(needle, self.text)

    def test_rejects_forbidden_phrases(self):
        for phrase in [
            "WESLR has passed MMLU",
            "official MMLU score",
            "leaderboard score",
            "memorize answer keys",
            "answer-key learning",
        ]:
            self.assertNotIn(phrase.lower(), self.lower)


if __name__ == "__main__":
    unittest.main()
