from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logical_form_normalizer import (  # noqa: E402
    create_atomic_term_candidates_from_surface,
    create_empty_normalized_logical_form,
    create_predicate_candidates_from_atomic_terms,
    extract_relation_hints_from_surface,
    normalized_logical_form_to_dict,
    summarize_predicate_decomposition_diagnostics,
)


class LogicalFormNormalizerRelationPreservationHelpersV1Tests(unittest.TestCase):
    def make_form(self):
        return create_empty_normalized_logical_form(
            normalization_id="norm-relation-1",
            source_parse_id="parse-relation-1",
            source_task_id="task-relation-1",
        )

    def run_direct(self, script: str) -> str:
        proc = subprocess.run(["bash", "-lc", script], cwd=str(ROOT), capture_output=True, text=True, check=True)
        return proc.stdout + proc.stderr

    def test_extract_relation_hints_is(self):
        self.assertEqual(["is"], extract_relation_hints_from_surface("A is B"))

    def test_are_normalizes_to_is(self):
        self.assertEqual(["is"], extract_relation_hints_from_surface("A are B"))

    def test_was_normalizes_to_is(self):
        self.assertEqual(["is"], extract_relation_hints_from_surface("A was B"))

    def test_supports_is_preserved(self):
        self.assertEqual(["supports"], extract_relation_hints_from_surface("A supports B"))

    def test_allows_normalizes_to_permits(self):
        self.assertEqual(["permits"], extract_relation_hints_from_surface("A allows B"))

    def test_no_relation_returns_empty_list(self):
        self.assertEqual([], extract_relation_hints_from_surface("cat dog bird"))

    def test_atomic_extraction_creates_relation_hint_candidate_for_is(self):
        form = self.make_form()
        created = create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="A is B")
        self.assertTrue(any(candidate.term_type_hint == "relation_hint" and candidate.canonical_hint == "is" for candidate in created))

    def test_relation_hint_candidate_stores_fingerprint_only(self):
        form = self.make_form()
        created = create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="A is B")
        relation_candidate = next(candidate for candidate in created if candidate.term_type_hint == "relation_hint")
        self.assertTrue(relation_candidate.token_fingerprints)
        self.assertNotIn("is", str(relation_candidate.token_fingerprints))

    def test_relation_hint_candidate_has_relation_hint_type(self):
        form = self.make_form()
        created = create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="A is B")
        relation_candidate = next(candidate for candidate in created if candidate.term_type_hint == "relation_hint")
        self.assertEqual("relation_hint", relation_candidate.term_type_hint)

    def test_relation_hint_candidate_does_not_store_raw_text(self):
        form = self.make_form()
        created = create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="Secret is Surface")
        relation_candidate = next(candidate for candidate in created if candidate.term_type_hint == "relation_hint")
        self.assertNotIn("Secret is Surface", str(relation_candidate.__dict__))

    def test_predicate_candidate_can_be_created_when_subject_relation_object_exist(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats is dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1", source_statement_role="premise")
        self.assertEqual(1, len(created))

    def test_predicate_candidate_references_existing_atomic_candidate_ids(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats is dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1")
        atomic_ids = {candidate.candidate_id for candidate in form.atomic_term_candidates}
        self.assertIn(created[0].subject_candidate_id, atomic_ids)
        self.assertIn(created[0].object_candidate_id, atomic_ids)

    def test_predicate_candidate_has_non_empty_human_explanation(self):
        form = self.make_form()
        create_atomic_term_candidates_from_surface(form, source_statement_id="stmt-1", source_statement_role="premise", surface="cats is dogs")
        created = create_predicate_candidates_from_atomic_terms(form, source_statement_id="stmt-1")
        self.assertTrue(created[0].human_explanation)

    def test_no_answer_selection_field_exists(self):
        data = normalized_logical_form_to_dict(self.make_form())
        self.assertNotIn("answer_selection", data)
        self.assertNotIn("selected_answer", data)

    def test_no_answer_key_field_exists_outside_anti_gaming_boolean_name(self):
        summary = summarize_predicate_decomposition_diagnostics(self.make_form())
        self.assertNotIn("answer_key", summary)
        self.assertNotIn("uses_answer_key", summary)

    def test_summary_remains_redacted(self):
        text = str(summarize_predicate_decomposition_diagnostics(self.make_form()))
        for term in ["question", "choices", "answer_label", "correct_answer", "raw_text"]:
            self.assertNotIn(term, text)

    def test_existing_atomic_helper_tests_pass(self):
        output = self.run_direct("python3 weslr/tests/test_logical_form_normalizer_atomic_helpers_v1.py")
        self.assertIn("OK", output)

    def test_existing_predicate_helper_tests_pass(self):
        output = self.run_direct("python3 weslr/tests/test_logical_form_normalizer_predicate_helpers_v1.py")
        self.assertIn("OK", output)

    def test_release_gate_and_check_pass(self):
        output = self.run_direct("python3 weslr/tests/release_gate_v1.py && bash scripts/weslr_release_check.sh")
        self.assertIn("WESLR_RELEASE_GATE_V1_OK", output)
        self.assertIn("WESLR_RELEASE_CHECK_OK", output)


if __name__ == "__main__":
    unittest.main()
