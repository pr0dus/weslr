from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.formal_logic_parser import parse_mcq_runtime_text_to_logical_form  # noqa: E402
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

    def _context(self, task, allow_raw=True, allow_mutation=True, allow_answer=False, metadata=None):
        return SolverRunContext(
            task=task,
            trace=create_empty_reasoning_trace(task_id=task.task_id),
            solver_descriptor=self.descriptor,
            dry_run=True,
            allow_answer_selection=allow_answer,
            allow_trace_mutation=allow_mutation,
            allow_raw_question_access=allow_raw,
            metadata=dict(metadata or {}),
        )

    def _neutral_parser_parse(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "If rain then wet streets. Which conclusion is best supported?",
            [
                {"label": "A", "text": "dry streets"},
                {"label": "B", "text": "city traffic"},
            ],
            parse_id="parse-neutral",
            source_task_id="t1",
            store_raw_text=False,
        )
        parse.premises = ["stmt_q1"]
        return parse

    def _supported_parser_parse(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "If rain then wet streets. Rain. Which conclusion is best supported?",
            [
                {"label": "A", "text": "wet streets"},
                {"label": "B", "text": "dry streets"},
            ],
            parse_id="parse-supported",
            source_task_id="t1",
            store_raw_text=False,
        )
        parse.premises = ["stmt_q1", "stmt_q2"]
        return parse

    def _contradiction_parser_parse(self):
        parse = parse_mcq_runtime_text_to_logical_form(
            "Not rain. Which conclusion is best supported?",
            [
                {"label": "A", "text": "rain"},
                {"label": "B", "text": "snow"},
            ],
            parse_id="parse-contradiction",
            source_task_id="t1",
            store_raw_text=False,
        )
        parse.premises = ["stmt_q1"]
        return parse

    def _syllogism_parser_parse(self):
        return parse_mcq_runtime_text_to_logical_form(
            "All cats are mammals. Felix is a cat. Which conclusion is best supported?",
            [
                {"label": "A", "text": "Felix is a mammal"},
                {"label": "B", "text": "Felix is a reptile"},
            ],
            parse_id="parse-syllogism",
            source_task_id="t1",
            store_raw_text=False,
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

    def test_solver_accepts_logical_form_parse_from_context_metadata(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._neutral_parser_parse()
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_no_supported_inference")
        self.assertEqual(result.proposed_answer, "")

    def test_solver_accepts_logical_form_parse_dict_from_context_metadata(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._neutral_parser_parse()
        result = self.solver.run(
            self._context(task, allow_raw=False, metadata={"logical_form_parse": dataclasses.asdict(parse)})
        )
        self.assertEqual(result.status, "parsed_no_supported_inference")

    def test_parser_mode_does_not_require_direct_raw_question_access(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._neutral_parser_parse()
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertNotEqual(result.status, "insufficient_input")

    def test_parser_mode_returns_parsed_no_supported_inference_when_no_inference_applies(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._neutral_parser_parse()
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_no_supported_inference")
        self.assertEqual(result.confidence, "low")
        self.assertIn("Parser extracted structured premises and candidate conclusions", result.explanation)

    def test_parser_mode_candidate_evaluations_are_created(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._supported_parser_parse()
        context = self._context(task, allow_raw=False, metadata={"logical_form_parse": parse})
        self.solver.run(context)
        evaluation_nodes = [node for node in context.trace.nodes if node.node_type in {"candidate_supported", "candidate_ambiguous", "candidate_contradicted"}]
        self.assertGreaterEqual(len(evaluation_nodes), 2)

    def test_universal_syllogism_selects_unique_candidate(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._syllogism_parser_parse()
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_candidate_selected")
        self.assertEqual(result.proposed_answer, "A")

    def test_negative_universal_selects_unique_candidate(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = parse_mcq_runtime_text_to_logical_form(
            "No cats are reptiles. Felix is a cat. Which conclusion is best supported?",
            [{"label": "A", "text": "Felix is not a reptile"}, {"label": "B", "text": "Felix is a reptile"}],
            parse_id="parse-negative-universal",
            source_task_id="t1",
            store_raw_text=False,
        )
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_candidate_selected")
        self.assertEqual(result.proposed_answer, "A")

    def test_direct_fact_match_selects_unique_candidate(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = parse_mcq_runtime_text_to_logical_form(
            "Alpha supports Beta. Which conclusion is best supported?",
            [{"label": "A", "text": "Alpha supports Beta"}, {"label": "B", "text": "Beta supports Alpha"}],
            parse_id="parse-direct-fact",
            source_task_id="t1",
            store_raw_text=False,
        )
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_candidate_selected")
        self.assertEqual(result.proposed_answer, "A")

    def test_direct_negation_conflict_blocks_candidate(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = parse_mcq_runtime_text_to_logical_form(
            "Alpha is helpful. Which conclusion is best supported?",
            [{"label": "A", "text": "Alpha is not helpful"}, {"label": "B", "text": "Beta is helpful"}],
            parse_id="parse-direct-negation",
            source_task_id="t1",
            store_raw_text=False,
        )
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.proposed_answer, "")
        self.assertIn(result.status, {"parsed_candidate_blocked_by_conflict", "parsed_no_supported_inference"})

    def test_class_transitivity_selects_unique_candidate(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = parse_mcq_runtime_text_to_logical_form(
            "All cats are mammals. All mammals are animals. Which conclusion is best supported?",
            [{"label": "A", "text": "All cats are animals"}, {"label": "B", "text": "All animals are cats"}],
            parse_id="parse-transitivity",
            source_task_id="t1",
            store_raw_text=False,
        )
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_candidate_selected")
        self.assertEqual(result.proposed_answer, "A")

    def test_ambiguous_two_supported_candidates_produce_no_answer(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = parse_mcq_runtime_text_to_logical_form(
            "Alpha supports Beta. Which conclusion is best supported?",
            [{"label": "A", "text": "Alpha supports Beta"}, {"label": "B", "text": "Alpha supports Beta"}],
            parse_id="parse-two-supported",
            source_task_id="t1",
            store_raw_text=False,
        )
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_ambiguous_candidates")
        self.assertEqual(result.proposed_answer, "")

    def test_parser_mode_creates_parser_summary_trace_node(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._neutral_parser_parse()
        context = self._context(task, allow_raw=False, metadata={"logical_form_parse": parse})
        result = self.solver.run(context)
        self.assertIn("formal_logic_solver_parser_summary", result.nodes_created)
        summary_nodes = [node for node in context.trace.nodes if node.node_type == "parser_summary"]
        self.assertEqual(len(summary_nodes), 1)

    def test_parser_mode_creates_choice_claim_candidate_conclusion_trace_nodes(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._supported_parser_parse()
        context = self._context(task, allow_raw=False, metadata={"logical_form_parse": parse})
        self.solver.run(context)
        premise_nodes = [node for node in context.trace.nodes if node.node_type == "parsed_premise"]
        choice_nodes = [node for node in context.trace.nodes if node.node_type == "choice_claim"]
        self.assertGreaterEqual(len(premise_nodes), 1)
        self.assertGreaterEqual(len(choice_nodes), 2)
        self.assertEqual({node.content for node in choice_nodes}, {"choice_A", "choice_B"})

    def test_parser_mode_adds_parser_warrants(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._supported_parser_parse()
        context = self._context(task, allow_raw=False, metadata={"logical_form_parse": parse})
        self.solver.run(context)
        warrant_types = {edge.warrant.warrant_type for edge in context.trace.edges}
        self.assertIn("parser logical-form extraction", warrant_types)
        self.assertIn("parser candidate-conclusion extraction", warrant_types)
        self.assertIn("parser candidate evaluation", warrant_types)

    def test_trace_includes_simple_entailment_or_categorical_warrant(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._syllogism_parser_parse()
        context = self._context(task, allow_raw=False, metadata={"logical_form_parse": parse})
        self.solver.run(context)
        warrant_types = {edge.warrant.warrant_type for edge in context.trace.edges}
        self.assertTrue("categorical syllogism" in warrant_types or "simple entailment check" in warrant_types)

    def test_parser_mode_candidate_evaluation_trace_nodes_are_created(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._supported_parser_parse()
        context = self._context(task, allow_raw=False, metadata={"logical_form_parse": parse})
        self.solver.run(context)
        summary_nodes = [node for node in context.trace.nodes if node.node_type == "candidate_evaluation_summary"]
        self.assertEqual(len(summary_nodes), 1)

    def test_parser_mode_records_unsupported_fragment_summary_without_raw_text(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = parse_mcq_runtime_text_to_logical_form(
            "Birds migrate seasonally. Which conclusion follows?",
            [{"label": "A", "text": "Robins migrate"}, {"label": "B", "text": "Robins do not migrate"}],
            parse_id="parse-unsupported",
            source_task_id="t1",
            store_raw_text=False,
        )
        context = self._context(task, allow_raw=False, metadata={"logical_form_parse": parse})
        result = self.solver.run(context)
        unsupported_nodes = [node for node in context.trace.nodes if node.node_type == "unsupported_fragment_summary"]
        self.assertEqual(len(unsupported_nodes), 1)
        self.assertIn("unsupported fragment summary: count=1", unsupported_nodes[0].content)
        self.assertNotIn("Birds migrate seasonally", unsupported_nodes[0].content)
        self.assertTrue(any("unsupported fragment(s)" in warning for warning in result.warnings))

    def test_explicit_contradiction_blocks_candidate(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._contradiction_parser_parse()
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_candidate_blocked_by_conflict")
        self.assertEqual(result.proposed_answer, "")

    def test_ambiguous_parser_candidates_produce_no_proposed_answer(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = parse_mcq_runtime_text_to_logical_form(
            "If rain then wet streets. Rain. Which conclusion is best supported?",
            [{"label": "A", "text": "wet streets"}, {"label": "B", "text": "wet streets"}],
            parse_id="parse-ambiguous",
            source_task_id="t1",
            store_raw_text=False,
        )
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_ambiguous_candidates")
        self.assertEqual(result.proposed_answer, "")

    def test_unique_supported_synthetic_parser_case_can_produce_proposed_answer(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._supported_parser_parse()
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_candidate_selected")
        self.assertEqual(result.proposed_answer, "A")

    def test_proposed_answer_is_candidate_identifier_only_not_answer_key(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = parse_mcq_runtime_text_to_logical_form(
            "If rain then wet streets. Rain. Which conclusion is best supported?",
            [
                {"label": "A", "text": "wet streets", "answer_key": "B", "correct_answer": "B"},
                {"label": "B", "text": "dry streets", "answer_key": "A", "correct_answer": "A"},
            ],
            parse_id="parse-ids",
            source_task_id="t1",
            store_raw_text=False,
        )
        parse.premises = ["stmt_q1", "stmt_q2"]
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.proposed_answer, "A")
        self.assertNotIn("answer_key", str(dataclasses.asdict(result)))

    def test_low_parse_confidence_blocks_confident_selection(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._supported_parser_parse()
        parse.parse_confidence = "low"
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.status, "parsed_no_supported_inference")
        self.assertEqual(result.proposed_answer, "")
        self.assertTrue(any("low parse confidence" in warning for warning in result.warnings))

    def test_unsupported_fragments_reduce_confidence_and_warn(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = parse_mcq_runtime_text_to_logical_form(
            "If rain then wet streets. Rain. Strange seasonal background. Which conclusion is best supported?",
            [{"label": "A", "text": "wet streets"}, {"label": "B", "text": "dry streets"}],
            parse_id="parse-warning",
            source_task_id="t1",
            store_raw_text=False,
        )
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertEqual(result.confidence, "low")
        self.assertTrue(any("unsupported fragment" in warning for warning in result.warnings))

    def test_parser_mode_keeps_official_score_claimed_false(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._supported_parser_parse()
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertFalse(result.official_score_claimed)

    def test_parser_mode_does_not_use_answer_key(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._supported_parser_parse()
        result = self.solver.run(self._context(task, allow_raw=False, metadata={"logical_form_parse": parse}))
        self.assertFalse(result.official_score_claimed)
        self.assertNotIn("answer_key", str(dataclasses.asdict(result)))

    def test_no_raw_question_or_choice_text_appears_in_solver_result_or_trace_summary(self):
        task = self._task("", [{"label": "A", "text": "unused"}])
        parse = self._supported_parser_parse()
        context = self._context(task, allow_raw=False, metadata={"logical_form_parse": parse})
        result = self.solver.run(context)
        self.assertNotIn("wet streets", result.explanation)
        summary_text = "\n".join(
            node.content
            for node in context.trace.nodes
            if node.node_type in {"parser_summary", "candidate_evaluation_summary", "unsupported_fragment_summary"}
        )
        self.assertNotIn("wet streets", summary_text)
        self.assertNotIn("dry streets", summary_text)

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
        self.assertNotIn("weslr/evals/official_mcq_adapter.py", {"weslr/formal_logic_solver.py", "weslr/tests/test_formal_logic_solver_v1.py"})


if __name__ == "__main__":
    unittest.main()
