from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logical_form_normalizer import (  # noqa: E402
    align_terms_by_canonical_form,
    create_empty_normalized_logical_form,
    create_normalized_term_from_surface,
    fingerprint_surface,
    infer_polarity,
    normalize_relation_surface,
    normalize_term_surface,
    normalized_logical_form_to_dict,
    safe_candidate_term_id,
    summarize_term_alignment_gaps,
    summarize_normalized_logical_form,
    validate_normalized_logical_form,
)
from weslr.tests.phase_scope_policy import (  # noqa: E402
    assert_logical_form_normalizer_atomic_helper_phase_allowed,
)


class LogicalFormNormalizerHelpersV1Tests(unittest.TestCase):
    def make_form(self):
        return create_empty_normalized_logical_form(
            normalization_id="norm-1",
            source_parse_id="parse-1",
            source_task_id="task-1",
        )

    def test_fingerprint_surface_is_stable(self):
        self.assertEqual(fingerprint_surface("  Hello World  "), fingerprint_surface("hello world"))

    def test_fingerprint_surface_does_not_return_raw_text(self):
        value = fingerprint_surface("Hello World")
        self.assertNotEqual("Hello World", value)
        self.assertEqual(64, len(value))

    def test_normalize_term_surface_lowercases_and_trims(self):
        self.assertEqual("hello", normalize_term_surface("  Hello  "))

    def test_normalize_term_surface_collapses_whitespace(self):
        self.assertEqual("many space here", normalize_term_surface("many   space\n here"))

    def test_normalize_term_surface_does_conservative_singularization(self):
        self.assertEqual("cat", normalize_term_surface("cats"))

    def test_normalize_relation_surface_maps_are_to_is(self):
        self.assertEqual("is", normalize_relation_surface("are"))

    def test_normalize_relation_surface_maps_allows_to_permits(self):
        self.assertEqual("permits", normalize_relation_surface("allows"))

    def test_infer_polarity_detects_positive(self):
        self.assertEqual("positive", infer_polarity("supports"))

    def test_infer_polarity_detects_negative(self):
        self.assertEqual("negative", infer_polarity("is not allowed"))

    def test_safe_candidate_term_id_a(self):
        self.assertEqual("choice_A", safe_candidate_term_id("A"))

    def test_unsafe_label_falls_back_to_choice_index(self):
        self.assertEqual("choice_7", safe_candidate_term_id("alpha", index=7))

    def test_create_normalized_term_from_surface_stores_fingerprint_not_raw_surface(self):
        form = self.make_form()
        term = create_normalized_term_from_surface(form, surface="Secret Surface")
        self.assertEqual(1, len(term.surface_fingerprints))
        self.assertNotIn("Secret Surface", term.surface_fingerprints[0])
        self.assertNotEqual("Secret Surface", term.human_translation)

    def test_created_term_has_canonical_form(self):
        form = self.make_form()
        term = create_normalized_term_from_surface(form, surface="Entities")
        self.assertEqual("entitie", term.canonical_form)

    def test_align_terms_by_canonical_form_aligns_duplicate_canonical_terms(self):
        form = self.make_form()
        create_normalized_term_from_surface(form, surface="Cats", term_id="term-1")
        create_normalized_term_from_surface(form, surface="cat", term_id="term-2")
        alignments = align_terms_by_canonical_form(form)
        self.assertEqual(1, len(alignments))

    def test_align_terms_by_canonical_form_does_not_align_different_canonical_terms(self):
        form = self.make_form()
        create_normalized_term_from_surface(form, surface="cat", term_id="term-1")
        create_normalized_term_from_surface(form, surface="dog", term_id="term-2")
        alignments = align_terms_by_canonical_form(form)
        self.assertEqual([], alignments)

    def test_alignment_record_contains_evidence_fingerprints_not_raw_text(self):
        form = self.make_form()
        create_normalized_term_from_surface(form, surface="Cats", term_id="term-1")
        create_normalized_term_from_surface(form, surface="cat", term_id="term-2")
        alignment = align_terms_by_canonical_form(form)[0]
        self.assertTrue(alignment.evidence_fingerprints)
        self.assertNotIn("Cats", str(alignment.evidence_fingerprints))

    def test_summarize_term_alignment_gaps_is_redacted(self):
        form = self.make_form()
        create_normalized_term_from_surface(form, surface="cat", term_id="term-1")
        summary = summarize_term_alignment_gaps(form)
        self.assertEqual({"term_count", "unique_canonical_term_count", "alignment_count", "unaligned_term_count", "warning_count", "unsupported_gap_count"}, set(summary.keys()))

    def test_summary_does_not_contain_raw_markers(self):
        form = self.make_form()
        create_normalized_term_from_surface(form, surface="cat", term_id="term-1")
        text = str(summarize_term_alignment_gaps(form)) + str(summarize_normalized_logical_form(form))
        for term in ["question", "choices", "answer_label", "correct_answer", "raw_text"]:
            self.assertNotIn(term, text)

    def test_helpers_do_not_create_answer_selection_field(self):
        form = self.make_form()
        create_normalized_term_from_surface(form, surface="cat", term_id="term-1")
        data = normalized_logical_form_to_dict(form)
        self.assertNotIn("answer_selection", data)
        self.assertNotIn("selected_answer", data)

    def test_validation_still_flags_anti_gaming_violations(self):
        form = self.make_form()
        form.anti_gaming.uses_answer_key = True
        self.assertTrue(any("uses_answer_key" in msg for msg in validate_normalized_logical_form(form)))

    def test_existing_schema_tests_still_pass(self):
        proc = subprocess.run(
            ["python3", "weslr/tests/test_logical_form_normalizer_schema_v1.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("OK", proc.stdout + proc.stderr)

    def test_existing_governed_proposal_test_file_exists(self):
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_normalization_governed_proposal_v1.py").exists())

    def test_no_parser_solver_runtime_files_changed(self):
        assert_logical_form_normalizer_atomic_helper_phase_allowed(self)


if __name__ == "__main__":
    unittest.main()
