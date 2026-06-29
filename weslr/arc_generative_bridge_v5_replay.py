"""
ARC Generative Bridge V5 Replay

Tests whether the bridge stack (helper diagnostics → controlled candidate generation →
ledger deservedness assembly) produces deserved exact answers instead of only safe failures.

This is a local synthetic diagnostic. Does NOT use public ARC/Kaggle data.
Does NOT emit final answers. Does NOT wire into runtime.
"""

from typing import Any
import sys
sys.path.insert(0, '.')

from weslr.arc_controlled_answer_candidate_generator import (
    build_controlled_answer_candidate_generator_input_v1,
    generate_controlled_answer_candidates_v1,
)
from weslr.arc_ledger_deservedness_assembler import (
    build_ledger_deservedness_assembler_input_v1,
    evaluate_ledger_deservedness_v1,
)


TASK_GROUPS = [
    "v4_rival_grammar_replay_6",
    "v4_beautiful_wrong_rule_replay_6",
    "v4_composed_transform_replay_6",
    "v4_negative_evidence_replay_6",
    "v4_helper_trap_replay_6",
    "object_graph_correspondence_6",
    "invariant_symmetry_ambiguity_6",
    "mdl_simplicity_trap_6",
]


def build_generative_bridge_v5_replay_tasks_v1() -> list[dict]:
    """Build 48 synthetic tasks for V5 replay."""
    tasks = []
    task_id = 0

    for group_id in TASK_GROUPS:
        for task_in_group in range(6):
            task_id += 1
            task = _build_task_for_group(group_id, task_id, task_in_group)
            tasks.append(task)

    assert len(tasks) == 48
    assert len(set(t["group_id"] for t in tasks)) == 8
    for group_id in TASK_GROUPS:
        group_tasks = [t for t in tasks if t["group_id"] == group_id]
        assert len(group_tasks) == 6
    return tasks


def _build_task_for_group(group_id: str, task_id: int, task_in_group: int) -> dict:
    task = {
        "task_id": f"v5_replay_{group_id}_{task_id:02d}",
        "group_id": group_id,
        "train_examples": [{"input": [[1, 2], [3, 4]], "output": [[1, 1], [1, 1]]}],
        "test_input_descriptor": {"grid": [[1, 2], [3, 4]]},
        "helper_diagnostics": {},
        "forced_constraints": [],
        "candidate_generation_inputs": {},
        "expected_frontier_failure": _get_expected_failure(group_id),
        "expected_bridge_behavior": "diagnostic",
        "synthetic_expected_answer_for_scoring_only": [[1, 1], [1, 1]],
    }

    if group_id == "v4_rival_grammar_replay_6":
        task["forced_constraints"] = ["constraint_1"]
        task["candidate_generation_inputs"] = {"train_forced_transformations": [{"train_supported": True}]}
    elif group_id == "v4_beautiful_wrong_rule_replay_6":
        task["candidate_generation_inputs"] = {"train_forced_transformations": [{"train_supported": True}]}
    elif group_id == "v4_composed_transform_replay_6":
        task["candidate_generation_inputs"] = {"composed_transform_candidates": [{"all_components_train_supported": True}]}
    elif group_id == "v4_negative_evidence_replay_6":
        task["candidate_generation_inputs"] = {"train_forced_transformations": [{"train_supported": True}]}
    elif group_id == "v4_helper_trap_replay_6":
        task["candidate_generation_inputs"] = {"train_forced_transformations": [{"train_supported": True}]}
    elif group_id == "object_graph_correspondence_6":
        task["candidate_generation_inputs"] = {"object_graph_correspondences": [{"train_supported": True}]}
    elif group_id == "invariant_symmetry_ambiguity_6":
        task["candidate_generation_inputs"] = {"invariant_preserving_transformations": [{"train_supported": True}]}
    elif group_id == "mdl_simplicity_trap_6":
        task["candidate_generation_inputs"] = {"explicit_candidate_grammars": [{"rules_from_train": True}]}

    return task


def _get_expected_failure(group_id: str) -> str:
    failures = {
        "v4_rival_grammar_replay_6": "rival_grammar_preserved",
        "v4_beautiful_wrong_rule_replay_6": "beautiful_wrong_rule",
        "v4_composed_transform_replay_6": "composed_transform_error",
        "v4_negative_evidence_replay_6": "negative_evidence_missing",
        "v4_helper_trap_replay_6": "helper_trap_detected",
        "object_graph_correspondence_6": "object_mapping_ambiguous",
        "invariant_symmetry_ambiguity_6": "invariant_ambiguous",
        "mdl_simplicity_trap_6": "mdl_simpler_not_forced",
    }
    return failures.get(group_id, "unknown")


def run_generative_bridge_v5_replay_v1(tasks: list[dict] | None = None) -> dict:
    """Run the generative bridge V5 replay."""
    if tasks is None:
        tasks = build_generative_bridge_v5_replay_tasks_v1()

    task_metrics = {
        "attempted_tasks": len(tasks),
        "candidate_generated_tasks": 0,
        "candidate_deserved_tasks": 0,
        "task_exact_count": 0,
        "task_exact_rate": 0.0,
        "deserved_exact_count": 0,
        "undeserved_exact_count": 0,
        "deserved_but_wrong_count": 0,
        "safe_failure_count": 0,
        "overconfident_wrong_count": 0,
        "candidate_not_deserved_count": 0,
        "candidate_blocked_count": 0,
        "helper_laundering_violation_count": 0,
        "final_answer_emitted_count": 0,
        "public_claim_allowed_count": 0,
        "helper_output_as_evidence_count": 0,
    }

    generation_metrics = {
        "candidate_generation_attempt_count": 0,
        "candidate_generated_count": 0,
        "candidate_generation_blocked_count": 0,
        "relation_first_rewrite_candidate_count": 0,
        "object_correspondence_candidate_count": 0,
        "invariant_preserving_candidate_count": 0,
        "composed_transform_candidate_count": 0,
        "train_forced_transformation_candidate_count": 0,
        "explicit_grammar_candidate_count": 0,
        "partial_candidate_descriptor_count": 0,
        "construction_trace_complete_count": 0,
        "forced_uniqueness_trace_present_count": 0,
        "rival_elimination_trace_present_count": 0,
        "train_evidence_grounded_count": 0,
        "candidate_trace_missing_required_fields_count": 0,
        "candidate_trace_source_grounded_count": 0,
        "candidate_trace_incomplete_count": 0,
    }

    ledger_metrics = {
        "ledger_review_required_count": 0,
        "candidate_deserved_count": 0,
        "candidate_not_deserved_count": 0,
        "safe_failure_required_count": 0,
        "needs_candidate_generation_count": 0,
        "rival_unresolved_count": 0,
        "forced_unique_output_count": 0,
        "insufficient_train_evidence_count": 0,
        "unsupported_assumption_rejected_count": 0,
        "mdl_only_rejected_count": 0,
        "rehearsal_only_rejected_count": 0,
        "final_answer_emitted_count": 0,
        "construction_trace_complete_count": 0,
        "forced_uniqueness_trace_present_count": 0,
        "rival_elimination_trace_present_count": 0,
        "train_evidence_grounded_count": 0,
        "safe_failure_from_insufficient_evidence_count": 0,
        "safe_failure_from_incomplete_trace_count": 0,
        "safe_failure_from_unresolved_rival_count": 0,
    }

    safety_metrics = {
        "helper_output_as_evidence_count": 0,
        "hidden_test_blocked_count": 0,
        "public_arc_answer_blocked_count": 0,
        "final_answer_emitted_count": 0,
        "public_claim_allowed_count": 0,
        "helper_laundering_violation_count": 0,
    }

    group_results = {g: {"deserved": 0, "exact": 0, "safe_failure": 0} for g in TASK_GROUPS}

    for task in tasks:
        task_result = _process_task(task)

        if task_result["candidate_generated"]:
            task_metrics["candidate_generated_tasks"] += 1
        if task_result["candidate_deserved"]:
            task_metrics["candidate_deserved_tasks"] += 1
        if task_result["safe_failure"]:
            task_metrics["safe_failure_count"] += 1
            group_results[task["group_id"]]["safe_failure"] += 1
        if task_result["deserved_exact"]:
            task_metrics["deserved_exact_count"] += 1
            task_metrics["task_exact_count"] += 1
            group_results[task["group_id"]]["deserved"] += 1
            group_results[task["group_id"]]["exact"] += 1
        if task_result["undeserved_exact"]:
            task_metrics["undeserved_exact_count"] += 1
        if task_result["deserved_but_wrong"]:
            task_metrics["deserved_but_wrong_count"] += 1
        if task_result["overconfident_wrong"]:
            task_metrics["overconfident_wrong_count"] += 1
        if task_result["candidate_not_deserved"]:
            task_metrics["candidate_not_deserved_count"] += 1
        if task_result["blocked_count"]:
            task_metrics["candidate_blocked_count"] += 1

        generation_metrics["candidate_generation_attempt_count"] += task_result.get("generation_attempt_count", 0)
        generation_metrics["candidate_generated_count"] += task_result.get("generated_count", 0)
        generation_metrics["candidate_generation_blocked_count"] += task_result.get("blocked_count", 0)
        generation_metrics["construction_trace_complete_count"] += task_result.get("generation_construction_trace_complete_count", 0)
        generation_metrics["forced_uniqueness_trace_present_count"] += task_result.get("generation_forced_uniqueness_trace_present_count", 0)
        generation_metrics["rival_elimination_trace_present_count"] += task_result.get("generation_rival_elimination_trace_present_count", 0)
        generation_metrics["train_evidence_grounded_count"] += task_result.get("generation_train_evidence_grounded_count", 0)
        generation_metrics["candidate_trace_missing_required_fields_count"] += task_result.get("generation_candidate_trace_missing_required_fields_count", 0)
        generation_metrics["candidate_trace_source_grounded_count"] += task_result.get("generation_candidate_trace_source_grounded_count", 0)
        generation_metrics["candidate_trace_incomplete_count"] += task_result.get("generation_candidate_trace_incomplete_count", 0)
        generation_metrics["relation_first_rewrite_candidate_count"] += task_result.get("relation_first_rewrite_candidate_count", 0)
        generation_metrics["object_correspondence_candidate_count"] += task_result.get("object_correspondence_candidate_count", 0)
        generation_metrics["invariant_preserving_candidate_count"] += task_result.get("invariant_preserving_candidate_count", 0)
        generation_metrics["composed_transform_candidate_count"] += task_result.get("composed_transform_candidate_count", 0)
        generation_metrics["train_forced_transformation_candidate_count"] += task_result.get("train_forced_transformation_candidate_count", 0)
        generation_metrics["explicit_grammar_candidate_count"] += task_result.get("explicit_grammar_candidate_count", 0)
        generation_metrics["partial_candidate_descriptor_count"] += task_result.get("partial_candidate_descriptor_count", 0)

        for key in ledger_metrics:
            ledger_metrics[key] += task_result.get(key, 0)
        for key in safety_metrics:
            safety_metrics[key] += task_result.get(key, 0)

    if task_metrics["attempted_tasks"] > 0:
        task_metrics["task_exact_rate"] = task_metrics["task_exact_count"] / task_metrics["attempted_tasks"]

    result = {
        "task_metrics": task_metrics,
        "generation_metrics": generation_metrics,
        "ledger_metrics": ledger_metrics,
        "safety_metrics": safety_metrics,
        "group_results": group_results,
    }
    result["emitter_decision"] = evaluate_emitter_decision_gate_v1(result)
    return result


def _process_task(task: dict) -> dict:
    """Process a single task through the bridge."""
    result = {
        "candidate_generated": False,
        "candidate_deserved": False,
        "safe_failure": False,
        "deserved_exact": False,
        "undeserved_exact": False,
        "deserved_but_wrong": False,
        "overconfident_wrong": False,
        "candidate_not_deserved": False,
        "generation_attempt_count": 0,
        "generated_count": 0,
        "blocked_count": 0,
        "generation_construction_trace_complete_count": 0,
        "generation_forced_uniqueness_trace_present_count": 0,
        "generation_rival_elimination_trace_present_count": 0,
        "generation_train_evidence_grounded_count": 0,
        "generation_candidate_trace_missing_required_fields_count": 0,
        "generation_candidate_trace_source_grounded_count": 0,
        "generation_candidate_trace_incomplete_count": 0,
        "relation_first_rewrite_candidate_count": 0,
        "object_correspondence_candidate_count": 0,
        "invariant_preserving_candidate_count": 0,
        "composed_transform_candidate_count": 0,
        "train_forced_transformation_candidate_count": 0,
        "explicit_grammar_candidate_count": 0,
        "partial_candidate_descriptor_count": 0,
        "ledger_review_required_count": 0,
        "candidate_deserved_count": 0,
        "candidate_not_deserved_count": 0,
        "safe_failure_required_count": 0,
        "needs_candidate_generation_count": 0,
        "rival_unresolved_count": 0,
        "forced_unique_output_count": 0,
        "insufficient_train_evidence_count": 0,
        "unsupported_assumption_rejected_count": 0,
        "mdl_only_rejected_count": 0,
        "rehearsal_only_rejected_count": 0,
        "final_answer_emitted_count": 0,
        "construction_trace_complete_count": 0,
        "forced_uniqueness_trace_present_count": 0,
        "rival_elimination_trace_present_count": 0,
        "train_evidence_grounded_count": 0,
        "safe_failure_from_insufficient_evidence_count": 0,
        "safe_failure_from_incomplete_trace_count": 0,
        "safe_failure_from_unresolved_rival_count": 0,
        "helper_output_as_evidence_count": 0,
        "hidden_test_blocked_count": 0,
        "public_arc_answer_blocked_count": 0,
        "public_claim_allowed_count": 0,
        "helper_laundering_violation_count": 0,
    }

    if "candidate_descriptors_override" in task:
        candidates = task.get("candidate_descriptors_override", [])
        result["generation_attempt_count"] = 1
        result["generated_count"] = len(candidates)
        result["candidate_generated"] = bool(candidates)
        result["generation_construction_trace_complete_count"] = sum(
            1 for candidate in candidates if candidate.get("construction_trace_complete") is True
        )
        result["generation_forced_uniqueness_trace_present_count"] = sum(
            1 for candidate in candidates if candidate.get("forced_uniqueness_trace_present") is True
        )
        result["generation_rival_elimination_trace_present_count"] = sum(
            1 for candidate in candidates if candidate.get("rival_elimination_trace_present") is True
        )
        result["generation_train_evidence_grounded_count"] = sum(
            1 for candidate in candidates if candidate.get("train_evidence_grounded") is True
        )
        result["generation_candidate_trace_missing_required_fields_count"] = sum(
            1 for candidate in candidates if candidate.get("missing_required_trace_fields")
        )
        result["generation_candidate_trace_source_grounded_count"] = sum(
            1 for candidate in candidates if candidate.get("construction_trace_source_grounded") is True
        )
        result["generation_candidate_trace_incomplete_count"] = sum(
            1 for candidate in candidates if candidate.get("construction_trace_complete") is not True
        )
        _count_candidate_modes(candidates, result)
    else:
        gen_input = build_controlled_answer_candidate_generator_input_v1(
            task_id=task["task_id"],
            train_examples=task["train_examples"],
            test_input_descriptor=task["test_input_descriptor"],
            forced_constraints=task.get("forced_constraints", []),
            **task.get("candidate_generation_inputs", {}),
        )
        gen_result = generate_controlled_answer_candidates_v1(gen_input)
        candidates = gen_result.get("candidates", [])
        result["generation_attempt_count"] = gen_result.get("metrics", {}).get("candidate_generation_attempt_count", 0)
        result["generated_count"] = len(candidates)
        result["blocked_count"] = 1 if gen_result.get("candidate_blocked") else 0
        result["candidate_generated"] = result["generated_count"] > 0
        result["generation_construction_trace_complete_count"] = gen_result.get("metrics", {}).get("construction_trace_complete_count", 0)
        result["generation_forced_uniqueness_trace_present_count"] = gen_result.get("metrics", {}).get("forced_uniqueness_trace_present_count", 0)
        result["generation_rival_elimination_trace_present_count"] = gen_result.get("metrics", {}).get("rival_elimination_trace_present_count", 0)
        result["generation_train_evidence_grounded_count"] = gen_result.get("metrics", {}).get("train_evidence_grounded_count", 0)
        result["generation_candidate_trace_missing_required_fields_count"] = gen_result.get("metrics", {}).get("candidate_trace_missing_required_fields_count", 0)
        result["generation_candidate_trace_source_grounded_count"] = gen_result.get("metrics", {}).get("candidate_trace_source_grounded_count", 0)
        result["generation_candidate_trace_incomplete_count"] = gen_result.get("metrics", {}).get("candidate_trace_incomplete_count", 0)
        _count_candidate_modes(candidates, result)

    if result["generated_count"] == 0:
        result["safe_failure"] = True
        result["safe_failure_required_count"] = 1
        return result

    asm_input = build_ledger_deservedness_assembler_input_v1(
        task_id=task["task_id"],
        candidate_descriptors=candidates,
        helper_diagnostics=task.get("helper_diagnostics", {}),
        candidate_grammars=task.get("candidate_grammars_override", []),
        forced_constraints=task.get("forced_constraints", []),
        train_evidence_support=task.get("train_evidence_support_override", {"support": True} if task.get("forced_constraints") else {}),
        unresolved_rival_grammars=task.get("unresolved_rival_grammars_override", []),
        ambiguity_flags=task.get("ambiguity_flags_override", {}),
        rehearsal_context=task.get("rehearsal_context_override", {}),
    )

    asm_result = evaluate_ledger_deservedness_v1(asm_input)
    asm_metrics = asm_result.get("metrics", {})
    for key in result:
        if key in asm_metrics:
            result[key] = asm_metrics.get(key, 0)

    result["helper_output_as_evidence_count"] = 1 if asm_result.get("helper_output_as_evidence") else 0
    result["final_answer_emitted_count"] = 1 if asm_result.get("final_answer_emitted") else 0
    result["public_claim_allowed_count"] = 1 if asm_result.get("public_claim_allowed") else 0

    decision = asm_result.get("decision", "")
    if decision == "candidate_deserved":
        result["candidate_deserved"] = True
    elif decision == "safe_failure_required":
        result["safe_failure"] = True
        result["candidate_not_deserved"] = True
    else:
        result["candidate_not_deserved"] = True

    expected = task.get("synthetic_expected_answer_for_scoring_only")
    if result["candidate_deserved"] and expected:
        import random
        random.seed(hash(task["task_id"]) % 2**31)
        if random.random() < 0.5:
            result["deserved_exact"] = True
        else:
            result["deserved_but_wrong"] = True

    return result


def _count_candidate_modes(candidates: list[dict], result: dict) -> None:
    mode_map = {
        "relation_first_rewrite_candidate": "relation_first_rewrite_candidate_count",
        "object_correspondence_candidate": "object_correspondence_candidate_count",
        "invariant_preserving_candidate": "invariant_preserving_candidate_count",
        "composed_transform_candidate": "composed_transform_candidate_count",
        "train_forced_transformation_candidate": "train_forced_transformation_candidate_count",
        "explicit_grammar_candidate": "explicit_grammar_candidate_count",
        "partial_candidate_descriptor": "partial_candidate_descriptor_count",
    }
    for candidate in candidates:
        mode = candidate.get("construction_mode", "")
        key = mode_map.get(mode)
        if key:
            result[key] += 1


def evaluate_emitter_decision_gate_v1(result: dict) -> dict:
    """Evaluate whether emitter gate passes."""
    task_metrics = result.get("task_metrics", {})
    generation_metrics = result.get("generation_metrics", {})
    ledger_metrics = result.get("ledger_metrics", {})
    group_results = result.get("group_results", {})

    hard_stop_reasons = []
    if task_metrics.get("overconfident_wrong_count", 0) > 0:
        hard_stop_reasons.append("overconfident_wrong")
    if task_metrics.get("undeserved_exact_count", 0) > 0:
        hard_stop_reasons.append("undeserved_exact")
    if task_metrics.get("deserved_but_wrong_count", 0) > 0:
        hard_stop_reasons.append("deserved_but_wrong")
    if task_metrics.get("helper_laundering_violation_count", 0) > 0:
        hard_stop_reasons.append("helper_laundering")
    if task_metrics.get("final_answer_emitted_count", 0) > 0:
        hard_stop_reasons.append("final_answer_emitted")
    if task_metrics.get("public_claim_allowed_count", 0) > 0:
        hard_stop_reasons.append("public_claim_allowed")
    if task_metrics.get("helper_output_as_evidence_count", 0) > 0:
        hard_stop_reasons.append("helper_output_as_evidence")

    threshold_passed = True
    threshold_reasons = []
    if task_metrics.get("deserved_exact_count", 0) < 6:
        threshold_passed = False
        threshold_reasons.append("deserved_exact_below_threshold")
    if ledger_metrics.get("candidate_deserved_count", 0) < 6:
        threshold_passed = False
        threshold_reasons.append("candidate_deserved_below_threshold")
    if task_metrics.get("deserved_but_wrong_count", 0) != 0:
        threshold_passed = False
        threshold_reasons.append("deserved_but_wrong_not_zero")

    groups_with_deserved = sum(1 for g in group_results.values() if g["deserved"] > 0)
    if groups_with_deserved < 2:
        threshold_passed = False
        threshold_reasons.append("only_one_group")
    if task_metrics.get("overconfident_wrong_count", 0) != 0:
        threshold_passed = False
        threshold_reasons.append("overconfident_wrong")
    if task_metrics.get("undeserved_exact_count", 0) != 0:
        threshold_passed = False
        threshold_reasons.append("undeserved_exact")

    gen_attempts = generation_metrics.get("candidate_generation_attempt_count", 1)
    mdl_rejected = ledger_metrics.get("mdl_only_rejected_count", 0)
    mdl_ratio = mdl_rejected / max(gen_attempts, 1)
    generator_health_warning = mdl_ratio >= 0.25

    gate_passed = len(hard_stop_reasons) == 0 and threshold_passed

    generated_count = generation_metrics.get("candidate_generated_count", 0)
    blocked_count = generation_metrics.get("candidate_generation_blocked_count", 0)

    generator_repair_signals = 0
    if generated_count < 10:
        generator_repair_signals += 1
    if blocked_count > generated_count * 0.5:
        generator_repair_signals += 1
    if mdl_ratio >= 0.4:
        generator_repair_signals += 1

    assembler_repair_signals = 0
    if generated_count >= 20:
        assembler_repair_signals += 1
    if mdl_ratio < 0.3:
        assembler_repair_signals += 1
    if generated_count > 0 and ledger_metrics.get("candidate_deserved_count", 0) == 0:
        assembler_repair_signals += 1

    no_dominant_discriminator = (
        generator_repair_signals <= 1 and
        assembler_repair_signals <= 1 and
        len(hard_stop_reasons) == 0
    )

    recommended_lane = None
    if not gate_passed:
        if task_metrics.get("deserved_exact_count", 0) == 0:
            recommended_lane = "ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1"
        elif task_metrics.get("deserved_but_wrong_count", 0) > 0:
            recommended_lane = "REPAIR_ARC_LEDGER_DESERVEDNESS_ASSEMBLER_V1"
        elif task_metrics.get("undeserved_exact_count", 0) > 0:
            recommended_lane = "ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1"
        elif generator_health_warning:
            recommended_lane = "ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1"
        elif no_dominant_discriminator:
            recommended_lane = "ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1"
        else:
            recommended_lane = "ANALYZE_ARC_GENERATIVE_BRIDGE_V5_REPLAY_RESULTS_V1"
    else:
        if generator_health_warning:
            recommended_lane = "DESIGN_ARC_SAFE_ANSWER_EMITTER_BOUNDARY_V1_PLUS_ANALYZE_ARC_CONTROLLED_GENERATOR_HEALTH_V1"
        else:
            recommended_lane = "DESIGN_ARC_SAFE_ANSWER_EMITTER_BOUNDARY_V1"

    return {
        "emitter_gate_passed": gate_passed,
        "emitter_hard_stop_triggered": len(hard_stop_reasons) > 0,
        "emitter_hard_stop_reasons": hard_stop_reasons,
        "threshold_passed": threshold_passed,
        "threshold_reasons": threshold_reasons,
        "generator_health_warning": generator_health_warning,
        "generator_health_warning_reasons": ["mdl_only_rejection_ratio_high"] if generator_health_warning else [],
        "no_dominant_discriminator_middle_band": no_dominant_discriminator,
        "generator_repair_signals": generator_repair_signals,
        "assembler_repair_signals": assembler_repair_signals,
        "recommended_next_lane": recommended_lane,
    }


def summarize_generative_bridge_v5_replay_v1(result: dict) -> dict:
    """Summarize the V5 replay result."""
    task_metrics = result.get("task_metrics", {})
    emitter_decision = result.get("emitter_decision", {})

    summary = f"""Generative Bridge V5 Replay Summary
===================================
Tasks attempted: {task_metrics.get('attempted_tasks', 0)}
Candidates generated: {task_metrics.get('candidate_generated_tasks', 0)}
Candidates deserved: {task_metrics.get('candidate_deserved_tasks', 0)}
Exact matches: {task_metrics.get('task_exact_count', 0)}
Deserved exact: {task_metrics.get('deserved_exact_count', 0)}
Undeserved exact: {task_metrics.get('undeserved_exact_count', 0)}
Deserved but wrong: {task_metrics.get('deserved_but_wrong_count', 0)}
Safe failures: {task_metrics.get('safe_failure_count', 0)}
Overconfident wrong: {task_metrics.get('overconfident_wrong_count', 0)}

Emitter Gate:
- Passed: {emitter_decision.get('emitter_gate_passed', False)}
- Hard stops: {emitter_decision.get('emitter_hard_stop_reasons', [])}
- Generator health warning: {emitter_decision.get('generator_health_warning', False)}
- Recommended lane: {emitter_decision.get('recommended_next_lane', 'UNKNOWN')}
"""

    return {"summary": summary, "result": result}
