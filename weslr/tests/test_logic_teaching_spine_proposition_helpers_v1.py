from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    create_proposition_candidate_from_predicate,
    create_proposition_candidates_from_predicates,
    proposition_candidate_to_dict,
    summarize_proposition_projection_diagnostics,
)

FORBIDDEN_CHANGED = {
    "weslr/logical_form_normalizer.py",
    "weslr/formal_logic_parser.py",
    "weslr/formal_logic_solver.py",
    "weslr/mcq_answer_formatting.py",
    "weslr/evals/official_mcq_adapter.py",
}
ALLOWED_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/tests/test_logic_teaching_spine_proposition_helpers_v1.py",
    "weslr/tests/test_logic_teaching_spine_schema_v1.py",
}


@dataclass
class PredicateLike:
    predicate_candidate_id: str = ""
    subject_candidate_id: str = ""
    relation_hint: str = ""
    object_candidate_id: str = ""
    polarity: str = "positive"
    quantifier_hint: str = ""
    modality_hint: str = ""
    confidence: str = "low"


class LogicTeachingSpinePropositionHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        proc = subprocess.run(
            ["bash", "-lc", "git diff --name-only && git diff --cached --name-only"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}

    def run_direct(self, script: str) -> str:
        proc = subprocess.run(["bash", "-lc", script], cwd=str(ROOT), capture_output=True, text=True, check=True)
        return proc.stdout + proc.stderr

    def test_helper_creates_proposition_from_predicate_fields(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            subject="cats",
            relation="supports",
            object="dogs",
        )
        self.assertEqual("proposition:pred:1", proposition.proposition_id)

    def test_proposition_stores_source_predicate_ids(self):
        proposition = create_proposition_candidate_from_predicate(predicate_id="pred:1")
        self.assertEqual(["pred:1"], proposition.source_predicate_ids)

    def test_proposition_uses_subject_relation_object_structurally(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            subject="left",
            relation="is",
            object="right",
        )
        self.assertEqual("left", proposition.subject)
        self.assertEqual("is", proposition.relation)
        self.assertEqual("right", proposition.object)

    def test_helper_creates_conservative_human_translation(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            subject="left",
            relation="supports",
            object="right",
            human_translation="",
        )
        self.assertEqual("left supports right", proposition.human_translation)

    def test_unsupported_gaps_remain_visible(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            subject="left",
            relation="",
            object="right",
            unsupported_gaps=["missing_context"],
        )
        self.assertIn("missing_context", proposition.unsupported_gaps)
        self.assertIn("missing_relation", proposition.unsupported_gaps)

    def test_helper_accepts_dict_like_predicate_input(self):
        propositions = create_proposition_candidates_from_predicates([
            {
                "predicate_candidate_id": "pred:1",
                "subject_candidate_id": "subj:1",
                "relation_hint": "supports",
                "object_candidate_id": "obj:1",
                "confidence": "medium",
            }
        ])
        self.assertEqual(1, len(propositions))
        self.assertEqual(["pred:1"], propositions[0].source_predicate_ids)

    def test_helper_accepts_object_like_predicate_input(self):
        propositions = create_proposition_candidates_from_predicates([
            PredicateLike(
                predicate_candidate_id="pred:1",
                subject_candidate_id="subj:1",
                relation_hint="supports",
                object_candidate_id="obj:1",
            )
        ])
        self.assertEqual(1, len(propositions))
        self.assertEqual("subj:1", propositions[0].subject)

    def test_helper_skips_predicate_without_id(self):
        propositions = create_proposition_candidates_from_predicates([
            {"predicate_candidate_id": "", "subject_candidate_id": "subj:1"},
            PredicateLike(predicate_candidate_id=""),
        ])
        self.assertEqual([], propositions)

    def test_projection_list_helper_returns_multiple_propositions(self):
        propositions = create_proposition_candidates_from_predicates([
            {"predicate_candidate_id": "pred:1", "subject_candidate_id": "a", "relation_hint": "is", "object_candidate_id": "b"},
            {"predicate_candidate_id": "pred:2", "subject_candidate_id": "c", "relation_hint": "supports", "object_candidate_id": "d"},
        ])
        self.assertEqual(2, len(propositions))

    def test_diagnostic_summary_is_redacted(self):
        propositions = create_proposition_candidates_from_predicates([
            {"predicate_candidate_id": "pred:1", "subject_candidate_id": "a", "relation_hint": "is", "object_candidate_id": "b"},
        ])
        summary = summarize_proposition_projection_diagnostics(propositions)
        summary_text = str(summary)
        for snippet in ["question", "choices", "answer_label", "correct_answer", "answer_key", "raw_text"]:
            self.assertNotIn(snippet, summary_text)

    def test_summary_contains_proposition_count(self):
        summary = summarize_proposition_projection_diagnostics([])
        self.assertIn("proposition_candidate_count", summary)

    def test_summary_contains_source_predicate_link_count(self):
        summary = summarize_proposition_projection_diagnostics([])
        self.assertIn("source_predicate_link_count", summary)

    def test_summary_does_not_contain_question(self):
        self.assertNotIn("question", str(summarize_proposition_projection_diagnostics([])))

    def test_summary_does_not_contain_choices(self):
        self.assertNotIn("choices", str(summarize_proposition_projection_diagnostics([])))

    def test_summary_does_not_contain_answer_label(self):
        self.assertNotIn("answer_label", str(summarize_proposition_projection_diagnostics([])))

    def test_summary_does_not_contain_correct_answer(self):
        self.assertNotIn("correct_answer", str(summarize_proposition_projection_diagnostics([])))

    def test_summary_does_not_contain_answer_key(self):
        self.assertNotIn("answer_key", str(summarize_proposition_projection_diagnostics([])))

    def test_no_answer_selection_field_exists(self):
        data = proposition_candidate_to_dict(create_proposition_candidate_from_predicate(predicate_id="pred:1"))
        self.assertNotIn("answer_selection", data)
        self.assertNotIn("selected_answer", data)

    def test_no_answer_key_field_exists_outside_anti_gaming_boolean_name(self):
        data = proposition_candidate_to_dict(create_proposition_candidate_from_predicate(predicate_id="pred:1"))
        self.assertNotIn("answer_key", data)

    def test_existing_schema_tests_still_pass(self):
        output = self.run_direct("python3 weslr/tests/test_logic_teaching_spine_schema_v1.py")
        self.assertIn("OK", output)

    def test_connectivity_contract_test_still_passes(self):
        output = self.run_direct("python3 weslr/tests/test_logic_teaching_spine_connectivity_contract_v1.py")
        self.assertIn("OK", output)

    def test_release_gate_and_check_pass(self):
        output = self.run_direct("python3 weslr/tests/release_gate_v1.py && bash scripts/weslr_release_check.sh")
        self.assertIn("WESLR_RELEASE_GATE_V1_OK", output)
        self.assertIn("WESLR_RELEASE_CHECK_OK", output)

    def test_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertTrue(changed.issubset(ALLOWED_CHANGED))


if __name__ == "__main__":
    unittest.main()
