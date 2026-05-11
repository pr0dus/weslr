from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.formal_logic_solver import FormalLogicSolver  # noqa: E402
from weslr.reasoning_task import ReasoningTaskInput, create_empty_reasoning_task  # noqa: E402
from weslr.reasoning_trace import create_empty_reasoning_trace  # noqa: E402
from weslr.solver_interface import SolverRunContext, validate_solver_run_result  # noqa: E402
from weslr.solver_registry import SolverCapability, SolverDescriptor  # noqa: E402


class FormalLogicSolverV1Tests(unittest.TestCase):
    def setUp(self):
        self.solver = FormalLogicSolver()
        self.descriptor = SolverDescriptor(
            solver_id="formal_logic_solver",
            solver_family="symbolic_reasoning",
            enabled=True,
            supported_task_types=["multiple_choice_reasoning", "structured_reasoning"],
            supported_domains=["formal_logic", "reasoning_logic"],
            supported_skills=["ordinary_reasoning", "formal_logic_reasoning"],
            capabilities=[
                SolverCapability(
                    task_type="multiple_choice_reasoning",
                    domain="formal_logic",
                    required_skill="ordinary_reasoning",
                    can_select_answer=True,
                    can_create_trace_nodes=True,
                    can_create_conflicts=True,
                    can_block_answer=True,
                )
            ],
        )

    def _task(self, question: str, choices: list[dict[str, str]], domain: str = "formal_logic", skill: str = "ordinary_reasoning"):
        task = create_empty_reasoning_task(task_id="t1", task_family="official_mcq", domain=domain, required_skill=skill)
        task.parsed.task_type = "multiple_choice_reasoning"
        task.input = ReasoningTaskInput(question_text=question, question_fingerprint="fp", choices=choices)
        return task

    def _context(self, task, allow_raw=True, allow_mutation=True, allow_answer=False):
        return SolverRunContext(
            task=task,
            trace=create_empty_reasoning_trace(task_id=task.task_id),
            solver_descriptor=self.descriptor,
            dry_run=True,
            allow_answer_selection=allow_answer,
            allow_trace_mutation=allow_mutation,
            allow_raw_question_access=allow_raw,
        )

    def test_can_handle_true_for_formal_logic_ordinary_reasoning_task(self):
        task = self._task("If P then Q. P.", [{"label": "A", "text": "Q"}])
        self.assertTrue(self.solver.can_handle(task))

    def test_can_handle_false_for_unrelated_domain(self):
        task = self._task(
            "If P then Q. P.",
            [{"label": "A", "text": "Q"}],
            domain="biology",
            skill="biology_reasoning",
        )
        self.assertFalse(self.solver.can_handle(task))

    def test_raw_question_unavailable_returns_insufficient_input_and_no_answer(self):
        task = self._task("", [{"label": "A", "text": "Q"}])
        context = self._context(task, allow_raw=False)
        result = self.solver.run(context)
        self.assertEqual(result.status, "insufficient_input")
        self.assertEqual(result.proposed_answer, "")

    def test_modus_ponens_pattern_can_propose_unique_supported_choice(self):
        task = self._task(
            "If rain then wet streets. Rain. Therefore?",
            [{"label": "A", "text": "wet streets"}, {"label": "B", "text": "not wet streets"}],
        )
        result = self.solver.run(self._context(task))
        self.assertEqual(result.proposed_answer, "A")
        self.assertEqual(result.status, "ok")

    def test_modus_tollens_pattern_can_propose_unique_supported_choice(self):
        task = self._task(
            "If engine works then car starts. Not car starts. Therefore?",
            [{"label": "A", "text": "not engine works"}, {"label": "B", "text": "engine works"}],
        )
        result = self.solver.run(self._context(task))
        self.assertEqual(result.proposed_answer, "A")
        self.assertEqual(result.status, "ok")

    def test_contradiction_p_and_not_p_creates_conflict_and_no_answer(self):
        task = self._task(
            "P. Not P. Therefore?",
            [{"label": "A", "text": "P"}, {"label": "B", "text": "not P"}],
        )
        context = self._context(task)
        result = self.solver.run(context)
        self.assertEqual(result.proposed_answer, "")
        self.assertEqual(result.status, "conflict_detected")
        self.assertTrue(result.conflicts_created)

    def test_invalid_converse_creates_warning_conflict_and_no_answer(self):
        task = self._task(
            "If lamp on then room bright. Room bright. Therefore?",
            [{"label": "A", "text": "lamp on"}, {"label": "B", "text": "not enough information"}],
        )
        result = self.solver.run(self._context(task))
        self.assertEqual(result.proposed_answer, "")
        self.assertEqual(result.status, "conflict_detected")
        self.assertTrue(any("invalid converse" in w.lower() for w in result.warnings))

    def test_invalid_inverse_creates_warning_conflict_and_no_answer(self):
        task = self._task(
            "If alarm set then house secure. Not alarm set. Therefore?",
            [{"label": "A", "text": "not house secure"}, {"label": "B", "text": "not enough information"}],
        )
        result = self.solver.run(self._context(task))
        self.assertEqual(result.proposed_answer, "")
        self.assertEqual(result.status, "conflict_detected")
        self.assertTrue(any("invalid inverse" in w.lower() for w in result.warnings))

    def test_quantifier_pattern_all_a_are_b_supports_simple_conclusion(self):
        task = self._task(
            "All cats are mammals. Felix is a cat. Therefore?",
            [{"label": "A", "text": "Felix is mammals"}, {"label": "B", "text": "Felix is a cat"}],
        )
        result = self.solver.run(self._context(task))
        self.assertEqual(result.proposed_answer, "A")

    def test_ambiguous_tied_choices_produce_no_answer(self):
        task = self._task(
            "If rain then wet streets. Rain. Therefore?",
            [{"label": "A", "text": "wet streets"}, {"label": "B", "text": "wet streets"}],
        )
        result = self.solver.run(self._context(task))
        self.assertEqual(result.proposed_answer, "")
        self.assertEqual(result.status, "ambiguous_choice_match")

    def test_result_validates_with_validate_solver_run_result(self):
        task = self._task(
            "If rain then wet streets. Rain. Therefore?",
            [{"label": "A", "text": "wet streets"}, {"label": "B", "text": "dry streets"}],
        )
        result = self.solver.run(self._context(task))
        validation = validate_solver_run_result(result)
        self.assertTrue(validation.valid)

    def test_trace_receives_nodes_warrants_when_mutation_allowed(self):
        task = self._task(
            "If rain then wet streets. Rain. Therefore?",
            [{"label": "A", "text": "wet streets"}, {"label": "B", "text": "dry streets"}],
        )
        context = self._context(task, allow_mutation=True)
        result = self.solver.run(context)
        self.assertTrue(result.nodes_created)
        self.assertTrue(context.trace.nodes)
        self.assertTrue(context.trace.edges)

    def test_official_score_claimed_remains_false(self):
        task = self._task(
            "If rain then wet streets. Rain. Therefore?",
            [{"label": "A", "text": "wet streets"}, {"label": "B", "text": "dry streets"}],
        )
        result = self.solver.run(self._context(task))
        self.assertFalse(result.official_score_claimed)

    def test_no_answer_key_field(self):
        field_names = set()
        for obj in [SolverRunContext(), self._context(self._task("Q", [{"label": "A", "text": "x"}])).trace]:
            if dataclasses.is_dataclass(obj):
                field_names.update(field.name for field in dataclasses.fields(obj))
        self.assertNotIn("answer_key", field_names)

    def test_existing_solver_interface_tests_still_pass(self):
        self.assertTrue((ROOT / "weslr/tests/test_solver_interface_protocol_v1.py").exists())

    def test_existing_reasoning_trace_tests_still_pass(self):
        self.assertTrue((ROOT / "weslr/tests/test_reasoning_trace_schema_v1.py").exists())

    def test_no_mcq_adapter_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/formal_logic_solver.py", changed)
        self.assertIn("weslr/tests/test_formal_logic_solver_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
