import inspect
import json
import subprocess
import sys

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
        "group_id": TASK_GROUPS[1],
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
        assert source.find("decision = asm_result.get") < source.rfind("_score_post_ledger")

    def test_no_python_hash_or_rng_used_for_scoring(self):
        source = inspect.getsource(sys.modules["weslr.arc_generative_bridge_v5_replay"])
        assert "hash(task" not in source
        assert "random.seed" not in source
        assert "random.random" not in source


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
        assert result["post_ledger_scoring_status"] == "unscorable_due_to_missing_candidate_output"

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
        assert result["candidate_trace_provenance"] == "candidate_descriptors_override"

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


class TestScoringRepair:
    def test_real_expected_comparison_used_when_candidate_output_available(self):
        candidate = _candidate(synthetic_candidate_output_for_scoring_only=[[1]])
        result = _process_task(_task_with_candidates(candidate))
        assert result["candidate_deserved"] is True
        assert result["deserved_exact"] is True
        assert result["deserved_but_wrong"] is False
        assert result["post_ledger_scoring_status"] == "scored_deserved_exact"
        assert result["post_ledger_scoring_mechanism"] == "deterministic_expected_output_equality"

    def test_real_expected_comparison_marks_deserved_but_wrong(self):
        candidate = _candidate(synthetic_candidate_output_for_scoring_only=[[9]])
        result = _process_task(_task_with_candidates(candidate))
        assert result["candidate_deserved"] is True
        assert result["deserved_exact"] is False
        assert result["deserved_but_wrong"] is True
        assert result["post_ledger_scoring_status"] == "scored_deserved_but_wrong"

    def test_candidate_output_missing_becomes_unscorable_not_random(self):
        result = _process_task(_task_with_candidates(_candidate()))
        assert result["candidate_deserved"] is True
        assert result["deserved_exact"] is False
        assert result["deserved_but_wrong"] is False
        assert result["post_ledger_scoring_status"] == "unscorable_due_to_missing_candidate_output"
        assert result["rng_or_hash_influenced_scoring"] is False

    def test_undeserved_exact_uses_real_comparison(self):
        incomplete = _candidate(
            construction_trace_complete=False,
            forced_uniqueness_trace_present=False,
            train_evidence_grounded=False,
            missing_required_trace_fields=["train_grounded_transformation_rule"],
            synthetic_candidate_output_for_scoring_only=[[1]],
        )
        result = _process_task(_task_with_candidates(incomplete))
        assert result["candidate_deserved"] is False
        assert result["undeserved_exact"] is True
        assert result["post_ledger_scoring_status"] == "scored_undeserved_exact"

    def test_no_candidate_generated_is_not_scored_candidate_not_generated(self):
        task = _task_with_candidates()
        result = _process_task(task)
        assert result["candidate_generated"] is False
        assert result["post_ledger_scoring_status"] == "not_scored_candidate_not_generated"


class TestPerTaskProvenance:
    def test_per_task_records_are_emitted_for_all_attempted_tasks(self):
        result = run_generative_bridge_v5_replay_v1()
        assert len(result["per_task_records"]) == result["task_metrics"]["attempted_tasks"]

    def test_named_task_id_lists_match_per_task_records(self):
        result = run_generative_bridge_v5_replay_v1([
            _task_with_candidates(_candidate(synthetic_candidate_output_for_scoring_only=[[1]]), task_id="exact_task"),
            _task_with_candidates(_candidate(synthetic_candidate_output_for_scoring_only=[[9]]), task_id="wrong_task"),
        ])
        records = {record["task_id"]: record for record in result["per_task_records"]}
        assert set(result["candidate_deserved_task_ids"]) == {task_id for task_id, record in records.items() if record["candidate_deserved"]}
        assert set(result["deserved_exact_task_ids"]) == {task_id for task_id, record in records.items() if record["deserved_exact"]}
        assert set(result["deserved_but_wrong_task_ids"]) == {task_id for task_id, record in records.items() if record["deserved_but_wrong"]}
        assert set(result["hard_stop_task_ids"]) == {task_id for task_id, record in records.items() if record["hard_stop_triggered"]}

    def test_hard_stop_task_ids_are_preserved(self):
        result = run_generative_bridge_v5_replay_v1([
            _task_with_candidates(_candidate(synthetic_candidate_output_for_scoring_only=[[9]]), task_id="wrong_task")
        ])
        assert result["deserved_but_wrong_task_ids"] == ["wrong_task"]
        assert result["hard_stop_task_ids"] == ["wrong_task"]
        assert result["emitter_decision"]["emitter_hard_stop_reasons"] == ["deserved_but_wrong"]

    def test_candidate_trace_provenance_is_recorded(self):
        result = run_generative_bridge_v5_replay_v1([
            _task_with_candidates(_candidate(synthetic_candidate_output_for_scoring_only=[[1]]), task_id="override_task"),
            build_generative_bridge_v5_replay_tasks_v1()[0],
        ])
        records = {record["task_id"]: record for record in result["per_task_records"]}
        assert records["override_task"]["candidate_trace_provenance"] == "candidate_descriptors_override"
        generated_task_id = build_generative_bridge_v5_replay_tasks_v1()[0]["task_id"]
        assert records[generated_task_id]["candidate_trace_provenance"] == "generated_from_candidate_generation_inputs"

    def test_all_8_groups_have_explicit_scoring_classification(self):
        result = run_generative_bridge_v5_replay_v1()
        assert set(result["group_scoring_audit"].keys()) == set(TASK_GROUPS)
        for group_id, audit in result["group_scoring_audit"].items():
            assert audit["task_count"] == 6
            assert audit["group_scoring_classification"] in {
                "real_post_ledger_expected_comparison",
                "synthetic_randomized_stress_label",
                "mixed_real_and_randomized_path",
                "rng_influenced_candidate_or_label_path",
                "unscorable_due_to_missing_candidate_output",
                "unknown",
            }
            assert audit["expected_output_available"] is True

    def test_aggregate_metrics_remain_consistent_with_per_task_records(self):
        result = run_generative_bridge_v5_replay_v1()
        records = result["per_task_records"]
        assert result["task_metrics"]["attempted_tasks"] == len(records)
        assert result["task_metrics"]["candidate_generated_tasks"] == sum(1 for record in records if record["candidate_generated"])
        assert result["task_metrics"]["candidate_deserved_tasks"] == sum(1 for record in records if record["candidate_deserved"])
        assert result["task_metrics"]["safe_failure_count"] == sum(1 for record in records if record["safe_failure"])
        assert result["task_metrics"]["deserved_exact_count"] == sum(1 for record in records if record["deserved_exact"])
        assert result["task_metrics"]["deserved_but_wrong_count"] == sum(1 for record in records if record["deserved_but_wrong"])
        assert result["task_metrics"]["undeserved_exact_count"] == sum(1 for record in records if record["undeserved_exact"])

    def test_scoring_is_durable_across_separate_python_processes(self):
        snippet = """
import json
from weslr.arc_generative_bridge_v5_replay import run_generative_bridge_v5_replay_v1
result = run_generative_bridge_v5_replay_v1()
print(json.dumps({
    'deserved_exact_task_ids': result['deserved_exact_task_ids'],
    'deserved_but_wrong_task_ids': result['deserved_but_wrong_task_ids'],
    'unscorable_task_ids': result['unscorable_task_ids'],
    'group_scoring_audit': result['group_scoring_audit'],
}, sort_keys=True))
"""
        run1 = subprocess.check_output([sys.executable, "-c", snippet], text=True)
        run2 = subprocess.check_output([sys.executable, "-c", snippet], text=True)
        assert json.loads(run1) == json.loads(run2)
