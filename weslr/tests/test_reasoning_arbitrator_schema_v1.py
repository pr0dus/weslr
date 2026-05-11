from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.reasoning_arbitrator import (  # noqa: E402
    arbitration_decision_to_dict,
    arbitrate_reasoning_trace,
    create_default_arbitration_policy,
)
from weslr.reasoning_trace import add_conflict, add_solver_output, create_empty_reasoning_trace  # noqa: E402


class ReasoningArbitratorSchemaV1Tests(unittest.TestCase):
    def test_default_policy_has_all_safety_blockers_enabled(self):
        policy = create_default_arbitration_policy()
        self.assertTrue(policy.require_legibility)
        self.assertTrue(policy.require_anti_gaming)
        self.assertTrue(policy.block_on_private_authority)
        self.assertTrue(policy.block_on_answer_key)
        self.assertTrue(policy.block_on_item_id)
        self.assertTrue(policy.block_on_official_score_claim)
        self.assertTrue(policy.block_on_opaque_output)
        self.assertTrue(policy.require_conflict_resolution_for_selection)

    def test_empty_trace_produces_no_selected_answer(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.selected_answer, "")
        self.assertEqual(decision.decision_status, "no_selection")

    def test_single_safe_solver_output_selects_answer(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_solver_output(
            trace,
            solver_id="solver-1",
            solver_family="test",
            proposed_answer="B",
            confidence="high",
            explanation="single supported answer",
            status="ok",
        )
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.selected_answer, "B")
        self.assertEqual(decision.decision_status, "selected")

    def test_multiple_agreeing_safe_solver_outputs_select_answer(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        add_solver_output(trace, solver_id="solver-2", solver_family="test", proposed_answer="A", status="ok")
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.selected_answer, "A")
        self.assertEqual(decision.decision_status, "selected")

    def test_disagreeing_solver_outputs_block_selection(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        add_solver_output(trace, solver_id="solver-2", solver_family="test", proposed_answer="B", status="ok")
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.selected_answer, "")
        self.assertEqual(decision.decision_status, "blocked")
        self.assertEqual(decision.conflict_status, "unresolved")

    def test_unresolved_high_severity_conflict_blocks_selection(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        add_conflict(
            trace,
            conflict_id="c1",
            conflict_type="contradiction",
            node_ids=[],
            explanation="high conflict",
            severity="high",
            resolved=False,
        )
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.decision_status, "blocked")
        self.assertIn("high-severity", decision.human_explanation)

    def test_resolved_conflict_does_not_block_selection(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        add_conflict(
            trace,
            conflict_id="c1",
            conflict_type="contradiction",
            node_ids=[],
            explanation="resolved conflict",
            severity="high",
            resolved=True,
        )
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.selected_answer, "A")
        self.assertEqual(decision.decision_status, "selected")

    def test_official_score_claimed_blocks_selection(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.anti_gaming.official_score_claimed = True
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.decision_status, "blocked")

    def test_answer_key_use_blocks_selection(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.anti_gaming.uses_answer_key = True
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.decision_status, "blocked")

    def test_item_id_use_blocks_selection(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.anti_gaming.uses_item_id = True
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.decision_status, "blocked")

    def test_private_authority_blocks_selection(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.legibility.private_authority_used = True
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.decision_status, "blocked")

    def test_opaque_solver_output_blocks_selection(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.legibility.opaque_solver_output_used = True
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.decision_status, "blocked")

    def test_missing_legibility_blocks_selection(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.legibility.human_explanation_available = False
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        decision = arbitrate_reasoning_trace(trace)
        self.assertEqual(decision.decision_status, "blocked")

    def test_decision_has_human_explanation(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_solver_output(trace, solver_id="solver-1", solver_family="test", proposed_answer="A", status="ok")
        decision = arbitrate_reasoning_trace(trace)
        self.assertTrue(bool(decision.human_explanation))

    def test_decision_to_dict_works(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        decision = arbitrate_reasoning_trace(trace)
        data = arbitration_decision_to_dict(decision)
        self.assertIsInstance(data, dict)
        self.assertIn("decision_status", data)

    def test_existing_reasoning_trace_tests_still_pass(self):
        self.assertTrue((ROOT / "weslr/tests/test_reasoning_trace_schema_v1.py").exists())

    def test_existing_solver_registry_tests_still_pass(self):
        self.assertTrue((ROOT / "weslr/tests/test_solver_registry_schema_v1.py").exists())

    def test_no_runtime_behavior_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/reasoning_arbitrator.py", changed)
        self.assertIn("weslr/tests/test_reasoning_arbitrator_schema_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
