from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.reasoning_task import create_empty_reasoning_task  # noqa: E402
from weslr.reasoning_trace import create_empty_reasoning_trace  # noqa: E402
from weslr.solver_interface import (  # noqa: E402
    ReasoningSolverProtocol,
    SolverRunContext,
    SolverRunResult,
    solver_run_result_to_solver_output,
    validate_solver_run_context,
    validate_solver_run_result,
)
from weslr.solver_registry import SolverCapability, SolverDescriptor  # noqa: E402


class FakeSolver:
    solver_id = "fake_solver"
    solver_family = "test"

    def can_handle(self, task):
        return True

    def run(self, context):
        return SolverRunResult(solver_id=self.solver_id, solver_family=self.solver_family, status="ok")


class SolverInterfaceProtocolV1Tests(unittest.TestCase):
    def _descriptor(self, **overrides):
        descriptor = SolverDescriptor(
            solver_id="solver-1",
            solver_family="test",
            enabled=False,
            supported_task_types=["multiple_choice_reasoning"],
            supported_domains=["formal_logic"],
            supported_skills=["ordinary_reasoning"],
            capabilities=[SolverCapability(can_select_answer=True)],
        )
        for key, value in overrides.items():
            setattr(descriptor, key, value)
        return descriptor

    def test_solver_run_context_defaults_are_safe(self):
        context = SolverRunContext()
        self.assertTrue(context.dry_run)
        self.assertFalse(context.allow_answer_selection)
        self.assertTrue(context.allow_trace_mutation)
        self.assertFalse(context.allow_raw_question_access)
        self.assertEqual(context.metadata, {})

    def test_solver_run_result_defaults_are_safe(self):
        result = SolverRunResult()
        self.assertEqual(result.proposed_answer, "")
        self.assertEqual(result.confidence, "")
        self.assertFalse(result.official_score_claimed)
        self.assertTrue(result.anti_gaming_passed)
        self.assertTrue(result.legibility_passed)

    def test_validate_context_flags_missing_task(self):
        context = SolverRunContext(trace=create_empty_reasoning_trace(task_id="t1"), solver_descriptor=self._descriptor())
        validation = validate_solver_run_context(context)
        self.assertFalse(validation.valid)
        self.assertTrue(any("context.task" in e for e in validation.errors))

    def test_validate_context_flags_missing_trace(self):
        context = SolverRunContext(task=create_empty_reasoning_task(), solver_descriptor=self._descriptor())
        validation = validate_solver_run_context(context)
        self.assertFalse(validation.valid)
        self.assertTrue(any("context.trace" in e for e in validation.errors))

    def test_validate_context_flags_missing_solver_descriptor(self):
        context = SolverRunContext(task=create_empty_reasoning_task(), trace=create_empty_reasoning_trace(task_id="t1"))
        validation = validate_solver_run_context(context)
        self.assertFalse(validation.valid)
        self.assertTrue(any("context.solver_descriptor" in e for e in validation.errors))

    def test_validate_context_flags_raw_question_access_when_no_raw_question_present(self):
        task = create_empty_reasoning_task()
        context = SolverRunContext(
            task=task,
            trace=create_empty_reasoning_trace(task_id="t1"),
            solver_descriptor=self._descriptor(),
            allow_raw_question_access=True,
        )
        validation = validate_solver_run_context(context)
        self.assertFalse(validation.valid)
        self.assertTrue(any("allow_raw_question_access" in e for e in validation.errors))

    def test_validate_context_flags_answer_selection_not_allowed_by_descriptor(self):
        descriptor = self._descriptor(capabilities=[SolverCapability(can_select_answer=False)])
        context = SolverRunContext(
            task=create_empty_reasoning_task(),
            trace=create_empty_reasoning_trace(task_id="t1"),
            solver_descriptor=descriptor,
            allow_answer_selection=True,
        )
        validation = validate_solver_run_context(context)
        self.assertFalse(validation.valid)
        self.assertTrue(any("cannot select answers" in e for e in validation.errors))

    def test_disabled_descriptor_gives_warning_in_dry_run_not_hard_error(self):
        context = SolverRunContext(
            task=create_empty_reasoning_task(),
            trace=create_empty_reasoning_trace(task_id="t1"),
            solver_descriptor=self._descriptor(enabled=False),
        )
        validation = validate_solver_run_context(context)
        self.assertTrue(validation.valid)
        self.assertTrue(any("disabled" in w for w in validation.warnings))

    def test_unsafe_descriptor_safety_profile_flags_error(self):
        descriptor = self._descriptor()
        descriptor.safety_profile.uses_answer_key = True
        context = SolverRunContext(
            task=create_empty_reasoning_task(),
            trace=create_empty_reasoning_trace(task_id="t1"),
            solver_descriptor=descriptor,
        )
        validation = validate_solver_run_context(context)
        self.assertFalse(validation.valid)
        self.assertTrue(any("answer key" in e for e in validation.errors))

    def test_validate_result_flags_official_score_claimed_true(self):
        result = SolverRunResult(solver_id="s1", official_score_claimed=True)
        validation = validate_solver_run_result(result)
        self.assertFalse(validation.valid)
        self.assertTrue(any("official_score_claimed" in e for e in validation.errors))

    def test_validate_result_flags_anti_gaming_passed_false(self):
        result = SolverRunResult(solver_id="s1", anti_gaming_passed=False)
        validation = validate_solver_run_result(result)
        self.assertFalse(validation.valid)

    def test_validate_result_flags_legibility_passed_false(self):
        result = SolverRunResult(solver_id="s1", legibility_passed=False)
        validation = validate_solver_run_result(result)
        self.assertFalse(validation.valid)

    def test_validate_result_flags_proposed_answer_without_explanation(self):
        result = SolverRunResult(solver_id="s1", proposed_answer="A", confidence="high")
        validation = validate_solver_run_result(result)
        self.assertFalse(validation.valid)
        self.assertTrue(any("requires explanation" in e for e in validation.errors))

    def test_validate_result_flags_proposed_answer_without_confidence(self):
        result = SolverRunResult(solver_id="s1", proposed_answer="A", explanation="because")
        validation = validate_solver_run_result(result)
        self.assertFalse(validation.valid)
        self.assertTrue(any("requires confidence" in e for e in validation.errors))

    def test_conversion_to_solver_output_works(self):
        result = SolverRunResult(
            solver_id="s1",
            solver_family="test",
            status="ok",
            proposed_answer="A",
            confidence="high",
            explanation="why",
            nodes_created=["n1"],
            conflicts_created=["c1"],
        )
        output = solver_run_result_to_solver_output(result)
        self.assertEqual(output.solver_id, "s1")
        self.assertEqual(output.proposed_answer, "A")
        self.assertEqual(output.conflicts_created, ["c1"])

    def test_protocol_base_interface_can_be_implemented_by_fake_solver(self):
        solver = FakeSolver()
        self.assertTrue(isinstance(solver, ReasoningSolverProtocol))
        result = solver.run(SolverRunContext())
        self.assertEqual(result.solver_id, "fake_solver")

    def test_no_field_named_answer_key_exists(self):
        field_names = set()
        for obj in [SolverRunContext(), SolverRunResult()]:
            field_names.update(field.name for field in dataclasses.fields(obj))
        self.assertNotIn("answer_key", field_names)

    def test_no_runtime_behavior_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/solver_interface.py", changed)
        self.assertIn("weslr/tests/test_solver_interface_protocol_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
