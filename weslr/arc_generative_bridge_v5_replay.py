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

# Candidate‑output / trace surface helpers for the bridge
from weslr.arc_candidate_output_trace_surface import (
    build_candidate_output_surface,
    build_candidate_trace_surface,
    build_replay_preserved_surface_bundle,
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
        "rival_context_detected_count": 0,
        "rival_context_missing_proof_count": 0,
        "train_forced_rival_bypass_blocked_count": 0,
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
        "rival_context_detected_count": 0,
        "rival_context_missing_proof_count": 0,
        "rival_context_safe_failure_count": 0,
        "train_forced_rival_bypass_blocked_count": 0,
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
    per_task_records = []

    for task in tasks:
        task_result = _process_task(task)
        per_task_records.append(task_result["per_task_record"])

        if task_result["candidate_generated"]:
            task_metrics["candidate_generated_tasks"] += 1
        if task_result["candidate_deserved"]:
            task_metrics["candidate_deserved_tasks"] += 1
            group_results[task["group_id"]]["deserved"] += 1
        if task_result["safe_failure"]:
            task_metrics["safe_failure_count"] += 1
            group_results[task["group_id"]]["safe_failure"] += 1
        if task_result["deserved_exact"]:
            task_metrics["deserved_exact_count"] += 1
            task_metrics["task_exact_count"] += 1
            group_results[task["group_id"]]["exact"] += 1
        if task_result["undeserved_exact"]:
            task_metrics["undeserved_exact_count"] += 1
            task_metrics["task_exact_count"] += 1
            group_results[task["group_id"]]["exact"] += 1
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
        generation_metrics["rival_context_detected_count"] += task_result.get("generation_rival_context_detected_count", 0)
        generation_metrics["rival_context_missing_proof_count"] += task_result.get("generation_rival_context_missing_proof_count", 0)
        generation_metrics["train_forced_rival_bypass_blocked_count"] += task_result.get("generation_train_forced_rival_bypass_blocked_count", 0)
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
        "per_task_records": per_task_records,
    }
    result.update(_build_named_task_id_lists(per_task_records))
    result["group_scoring_audit"] = _build_group_scoring_audit(per_task_records)
    result["emitter_decision"] = evaluate_emitter_decision_gate_v1(result)
    _attach_per_task_hard_stop_context(result)
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
        "candidate_blocked": False,
        "ledger_decision": "",
        "post_ledger_scoring_status": "not_scored_before_ledger_decision",
        "post_ledger_scoring_mechanism": "not_scored",
        "post_ledger_scoring_seed_or_determinism_note": "No post-ledger scoring executed yet.",
        "rng_or_hash_influenced_scoring": False,
        "rng_or_hash_influence_type": "none",
        "candidate_output_available": False,
        "expected_output_available": False,
        "candidate_trace_provenance": _candidate_trace_provenance(task),
        "scoring_mechanism_classification": "unknown",
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
        "generation_rival_context_detected_count": 0,
        "generation_rival_context_missing_proof_count": 0,
        "generation_train_forced_rival_bypass_blocked_count": 0,
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
        "rival_context_detected_count": 0,
        "rival_context_missing_proof_count": 0,
        "rival_context_safe_failure_count": 0,
        "train_forced_rival_bypass_blocked_count": 0,
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
        result["generation_rival_context_detected_count"] = sum(
            1 for candidate in candidates if candidate.get("rival_context_detected") is True
        )
        result["generation_rival_context_missing_proof_count"] = sum(
            1
            for candidate in candidates
            if candidate.get("rival_context_detected") is True and candidate.get("missing_required_trace_fields")
        )
        result["generation_train_forced_rival_bypass_blocked_count"] = sum(
            1
            for candidate in candidates
            if candidate.get("construction_mode") == "train_forced_transformation_candidate"
            and candidate.get("rival_context_detected") is True
            and candidate.get("construction_trace_complete") is not True
        )
        _count_candidate_modes(candidates, result)
    else:
        gen_input = build_controlled_answer_candidate_generator_input_v1(
            task_id=task["task_id"],
            train_examples=task["train_examples"],
            test_input_descriptor=task["test_input_descriptor"],
            group_id=task.get("group_id"),
            expected_frontier_failure=task.get("expected_frontier_failure"),
            rival_context_hint=task.get("rival_context_hint", False),
            multiple_plausible_transformations=task.get("multiple_plausible_transformations", False),
            forced_constraints=task.get("forced_constraints", []),
            **task.get("candidate_generation_inputs", {}),
        )
        gen_result = generate_controlled_answer_candidates_v1(gen_input)
        candidates = gen_result.get("candidates", [])

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
        result["generation_rival_context_detected_count"] = gen_result.get("metrics", {}).get("rival_context_detected_count", 0)
        result["generation_rival_context_missing_proof_count"] = gen_result.get("metrics", {}).get("rival_context_missing_proof_count", 0)
        result["generation_train_forced_rival_bypass_blocked_count"] = gen_result.get("metrics", {}).get("train_forced_rival_bypass_blocked_count", 0)
        _count_candidate_modes(candidates, result)

    result["candidate_blocked"] = result["blocked_count"] > 0

    if result["generated_count"] == 0:
        result["safe_failure"] = True
        result["safe_failure_required_count"] = 1
        result["ledger_decision"] = "needs_candidate_generation"
        result.update(_score_post_ledger(task, candidates, result))
        result["per_task_record"] = _build_per_task_record(task, result)
        # Attach candidate output and trace surfaces if they were built above (in candidates loop)
        # Find first candidate that has a candidate_output_surface
        for cand in candidates:
            if "candidate_output_surface" in cand:
                result["per_task_record"]["candidate_output_surface"] = cand["candidate_output_surface"]
                # Build a matching trace surface using helper (reuse existing if present)
                trace_surface = build_candidate_trace_surface(
                    construction_mode=cand.get("construction_mode", "unknown"),
                    construction_trace_complete=cand.get("construction_trace_complete", False),
                    forced_uniqueness_trace_present=cand.get("forced_uniqueness_trace_present", False),
                    train_evidence_grounded=cand.get("train_evidence_grounded", False),
                    candidate_trace_provenance="generator",
                    candidate_output_surface_present=True,
                    candidate_output_surface_type="grid_int_matrix",
                )
                result["per_task_record"]["candidate_trace_surface"] = trace_surface
                # Preserve replay bundle as well
                result["per_task_record"]["replay_preserved_surface_bundle"] = build_replay_preserved_surface_bundle(
                    candidate_output_surface=cand["candidate_output_surface"],
                    candidate_trace_surface=trace_surface,
                    expected_output_available=False,
                )
                break

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
        group_id=task.get("group_id"),
        expected_frontier_failure=task.get("expected_frontier_failure"),
        rival_context_hint=task.get("rival_context_hint", False),
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
    result["ledger_decision"] = decision
    if decision == "candidate_deserved":
        result["candidate_deserved"] = True
    elif decision == "safe_failure_required":
        result["safe_failure"] = True
        result["candidate_not_deserved"] = True
    else:
        result["candidate_not_deserved"] = True

    result.update(_score_post_ledger(task, candidates, result))
    # Attach candidate output surface if any candidate has it (already built above)
    base_record = _build_per_task_record(task, result)
    for cand in candidates:
        if "candidate_output_surface" in cand:
            base_record["candidate_output_surface"] = cand["candidate_output_surface"]
            # Build matching trace surface
            trace_surface = build_candidate_trace_surface(
                construction_mode=cand.get("construction_mode", "unknown"),
                construction_trace_complete=cand.get("construction_trace_complete", False),
                forced_uniqueness_trace_present=cand.get("forced_uniqueness_trace_present", False),
                train_evidence_grounded=cand.get("train_evidence_grounded", False),
                candidate_trace_provenance="generator",
                candidate_output_surface_present=True,
                candidate_output_surface_type="grid_int_matrix",
            )
            base_record["candidate_trace_surface"] = trace_surface
            base_record["replay_preserved_surface_bundle"] = build_replay_preserved_surface_bundle(
                candidate_output_surface=cand["candidate_output_surface"],
                candidate_trace_surface=trace_surface,
                expected_output_available=False,
            )
            break
    # Ensure per-task record always includes the candidate_output_surface key (even if absent)
    if "candidate_output_surface" not in base_record:
        base_record["candidate_output_surface"] = None
    # After ledger processing, enforce scoring status to reflect missing expected output (no leakage)
    result["post_ledger_scoring_status"] = "unscorable_due_to_missing_expected_output"
    result["candidate_output_available"] = any('candidate_output_surface' in c for c in candidates)
    # Ensure per-task record always includes candidate_output_surface (None if absent)
    result["per_task_record"] = base_record
    return result



def _candidate_trace_provenance(task: dict) -> str:
    if "candidate_descriptors_override" in task:
        return "candidate_descriptors_override"
    return "generated_from_candidate_generation_inputs"



def _normalise_scoring_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_normalise_scoring_value(v) for v in value]
    if isinstance(value, list):
        return [_normalise_scoring_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _normalise_scoring_value(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    return value



def _extract_candidate_output_for_scoring(task: dict, candidates: list[dict]) -> tuple[bool, Any, str]:
    if "candidate_output_for_scoring_only_override" in task:
        return True, task.get("candidate_output_for_scoring_only_override"), "task_candidate_output_override"

    if len(candidates) != 1:
        return False, None, "candidate_output_missing_or_ambiguous"

    candidate = candidates[0]
    for key in (
        "synthetic_candidate_output_for_scoring_only",
        "candidate_output_for_scoring_only",
        "candidate_output",
        "output_grid",
    ):
        if key in candidate:
            return True, candidate.get(key), f"candidate_field:{key}"

    return False, None, "candidate_output_missing_or_ambiguous"



def _score_post_ledger(task: dict, candidates: list[dict], result: dict) -> dict:
    expected_available = "synthetic_expected_answer_for_scoring_only" in task
    expected = task.get("synthetic_expected_answer_for_scoring_only")
    candidate_output_available, candidate_output, candidate_output_source = _extract_candidate_output_for_scoring(task, candidates)

    scoring = {
        "deserved_exact": False,
        "undeserved_exact": False,
        "deserved_but_wrong": False,
        "post_ledger_scoring_status": "not_scored_before_ledger_decision",
        "post_ledger_scoring_mechanism": "not_scored",
        "post_ledger_scoring_seed_or_determinism_note": "No post-ledger scoring executed.",
        "rng_or_hash_influenced_scoring": False,
        "rng_or_hash_influence_type": "none",
        "candidate_output_available": bool(candidate_output_available),
        "expected_output_available": bool(expected_available),
        "scoring_mechanism_classification": "unknown",
    }

    if result.get("ledger_decision") == "":
        return scoring

    if result.get("generated_count", 0) == 0:
        scoring["post_ledger_scoring_status"] = "not_scored_candidate_not_generated"
        scoring["post_ledger_scoring_mechanism"] = "candidate_output_unavailable"
        scoring["post_ledger_scoring_seed_or_determinism_note"] = "No candidate was generated, so post-ledger scoring could not run."
        scoring["scoring_mechanism_classification"] = "unscorable_due_to_missing_candidate_output"
        return scoring

    if not candidate_output_available:
        scoring["post_ledger_scoring_status"] = "unscorable_due_to_missing_candidate_output"
        scoring["post_ledger_scoring_mechanism"] = "candidate_output_unavailable"
        scoring["post_ledger_scoring_seed_or_determinism_note"] = (
            f"No comparable candidate output surface was available after ledger decision ({candidate_output_source})."
        )
        scoring["scoring_mechanism_classification"] = "unscorable_due_to_missing_candidate_output"
        return scoring

    if not expected_available:
        scoring["post_ledger_scoring_status"] = "unscorable_due_to_missing_expected_output"
        scoring["post_ledger_scoring_mechanism"] = "expected_output_unavailable"
        scoring["post_ledger_scoring_seed_or_determinism_note"] = "No expected/scoring output was available for deterministic post-ledger comparison."
        scoring["scoring_mechanism_classification"] = "unknown"
        return scoring

    candidate_normalized = _normalise_scoring_value(candidate_output)
    expected_normalized = _normalise_scoring_value(expected)
    exact = candidate_normalized == expected_normalized

    scoring["post_ledger_scoring_mechanism"] = "deterministic_expected_output_equality"
    scoring["post_ledger_scoring_seed_or_determinism_note"] = "Deterministic equality comparison after ledger decision; no RNG or hash influence."
    scoring["scoring_mechanism_classification"] = "real_post_ledger_expected_comparison"

    if result.get("candidate_deserved"):
        if exact:
            scoring["deserved_exact"] = True
            scoring["post_ledger_scoring_status"] = "scored_deserved_exact"
        else:
            scoring["deserved_but_wrong"] = True
            scoring["post_ledger_scoring_status"] = "scored_deserved_but_wrong"
        return scoring

    if exact:
        scoring["undeserved_exact"] = True
        scoring["post_ledger_scoring_status"] = "scored_undeserved_exact"
    else:
        scoring["post_ledger_scoring_status"] = "scored_candidate_not_deserved_non_exact"
    return scoring



def _build_per_task_record(task: dict, result: dict) -> dict:
    hard_stop_reason_list = []
    if result.get("overconfident_wrong"):
        hard_stop_reason_list.append("overconfident_wrong")
    if result.get("undeserved_exact"):
        hard_stop_reason_list.append("undeserved_exact")
    if result.get("deserved_but_wrong"):
        hard_stop_reason_list.append("deserved_but_wrong")
    if result.get("helper_laundering_violation_count", 0) > 0:
        hard_stop_reason_list.append("helper_laundering")
    if result.get("final_answer_emitted_count", 0) > 0:
        hard_stop_reason_list.append("final_answer_emitted")
    if result.get("public_claim_allowed_count", 0) > 0:
        hard_stop_reason_list.append("public_claim_allowed")
    if result.get("helper_output_as_evidence_count", 0) > 0:
        hard_stop_reason_list.append("helper_output_as_evidence")

    return {
        "task_id": task["task_id"],
        "group_id": task.get("group_id", "unknown"),
        "candidate_generated": bool(result.get("candidate_generated")),
        "candidate_blocked": bool(result.get("candidate_blocked")),
        "ledger_decision": result.get("ledger_decision", ""),
        "candidate_deserved": bool(result.get("candidate_deserved")),
        "candidate_not_deserved": bool(result.get("candidate_not_deserved")),
        "safe_failure": bool(result.get("safe_failure")),
        "post_ledger_scoring_status": result.get("post_ledger_scoring_status", "unknown"),
        "deserved_exact": bool(result.get("deserved_exact")),
        "deserved_but_wrong": bool(result.get("deserved_but_wrong")),
        "undeserved_exact": bool(result.get("undeserved_exact")),
        "hard_stop_triggered": bool(hard_stop_reason_list),
        "hard_stop_reason_list": hard_stop_reason_list,
        "post_ledger_scoring_mechanism": result.get("post_ledger_scoring_mechanism", "unknown"),
        "post_ledger_scoring_seed_or_determinism_note": result.get("post_ledger_scoring_seed_or_determinism_note", ""),
        "rng_or_hash_influenced_scoring": bool(result.get("rng_or_hash_influenced_scoring")),
        "rng_or_hash_influence_type": result.get("rng_or_hash_influence_type", "none"),
        "candidate_output_available": bool(result.get("candidate_output_available")),
        "expected_output_available": bool(result.get("expected_output_available")),
        "candidate_trace_provenance": result.get("candidate_trace_provenance", "unknown"),
        "scoring_mechanism_classification": result.get("scoring_mechanism_classification", "unknown"),
    }



def _build_named_task_id_lists(per_task_records: list[dict]) -> dict:
    return {
        "candidate_generated_task_ids": [r["task_id"] for r in per_task_records if r.get("candidate_generated")],
        "candidate_deserved_task_ids": [r["task_id"] for r in per_task_records if r.get("candidate_deserved")],
        "candidate_not_deserved_task_ids": [r["task_id"] for r in per_task_records if r.get("candidate_not_deserved")],
        "safe_failure_task_ids": [r["task_id"] for r in per_task_records if r.get("safe_failure")],
        "deserved_exact_task_ids": [r["task_id"] for r in per_task_records if r.get("deserved_exact")],
        "deserved_but_wrong_task_ids": [r["task_id"] for r in per_task_records if r.get("deserved_but_wrong")],
        "undeserved_exact_task_ids": [r["task_id"] for r in per_task_records if r.get("undeserved_exact")],
        "unscorable_task_ids": [
            r["task_id"]
            for r in per_task_records
            if str(r.get("post_ledger_scoring_status", "")).startswith("unscorable")
        ],
        "synthetic_randomized_stress_label_task_ids": [
            r["task_id"]
            for r in per_task_records
            if r.get("scoring_mechanism_classification") == "synthetic_randomized_stress_label"
        ],
        "rng_influenced_scoring_task_ids": [r["task_id"] for r in per_task_records if r.get("rng_or_hash_influenced_scoring")],
        "hard_stop_task_ids": [r["task_id"] for r in per_task_records if r.get("hard_stop_triggered")],
    }



def _build_group_scoring_audit(per_task_records: list[dict]) -> dict:
    audit = {}
    for group_id in TASK_GROUPS:
        records = [record for record in per_task_records if record.get("group_id") == group_id]
        mechanisms = sorted({record.get("post_ledger_scoring_mechanism", "unknown") for record in records})
        classifications = sorted({record.get("scoring_mechanism_classification", "unknown") for record in records})
        statuses = sorted({record.get("post_ledger_scoring_status", "unknown") for record in records})
        audit[group_id] = {
            "task_count": len(records),
            "uses_real_expected_comparison": any(
                record.get("post_ledger_scoring_mechanism") == "deterministic_expected_output_equality"
                for record in records
            ),
            "uses_rng_or_hash_scoring": any(record.get("rng_or_hash_influenced_scoring") for record in records),
            "uses_rng_or_hash_fallback": any(record.get("rng_or_hash_influence_type") == "fallback" for record in records),
            "uses_rng_or_hash_tie_breaker": any(record.get("rng_or_hash_influence_type") == "tie_breaker" for record in records),
            "uses_rng_or_hash_candidate_selection": any(
                record.get("rng_or_hash_influence_type") == "candidate_selection" for record in records
            ),
            "candidate_output_surface_suitable": any(record.get("candidate_output_available") for record in records),
            "expected_output_available": all(record.get("expected_output_available") for record in records) if records else False,
            "expected_output_present_but_unused": any(
                record.get("expected_output_available") and not record.get("candidate_output_available")
                for record in records
            ),
            "post_ledger_scoring_mechanisms": mechanisms,
            "post_ledger_scoring_statuses": statuses,
            "scoring_mechanism_classifications": classifications,
            "group_scoring_classification": _classify_group_scoring(records),
        }
    return audit



def _classify_group_scoring(records: list[dict]) -> str:
    if not records:
        return "unknown"
    if any(record.get("rng_or_hash_influenced_scoring") for record in records):
        return "rng_influenced_candidate_or_label_path"
    if all(record.get("scoring_mechanism_classification") == "real_post_ledger_expected_comparison" for record in records):
        return "real_post_ledger_expected_comparison"
    if all(record.get("scoring_mechanism_classification") == "unscorable_due_to_missing_candidate_output" for record in records):
        return "unscorable_due_to_missing_candidate_output"
    if any(record.get("scoring_mechanism_classification") == "real_post_ledger_expected_comparison" for record in records):
        return "mixed_real_and_randomized_path"
    return "unknown"



def _attach_per_task_hard_stop_context(result: dict) -> None:
    emitter_hard_stop_reasons = result.get("emitter_decision", {}).get("emitter_hard_stop_reasons", [])
    for record in result.get("per_task_records", []):
        task_specific_reasons = list(record.get("hard_stop_reason_list", []))
        record["hard_stop_reason_list"] = sorted(set(task_specific_reasons + [
            reason for reason in emitter_hard_stop_reasons if reason in task_specific_reasons
        ]))
        record["hard_stop_triggered"] = bool(record["hard_stop_reason_list"])



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
