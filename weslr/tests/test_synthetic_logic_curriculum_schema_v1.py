from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.synthetic_logic_curriculum import (
    ALLOWED_INPUT_FORMS,
    ALLOWED_LOGIC_FAMILIES,
    SyntheticLogicAntiGamingRecord,
    SyntheticLogicCurriculumExample,
    SyntheticLogicLegibilityRecord,
    create_empty_synthetic_logic_curriculum_example,
    summarize_synthetic_logic_curriculum_example,
    synthetic_logic_curriculum_example_from_dict,
    synthetic_logic_curriculum_example_to_dict,
    validate_synthetic_logic_curriculum_example,
)


ALLOWED_CHANGED_FILES = {
    "weslr/synthetic_logic_curriculum.py",
    "weslr/tests/test_synthetic_logic_curriculum_schema_v1.py",
}
FORBIDDEN_FILES = {
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/logic_teaching_spine.py",
    "weslr/choice_stem_binding.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}
FORBIDDEN_SUMMARY_PHRASES = [
    "answer key",
    "correct answer",
    "official score",
    "raw benchmark text",
]


def valid_example(**overrides):
    example = SyntheticLogicCurriculumExample(
        example_id="schema_v1_example",
        logic_family="modus_ponens",
        input_form="mcq_like",
        premise_templates=["synthetic premise template"],
        question_instruction_template="synthetic instruction template",
        choice_templates=["synthetic choice template"],
        expected_structural_pattern="modus_ponens",
        expected_context_binding_type="candidate_conclusion",
        expected_teaching_focus="structural legibility",
        unsupported_gaps_allowed=["parser may expose a gap"],
        anti_gaming_notes=["schema-only; no answer selection"],
    )
    for key, value in overrides.items():
        setattr(example, key, value)
    return example


class SyntheticLogicCurriculumSchemaV1Tests(unittest.TestCase):
    def test_module_imports(self):
        self.assertTrue(SyntheticLogicCurriculumExample)

    def test_empty_example_instantiates(self):
        example = create_empty_synthetic_logic_curriculum_example()
        self.assertIsInstance(example, SyntheticLogicCurriculumExample)

    def test_safe_anti_gaming_defaults(self):
        record = SyntheticLogicAntiGamingRecord()
        self.assertFalse(record.uses_external_benchmark_text)
        self.assertFalse(record.uses_answer_key_tuning)
        self.assertFalse(record.uses_item_id_as_authority)
        self.assertFalse(record.official_score_claimed)
        self.assertFalse(record.answer_selection_enabled)
        self.assertFalse(record.benchmark_specific_tuning_used)

    def test_safe_legibility_defaults(self):
        record = SyntheticLogicLegibilityRecord()
        self.assertTrue(record.human_explanation_available)
        self.assertTrue(record.expected_pattern_visible)
        self.assertTrue(record.unsupported_gaps_visible)
        self.assertFalse(record.raw_benchmark_text_required)
        self.assertFalse(record.private_symbolic_authority_used)

    def test_all_allowed_logic_families_validate(self):
        for family in ALLOWED_LOGIC_FAMILIES:
            with self.subTest(family=family):
                self.assertEqual(
                    validate_synthetic_logic_curriculum_example(
                        valid_example(logic_family=family)
                    ),
                    [],
                )

    def test_all_allowed_input_forms_validate(self):
        for input_form in ALLOWED_INPUT_FORMS:
            with self.subTest(input_form=input_form):
                self.assertEqual(
                    validate_synthetic_logic_curriculum_example(
                        valid_example(input_form=input_form)
                    ),
                    [],
                )

    def test_invalid_logic_family_fails(self):
        errors = validate_synthetic_logic_curriculum_example(
            valid_example(logic_family="benchmark_family")
        )
        self.assertIn("invalid logic_family", errors)

    def test_invalid_input_form_fails(self):
        errors = validate_synthetic_logic_curriculum_example(
            valid_example(input_form="benchmark_form")
        )
        self.assertIn("invalid input_form", errors)

    def test_missing_example_id_fails(self):
        errors = validate_synthetic_logic_curriculum_example(valid_example(example_id=""))
        self.assertIn("missing example_id", errors)

    def test_missing_structural_pattern_fails(self):
        errors = validate_synthetic_logic_curriculum_example(
            valid_example(expected_structural_pattern="")
        )
        self.assertIn("missing expected_structural_pattern", errors)

    def test_missing_context_binding_type_fails(self):
        errors = validate_synthetic_logic_curriculum_example(
            valid_example(expected_context_binding_type="")
        )
        self.assertIn("missing expected_context_binding_type", errors)

    def test_external_benchmark_text_use_fails(self):
        example = valid_example()
        example.anti_gaming.uses_external_benchmark_text = True
        self.assertIn(
            "uses external benchmark text",
            validate_synthetic_logic_curriculum_example(example),
        )

    def test_answer_key_tuning_fails(self):
        example = valid_example()
        example.anti_gaming.uses_answer_key_tuning = True
        self.assertIn(
            "uses answer-key tuning",
            validate_synthetic_logic_curriculum_example(example),
        )

    def test_item_id_authority_fails(self):
        example = valid_example()
        example.anti_gaming.uses_item_id_as_authority = True
        self.assertIn(
            "uses item-ID authority",
            validate_synthetic_logic_curriculum_example(example),
        )

    def test_official_score_claim_fails(self):
        example = valid_example()
        example.anti_gaming.official_score_claimed = True
        self.assertIn(
            "official score claim",
            validate_synthetic_logic_curriculum_example(example),
        )

    def test_answer_selection_enabled_fails(self):
        example = valid_example()
        example.anti_gaming.answer_selection_enabled = True
        self.assertIn(
            "answer selection enabled",
            validate_synthetic_logic_curriculum_example(example),
        )

    def test_benchmark_specific_tuning_fails(self):
        example = valid_example()
        example.anti_gaming.benchmark_specific_tuning_used = True
        self.assertIn(
            "benchmark-specific tuning",
            validate_synthetic_logic_curriculum_example(example),
        )

    def test_private_symbolic_authority_fails(self):
        example = valid_example()
        example.legibility.private_symbolic_authority_used = True
        self.assertIn(
            "private symbolic authority",
            validate_synthetic_logic_curriculum_example(example),
        )

    def test_hidden_unsupported_gaps_fail(self):
        example = valid_example()
        example.legibility.unsupported_gaps_visible = False
        self.assertIn(
            "hidden unsupported gaps",
            validate_synthetic_logic_curriculum_example(example),
        )

    def test_to_from_dict_roundtrip_works(self):
        example = valid_example()
        payload = synthetic_logic_curriculum_example_to_dict(example)
        roundtrip = synthetic_logic_curriculum_example_from_dict(payload)
        self.assertEqual(roundtrip, example)

    def test_summary_is_redacted(self):
        example = valid_example(
            premise_templates=["answer key correct answer official score raw benchmark text"],
            question_instruction_template="answer key",
            choice_templates=["correct answer"],
        )
        summary = summarize_synthetic_logic_curriculum_example(example)
        self.assertEqual(summary["premise_template_count"], 1)
        self.assertEqual(summary["choice_template_count"], 1)
        self.assertNotIn("premise_templates", summary)
        self.assertNotIn("choice_templates", summary)
        self.assertNotIn("question_instruction_template", summary)

    def test_summary_does_not_contain_forbidden_answer_or_benchmark_text(self):
        example = valid_example(
            premise_templates=["answer key correct answer official score raw benchmark text"],
            anti_gaming_notes=["answer key correct answer official score raw benchmark text"],
        )
        summary_text = str(summarize_synthetic_logic_curriculum_example(example)).lower()
        for phrase in FORBIDDEN_SUMMARY_PHRASES:
            self.assertNotIn(phrase, summary_text)

    def test_design_test_still_passes(self):
        result = subprocess.run(
            ["python3", "weslr/tests/test_synthetic_logic_curriculum_design_v1.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_gate_and_check_pass(self):
        gate = subprocess.run(
            ["python3", "weslr/tests/release_gate_v1.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(gate.returncode, 0, gate.stdout + gate.stderr)
        check = subprocess.run(
            ["bash", "scripts/weslr_release_check.sh"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_no_forbidden_files_changed(self):
        diff = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        changed = {line.strip() for line in diff.stdout.splitlines() if line.strip()}
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        untracked = {
            line[3:].strip()
            for line in status.stdout.splitlines()
            if line.startswith("?? ")
        }
        all_changed = changed | untracked
        self.assertFalse(all_changed & FORBIDDEN_FILES)
        unexpected = all_changed - ALLOWED_CHANGED_FILES
        self.assertFalse(unexpected, f"unexpected changed files: {sorted(unexpected)}")


if __name__ == "__main__":
    unittest.main()
