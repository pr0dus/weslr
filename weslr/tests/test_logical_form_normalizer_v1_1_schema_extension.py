from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logical_form_normalizer import (  # noqa: E402
    add_alignment_evidence_record,
    add_atomic_term_candidate,
    add_normalizer_diagnostic_summary,
    add_predicate_candidate,
    add_role_aware_term_index,
    create_empty_normalized_logical_form,
    normalized_logical_form_from_dict,
    normalized_logical_form_to_dict,
    summarize_normalized_logical_form,
    validate_normalized_logical_form,
    AtomicTermCandidate,
    PredicateCandidate,
    RoleAwareTermIndex,
    AlignmentEvidenceRecord,
    NormalizerDiagnosticSummary,
)
from weslr.tests.phase_scope_policy import (  # noqa: E402
    assert_logical_form_normalizer_atomic_helper_phase_allowed,
)


class LogicalFormNormalizerV11SchemaExtensionTests(unittest.TestCase):
    def make_form(self):
        return create_empty_normalized_logical_form(
            normalization_id="norm-1",
            source_parse_id="parse-1",
            source_task_id="task-1",
        )

    def run_direct(self, script: str) -> str:
        proc = subprocess.run(["bash", "-lc", script], cwd=str(ROOT), capture_output=True, text=True, check=True)
        return proc.stdout + proc.stderr

    def test_v11_dataclasses_can_be_instantiated(self):
        self.assertIsInstance(AtomicTermCandidate(), AtomicTermCandidate)
        self.assertIsInstance(PredicateCandidate(), PredicateCandidate)
        self.assertIsInstance(RoleAwareTermIndex(), RoleAwareTermIndex)
        self.assertIsInstance(AlignmentEvidenceRecord(), AlignmentEvidenceRecord)
        self.assertIsInstance(NormalizerDiagnosticSummary(), NormalizerDiagnosticSummary)

    def test_empty_normalized_logical_form_includes_v11_empty_lists(self):
        form = self.make_form()
        self.assertEqual([], form.atomic_term_candidates)
        self.assertEqual([], form.predicate_candidates)
        self.assertEqual([], form.role_aware_indexes)
        self.assertEqual([], form.alignment_evidence)
        self.assertEqual([], form.diagnostic_summaries)

    def test_add_atomic_term_candidate(self):
        form = self.make_form()
        candidate = add_atomic_term_candidate(form, candidate_id="choice_A", human_explanation="safe candidate")
        self.assertEqual("choice_A", candidate.candidate_id)
        self.assertEqual(1, len(form.atomic_term_candidates))

    def test_atomic_term_candidate_stores_fingerprints_not_raw_text(self):
        form = self.make_form()
        candidate = add_atomic_term_candidate(
            form,
            candidate_id="choice_A",
            token_fingerprints=["abc123"],
            human_explanation="fingerprint only",
        )
        self.assertEqual(["abc123"], candidate.token_fingerprints)
        self.assertNotIn("raw text", str(candidate.token_fingerprints))

    def test_validation_flags_atomic_term_candidate_missing_id(self):
        form = self.make_form()
        add_atomic_term_candidate(form, candidate_id="", human_explanation="missing id")
        self.assertTrue(any("AtomicTermCandidate missing candidate_id" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_atomic_term_candidate_without_human_explanation(self):
        form = self.make_form()
        add_atomic_term_candidate(form, candidate_id="cand-1")
        self.assertTrue(any("AtomicTermCandidate cand-1 must include human_explanation" in msg for msg in validate_normalized_logical_form(form)))

    def test_add_predicate_candidate_referencing_existing_atomic_candidates(self):
        form = self.make_form()
        add_atomic_term_candidate(form, candidate_id="left", human_explanation="left")
        add_atomic_term_candidate(form, candidate_id="right", human_explanation="right")
        pred = add_predicate_candidate(form, predicate_candidate_id="pred-1", subject_candidate_id="left", object_candidate_id="right", human_explanation="predicate")
        self.assertEqual("pred-1", pred.predicate_candidate_id)
        self.assertEqual([], validate_normalized_logical_form(form))

    def test_validation_flags_predicate_candidate_referencing_missing_atomic_candidate(self):
        form = self.make_form()
        add_predicate_candidate(form, predicate_candidate_id="pred-1", subject_candidate_id="left", human_explanation="predicate")
        self.assertTrue(any("references missing subject_candidate_id left" in msg for msg in validate_normalized_logical_form(form)))

    def test_add_role_aware_term_index(self):
        form = self.make_form()
        add_atomic_term_candidate(form, candidate_id="prem-1", human_explanation="prem")
        index = add_role_aware_term_index(form, index_id="index-1", premise_term_candidate_ids=["prem-1"], human_explanation="index")
        self.assertEqual("index-1", index.index_id)

    def test_validation_flags_role_index_referencing_missing_atomic_candidate(self):
        form = self.make_form()
        add_role_aware_term_index(form, index_id="index-1", premise_term_candidate_ids=["prem-1"], human_explanation="index")
        self.assertTrue(any("RoleAwareTermIndex index-1 references missing atomic term candidate prem-1" in msg for msg in validate_normalized_logical_form(form)))

    def test_add_alignment_evidence_record(self):
        form = self.make_form()
        add_atomic_term_candidate(form, candidate_id="left", human_explanation="left")
        add_atomic_term_candidate(form, candidate_id="right", human_explanation="right")
        evidence = add_alignment_evidence_record(form, evidence_id="ev-1", left_candidate_id="left", right_candidate_id="right", human_explanation="evidence")
        self.assertEqual("ev-1", evidence.evidence_id)

    def test_validation_flags_alignment_evidence_referencing_missing_atomic_candidate(self):
        form = self.make_form()
        add_alignment_evidence_record(form, evidence_id="ev-1", left_candidate_id="left", human_explanation="evidence")
        self.assertTrue(any("AlignmentEvidenceRecord ev-1 references missing left_candidate_id left" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_alignment_evidence_without_human_explanation(self):
        form = self.make_form()
        add_atomic_term_candidate(form, candidate_id="left", human_explanation="left")
        add_alignment_evidence_record(form, evidence_id="ev-1", left_candidate_id="left")
        self.assertTrue(any("AlignmentEvidenceRecord ev-1 must include human_explanation" in msg for msg in validate_normalized_logical_form(form)))

    def test_add_normalizer_diagnostic_summary(self):
        form = self.make_form()
        summary = add_normalizer_diagnostic_summary(form, summary_id="sum-1", human_explanation="summary")
        self.assertEqual("sum-1", summary.summary_id)

    def test_validation_flags_diagnostic_summary_official_score_claim(self):
        form = self.make_form()
        add_normalizer_diagnostic_summary(form, summary_id="sum-1", official_score_claimed=True, human_explanation="summary")
        self.assertTrue(any("official_score_claimed must remain False" in msg for msg in validate_normalized_logical_form(form)))

    def test_validation_flags_diagnostic_summary_without_human_explanation(self):
        form = self.make_form()
        add_normalizer_diagnostic_summary(form, summary_id="sum-1")
        self.assertTrue(any("NormalizerDiagnosticSummary sum-1 must include human_explanation" in msg for msg in validate_normalized_logical_form(form)))

    def test_to_from_dict_roundtrip_preserves_v11_fields(self):
        form = self.make_form()
        add_atomic_term_candidate(form, candidate_id="choice_A", human_explanation="candidate")
        add_predicate_candidate(form, predicate_candidate_id="pred-1", subject_candidate_id="choice_A", human_explanation="predicate")
        add_role_aware_term_index(form, index_id="index-1", candidate_term_candidate_ids=["choice_A"], human_explanation="index")
        add_alignment_evidence_record(form, evidence_id="ev-1", left_candidate_id="choice_A", human_explanation="evidence")
        add_normalizer_diagnostic_summary(form, summary_id="sum-1", human_explanation="summary")
        loaded = normalized_logical_form_from_dict(normalized_logical_form_to_dict(form))
        self.assertEqual(normalized_logical_form_to_dict(form), normalized_logical_form_to_dict(loaded))

    def test_summary_includes_v11_counts(self):
        form = self.make_form()
        add_atomic_term_candidate(form, candidate_id="choice_A", human_explanation="candidate")
        add_predicate_candidate(form, predicate_candidate_id="pred-1", human_explanation="predicate")
        add_role_aware_term_index(form, index_id="index-1", human_explanation="index")
        add_alignment_evidence_record(form, evidence_id="ev-1", human_explanation="evidence")
        add_normalizer_diagnostic_summary(form, summary_id="sum-1", human_explanation="summary")
        summary = summarize_normalized_logical_form(form)
        self.assertEqual(1, summary["atomic_term_candidate_count"])
        self.assertEqual(1, summary["predicate_candidate_count"])
        self.assertEqual(1, summary["role_index_count"])
        self.assertEqual(1, summary["alignment_evidence_count"])
        self.assertEqual(1, summary["diagnostic_summary_count"])

    def test_summary_is_redacted(self):
        summary = summarize_normalized_logical_form(self.make_form())
        text = str(summary)
        for term in ["question", "choices", "answer_label", "correct_answer", "raw_text"]:
            self.assertNotIn(term, text)

    def test_summary_does_not_contain_question(self):
        self.assertNotIn("question", str(summarize_normalized_logical_form(self.make_form())))

    def test_summary_does_not_contain_choices(self):
        self.assertNotIn("choices", str(summarize_normalized_logical_form(self.make_form())))

    def test_summary_does_not_contain_answer_label(self):
        self.assertNotIn("answer_label", str(summarize_normalized_logical_form(self.make_form())))

    def test_summary_does_not_contain_correct_answer(self):
        self.assertNotIn("correct_answer", str(summarize_normalized_logical_form(self.make_form())))

    def test_summary_does_not_contain_raw_text(self):
        self.assertNotIn("raw_text", str(summarize_normalized_logical_form(self.make_form())))

    def test_no_answer_selection_field_exists(self):
        data = normalized_logical_form_to_dict(self.make_form())
        self.assertNotIn("answer_selection", data)
        self.assertNotIn("selected_answer", data)

    def test_no_answer_key_field_exists_outside_anti_gaming_boolean(self):
        data = normalized_logical_form_to_dict(self.make_form())
        self.assertNotIn("answer_key", data)
        self.assertIn("uses_answer_key", data["anti_gaming"])

    def test_existing_schema_tests_still_pass(self):
        output = self.run_direct("python3 weslr/tests/test_logical_form_normalizer_schema_v1.py")
        self.assertIn("OK", output)

    def test_existing_helper_tests_still_pass(self):
        output = self.run_direct("python3 weslr/tests/test_logical_form_normalizer_helpers_v1.py")
        self.assertIn("OK", output)

    def test_existing_v11_revision_doc_test_file_exists(self):
        self.assertTrue((ROOT / "weslr/tests/test_logical_form_normalizer_v1_1_revision.py").exists())

    def test_no_parser_solver_runtime_files_changed(self):
        assert_logical_form_normalizer_atomic_helper_phase_allowed(self)


if __name__ == "__main__":
    unittest.main()
