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
    compare_proposition_terms_for_alignment,
    create_proposition_candidate_from_predicate,
    create_proposition_candidates_from_predicates,
    normalize_proposition_role,
    normalize_term_for_alignment,
    proposition_candidate_to_dict,
    summarize_proposition_projection_diagnostics,
    summarize_term_alignment_candidates,
    term_alignment_key,
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
    source_statement_id: str = ""
    source_statement_role: str = ""
    role: str = ""
    statement_role: str = ""
    subject_candidate_id: str = ""
    relation_hint: str = ""
    object_candidate_id: str = ""
    subject_canonical_hint: str = ""
    object_canonical_hint: str = ""
    relation_canonical_hint: str = ""
    subject_hint: str = ""
    object_hint: str = ""
    canonical_subject: str = ""
    canonical_object: str = ""
    subject_fingerprint: str = ""
    object_fingerprint: str = ""
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

    def test_proposition_can_store_source_statement_ids(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            source_statement_id="stmt:1",
        )
        self.assertEqual(["stmt:1"], proposition.source_statement_ids)

    def test_proposition_can_store_source_statement_roles(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            source_statement_role="parsed_premise",
        )
        self.assertEqual(["premise"], proposition.source_statement_roles)

    def test_proposition_stores_normalized_proposition_role(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            proposition_role="candidate_term",
        )
        self.assertEqual("choice_claim", proposition.proposition_role)

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

    def test_proposition_stores_subject_canonical_hint(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            subject="atomic:left",
            subject_canonical_hint="left term",
        )
        self.assertEqual("left term", proposition.subject_canonical_hint)

    def test_proposition_stores_object_canonical_hint(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            object="atomic:right",
            object_canonical_hint="right term",
        )
        self.assertEqual("right term", proposition.object_canonical_hint)

    def test_proposition_stores_relation_canonical_hint(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            relation="supports",
            relation_canonical_hint="supports",
        )
        self.assertEqual("supports", proposition.relation_canonical_hint)

    def test_proposition_stores_subject_and_object_fingerprints(self):
        proposition = create_proposition_candidate_from_predicate(
            predicate_id="pred:1",
            subject_fingerprint="abc123",
            object_fingerprint="def456",
        )
        self.assertEqual("abc123", proposition.subject_fingerprint)
        self.assertEqual("def456", proposition.object_fingerprint)

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

    def test_premise_role_normalizes_from_parsed_premise(self):
        self.assertEqual("premise", normalize_proposition_role("parsed_premise"))

    def test_choice_role_normalizes_from_choice_claim(self):
        self.assertEqual("choice_claim", normalize_proposition_role("choice_claim"))

    def test_background_role_normalizes_from_question_instruction(self):
        self.assertEqual("background", normalize_proposition_role("question_instruction"))

    def test_unknown_role_becomes_unknown(self):
        self.assertEqual("unknown", normalize_proposition_role("surprising_role"))

    def test_helper_accepts_dict_like_predicate_input(self):
        propositions = create_proposition_candidates_from_predicates([
            {
                "predicate_candidate_id": "pred:1",
                "source_statement_id": "stmt:1",
                "source_statement_role": "parsed_premise",
                "subject_candidate_id": "subj:1",
                "relation_hint": "supports",
                "object_candidate_id": "obj:1",
                "confidence": "medium",
            }
        ])
        self.assertEqual(1, len(propositions))
        self.assertEqual(["pred:1"], propositions[0].source_predicate_ids)

    def test_dict_like_predicate_role_is_projected(self):
        propositions = create_proposition_candidates_from_predicates([
            {
                "predicate_candidate_id": "pred:1",
                "source_statement_id": "stmt:1",
                "source_statement_role": "parsed_premise",
                "subject_candidate_id": "subj:1",
                "relation_hint": "supports",
                "object_candidate_id": "obj:1",
            }
        ])
        self.assertEqual("premise", propositions[0].proposition_role)
        self.assertEqual(["stmt:1"], propositions[0].source_statement_ids)
        self.assertEqual(["premise"], propositions[0].source_statement_roles)

    def test_projection_helper_reads_canonical_hints_from_dict_like_predicate(self):
        propositions = create_proposition_candidates_from_predicates([
            {
                "predicate_candidate_id": "pred:1",
                "subject_candidate_id": "subj:1",
                "object_candidate_id": "obj:1",
                "relation_hint": "supports",
                "subject_canonical_hint": "alpha",
                "object_canonical_hint": "beta",
                "relation_canonical_hint": "supports",
                "subject_fingerprint": "fp-subj",
                "object_fingerprint": "fp-obj",
            }
        ])
        proposition = propositions[0]
        self.assertEqual("alpha", proposition.subject_canonical_hint)
        self.assertEqual("beta", proposition.object_canonical_hint)
        self.assertEqual("supports", proposition.relation_canonical_hint)
        self.assertEqual("fp-subj", proposition.subject_fingerprint)
        self.assertEqual("fp-obj", proposition.object_fingerprint)

    def test_object_like_predicate_role_is_projected(self):
        propositions = create_proposition_candidates_from_predicates([
            PredicateLike(
                predicate_candidate_id="pred:1",
                source_statement_id="stmt:2",
                role="candidate_term",
                subject_candidate_id="subj:1",
                relation_hint="supports",
                object_candidate_id="obj:1",
            )
        ])
        self.assertEqual(1, len(propositions))
        self.assertEqual("subj:1", propositions[0].subject)
        self.assertEqual("choice_claim", propositions[0].proposition_role)
        self.assertEqual(["choice_claim"], propositions[0].source_statement_roles)

    def test_projection_helper_reads_canonical_hints_from_object_like_predicate(self):
        propositions = create_proposition_candidates_from_predicates([
            PredicateLike(
                predicate_candidate_id="pred:1",
                subject_candidate_id="subj:1",
                object_candidate_id="obj:1",
                relation_hint="supports",
                subject_hint="alpha",
                canonical_object="beta",
                subject_fingerprint="fp-subj",
                object_fingerprint="fp-obj",
            )
        ])
        proposition = propositions[0]
        self.assertEqual("alpha", proposition.subject_canonical_hint)
        self.assertEqual("beta", proposition.object_canonical_hint)
        self.assertEqual("supports", proposition.relation_canonical_hint)
        self.assertEqual("fp-subj", proposition.subject_fingerprint)
        self.assertEqual("fp-obj", proposition.object_fingerprint)

    def test_projection_helper_does_not_invent_canonical_hints_from_opaque_ids(self):
        propositions = create_proposition_candidates_from_predicates([
            {
                "predicate_candidate_id": "pred:1",
                "subject_candidate_id": "atomic:stmt_q1:1",
                "relation_hint": "is",
                "object_candidate_id": "atomic:stmt_q1:2",
            }
        ])
        proposition = propositions[0]
        self.assertEqual("", proposition.subject_canonical_hint)
        self.assertEqual("", proposition.object_canonical_hint)
        self.assertEqual("is", proposition.relation_canonical_hint)

    def test_alignment_normalization_lowercases_terms(self):
        self.assertEqual("alpha beta", normalize_term_for_alignment("  Alpha Beta  "))

    def test_alignment_normalization_strips_punctuation(self):
        self.assertEqual("alpha beta", normalize_term_for_alignment("alpha, beta!"))

    def test_alignment_normalization_handles_separator_characters(self):
        self.assertEqual("alpha beta gamma", normalize_term_for_alignment("alpha_beta-gamma"))

    def test_alignment_normalization_removes_standalone_tiny_stopwords(self):
        self.assertEqual("cat dog", normalize_term_for_alignment("the cat and a dog"))

    def test_alignment_normalization_singularizes_simple_plurals(self):
        self.assertEqual("policy cat", normalize_term_for_alignment("policies cats"))

    def test_no_benchmark_specific_mappings_exist(self):
        self.assertNotEqual("answer", normalize_term_for_alignment("choice_a"))
        self.assertNotEqual("correct", normalize_term_for_alignment("correct_answer"))

    def test_term_alignment_key_returns_empty_for_empty_input(self):
        self.assertEqual("", term_alignment_key("   "))

    def test_proposition_term_comparison_detects_subject_match(self):
        left = create_proposition_candidate_from_predicate(predicate_id="pred:l", subject_canonical_hint="Alpha-Cats")
        right = create_proposition_candidate_from_predicate(predicate_id="pred:r", subject_canonical_hint="alpha cats")
        match = compare_proposition_terms_for_alignment(left, right)
        self.assertTrue(match["subject_match"])
        self.assertEqual("subject_only", match["match_type"])

    def test_proposition_term_comparison_detects_object_match(self):
        left = create_proposition_candidate_from_predicate(predicate_id="pred:l", object_canonical_hint="Policies")
        right = create_proposition_candidate_from_predicate(predicate_id="pred:r", object_canonical_hint="policy")
        match = compare_proposition_terms_for_alignment(left, right)
        self.assertTrue(match["object_match"])
        self.assertEqual("object_only", match["match_type"])

    def test_proposition_term_comparison_detects_relation_match(self):
        left = create_proposition_candidate_from_predicate(predicate_id="pred:l", relation_canonical_hint="supports")
        right = create_proposition_candidate_from_predicate(predicate_id="pred:r", relation_canonical_hint="supports")
        match = compare_proposition_terms_for_alignment(left, right)
        self.assertTrue(match["relation_match"])
        self.assertEqual("relation_only", match["match_type"])

    def test_proposition_term_comparison_returns_none_when_no_match(self):
        left = create_proposition_candidate_from_predicate(predicate_id="pred:l", subject_canonical_hint="alpha")
        right = create_proposition_candidate_from_predicate(predicate_id="pred:r", object_canonical_hint="beta")
        match = compare_proposition_terms_for_alignment(left, right)
        self.assertFalse(match["any_term_match"])
        self.assertEqual("none", match["match_type"])

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

    def test_summary_compares_only_premise_vs_choice_claim_propositions(self):
        propositions = [
            create_proposition_candidate_from_predicate(predicate_id="pred:1", proposition_role="premise"),
            create_proposition_candidate_from_predicate(predicate_id="pred:2", proposition_role="choice_claim"),
            create_proposition_candidate_from_predicate(predicate_id="pred:3", proposition_role="background"),
        ]
        summary = summarize_term_alignment_candidates(propositions)
        self.assertEqual(1, summary["comparison_count"])

    def test_summary_counts_subject_matches(self):
        propositions = [
            create_proposition_candidate_from_predicate(predicate_id="pred:1", proposition_role="premise", subject_canonical_hint="alpha"),
            create_proposition_candidate_from_predicate(predicate_id="pred:2", proposition_role="choice_claim", subject_canonical_hint="alpha"),
        ]
        summary = summarize_term_alignment_candidates(propositions)
        self.assertEqual(1, summary["subject_match_count"])

    def test_summary_counts_object_matches(self):
        propositions = [
            create_proposition_candidate_from_predicate(predicate_id="pred:1", proposition_role="premise", object_canonical_hint="policy"),
            create_proposition_candidate_from_predicate(predicate_id="pred:2", proposition_role="choice_claim", object_canonical_hint="policies"),
        ]
        summary = summarize_term_alignment_candidates(propositions)
        self.assertEqual(1, summary["object_match_count"])

    def test_summary_counts_relation_matches(self):
        propositions = [
            create_proposition_candidate_from_predicate(predicate_id="pred:1", proposition_role="premise", relation_canonical_hint="supports"),
            create_proposition_candidate_from_predicate(predicate_id="pred:2", proposition_role="choice_claim", relation_canonical_hint="supports"),
        ]
        summary = summarize_term_alignment_candidates(propositions)
        self.assertEqual(1, summary["relation_match_count"])

    def test_summary_contains_proposition_count(self):
        summary = summarize_proposition_projection_diagnostics([])
        self.assertIn("proposition_candidate_count", summary)

    def test_summary_contains_source_predicate_link_count(self):
        summary = summarize_proposition_projection_diagnostics([])
        self.assertIn("source_predicate_link_count", summary)

    def test_summary_includes_subject_canonical_hint_count(self):
        summary = summarize_proposition_projection_diagnostics([
            create_proposition_candidate_from_predicate(predicate_id="pred:1", subject_canonical_hint="alpha")
        ])
        self.assertEqual(1, summary["subject_canonical_hint_count"])

    def test_summary_includes_object_canonical_hint_count(self):
        summary = summarize_proposition_projection_diagnostics([
            create_proposition_candidate_from_predicate(predicate_id="pred:1", object_canonical_hint="beta")
        ])
        self.assertEqual(1, summary["object_canonical_hint_count"])

    def test_summary_includes_relation_canonical_hint_count(self):
        summary = summarize_proposition_projection_diagnostics([
            create_proposition_candidate_from_predicate(predicate_id="pred:1", relation_canonical_hint="supports")
        ])
        self.assertEqual(1, summary["relation_canonical_hint_count"])

    def test_summary_includes_premise_proposition_count(self):
        summary = summarize_proposition_projection_diagnostics([
            create_proposition_candidate_from_predicate(predicate_id="pred:1", proposition_role="premise")
        ])
        self.assertEqual(1, summary["premise_proposition_count"])

    def test_summary_includes_choice_proposition_count(self):
        summary = summarize_proposition_projection_diagnostics([
            create_proposition_candidate_from_predicate(predicate_id="pred:1", proposition_role="choice_claim")
        ])
        self.assertEqual(1, summary["choice_claim_proposition_count"])

    def test_summary_includes_unknown_role_proposition_count(self):
        summary = summarize_proposition_projection_diagnostics([
            create_proposition_candidate_from_predicate(predicate_id="pred:1")
        ])
        self.assertEqual(1, summary["unknown_role_proposition_count"])

    def test_no_raw_text_appears_in_summary(self):
        summary_text = str(summarize_proposition_projection_diagnostics([]))
        self.assertNotIn("question", summary_text)
        self.assertNotIn("choices", summary_text)
        self.assertNotIn("answer_label", summary_text)
        self.assertNotIn("correct_answer", summary_text)
        self.assertNotIn("raw_text", summary_text)

    def test_summary_remains_redacted_with_canonical_hints(self):
        summary = summarize_proposition_projection_diagnostics([
            create_proposition_candidate_from_predicate(
                predicate_id="pred:1",
                subject_canonical_hint="hidden subject",
                object_canonical_hint="hidden object",
                relation_canonical_hint="hidden relation",
                subject_fingerprint="finger-a",
                object_fingerprint="finger-b",
            )
        ])
        summary_text = str(summary)
        for snippet in ["hidden subject", "hidden object", "hidden relation", "finger-a", "finger-b"]:
            self.assertNotIn(snippet, summary_text)

    def test_term_alignment_summary_remains_redacted(self):
        summary = summarize_term_alignment_candidates([
            create_proposition_candidate_from_predicate(
                predicate_id="pred:1",
                proposition_role="premise",
                subject_canonical_hint="hidden subject",
            ),
            create_proposition_candidate_from_predicate(
                predicate_id="pred:2",
                proposition_role="choice_claim",
                subject_canonical_hint="hidden subject",
            ),
        ])
        self.assertNotIn("hidden subject", str(summary))

    def test_term_alignment_summary_does_not_contain_question_choices_or_answer_fields(self):
        summary_text = str(summarize_term_alignment_candidates([]))
        for snippet in ["question", "choices", "answer_key", "correct_answer"]:
            self.assertNotIn(snippet, summary_text)

    def test_summary_does_not_contain_question_choices_or_answer_fields(self):
        summary_text = str(summarize_proposition_projection_diagnostics([]))
        for snippet in ["question", "choices", "answer_key", "correct_answer"]:
            self.assertNotIn(snippet, summary_text)

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
