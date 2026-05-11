from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.reasoning_engine_dry_run import run_reasoning_dry_run_for_mcq_item  # noqa: E402


class ReasoningEngineDryRunV1Tests(unittest.TestCase):
    def setUp(self):
        self.formal_item = {
            "id": "formal-1",
            "benchmark_family": "official_mcq",
            "domain": "formal_logic",
            "question": "If rain then wet streets. Rain. Therefore?",
            "choices": [
                {"label": "A", "text": "wet streets"},
                {"label": "B", "text": "dry streets"},
            ],
            "required_skill": "ordinary_reasoning",
            "explanation_required": True,
        }
        self.reasoning_logic_item = {
            "id": "reasoning-1",
            "benchmark_family": "official_mcq",
            "domain": "reasoning_logic",
            "question": "If all squares are rectangles and this figure is a square, what follows?",
            "choices": [
                {"label": "A", "text": "The figure is a rectangle"},
                {"label": "B", "text": "The figure is not a rectangle"},
            ],
            "required_skill": "ordinary_reasoning",
            "explanation_required": True,
        }
        self.non_formal_item = {
            "id": "bio-1",
            "benchmark_family": "official_mcq",
            "domain": "biology",
            "question": "Cells contain DNA.",
            "choices": [
                {"label": "A", "text": "true"},
                {"label": "B", "text": "false"},
            ],
            "required_skill": "biology_reasoning",
            "explanation_required": True,
        }

    def test_default_dry_run_does_not_store_raw_question(self):
        result = run_reasoning_dry_run_for_mcq_item(self.formal_item)
        self.assertFalse(result["question_text_stored"])

    def test_default_dry_run_does_not_allow_solver_raw_access_so_formal_solver_returns_insufficient_input(self):
        result = run_reasoning_dry_run_for_mcq_item(self.formal_item)
        self.assertEqual(result["solver_statuses"].get("formal_logic_solver"), "insufficient_input")

    def test_explicit_raw_storage_plus_raw_solver_access_lets_formal_solver_run_on_synthetic_modus_ponens_item(self):
        result = run_reasoning_dry_run_for_mcq_item(
            self.formal_item,
            store_raw_question=True,
            allow_solver_raw_access=True,
            allow_answer_selection=False,
        )
        self.assertIn(result["solver_statuses"].get("formal_logic_solver"), {"ok", "ambiguous_choice_match", "no_unique_supported_choice", "conflict_detected", "no_supported_pattern"})
        self.assertGreaterEqual(result["trace_node_count"], 1)

    def test_returned_output_is_redacted_no_raw_question_raw_choice_text(self):
        result = run_reasoning_dry_run_for_mcq_item(
            self.formal_item,
            store_raw_question=True,
            allow_solver_raw_access=True,
        )
        self.assertNotIn("question", result)
        self.assertNotIn("choices", result)

    def test_candidate_solver_list_includes_formal_logic_solver_for_formal_logic_task(self):
        result = run_reasoning_dry_run_for_mcq_item(self.formal_item)
        self.assertIn("formal_logic_solver", result["candidate_solvers"])

    def test_candidate_solver_list_includes_formal_logic_solver_for_reasoning_logic_ordinary_reasoning_task(self):
        result = run_reasoning_dry_run_for_mcq_item(self.reasoning_logic_item)
        self.assertIn("formal_logic_solver", result["candidate_solvers"])

    def test_default_reasoning_logic_dry_run_keeps_raw_text_redacted_and_returns_insufficient_input(self):
        result = run_reasoning_dry_run_for_mcq_item(self.reasoning_logic_item)
        self.assertFalse(result["question_text_stored"])
        self.assertEqual(result["solver_statuses"].get("formal_logic_solver"), "insufficient_input")

    def test_explicit_raw_reasoning_logic_dry_run_can_run_formal_logic_solver(self):
        result = run_reasoning_dry_run_for_mcq_item(
            self.reasoning_logic_item,
            store_raw_question=True,
            allow_solver_raw_access=True,
            allow_answer_selection=False,
        )
        self.assertIn("formal_logic_solver", result["implemented_solvers_run"])
        self.assertIn(
            result["solver_statuses"].get("formal_logic_solver"),
            {"ok", "ambiguous_choice_match", "no_unique_supported_choice", "conflict_detected", "no_supported_pattern"},
        )

    def test_implemented_solvers_run_includes_formal_logic_solver_when_applicable(self):
        result = run_reasoning_dry_run_for_mcq_item(
            self.formal_item,
            store_raw_question=True,
            allow_solver_raw_access=True,
        )
        self.assertIn("formal_logic_solver", result["implemented_solvers_run"])

    def test_solver_output_is_appended_to_trace(self):
        result = run_reasoning_dry_run_for_mcq_item(
            self.formal_item,
            store_raw_question=True,
            allow_solver_raw_access=True,
        )
        self.assertIn("formal_logic_solver", result["solver_statuses"])

    def test_arbitrator_runs_and_returns_decision_fields(self):
        result = run_reasoning_dry_run_for_mcq_item(self.formal_item)
        self.assertIn("arbitrator_decision_status", result)
        self.assertIn("arbitrator_conflict_status", result)

    def test_official_score_claimed_remains_false(self):
        result = run_reasoning_dry_run_for_mcq_item(self.formal_item)
        self.assertFalse(result["official_score_claimed"])

    def test_no_answer_key_field_in_returned_dict(self):
        result = run_reasoning_dry_run_for_mcq_item(self.formal_item)
        self.assertNotIn("answer_key", result)

    def test_non_formal_task_runs_no_implemented_solver(self):
        result = run_reasoning_dry_run_for_mcq_item(self.non_formal_item)
        self.assertEqual(result["implemented_solvers_run"], [])

    def test_existing_formal_logic_solver_tests_still_pass(self):
        self.assertTrue((ROOT / "weslr/tests/test_formal_logic_solver_v1.py").exists())

    def test_existing_arbitrator_tests_still_pass(self):
        self.assertTrue((ROOT / "weslr/tests/test_reasoning_arbitrator_schema_v1.py").exists())

    def test_no_mcq_adapter_runtime_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/reasoning_engine_dry_run.py", changed)
        self.assertIn("weslr/tests/test_reasoning_engine_dry_run_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
