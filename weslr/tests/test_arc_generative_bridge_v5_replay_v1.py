"""Tests for ARC Generative Bridge V5 Replay."""

import inspect
import sys

sys.path.insert(0, '.')

from weslr.arc_generative_bridge_v5_replay import (
    TASK_GROUPS,
    _process_task,
    build_generative_bridge_v5_replay_tasks_v1,
    evaluate_emitter_decision_gate_v1,
    run_generative_bridge_v5_replay_v1,
)


def _candidate(**overrides):
    candidate = {
        "candidate_id": "c1",
        "requires_ledger_review": True,
        "treated_as_final_answer": False,
        "generation_status": "generated",
        "unsupported_assumptions": [],
        "unresolved_rivals": [],
        "construction_mode": "train_forced_transformation_candidate",
        "construction_trace": [{
            "step_id": 1,
            "source_train_example_ids": ["train_1"],
            "train_grounded_transformation_rule": "rule",
            "forced_constraints_tied_to_train_evidence": ["constraint_1"],
        }],
        "construction_trace_complete": True,
        "construction_trace_source_grounded": True,
        "forced_uniqueness_trace_present": True,
        "rival_elimination_trace_present": False,
        "train_evidence_grounded": True,
        "source_train_example_ids": ["train_1"],
        "train_grounded_transformation_rule": "rule",
        "forced_constraints_tied_to_train_evidence": ["constraint_1"],
        "ambiguity_check": "clear",
        "competing_outputs_rejected_reason": "reject competitor",
        "uniquely_forced_reason": "uniquely forced",
        "output_affecting_ambiguity": False,
    }
    candidate.update(overrides)
    return candidate


def _task_with_candidates(*candidates, **overrides):
    task = {
        "task_id": "task_001",
        "group_id": TASK_GROUPS[0],
        "train_examples": [{"input": [[1]], "output": [[1]]}],
        "test_input_descriptor": {"grid": [[1]]},
        "helper_diagnostics": {},
        "forced_constraints": ["constraint_1"],
        "candidate_generation_inputs": {},
        "expected_frontier_failure": "diagnostic",
        "expected_bridge_behavior": "diagnostic",
        "synthetic_expected_answer_for_scoring_only": [[1]],
        "candidate_descriptors_override": list(candidates),
    }
    task.update(overrides)
    return task


class TestTaskSuite:
    def test_48_tasks_generated(self):
        assert len(build_generative_bridge_v5_replay_tasks_v1()) == 48

    def test_8_groups_generated(self):
        groups = {t["group_id"] for t in build_generative_bridge_v5_replay_tasks_v1()}
        assert len(groups) == 8

    def test_6_tasks_per_group(self):
        tasks = build_generative_bridge_v5_replay_tasks_v1()
        for group_id in TASK_GROUPS:
            assert len([t for t in tasks if t["group_id"] == group_id]) == 6


class TestScoringBoundary:
    def test_expected_answer_is_scoring_only(self):
        for task in build_generative_bridge_v5_replay_tasks_v1():
            assert "synthetic_expected_answer_for_scoring_only" in task
            assert "expected_answer" not in task.get("candidate_generation_inputs", {})
            assert "expected_answer" not in task.get("helper_diagnostics", {})

    def test_candidate_generation_before_ledger(self):
        source = inspect.getsource(_process_task)
        assert source.find("build_controlled_answer_candidate_generator_input_v1") < source.find("evaluate_ledger_deservedness_v1")

    def test_ledger_decision_before_scoring(self):
        source = inspect.getsource(_process_task)
        assert source.find("evaluate_ledger_deservedness_v1") < source.find("synthetic_expected_answer_for_scoring_only")


class TestReplayRepairMetrics:
    def test_ledger_review_required_count_increments_correctly(self):
        result = _process_task(_task_with_candidates(_candidate()))
        assert result["ledger_review_required_count"] == 1

    def test_construction_trace_complete_count_increments_correctly(self):
        result = _process_task(_task_with_candidates(_candidate()))
        assert result["construction_trace_complete_count"] == 1

    def test_incomplete_trace_cannot_produce_deserved_candidate_in_replay(self):
        result = _process_task(_task_with_candidates(_candidate(construction_trace_complete=False)))
        assert result["candidate_deserved"] is False
        assert result["safe_failure"] is True

    def test_missing_ledger_review_flag_cannot_produce_deserved_candidate_in_replay(self):
        candidate = _candidate()
        del candidate["requires_ledger_review"]
        result = _process_task(_task_with_candidates(candidate))
        assert result["candidate_deserved"] is False
        assert result["safe_failure"] is True

    def test_insufficient_evidence_contributes_to_task_level_safe_failure(self):
        result = _process_task(_task_with_candidates(_candidate(forced_uniqueness_trace_present=False)))
        assert result["safe_failure"] is True
        assert result["safe_failure_from_insufficient_evidence_count"] == 1

    def test_safe_failure_preserved_when_all_candidates_rejected(self):
        result = _process_task(
            _task_with_candidates(
                _candidate(forced_uniqueness_trace_present=False),
                _candidate(candidate_id="c2", train_evidence_grounded=False),
            )
        )
        assert result["safe_failure"] is True
        assert result["candidate_deserved"] is False

    def test_expected_answers_used_only_after_ledger_decision(self):
        source = inspect.getsource(_process_task)
        assert source.find("decision = asm_result.get") < source.find("expected = task.get")

    def test_deserved_but_wrong_hard_stops_emitter(self):
        gate = evaluate_emitter_decision_gate_v1(
            {
                "task_metrics": {"deserved_but_wrong_count": 1},
                "generation_metrics": {"candidate_generation_attempt_count": 10},
                "ledger_metrics": {"mdl_only_rejected_count": 0},
                "group_results": {"g1": {"deserved": 1}},
                "safety_metrics": {},
            }
        )
        assert gate["emitter_hard_stop_triggered"] is True
        assert "deserved_but_wrong" in gate["emitter_hard_stop_reasons"]

    def test_no_replay_to_runtime_wiring(self):
        source = inspect.getsource(sys.modules['weslr.arc_generative_bridge_v5_replay'])
        assert "chat_responder" not in source
        assert "runtime_wiring_changed = True" not in source


class TestEndToEnd:
    def test_replay_runs_without_error(self):
        result = run_generative_bridge_v5_replay_v1()
        assert "task_metrics" in result
        assert "emitter_decision" in result

    def test_emitter_gate_function_works(self):
        gate = evaluate_emitter_decision_gate_v1(
            {
                "task_metrics": {
                    "deserved_exact_count": 6,
                    "undeserved_exact_count": 0,
                    "deserved_but_wrong_count": 0,
                    "overconfident_wrong_count": 0,
                    "helper_laundering_violation_count": 0,
                    "final_answer_emitted_count": 0,
                    "public_claim_allowed_count": 0,
                    "helper_output_as_evidence_count": 0,
                },
                "generation_metrics": {"candidate_generation_attempt_count": 48},
                "ledger_metrics": {"candidate_deserved_count": 6, "mdl_only_rejected_count": 0},
                "group_results": {"g1": {"deserved": 3}, "g2": {"deserved": 3}},
                "safety_metrics": {},
            }
        )
        assert gate["emitter_gate_passed"] is True
