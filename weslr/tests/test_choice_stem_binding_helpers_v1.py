from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.choice_stem_binding import (  # noqa: E402
    ChoiceStemBindingCandidate,
    classify_choice_stem_binding_type,
    create_choice_stem_binding_candidate,
    create_choice_stem_bindings_for_item,
    summarize_choice_stem_binding_diagnostics,
)


class ChoiceStemBindingHelpersV1Tests(unittest.TestCase):
    def test_classifier_identifies_full_claim(self):
        self.assertEqual(
            classify_choice_stem_binding_type(choice_is_full_claim_like=True),
            "choice_is_full_claim",
        )

    def test_classifier_identifies_fragment_unknown(self):
        self.assertEqual(
            classify_choice_stem_binding_type(
                question_instruction_markers=["select"],
                choice_markers=["alpha"],
                choice_is_noun_phrase_like=True,
            ),
            "choice_is_fragment_unknown",
        )

    def test_classifier_identifies_supplies_conclusion(self):
        self.assertEqual(
            classify_choice_stem_binding_type(
                question_instruction_markers=["which", "conclusion", "follows"],
                choice_markers=["alpha"],
                choice_is_noun_phrase_like=True,
            ),
            "choice_supplies_conclusion",
        )

    def test_classifier_identifies_completes_predicate(self):
        self.assertEqual(
            classify_choice_stem_binding_type(
                question_instruction_markers=["which", "statement", "is", "true"],
                choice_markers=["alpha"],
                choice_is_noun_phrase_like=True,
            ),
            "choice_completes_question_predicate",
        )

    def test_helper_creates_binding_candidate(self):
        candidate = create_choice_stem_binding_candidate(
            binding_id="b1",
            source_question_instruction_id="q1",
            source_choice_statement_id="c1",
            question_instruction_markers=["which", "conclusion", "follows"],
            choice_markers=["alpha"],
            choice_is_noun_phrase_like=True,
        )
        self.assertIsInstance(candidate, ChoiceStemBindingCandidate)

    def test_binding_candidate_has_source_question_instruction_id(self):
        candidate = create_choice_stem_binding_candidate(binding_id="b1", source_question_instruction_id="q1")
        self.assertEqual(candidate.source_question_instruction_id, "q1")

    def test_binding_candidate_has_source_choice_statement_id(self):
        candidate = create_choice_stem_binding_candidate(binding_id="b1", source_choice_statement_id="c1")
        self.assertEqual(candidate.source_choice_statement_id, "c1")

    def test_weak_binding_records_unsupported_gap(self):
        candidate = create_choice_stem_binding_candidate(
            binding_id="b1",
            source_question_instruction_id="q1",
            source_choice_statement_id="c1",
            question_instruction_markers=["select"],
            choice_markers=["alpha"],
            choice_is_noun_phrase_like=True,
        )
        self.assertIn("binding_not_explicit", candidate.unsupported_gaps)

    def test_helper_creates_human_explanation(self):
        candidate = create_choice_stem_binding_candidate(binding_id="b1")
        self.assertTrue(candidate.human_explanation)

    def test_helper_does_not_store_raw_text(self):
        candidate = create_choice_stem_binding_candidate(binding_id="b1")
        self.assertFalse(candidate.legibility.raw_text_required_for_review)
        self.assertFalse(candidate.anti_gaming.stores_raw_benchmark_text_by_default)

    def test_helper_does_not_select_answers(self):
        candidate = create_choice_stem_binding_candidate(binding_id="b1")
        self.assertFalse(candidate.anti_gaming.answer_selection_enabled)

    def test_helper_does_not_use_answer_key(self):
        candidate = create_choice_stem_binding_candidate(binding_id="b1")
        self.assertFalse(candidate.anti_gaming.uses_answer_key)

    def test_item_helper_creates_multiple_bindings(self):
        candidates = create_choice_stem_bindings_for_item(
            item_ref="safe_ref",
            question_instruction_records=[{"statement_id": "q1", "role": "question_instruction", "normalized_text": "which conclusion follows"}],
            choice_claim_records=[
                {"statement_id": "c1", "role": "choice_claim", "normalized_text": "alpha"},
                {"statement_id": "c2", "role": "choice_claim", "normalized_text": "beta"},
            ],
        )
        self.assertEqual(len(candidates), 2)

    def test_item_helper_skips_missing_ids(self):
        candidates = create_choice_stem_bindings_for_item(
            question_instruction_records=[{"statement_id": "", "role": "question_instruction", "normalized_text": "which conclusion follows"}],
            choice_claim_records=[{"statement_id": "c1", "role": "choice_claim", "normalized_text": "alpha"}],
        )
        self.assertEqual(candidates, [])

    def test_diagnostic_summary_counts_binding_types(self):
        candidates = [
            create_choice_stem_binding_candidate(
                binding_id="b1",
                source_question_instruction_id="q1",
                source_choice_statement_id="c1",
                choice_is_full_claim_like=True,
                confidence="medium",
            )
        ]
        summary = summarize_choice_stem_binding_diagnostics(candidates)
        self.assertEqual(summary["binding_candidate_count"], 1)
        self.assertEqual(summary["type_counts"]["full_claim"], 1)
        self.assertEqual(summary["medium_confidence_count"], 1)

    def test_diagnostic_summary_is_redacted(self):
        summary = summarize_choice_stem_binding_diagnostics([])
        self.assertIsInstance(summary, dict)
        self.assertNotIn("raw", repr(summary).lower())

    def test_diagnostic_summary_forbidden_terms_absent(self):
        summary_text = repr(summarize_choice_stem_binding_diagnostics([])).lower()
        for forbidden in ["question", "choice", "answer_key", "correct_answer", "raw_text"]:
            self.assertNotIn(forbidden, summary_text)

    def test_schema_tests_still_pass(self):
        result = subprocess.run(
            [sys.executable, "weslr/tests/test_choice_stem_binding_schema_v1.py"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_design_tests_still_pass(self):
        result = subprocess.run(
            [sys.executable, "weslr/tests/test_choice_stem_binding_design_v1.py"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_gate_and_check_pass(self):
        for command in [
            [sys.executable, "weslr/tests/release_gate_v1.py"],
            ["bash", "scripts/weslr_release_check.sh"],
        ]:
            with self.subTest(command=command):
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
