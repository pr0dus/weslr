from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logical_form_normalizer import (  # noqa: E402
    build_role_aware_index_from_atomic_candidates,
    create_alignment_evidence_from_role_index,
    create_atomic_term_candidates_from_surface,
    create_empty_normalized_logical_form,
    summarize_atomic_extraction_diagnostics,
    tokenize_surface_for_atomic_terms,
)
from weslr.tests.phase_scope_policy import (  # noqa: E402
    assert_logical_form_normalizer_atomic_helper_phase_allowed,
)


class LogicalFormNormalizerAtomicHelpersV1Tests(unittest.TestCase):
    def make_form(self):
        return create_empty_normalized_logical_form(
            normalization_id="norm-atomic-1",
            source_parse_id="parse-atomic-1",
            source_task_id="task-atomic-1",
        )

    def test_tokenize_surface_for_atomic_terms_lowercases(self):
        self.assertEqual(["cat"], tokenize_surface_for_atomic_terms("CAT"))

    def test_tokenizer_removes_simple_stopwords(self):
        self.assertEqual(["cat", "dog"], tokenize_surface_for_atomic_terms("the cat and the dog"))

    def test_tokenizer_deduplicates_while_preserving_order(self):
        self.assertEqual(["cat", "dog"], tokenize_surface_for_atomic_terms("cat dog cat dog"))

    def test_tokenizer_does_conservative_singularization(self):
        self.assertEqual(["cat", "glass"], tokenize_surface_for_atomic_terms("cats glass"))

    def test_tokenizer_has_no_benchmark_specific_phrase_rule(self):
        self.assertEqual(["above", "follow"], tokenize_surface_for_atomic_terms("all of the above follows"))

    def test_create_atomic_term_candidates_from_surface_creates_candidates(self):
        form = self.make_form()
        created = create_atomic_term_candidates_from_surface(
            form,
            source_statement_id="stmt-1",
            source_statement_role="premise",
            surface="cats and dogs",
        )
        self.assertEqual(2, len(created))
        self.assertEqual(2, len(form.atomic_term_candidates))

    def test_atomic_candidates_store_fingerprints(self):
        form = self.make_form()
        created = create_atomic_term_candidates_from_surface(
            form,
            source_statement_id="stmt-1",
            source_statement_role="premise",
            surface="cats",
        )
        self.assertEqual(1, len(created[0].token_fingerprints))
        self.assertNotEqual("cat", created[0].token_fingerprints[0])

    def test_atomic_candidates_do_not_store_raw_surface_text(self):
        form = self.make_form()
        created = create_atomic_term_candidates_from_surface(
            form,
            source_statement_id="stmt-1",
            source_statement_role="premise",
            surface="Secret Surface",
        )
        candidate_text = str(created[0].__dict__)
        self.assertNotIn("Secret Surface", candidate_text)
        self.assertNotIn("secret surface", candidate_text.lower())

    def test_atomic_candidates_have_non_empty_human_explanations(self):
        form = self.make_form()
        created = create_atomic_term_candidates_from_surface(
            form,
            source_statement_id="stmt-1",
            source_statement_role="premise",
            surface="cats",
        )
        self.assertTrue(created[0].human_explanation)

    def test_atomic_candidate_ids_are_deterministic_enough_for_same_source_statement_token_order(self):
        form_a = self.make_form()
        form_b = self.make_form()
        created_a = create_atomic_term_candidates_from_surface(
            form_a,
            source_statement_id="stmt-1",
            source_statement_role="premise",
            surface="cats dogs",
        )
        created_b = create_atomic_term_candidates_from_surface(
            form_b,
            source_statement_id="stmt-1",
            source_statement_role="premise",
            surface="cats dogs",
        )
        self.assertEqual([c.candidate_id for c in created_a], [c.candidate_id for c in created_b])

    def test_role_aware_index_groups_premise_candidates(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats")
        index = build_role_aware_index_from_atomic_candidates(form, index_id="idx-1")
        self.assertEqual(["atomic:stmt-1:1"], index.premise_term_candidate_ids)

    def test_role_aware_index_groups_choice_candidate_candidates(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-2", source_statement_role="choice_claim", surface="dogs")
        index = build_role_aware_index_from_atomic_candidates(form, index_id="idx-1")
        self.assertEqual(["atomic:stmt-2:1"], index.candidate_term_candidate_ids)

    def test_role_aware_index_groups_background_question_instruction_candidates(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-3", source_statement_role="question_instruction", surface="birds")
        index = build_role_aware_index_from_atomic_candidates(form, index_id="idx-1")
        self.assertEqual(["atomic:stmt-3:1"], index.background_term_candidate_ids)

    def test_role_aware_index_groups_unknown_roles_into_unsupported(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-4", source_statement_role="mystery", surface="fish")
        index = build_role_aware_index_from_atomic_candidates(form, index_id="idx-1")
        self.assertEqual(["atomic:stmt-4:1"], index.unsupported_term_candidate_ids)

    def test_alignment_evidence_is_created_for_exact_canonical_hint_match(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats")
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-2", source_statement_role="choice_claim", surface="cat")
        index = build_role_aware_index_from_atomic_candidates(form, index_id="idx-1")
        evidence = create_alignment_evidence_from_role_index(form, index=index)
        self.assertEqual(1, len(evidence))
        self.assertEqual("exact_canonical_hint_match", evidence[0].evidence_type)

    def test_no_alignment_evidence_is_created_for_non_matching_canonical_hints(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cat")
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-2", source_statement_role="choice_claim", surface="dog")
        index = build_role_aware_index_from_atomic_candidates(form, index_id="idx-1")
        self.assertEqual([], create_alignment_evidence_from_role_index(form, index=index))

    def test_alignment_evidence_stores_fingerprints_not_raw_text(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cat")
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-2", source_statement_role="choice_claim", surface="cat")
        index = build_role_aware_index_from_atomic_candidates(form, index_id="idx-1")
        evidence = create_alignment_evidence_from_role_index(form, index=index)[0]
        self.assertTrue(evidence.evidence_fingerprints)
        self.assertNotIn("cat", str(evidence.evidence_fingerprints))

    def test_alignment_evidence_has_non_empty_human_explanation(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cat")
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-2", source_statement_role="choice_claim", surface="cat")
        index = build_role_aware_index_from_atomic_candidates(form, index_id="idx-1")
        evidence = create_alignment_evidence_from_role_index(form, index=index)[0]
        self.assertTrue(evidence.human_explanation)

    def test_atomic_diagnostic_summary_is_redacted(self):
        form = self.make_form()
        summary = summarize_atomic_extraction_diagnostics(form)
        self.assertEqual(
            {
                "atomic_term_candidate_count",
                "predicate_candidate_count",
                "role_index_count",
                "alignment_evidence_count",
                "premise_atomic_count",
                "candidate_atomic_count",
                "background_atomic_count",
                "unsupported_atomic_count",
                "unique_canonical_hint_count",
                "anti_gaming_safe",
                "legibility_safe",
            },
            set(summary.keys()),
        )

    def test_atomic_diagnostic_summary_includes_premise_candidate_atomic_counts(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cat")
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-2", source_statement_role="choice_claim", surface="dog")
        summary = summarize_atomic_extraction_diagnostics(form)
        self.assertEqual(1, summary["premise_atomic_count"])
        self.assertEqual(1, summary["candidate_atomic_count"])

    def test_summary_does_not_contain_question(self):
        self.assertNotIn("question", str(summarize_atomic_extraction_diagnostics(self.make_form())))

    def test_summary_does_not_contain_choices(self):
        self.assertNotIn("choices", str(summarize_atomic_extraction_diagnostics(self.make_form())))

    def test_summary_does_not_contain_answer_label(self):
        self.assertNotIn("answer_label", str(summarize_atomic_extraction_diagnostics(self.make_form())))

    def test_summary_does_not_contain_correct_answer(self):
        self.assertNotIn("correct_answer", str(summarize_atomic_extraction_diagnostics(self.make_form())))

    def test_summary_does_not_contain_raw_text(self):
        self.assertNotIn("raw_text", str(summarize_atomic_extraction_diagnostics(self.make_form())))

    def test_no_answer_selection_field_exists(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cat")
        summary = summarize_atomic_extraction_diagnostics(form)
        self.assertNotIn("answer_selection", summary)
        self.assertNotIn("selected_answer", summary)

    def test_no_answer_key_field_exists_outside_anti_gaming_boolean_name_uses_answer_key(self):
        summary = summarize_atomic_extraction_diagnostics(self.make_form())
        self.assertNotIn("answer_key", summary)
        self.assertNotIn("uses_answer_key", summary)

    def run_direct(self, script: str) -> str:
        proc = subprocess.run(["bash", "-lc", script], cwd=str(ROOT), capture_output=True, text=True, check=True)
        return proc.stdout + proc.stderr

    def test_existing_v11_schema_tests_still_pass(self):
        output = self.run_direct("python3 weslr/tests/test_logical_form_normalizer_v1_1_schema_extension.py")
        self.assertIn("OK", output)

    def test_existing_helper_tests_still_pass(self):
        output = self.run_direct("python3 weslr/tests/test_logical_form_normalizer_helpers_v1.py")
        self.assertIn("OK", output)

    def test_no_parser_solver_runtime_files_changed(self):
        assert_logical_form_normalizer_atomic_helper_phase_allowed(self)


if __name__ == "__main__":
    unittest.main()
