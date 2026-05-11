from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logical_form_normalizer import (  # noqa: E402
    add_atomic_term_candidate,
    create_atomic_term_candidates_from_surface,
    create_empty_normalized_logical_form,
    create_predicate_candidates_for_form,
    create_predicate_candidates_from_atomic_terms,
    detect_relation_hint_from_tokens,
    normalized_logical_form_to_dict,
    summarize_predicate_decomposition_diagnostics,
)


class LogicalFormNormalizerPredicateHelpersV1Tests(unittest.TestCase):
    def make_form(self):
        return create_empty_normalized_logical_form(
            normalization_id="norm-predicate-1",
            source_parse_id="parse-predicate-1",
            source_task_id="task-predicate-1",
        )

    def run_direct(self, script: str) -> str:
        proc = subprocess.run(["bash", "-lc", script], cwd=str(ROOT), capture_output=True, text=True, check=True)
        return proc.stdout + proc.stderr

    def test_relation_hint_detection_for_is(self):
        self.assertEqual("is", detect_relation_hint_from_tokens(["cat", "is", "animal"]))

    def test_relation_hint_detection_for_supports(self):
        self.assertEqual("supports", detect_relation_hint_from_tokens(["claim", "supports", "result"]))

    def test_relation_hint_detection_for_requires(self):
        self.assertEqual("requires", detect_relation_hint_from_tokens(["input", "requires", "output"]))

    def test_unknown_relation_returns_empty_string(self):
        self.assertEqual("", detect_relation_hint_from_tokens(["cat", "dog", "bird"]))

    def test_predicate_candidate_is_created_from_atomic_terms(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats supports dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1", source_statement_role="premise")
        self.assertEqual(1, len(created))

    def test_predicate_candidate_references_existing_atomic_candidate_ids(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats supports dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1")
        atomic_ids = {candidate.candidate_id for candidate in form.atomic_term_candidates}
        self.assertIn(created[0].subject_candidate_id, atomic_ids)
        self.assertIn(created[0].object_candidate_id, atomic_ids)

    def test_predicate_candidate_has_non_empty_human_explanation(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats supports dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1")
        self.assertTrue(created[0].human_explanation)

    def test_predicate_created_from_premise_atomic_terms_has_premise_role(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats supports dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1", source_statement_role="premise")
        self.assertEqual("premise", created[0].role)

    def test_predicate_created_from_choice_claim_atomic_terms_has_choice_claim_role(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="choice_claim", surface="cats supports dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1", source_statement_role="choice_claim")
        self.assertEqual("choice_claim", created[0].role)

    def test_predicate_created_from_background_atomic_terms_has_background_role(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="question_instruction", surface="cats supports dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1", source_statement_role="question_instruction")
        self.assertEqual("background", created[0].role)

    def test_mixed_unclear_roles_become_unknown(self):
        form = self.make_form()
        add_atomic_term_candidate(
            form,
            candidate_id="atomic:stmt-1:1",
            source_statement_id="stmt-1",
            source_statement_role="premise",
            safe_origin_type="parsed_statement",
            token_fingerprints=["a"],
            canonical_hint="cats",
            term_type_hint="atomic_term",
        )
        add_atomic_term_candidate(
            form,
            candidate_id="atomic:stmt-1:2",
            source_statement_id="stmt-1",
            source_statement_role="choice_claim",
            safe_origin_type="parsed_statement",
            token_fingerprints=["b"],
            canonical_hint="supports",
            term_type_hint="relation_hint",
        )
        add_atomic_term_candidate(
            form,
            candidate_id="atomic:stmt-1:3",
            source_statement_id="stmt-1",
            source_statement_role="background",
            safe_origin_type="parsed_statement",
            token_fingerprints=["c"],
            canonical_hint="dogs",
            term_type_hint="atomic_term",
        )
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1")
        self.assertEqual("unknown", created[0].role)

    def test_predicate_preserves_source_statement_id(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-9", source_statement_role="premise", surface="cats supports dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-9", source_statement_role="premise")
        self.assertEqual("stmt-9", created[0].source_statement_id)

    def test_predicate_preserves_source_statement_role(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-9", source_statement_role="parsed_premise", surface="cats supports dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-9", source_statement_role="parsed_premise")
        self.assertEqual("premise", created[0].source_statement_role)

    def test_predicate_candidate_does_not_store_raw_text(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="Secret supports Surface")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1")
        self.assertNotIn("Secret supports Surface", str(created[0].__dict__))

    def test_no_predicate_created_when_too_few_atomic_terms_exist(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats")
        self.assertEqual([], create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1"))

    def test_form_level_predicate_helper_works_across_multiple_statements(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats supports dogs")
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-2", source_statement_role="choice_claim", surface="birds require nests")
        created = create_predicate_candidates_for_form(form)
        self.assertEqual(2, len(created))

    def test_diagnostic_summary_is_redacted(self):
        form = self.make_form()
        summary = summarize_predicate_decomposition_diagnostics(form)
        self.assertEqual(
            {
                "atomic_term_candidate_count",
                "predicate_candidate_count",
                "predicate_source_statement_count",
                "relation_hint_count",
                "empty_relation_hint_count",
                "anti_gaming_safe",
                "legibility_safe",
            },
            set(summary.keys()),
        )

    def test_summary_does_not_contain_question(self):
        self.assertNotIn("question", str(summarize_predicate_decomposition_diagnostics(self.make_form())))

    def test_summary_does_not_contain_choices(self):
        self.assertNotIn("choices", str(summarize_predicate_decomposition_diagnostics(self.make_form())))

    def test_summary_does_not_contain_answer_label(self):
        self.assertNotIn("answer_label", str(summarize_predicate_decomposition_diagnostics(self.make_form())))

    def test_summary_does_not_contain_correct_answer(self):
        self.assertNotIn("correct_answer", str(summarize_predicate_decomposition_diagnostics(self.make_form())))

    def test_summary_does_not_contain_raw_text(self):
        self.assertNotIn("raw_text", str(summarize_predicate_decomposition_diagnostics(self.make_form())))

    def test_no_answer_selection_field_exists(self):
        data = normalized_logical_form_to_dict(self.make_form())
        self.assertNotIn("answer_selection", data)
        self.assertNotIn("selected_answer", data)

    def test_no_answer_key_field_exists_outside_anti_gaming_boolean_name(self):
        summary = summarize_predicate_decomposition_diagnostics(self.make_form())
        self.assertNotIn("answer_key", summary)
        self.assertNotIn("uses_answer_key", summary)

    def test_existing_atomic_helper_tests_still_pass(self):
        output = self.run_direct("python3 weslr/tests/test_logical_form_normalizer_atomic_helpers_v1.py")
        self.assertIn("OK", output)

    def test_release_gate_and_check_still_pass(self):
        output = self.run_direct("python3 weslr/tests/release_gate_v1.py && bash scripts/weslr_release_check.sh")
        self.assertIn("WESLR_RELEASE_GATE_V1_OK", output)
        self.assertIn("WESLR_RELEASE_CHECK_OK", output)


if __name__ == "__main__":
    unittest.main()
