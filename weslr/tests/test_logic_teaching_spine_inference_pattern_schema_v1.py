from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.logic_teaching_spine import (  # noqa: E402
    create_empty_inference_pattern,
    inference_pattern_from_dict,
    inference_pattern_to_dict,
    make_affirming_consequent_fallacy_pattern,
    make_denying_antecedent_fallacy_pattern,
    make_modus_ponens_pattern,
    make_modus_tollens_pattern,
    make_necessary_sufficient_confusion_pattern,
    make_universal_syllogism_pattern,
    summarize_inference_pattern,
    validate_inference_pattern,
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
    "weslr/tests/test_logic_teaching_spine_schema_v1.py",
    "weslr/tests/test_logic_teaching_spine_inference_pattern_schema_v1.py",
}


class LogicTeachingSpineInferencePatternSchemaV1Tests(unittest.TestCase):
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

    def test_instantiate_empty_pattern(self):
        pattern = create_empty_inference_pattern(pattern_id="pattern:1")
        self.assertEqual("pattern:1", pattern.pattern_id)

    def test_safe_anti_gaming_defaults(self):
        pattern = create_empty_inference_pattern()
        self.assertFalse(pattern.anti_gaming.uses_answer_key)
        self.assertFalse(pattern.anti_gaming.uses_item_id_as_authority)
        self.assertFalse(pattern.anti_gaming.uses_answer_position_bias)
        self.assertFalse(pattern.anti_gaming.claims_official_score)
        self.assertTrue(pattern.anti_gaming.no_answer_selection)

    def test_safe_legibility_defaults(self):
        pattern = create_empty_inference_pattern()
        self.assertFalse(pattern.legibility.stores_raw_benchmark_text)
        self.assertTrue(pattern.legibility.redacted_summary_only)
        self.assertFalse(pattern.legibility.private_symbolic_authority)

    def test_roundtrip_to_from_dict(self):
        pattern = create_empty_inference_pattern(
            pattern_id="pattern:1",
            pattern_family="conditional_inference",
            pattern_name="modus ponens",
            validity_type="valid",
        )
        pattern.required_proposition_roles = ["conditional_premise", "antecedent_premise"]
        pattern.supported_proposition_types = ["conditional"]
        pattern.human_explanation = "Valid conditional inference pattern."
        data = inference_pattern_to_dict(pattern)
        restored = inference_pattern_from_dict(data)
        self.assertEqual(data, inference_pattern_to_dict(restored))

    def test_summary_redacted(self):
        pattern = create_empty_inference_pattern(pattern_id="pattern:1", pattern_name="secret", pattern_family="family")
        pattern.description = "Hidden description"
        pattern.human_explanation = "Hidden explanation"
        summary = summarize_inference_pattern(pattern)
        self.assertNotIn("description", summary)
        self.assertNotIn("human_explanation", summary)

    def test_validation_flags_missing_id(self):
        self.assertIn("missing pattern id", validate_inference_pattern(create_empty_inference_pattern(pattern_name="name")))

    def test_validation_flags_missing_name(self):
        self.assertIn("missing pattern name", validate_inference_pattern(create_empty_inference_pattern(pattern_id="pattern:1")))

    def test_validation_flags_official_score_claim(self):
        pattern = create_empty_inference_pattern(pattern_id="pattern:1", pattern_name="name")
        pattern.anti_gaming.claims_official_score = True
        self.assertIn("official-score claim is forbidden", validate_inference_pattern(pattern))

    def test_validation_flags_answer_key_use(self):
        pattern = create_empty_inference_pattern(pattern_id="pattern:1", pattern_name="name")
        pattern.anti_gaming.uses_answer_key = True
        self.assertIn("answer-key use is forbidden", validate_inference_pattern(pattern))

    def test_validation_flags_item_id_authority(self):
        pattern = create_empty_inference_pattern(pattern_id="pattern:1", pattern_name="name")
        pattern.anti_gaming.uses_item_id_as_authority = True
        self.assertIn("item-id authority is forbidden", validate_inference_pattern(pattern))

    def test_validation_flags_raw_benchmark_storage(self):
        pattern = create_empty_inference_pattern(pattern_id="pattern:1", pattern_name="name")
        pattern.legibility.stores_raw_benchmark_text = True
        self.assertIn("raw benchmark storage by default is forbidden", validate_inference_pattern(pattern))

    def test_validation_flags_answer_selection(self):
        pattern = create_empty_inference_pattern(pattern_id="pattern:1", pattern_name="name")
        pattern.anti_gaming.no_answer_selection = False
        self.assertIn("answer selection must remain disabled", validate_inference_pattern(pattern))

    def test_predefined_constructor_returns_modus_ponens(self):
        pattern = make_modus_ponens_pattern()
        self.assertEqual("modus ponens", pattern.pattern_name)
        self.assertEqual("conditional_inference", pattern.pattern_family)

    def test_predefined_constructor_returns_modus_tollens(self):
        pattern = make_modus_tollens_pattern()
        self.assertEqual("modus tollens", pattern.pattern_name)
        self.assertEqual("conditional_inference", pattern.pattern_family)

    def test_predefined_constructor_returns_universal_syllogism(self):
        pattern = make_universal_syllogism_pattern()
        self.assertEqual("universal syllogism", pattern.pattern_name)
        self.assertEqual("syllogism", pattern.pattern_family)

    def test_predefined_constructor_returns_affirming_consequent_fallacy(self):
        pattern = make_affirming_consequent_fallacy_pattern()
        self.assertEqual("affirming the consequent", pattern.pattern_name)
        self.assertEqual("conditional_fallacy", pattern.pattern_family)

    def test_predefined_constructor_returns_denying_antecedent_fallacy(self):
        pattern = make_denying_antecedent_fallacy_pattern()
        self.assertEqual("denying the antecedent", pattern.pattern_name)
        self.assertEqual("conditional_fallacy", pattern.pattern_family)

    def test_predefined_constructor_returns_necessary_sufficient_confusion(self):
        pattern = make_necessary_sufficient_confusion_pattern()
        self.assertEqual("necessary/sufficient confusion", pattern.pattern_name)
        self.assertEqual("condition_confusion", pattern.pattern_family)

    def test_fallacy_patterns_are_invalid(self):
        for pattern in [
            make_affirming_consequent_fallacy_pattern(),
            make_denying_antecedent_fallacy_pattern(),
            make_necessary_sufficient_confusion_pattern(),
        ]:
            self.assertEqual("invalid", pattern.validity_type)

    def test_valid_patterns_are_valid(self):
        for pattern in [
            make_modus_ponens_pattern(),
            make_modus_tollens_pattern(),
            make_universal_syllogism_pattern(),
        ]:
            self.assertEqual("valid", pattern.validity_type)

    def test_counterexample_required_patterns_marked_correctly(self):
        self.assertFalse(make_modus_ponens_pattern().counterexample_required)
        self.assertFalse(make_modus_tollens_pattern().counterexample_required)
        self.assertFalse(make_universal_syllogism_pattern().counterexample_required)
        self.assertTrue(make_affirming_consequent_fallacy_pattern().counterexample_required)
        self.assertTrue(make_denying_antecedent_fallacy_pattern().counterexample_required)
        self.assertTrue(make_necessary_sufficient_confusion_pattern().counterexample_required)

    def test_existing_proposition_schema_tests_still_pass(self):
        output = self.run_direct("python3 weslr/tests/test_logic_teaching_spine_schema_v1.py")
        self.assertIn("OK", output)

    def test_existing_teaching_spine_design_test_still_passes(self):
        output = self.run_direct("python3 weslr/tests/test_logic_teaching_spine_design_v1.py")
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
