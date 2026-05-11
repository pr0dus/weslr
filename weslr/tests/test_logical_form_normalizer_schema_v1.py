from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logical_form_normalizer import (  # noqa: E402
    add_normalization_warning,
    add_normalized_predicate,
    add_normalized_term,
    add_term_alignment,
    create_empty_normalized_logical_form,
    normalized_logical_form_from_dict,
    normalized_logical_form_to_dict,
    summarize_normalized_logical_form,
    validate_normalized_logical_form,
)
from weslr.tests.phase_scope_policy import (  # noqa: E402
    assert_logical_form_normalizer_atomic_helper_phase_allowed,
)


class LogicalFormNormalizerSchemaV1Tests(unittest.TestCase):
    def make_form(self):
        return create_empty_normalized_logical_form(
            normalization_id="norm-1",
            source_parse_id="parse-1",
            source_task_id="task-1",
        )

    def test_empty_normalized_form_can_be_created(self):
        form = self.make_form()
        self.assertEqual("1.0", form.schema_version)
        self.assertEqual([], form.normalized_terms)
        self.assertEqual([], form.normalized_predicates)

    def test_defaults_are_anti_gaming_safe(self):
        form = self.make_form()
        anti = form.anti_gaming
        self.assertFalse(anti.uses_answer_key)
        self.assertFalse(anti.uses_item_id)
        self.assertFalse(anti.uses_answer_position_bias)
        self.assertFalse(anti.stores_raw_text_by_default)
        self.assertFalse(anti.official_score_claimed)
        self.assertFalse(anti.benchmark_specific_rule_used)

    def test_defaults_are_legible(self):
        legibility = self.make_form().legibility
        self.assertTrue(legibility.human_explanation_available)
        self.assertTrue(legibility.normalization_warrants_available)
        self.assertTrue(legibility.unsupported_gaps_visible)
        self.assertFalse(legibility.private_symbolic_authority_used)

    def test_validation_passes_on_empty_safe_form_with_required_ids(self):
        self.assertEqual([], validate_normalized_logical_form(self.make_form()))

    def test_validation_flags_official_score_claim(self):
        form = self.make_form()
        form.anti_gaming.official_score_claimed = True
        self.assertTrue(any("official_score_claimed" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_answer_key_use(self):
        form = self.make_form()
        form.anti_gaming.uses_answer_key = True
        self.assertTrue(any("uses_answer_key" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_item_id_use(self):
        form = self.make_form()
        form.anti_gaming.uses_item_id = True
        self.assertTrue(any("uses_item_id" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_answer_position_bias(self):
        form = self.make_form()
        form.anti_gaming.uses_answer_position_bias = True
        self.assertTrue(any("uses_answer_position_bias" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_raw_text_storage_by_default(self):
        form = self.make_form()
        form.anti_gaming.stores_raw_text_by_default = True
        self.assertTrue(any("stores_raw_text_by_default" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_benchmark_specific_rule_use(self):
        form = self.make_form()
        form.anti_gaming.benchmark_specific_rule_used = True
        self.assertTrue(any("benchmark_specific_rule_used" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_private_symbolic_authority(self):
        form = self.make_form()
        form.legibility.private_symbolic_authority_used = True
        self.assertTrue(any("private_symbolic_authority_used" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_missing_normalization_id(self):
        form = create_empty_normalized_logical_form(source_parse_id="parse-1", source_task_id="task-1")
        self.assertTrue(any("normalization_id" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_missing_source_parse_id(self):
        form = create_empty_normalized_logical_form(normalization_id="norm-1", source_task_id="task-1")
        self.assertTrue(any("source_parse_id" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_missing_source_task_id(self):
        form = create_empty_normalized_logical_form(normalization_id="norm-1", source_parse_id="parse-1")
        self.assertTrue(any("source_task_id" in msg for msg in validate_normalized_logical_form(form)))

    def test_add_normalized_term(self):
        form = self.make_form()
        term = add_normalized_term(form, term_id="term-1", canonical_form="entity", term_type="noun")
        self.assertEqual("term-1", term.term_id)
        self.assertEqual(1, len(form.normalized_terms))

    def test_add_normalized_predicate_referencing_existing_term_ids(self):
        form = self.make_form()
        add_normalized_term(form, term_id="left")
        add_normalized_term(form, term_id="right")
        predicate = add_normalized_predicate(form, predicate_id="pred-1", subject_term_id="left", object_term_id="right")
        self.assertEqual("pred-1", predicate.predicate_id)
        self.assertEqual([], validate_normalized_logical_form(form))

    def test_validation_flags_predicate_referencing_missing_term_ids(self):
        form = self.make_form()
        add_normalized_predicate(form, predicate_id="pred-1", subject_term_id="left", object_term_id="right")
        messages = validate_normalized_logical_form(form)
        self.assertTrue(any("missing subject_term_id" in msg for msg in messages))
        self.assertTrue(any("missing object_term_id" in msg for msg in messages))

    def test_add_term_alignment(self):
        form = self.make_form()
        add_normalized_term(form, term_id="left")
        add_normalized_term(form, term_id="right")
        alignment = add_term_alignment(form, alignment_id="align-1", left_term_id="left", right_term_id="right")
        self.assertEqual("align-1", alignment.alignment_id)
        self.assertEqual(1, len(form.term_alignments))

    def test_validation_flags_alignment_referencing_missing_term_ids(self):
        form = self.make_form()
        add_term_alignment(form, alignment_id="align-1", left_term_id="left", right_term_id="right")
        messages = validate_normalized_logical_form(form)
        self.assertTrue(any("missing left_term_id" in msg for msg in messages))
        self.assertTrue(any("missing right_term_id" in msg for msg in messages))

    def test_add_warning_with_human_explanation(self):
        form = self.make_form()
        warning = add_normalization_warning(form, warning_id="warn-1", human_explanation="visible reason")
        self.assertEqual("warn-1", warning.warning_id)
        self.assertEqual([], validate_normalized_logical_form(form))

    def test_validation_flags_warning_without_explanation(self):
        form = self.make_form()
        add_normalization_warning(form, warning_id="warn-1")
        self.assertTrue(any("human_explanation" in msg for msg in validate_normalized_logical_form(form)))

    def test_unsupported_normalization_gap_is_visible_in_summary_count(self):
        form = self.make_form()
        add_normalization_warning(
            form,
            warning_id="gap-1",
            human_explanation="gap remains visible",
            unsupported_gap=True,
        )
        summary = summarize_normalized_logical_form(form)
        self.assertEqual(1, summary["unsupported_gap_count"])

    def test_roundtrip_to_dict_from_dict_preserves_fields(self):
        form = self.make_form()
        add_normalized_term(form, term_id="choice_A", canonical_form="choice_A", human_translation="safe id")
        add_normalized_term(form, term_id="term-2", canonical_form="entity")
        add_normalized_predicate(form, predicate_id="pred-1", subject_term_id="choice_A", object_term_id="term-2")
        add_term_alignment(form, alignment_id="align-1", left_term_id="choice_A", right_term_id="term-2")
        add_normalization_warning(form, warning_id="warn-1", human_explanation="visible reason")
        loaded = normalized_logical_form_from_dict(normalized_logical_form_to_dict(form))
        self.assertEqual(normalized_logical_form_to_dict(form), normalized_logical_form_to_dict(loaded))

    def test_summary_is_redacted_and_does_not_expose_raw_text(self):
        form = self.make_form()
        add_normalized_term(form, term_id="term-1", canonical_form="entity", human_translation="human readable")
        summary = summarize_normalized_logical_form(form)
        text = str(summary)
        for term in ["answer_label", "correct_answer", "question", "choices", "raw_text", "human readable"]:
            self.assertNotIn(term, text)

    def test_candidate_identity_can_be_represented_only_as_safe_ids_like_choice_a(self):
        form = self.make_form()
        term = add_normalized_term(form, term_id="choice_A", canonical_form="choice_A", term_type="candidate")
        self.assertEqual("choice_A", term.term_id)
        self.assertEqual("choice_A", term.canonical_form)

    def test_no_answer_selection_field_exists_in_top_level_dict(self):
        data = normalized_logical_form_to_dict(self.make_form())
        self.assertNotIn("answer_selection", data)
        self.assertNotIn("selected_answer", data)

    def test_no_answer_key_field_exists_in_top_level_dict_except_nested_boolean(self):
        data = normalized_logical_form_to_dict(self.make_form())
        self.assertNotIn("answer_key", data)
        self.assertIn("anti_gaming", data)
        self.assertIn("uses_answer_key", data["anti_gaming"])

    def test_official_score_claim_defaults_false(self):
        self.assertFalse(self.make_form().anti_gaming.official_score_claimed)

    def test_existing_governed_proposal_test_file_exists(self):
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_normalization_governed_proposal_v1.py").exists())

    def test_no_parser_solver_runtime_files_changed(self):
        assert_logical_form_normalizer_atomic_helper_phase_allowed(self)


if __name__ == "__main__":
    unittest.main()
