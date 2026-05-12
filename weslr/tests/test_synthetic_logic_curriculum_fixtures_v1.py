from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.synthetic_logic_curriculum import (
    SyntheticLogicCurriculumExample,
    load_synthetic_logic_curriculum_v1,
    summarize_synthetic_logic_curriculum_example,
    synthetic_logic_curriculum_example_to_dict,
    validate_synthetic_logic_curriculum_example,
)


REQUIRED_FAMILIES = {
    "universal_syllogism",
    "modus_ponens",
    "modus_tollens",
    "affirming_consequent",
    "denying_antecedent",
    "contradiction",
    "counterexample",
    "irrelevant_choice",
    "noun_phrase_choice_binding",
    "invalid_argument_identification",
    "necessary_sufficient_confusion",
    "quantifier_reasoning",
    "negation_reasoning",
    "disjunction_reasoning",
}
ALLOWED_CHANGED_FILES = {
    "weslr/synthetic_logic_curriculum.py",
    "weslr/tests/test_synthetic_logic_curriculum_fixtures_v1.py",
}
FORBIDDEN_FILES = {
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/logic_teaching_spine.py",
    "weslr/choice_stem_binding.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
}
FORBIDDEN_TEXT_MARKERS = [
    "mmlu",
    "external benchmark passage",
    "benchmark question",
    "official score",
    "correct answer",
]


class SyntheticLogicCurriculumFixturesV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = load_synthetic_logic_curriculum_v1()

    def test_fixture_loader_imports(self):
        self.assertTrue(callable(load_synthetic_logic_curriculum_v1))

    def test_fixture_loader_returns_list(self):
        self.assertIsInstance(self.fixtures, list)
        self.assertTrue(all(isinstance(item, SyntheticLogicCurriculumExample) for item in self.fixtures))

    def test_fixture_count_is_at_least_10(self):
        self.assertGreaterEqual(len(self.fixtures), 10)

    def test_every_fixture_validates(self):
        for fixture in self.fixtures:
            with self.subTest(example_id=fixture.example_id):
                self.assertEqual(validate_synthetic_logic_curriculum_example(fixture), [])

    def test_every_fixture_has_example_id(self):
        for fixture in self.fixtures:
            self.assertTrue(fixture.example_id.strip())

    def test_every_fixture_has_logic_family(self):
        for fixture in self.fixtures:
            self.assertTrue(fixture.logic_family.strip())

    def test_every_fixture_has_expected_structural_pattern(self):
        for fixture in self.fixtures:
            self.assertTrue(fixture.expected_structural_pattern.strip())

    def test_every_fixture_has_expected_context_binding_type(self):
        for fixture in self.fixtures:
            self.assertTrue(fixture.expected_context_binding_type.strip())

    def test_required_families_are_covered(self):
        families = {fixture.logic_family for fixture in self.fixtures}
        self.assertTrue(REQUIRED_FAMILIES <= families)

    def test_fixtures_contain_no_external_benchmark_text_markers(self):
        joined = "\n".join(str(synthetic_logic_curriculum_example_to_dict(f)) for f in self.fixtures).lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            self.assertNotIn(marker, joined)

    def test_fixtures_contain_no_answer_key_field(self):
        for fixture in self.fixtures:
            payload = synthetic_logic_curriculum_example_to_dict(fixture)
            self.assertNotIn("answer_key", payload)
            self.assertNotIn("answer_key", payload.get("legibility", {}))

    def test_fixtures_contain_no_correct_answer_field(self):
        for fixture in self.fixtures:
            payload = synthetic_logic_curriculum_example_to_dict(fixture)
            self.assertNotIn("correct_answer", payload)
            self.assertNotIn("correct_answer", payload.get("legibility", {}))
            self.assertNotIn("correct_answer", payload.get("anti_gaming", {}))

    def test_fixtures_do_not_enable_answer_selection(self):
        for fixture in self.fixtures:
            self.assertFalse(fixture.anti_gaming.answer_selection_enabled)

    def test_fixtures_do_not_claim_official_score(self):
        for fixture in self.fixtures:
            self.assertFalse(fixture.anti_gaming.official_score_claimed)

    def test_summaries_are_redacted(self):
        for fixture in self.fixtures:
            summary = summarize_synthetic_logic_curriculum_example(fixture)
            self.assertNotIn("premise_templates", summary)
            self.assertNotIn("question_instruction_template", summary)
            self.assertNotIn("choice_templates", summary)
            summary_text = str(summary).lower()
            self.assertNotIn("correct answer", summary_text)
            self.assertNotIn("official score", summary_text)
            self.assertNotIn("raw benchmark text", summary_text)

    def test_schema_tests_still_pass(self):
        result = subprocess.run(
            ["python3", "weslr/tests/test_synthetic_logic_curriculum_schema_v1.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_design_tests_still_pass(self):
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
            ["git", "diff", "--name-only", "HEAD"],
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
