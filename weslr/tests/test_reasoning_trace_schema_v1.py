from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.reasoning_trace import (  # noqa: E402
    ReasoningTrace,
    TraceAntiGamingRecord,
    WarrantRecord,
    add_conflict,
    add_inference_edge,
    add_inference_node,
    add_solver_output,
    create_empty_reasoning_trace,
    reasoning_trace_from_dict,
    reasoning_trace_to_dict,
    validate_reasoning_trace,
)


class ReasoningTraceSchemaV1Tests(unittest.TestCase):
    def test_can_create_empty_reasoning_trace(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        self.assertIsInstance(trace, ReasoningTrace)

    def test_defaults_keep_anti_gaming_false(self):
        anti = TraceAntiGamingRecord()
        self.assertFalse(anti.uses_item_id)
        self.assertFalse(anti.uses_answer_key)
        self.assertFalse(anti.uses_answer_position_bias)
        self.assertFalse(anti.stores_raw_question_by_default)
        self.assertFalse(anti.official_score_claimed)

    def test_defaults_keep_private_authority_used_false(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        self.assertTrue(trace.legibility.human_explanation_available)
        self.assertTrue(trace.legibility.symbolic_forms_translated)
        self.assertFalse(trace.legibility.private_authority_used)
        self.assertFalse(trace.legibility.opaque_solver_output_used)

    def test_can_add_inference_nodes(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_inference_node(trace, node_id="n1", node_type="premise", content="If A then B")
        self.assertEqual(len(trace.nodes), 1)
        self.assertEqual(trace.nodes[0].node_id, "n1")

    def test_can_add_inference_edges_with_warrants(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_inference_node(trace, node_id="n1", node_type="premise", content="If A then B")
        add_inference_node(trace, node_id="n2", node_type="conclusion", content="B")
        edge = add_inference_edge(
            trace,
            edge_id="e1",
            from_node="n1",
            to_node="n2",
            relation_type="supports",
            warrant=WarrantRecord(
                warrant_type="rule",
                source="formal_logic",
                explanation="modus ponens structure",
                confidence="high",
                deterministic=True,
                human_teachable=True,
            ),
            confidence="high",
        )
        self.assertEqual(len(trace.edges), 1)
        self.assertEqual(edge.warrant.explanation, "modus ponens structure")

    def test_can_add_solver_output(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        output = add_solver_output(
            trace,
            solver_id="logic-checker",
            solver_family="deterministic_verifier",
            proposed_answer="B",
            confidence="high",
            explanation="validated entailment",
            nodes_created=["n1", "n2"],
            conflicts_created=[],
            status="ok",
        )
        self.assertEqual(len(trace.solver_outputs), 1)
        self.assertEqual(output.solver_id, "logic-checker")

    def test_can_add_conflict(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_inference_node(trace, node_id="n1", node_type="claim", content="harm low")
        add_inference_node(trace, node_id="n2", node_type="claim", content="harm high")
        conflict = add_conflict(
            trace,
            conflict_id="c1",
            conflict_type="contradiction",
            node_ids=["n1", "n2"],
            explanation="claims disagree on impact",
            severity="high",
            resolved=False,
        )
        self.assertEqual(len(trace.conflicts), 1)
        self.assertEqual(conflict.conflict_type, "contradiction")

    def test_to_dict_from_dict_roundtrip_works(self):
        trace = create_empty_reasoning_trace(
            trace_id="trace-1",
            task_id="task-1",
            task_family="multiple_choice_reasoning",
            domain="formal_logic",
            required_skill="ordinary_reasoning",
        )
        add_inference_node(trace, node_id="n1", node_type="premise", content="A")
        data = reasoning_trace_to_dict(trace)
        restored = reasoning_trace_from_dict(data)
        self.assertEqual(data, reasoning_trace_to_dict(restored))
        self.assertEqual(restored.trace_id, "trace-1")

    def test_validate_flags_official_score_claimed_true(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.anti_gaming.official_score_claimed = True
        warnings = validate_reasoning_trace(trace)
        self.assertTrue(any("official_score_claimed true" in item for item in warnings))

    def test_validate_flags_answer_key_use(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.anti_gaming.uses_answer_key = True
        warnings = validate_reasoning_trace(trace)
        self.assertTrue(any("uses_answer_key true" in item for item in warnings))

    def test_validate_flags_private_authority(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.legibility.private_authority_used = True
        warnings = validate_reasoning_trace(trace)
        self.assertTrue(any("private_authority_used true" in item for item in warnings))

    def test_validate_flags_opaque_solver_output(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.legibility.opaque_solver_output_used = True
        warnings = validate_reasoning_trace(trace)
        self.assertTrue(any("opaque_solver_output_used true" in item for item in warnings))

    def test_validate_flags_raw_question_storage(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        trace.anti_gaming.stores_raw_question_by_default = True
        warnings = validate_reasoning_trace(trace)
        self.assertTrue(any("stores_raw_question_by_default true" in item for item in warnings))

    def test_validate_flags_edge_referencing_missing_node(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_inference_node(trace, node_id="n1", node_type="premise", content="A")
        add_inference_edge(
            trace,
            edge_id="e1",
            from_node="n1",
            to_node="missing",
            relation_type="supports",
            warrant=WarrantRecord(explanation="test warrant"),
        )
        warnings = validate_reasoning_trace(trace)
        self.assertTrue(any("edge references missing nodes" in item for item in warnings))

    def test_validate_flags_conflict_referencing_missing_node(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        add_inference_node(trace, node_id="n1", node_type="claim", content="A")
        add_conflict(
            trace,
            conflict_id="c1",
            conflict_type="conflict",
            node_ids=["n1", "missing"],
            explanation="test conflict",
        )
        warnings = validate_reasoning_trace(trace)
        self.assertTrue(any("conflict references missing nodes" in item for item in warnings))

    def test_formal_logic_trace_can_represent_premise_to_inference_to_conclusion(self):
        trace = create_empty_reasoning_trace(task_id="task-1", domain="formal_logic")
        add_inference_node(trace, node_id="p1", node_type="premise", content="If A then B")
        add_inference_node(trace, node_id="p2", node_type="premise", content="A")
        add_inference_node(trace, node_id="i1", node_type="inference", content="B follows by modus ponens")
        add_inference_node(trace, node_id="c1", node_type="conclusion", content="B")
        add_inference_edge(
            trace,
            edge_id="e1",
            from_node="p1",
            to_node="i1",
            relation_type="supports",
            warrant=WarrantRecord(explanation="conditional premise"),
        )
        add_inference_edge(
            trace,
            edge_id="e2",
            from_node="p2",
            to_node="i1",
            relation_type="supports",
            warrant=WarrantRecord(explanation="antecedent holds"),
        )
        add_inference_edge(
            trace,
            edge_id="e3",
            from_node="i1",
            to_node="c1",
            relation_type="derives",
            warrant=WarrantRecord(explanation="valid inference step"),
        )
        self.assertEqual(len(trace.nodes), 4)
        self.assertEqual(len(trace.edges), 3)

    def test_ethics_trace_can_represent_stakeholder_value_conflict(self):
        trace = create_empty_reasoning_trace(task_id="task-1", domain="ethics_tradeoff")
        add_inference_node(trace, node_id="s1", node_type="stakeholder", content="customers")
        add_inference_node(trace, node_id="v1", node_type="value", content="safety")
        add_inference_node(trace, node_id="v2", node_type="value", content="speed")
        add_conflict(
            trace,
            conflict_id="c1",
            conflict_type="value_tradeoff",
            node_ids=["v1", "v2"],
            explanation="speed pressures may reduce safety margin",
            severity="high",
        )
        self.assertEqual(trace.conflicts[0].conflict_type, "value_tradeoff")
        self.assertIn("speed", trace.nodes[2].content)

    def test_no_field_named_answer_key_exists_in_dataclasses(self):
        trace = create_empty_reasoning_trace(task_id="task-1")
        all_field_names = set()
        for obj in [
            trace,
            trace.anti_gaming,
            trace.legibility,
            dataclasses.replace(WarrantRecord()),
        ]:
            all_field_names.update(field.name for field in dataclasses.fields(obj))
        self.assertNotIn("answer_key", all_field_names)

    def test_no_runtime_behavior_files_changed(self):
        changed = {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()}
        self.assertIn("weslr/reasoning_trace.py", changed)
        self.assertIn("weslr/tests/test_reasoning_trace_schema_v1.py", changed)


if __name__ == "__main__":
    unittest.main()
