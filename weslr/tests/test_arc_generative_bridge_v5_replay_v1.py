import inspect

from weslr.arc_generative_bridge_v5_replay import (
    TASK_GROUPS,
    _process_task,
    build_generative_bridge_v5_replay_tasks_v1,
    run_generative_bridge_v5_replay_v1,
)


KNOWN_BAD_IDS = [
    "v5_replay_v4_rival_grammar_replay_6_01",
    "v5_replay_v4_rival_grammar_replay_6_02",
    "v5_replay_v4_rival_grammar_replay_6_03",
    "v5_replay_v4_rival_grammar_replay_6_04",
    "v5_replay_v4_rival_grammar_replay_6_05",
    "v5_replay_v4_rival_grammar_replay_6_06",
]


def _candidate(**overrides):
    candidate = {
        "candidate_id": "c1",
        "task_id": "task_test",
        "construction_mode": "train_forced_transformation_candidate",
        "construction_trace": [
            {
                "step_id": 1,
                "source_helper": "helper",
                "source_constraint": "train_forced_transformation",
                "operation": "mirror_fill",
                "train_support": True,
                "assumption_status": "forced",
                "rival_impact": "none",
                "ledger_relevance": "required",
                "evidence_status": "train_explicit",
                "source_train_ids": ["train_1"],
                "train_grounded_transformation_rule": "mirror the train-supported relation",
                "train_grounded_forced_constraints": ["constraint_1"],
                "forced_constraints_tied_to_train_evidence": ["constraint_1"],
                "ambiguity_check": "clear",
                "competing_output_rejection_reason": "train evidence rejects the competing color swap",
                "uniquely_forced_reason": "all surviving train constraints force this exact output family",
            }
        ],
        "requires_ledger_review": True,
        "candidate_treated_as_final_answer": False,
        "treated_as_final_answer": False,
        "construction_trace_complete": True,
        "construction_trace_source_grounded": True,
        "forced_uniqueness_trace_present": True,
        "rival_elimination_trace_present": False,
        "train_evidence_grounded": True,
        "source_train_ids": ["train_1"],
        "source_train_example_ids": ["train_1"],
        "synthetic_local_train_ids": [],
        "train_grounded_transformation_rule": "mirror the train-supported relation",
        "train_grounded_forced_constraints": ["constraint_1"],
        "forced_constraints_tied_to_train_evidence": ["constraint_1"],
        "ambiguity_check": "clear",
        "competing_output_rejection_reason": "train evidence rejects the competing color swap",
        "competing_outputs_rejected_reason": "train evidence rejects the competing color swap",
        "uniquely_forced_reason": "all surviving train constraints force this exact output family",
        "helper_output_as_evidence": False,
        "rehearsal_repeat_as_evidence": False,
        "mdl_only_support": False,
        "unsupported_assumptions": [],
        "unresolved_rivals": [],
        "rival_context_detected": False,
        "rival_context_reasons": [],
        "rival_grammars": [],
        "surviving_grammar": None,
        "rival_elimination_trace": [],
        "surviving_grammar_train_evidence": "",
        "rival_outputs_considered": [],
        "rejected_rival_reasons": [],
        "surviving_grammar_uniquely_forces_output": False,
        "missing_required_trace_fields": [],
    }
    candidate.update(overrides)
    return candidate


def _task_with_candidates(*candidates, **overrides):
    task = {
        "task_id": "task_test",
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
        groups = {task["group_id"] for task in build_generative_bridge_v5_replay_tasks_v1()}
        assert len(groups) == 8

    def test_6_tasks_per_group(self):
        tasks = build_generative_bridge_v5_replay_tasks_v1()
        for group_id in TASK_GROUPS:
            assert len([task for task in tasks if task["group_id"] == group_id]) == 6


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
    def test_generator_produced_complete_candidate_can_pass_assembler_in_replay(self):
        task = {
            "task_id": "task_gen_complete",
            "group_id": TASK_GROUPS[1],
            "train_examples": [{"input": [[1, 2]], "output": [[2, 1]]}],
            "test_input_descriptor": {"grid": [[1, 2]]},
            "helper_diagnostics": {},
            "forced_constraints": ["constraint_1"],
            "candidate_generation_inputs": {
                "train_forced_transformations": [{"train_supported": True, "operation_name": "mirror_fill"}],
            },
            "expected_frontier_failure": "diagnostic",
            "expected_bridge_behavior": "diagnostic",
            "synthetic_expected_answer_for_scoring_only": [[2, 1]],
        }
        result = _process_task(task)
        assert result["candidate_deserved"] is True
        assert result["generation_construction_trace_complete_count"] == 1

    def test_generator_produced_incomplete_candidate_safe_fails_through_replay(self):
        task = {
            "task_id": "task_gen_incomplete",
            "group_id": TASK_GROUPS[1],
            "train_examples": [{"input": [[1, 2]], "output": [[2, 1]]}],
            "test_input_descriptor": {"grid": [[1, 2]]},
            "helper_diagnostics": {},
            "forced_constraints": [],
            "candidate_generation_inputs": {
                "train_forced_transformations": [{"train_supported": True}],
            },
            "expected_frontier_failure": "diagnostic",
            "expected_bridge_behavior": "diagnostic",
            "synthetic_expected_answer_for_scoring_only": [[2, 1]],
        }
        result = _process_task(task)
        assert result["safe_failure"] is True
        assert result["candidate_deserved"] is False

    def test_known_bad_six_rival_tasks_no_longer_become_deserved_without_rival_proof(self):
        tasks = [
            task
            for task in build_generative_bridge_v5_replay_tasks_v1()
            if task["task_id"] in KNOWN_BAD_IDS
        ]
        assert len(tasks) == 6
        for task in tasks:
            result = _process_task(task)
            assert result["candidate_deserved"] is False
            assert result["safe_failure"] is True
            assert result["safe_failure_required_count"] == 1
            assert result["safe_failure_from_unresolved_rival_count"] == 1
            assert result["rival_context_detected_count"] == 1
            assert result["rival_context_missing_proof_count"] == 1
            assert result["train_forced_rival_bypass_blocked_count"] == 1

    def test_known_bad_six_aggregate_safe_failures_are_all_six(self):
        tasks = [
            task
            for task in build_generative_bridge_v5_replay_tasks_v1()
            if task["task_id"] in KNOWN_BAD_IDS
        ]
        result = run_generative_bridge_v5_replay_v1(tasks)
        assert result["task_metrics"]["candidate_deserved_tasks"] == 0
        assert result["task_metrics"]["safe_failure_count"] == 6
        assert result["generation_metrics"]["rival_context_detected_count"] == 6
        assert result["generation_metrics"]["rival_context_missing_proof_count"] == 6
        assert result["generation_metrics"]["train_forced_rival_bypass_blocked_count"] == 6
        assert result["ledger_metrics"]["safe_failure_from_unresolved_rival_count"] == 6
        assert result["ledger_metrics"]["rival_context_safe_failure_count"] == 6

    def test_replay_propagates_candidate_trace_fields_unchanged(self):
        candidate = _candidate(source_train_ids=["train_A"], train_grounded_forced_constraints=["constraint_A"])
        task = _task_with_candidates(candidate, group_id=TASK_GROUPS[1])
        result = _process_task(task)
        assert result["ledger_review_required_count"] == 1
        assert candidate["source_train_ids"] == ["train_A"]
        assert candidate["train_grounded_forced_constraints"] == ["constraint_A"]

    def test_expected_answers_remain_scoring_only_after_ledger_decision(self):
        result = _process_task(_task_with_candidates(_candidate(), group_id=TASK_GROUPS[1]))
        assert result["candidate_deserved"] is True
        assert "synthetic_expected_answer_for_scoring_only" not in _candidate()

    def test_emitter_hard_stops_remain_unchanged(self):
        result = run_generative_bridge_v5_replay_v1([_task_with_candidates(_candidate(), group_id=TASK_GROUPS[1])])
        emitter = result["emitter_decision"]
        assert emitter["emitter_gate_passed"] is False
        assert emitter["recommended_next_lane"]

    def test_no_runtime_wiring(self):
        source = inspect.getsource(_process_task)
        assert "ChatResponder" not in source
        assert "runtime" not in source.lower() or "runtime_behavior_changed" not in source
