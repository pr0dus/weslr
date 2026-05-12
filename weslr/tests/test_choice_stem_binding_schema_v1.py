from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.choice_stem_binding import (  # noqa: E402
    ALLOWED_STEM_BINDING_TYPES,
    ChoiceStemBindingAntiGamingRecord,
    ChoiceStemBindingCandidate,
    ChoiceStemBindingLegibilityRecord,
    choice_stem_binding_candidate_from_dict,
    choice_stem_binding_candidate_to_dict,
    create_empty_choice_stem_binding_candidate,
    summarize_choice_stem_binding_candidate,
    validate_choice_stem_binding_candidate,
)


class ChoiceStemBindingSchemaV1Tests(unittest.TestCase):
    def _valid_candidate(self) -> ChoiceStemBindingCandidate:
        return ChoiceStemBindingCandidate(
            binding_id="binding-ref-1",
            source_question_instruction_id="instruction-ref-1",
            source_choice_statement_id="statement-ref-1",
            stem_binding_type="choice_is_full_claim",
            confidence="medium",
            human_explanation="Structural schema record only.",
        )

    def test_schema_module_imports(self):
        self.assertTrue(callable(validate_choice_stem_binding_candidate))

    def test_empty_candidate_can_instantiate(self):
        candidate = create_empty_choice_stem_binding_candidate()
        self.assertIsInstance(candidate, ChoiceStemBindingCandidate)

    def test_safe_anti_gaming_defaults(self):
        record = ChoiceStemBindingAntiGamingRecord()
        self.assertFalse(record.uses_answer_key)
        self.assertFalse(record.uses_item_id_as_authority)
        self.assertFalse(record.uses_answer_position_bias)
        self.assertFalse(record.stores_raw_benchmark_text_by_default)
        self.assertFalse(record.benchmark_specific_tuning_used)
        self.assertFalse(record.answer_selection_enabled)
        self.assertFalse(record.official_score_claimed)

    def test_safe_legibility_defaults(self):
        record = ChoiceStemBindingLegibilityRecord()
        self.assertTrue(record.human_explanation_available)
        self.assertTrue(record.unsupported_gaps_visible)
        self.assertTrue(record.binding_warrants_available)
        self.assertFalse(record.private_symbolic_authority_used)
        self.assertFalse(record.raw_text_required_for_review)

    def test_all_allowed_binding_types_validate(self):
        for binding_type in ALLOWED_STEM_BINDING_TYPES:
            with self.subTest(binding_type=binding_type):
                candidate = self._valid_candidate()
                candidate.stem_binding_type = binding_type
                self.assertEqual(validate_choice_stem_binding_candidate(candidate), [])

    def test_invalid_binding_type_fails_validation(self):
        candidate = self._valid_candidate()
        candidate.stem_binding_type = "benchmark_patch"
        self.assertIn(
            "invalid_stem_binding_type",
            validate_choice_stem_binding_candidate(candidate),
        )

    def test_invalid_confidence_fails_validation(self):
        candidate = self._valid_candidate()
        candidate.confidence = "certain"
        self.assertIn("invalid_confidence", validate_choice_stem_binding_candidate(candidate))

    def test_missing_binding_id_fails_validation(self):
        candidate = self._valid_candidate()
        candidate.binding_id = ""
        self.assertIn("missing_binding_id", validate_choice_stem_binding_candidate(candidate))

    def test_high_confidence_missing_choice_statement_id_fails_validation(self):
        candidate = self._valid_candidate()
        candidate.confidence = "high"
        candidate.source_choice_statement_id = ""
        self.assertIn(
            "high_confidence_missing_source_choice_statement_id",
            validate_choice_stem_binding_candidate(candidate),
        )

    def test_high_confidence_missing_explanation_fails_validation(self):
        candidate = self._valid_candidate()
        candidate.confidence = "high"
        candidate.human_explanation = ""
        self.assertIn(
            "high_confidence_missing_human_explanation",
            validate_choice_stem_binding_candidate(candidate),
        )

    def test_validation_flags_answer_key_use(self):
        candidate = self._valid_candidate()
        candidate.anti_gaming.uses_answer_key = True
        self.assertIn("answer_key_use", validate_choice_stem_binding_candidate(candidate))

    def test_validation_flags_item_id_authority(self):
        candidate = self._valid_candidate()
        candidate.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item_id_authority", validate_choice_stem_binding_candidate(candidate))

    def test_validation_flags_answer_position_bias(self):
        candidate = self._valid_candidate()
        candidate.anti_gaming.uses_answer_position_bias = True
        self.assertIn("answer_position_bias", validate_choice_stem_binding_candidate(candidate))

    def test_validation_flags_raw_benchmark_text_storage_by_default(self):
        candidate = self._valid_candidate()
        candidate.anti_gaming.stores_raw_benchmark_text_by_default = True
        self.assertIn(
            "raw_benchmark_text_storage_by_default",
            validate_choice_stem_binding_candidate(candidate),
        )

    def test_validation_flags_benchmark_specific_tuning(self):
        candidate = self._valid_candidate()
        candidate.anti_gaming.benchmark_specific_tuning_used = True
        self.assertIn(
            "benchmark_specific_tuning",
            validate_choice_stem_binding_candidate(candidate),
        )

    def test_validation_flags_answer_selection_enabled(self):
        candidate = self._valid_candidate()
        candidate.anti_gaming.answer_selection_enabled = True
        self.assertIn(
            "answer_selection_enabled",
            validate_choice_stem_binding_candidate(candidate),
        )

    def test_validation_flags_official_score_claim(self):
        candidate = self._valid_candidate()
        candidate.anti_gaming.official_score_claimed = True
        self.assertIn(
            "official_score_claim",
            validate_choice_stem_binding_candidate(candidate),
        )

    def test_validation_flags_private_symbolic_authority(self):
        candidate = self._valid_candidate()
        candidate.legibility.private_symbolic_authority_used = True
        self.assertIn(
            "private_symbolic_authority",
            validate_choice_stem_binding_candidate(candidate),
        )

    def test_validation_flags_hidden_unsupported_gaps(self):
        candidate = self._valid_candidate()
        candidate.unsupported_gaps = ["relation_not_explicit"]
        candidate.legibility.unsupported_gaps_visible = False
        self.assertIn(
            "hidden_unsupported_gaps",
            validate_choice_stem_binding_candidate(candidate),
        )

    def test_to_from_dict_roundtrip_works(self):
        candidate = self._valid_candidate()
        candidate.unsupported_gaps = ["relation_not_explicit"]
        roundtrip = choice_stem_binding_candidate_from_dict(
            choice_stem_binding_candidate_to_dict(candidate)
        )
        self.assertEqual(roundtrip, candidate)

    def test_summary_is_redacted(self):
        candidate = self._valid_candidate()
        summary = summarize_choice_stem_binding_candidate(candidate)
        self.assertIsInstance(summary, dict)
        self.assertIn("unsupported_gap_count", summary)
        self.assertNotIn("choice_is_full_claim", repr(summary))

    def test_summary_forbidden_terms_absent(self):
        candidate = self._valid_candidate()
        summary_text = repr(summarize_choice_stem_binding_candidate(candidate)).lower()
        for forbidden in [
            "question",
            "choice",
            "answer_label",
            "correct_answer",
            "answer_key",
            "raw_text",
        ]:
            self.assertNotIn(forbidden, summary_text)

    def test_design_doc_test_still_passes(self):
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

    def test_no_forbidden_files_changed(self):
        forbidden = {
            "weslr/formal_logic_parser.py",
            "weslr/logical_form_normalizer.py",
            "weslr/logic_teaching_spine.py",
            "weslr/formal_logic_solver.py",
            "weslr/evals/official_mcq_adapter.py",
        }
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        self.assertFalse(changed & forbidden, f"Forbidden files changed: {sorted(changed & forbidden)}")


if __name__ == "__main__":
    unittest.main()
