"""
ARC Controlled Answer Candidate Generator

This component creates candidate output descriptors from train-forced constraints.
It does NOT generate final answers. Every candidate must require ledger review.

Core law:
- Generator creates candidates, NOT final answers
- Every candidate must pass through the ledger deservedness assembler
- No guessing
- No hidden test output
- No public ARC answers
- No repeated-rehearsal deservedness
- No MDL/elegance-only candidate choice
- No runtime wiring
"""

from typing import Any


ANTILAUNDERING_LAWS = [
    "candidate_generation_is_not_final_answer",
    "every_candidate_requires_ledger_review",
    "hidden_test_output_cannot_be_used",
    "public_arc_answers_cannot_be_used",
    "repeated_rehearsal_cannot_create_deservedness",
    "mdl_elegance_cannot_choose_candidate_alone",
    "ambiguous_correspondence_blocks_generation",
    "unresolved_rivals_block_unique_generation",
    "unforced_invariant_blocks_unique_generation",
    "unsupported_assumptions_block_generation",
    "holdout_answers_cannot_train_generator",
    "generator_cannot_mutate_solver_behavior",
]

CONSTRUCTION_MODES = [
    "relation_first_rewrite_candidate",
    "object_correspondence_candidate",
    "invariant_preserving_candidate",
    "composed_transform_candidate",
    "train_forced_transformation_candidate",
    "explicit_grammar_candidate",
    "partial_candidate_descriptor",
]

BLOCKING_STATUSES = [
    "candidate_generation_blocked",
    "safe_failure_required",
    "unsupported_assumption_blocked",
    "unresolved_rival_blocked",
    "ambiguous_correspondence_blocked",
    "unforced_invariant_blocked",
    "mdl_only_choice_blocked",
    "hidden_test_request_blocked",
    "public_answer_request_blocked",
    "ledger_bypass_blocked",
]

FORBIDDEN_STATUSES = [
    "final_answer_generated",
    "candidate_deserved_without_ledger",
    "answer_by_guessing",
    "answer_by_mdl_only",
    "answer_by_rehearsal_memory",
    "hidden_test_answer_used",
    "public_arc_answer_used",
    "runtime_behavior_changed",
]

_TRACE_REQUIRED_FIELDS_BY_MODE = {
    "relation_first_rewrite_candidate": [
        "construction_trace",
        "construction_trace_source_grounded",
        "train_evidence_grounded",
        "forced_uniqueness_trace_present",
        "source_train_ids",
        "train_grounded_transformation_rule",
        "train_grounded_forced_constraints",
        "ambiguity_check",
        "competing_output_rejection_reason",
        "uniquely_forced_reason",
    ],
    "object_correspondence_candidate": [
        "construction_trace",
        "construction_trace_source_grounded",
        "train_evidence_grounded",
        "forced_uniqueness_trace_present",
        "source_train_ids",
        "train_grounded_transformation_rule",
        "train_grounded_forced_constraints",
        "ambiguity_check",
        "competing_output_rejection_reason",
        "uniquely_forced_reason",
    ],
    "invariant_preserving_candidate": [
        "construction_trace",
        "construction_trace_source_grounded",
        "train_evidence_grounded",
        "forced_uniqueness_trace_present",
        "source_train_ids",
        "train_grounded_transformation_rule",
        "train_grounded_forced_constraints",
        "ambiguity_check",
        "competing_output_rejection_reason",
        "uniquely_forced_reason",
    ],
    "composed_transform_candidate": [
        "construction_trace",
        "construction_trace_source_grounded",
        "train_evidence_grounded",
        "forced_uniqueness_trace_present",
        "source_train_ids",
        "train_grounded_transformation_rule",
        "train_grounded_forced_constraints",
        "ambiguity_check",
        "competing_output_rejection_reason",
        "uniquely_forced_reason",
    ],
    "train_forced_transformation_candidate": [
        "construction_trace",
        "construction_trace_source_grounded",
        "train_evidence_grounded",
        "forced_uniqueness_trace_present",
        "source_train_ids",
        "train_grounded_transformation_rule",
        "train_grounded_forced_constraints",
        "ambiguity_check",
        "competing_output_rejection_reason",
        "uniquely_forced_reason",
    ],
    "explicit_grammar_candidate": [
        "construction_trace",
        "construction_trace_source_grounded",
        "train_evidence_grounded",
        "forced_uniqueness_trace_present",
        "source_train_ids",
        "train_grounded_transformation_rule",
        "train_grounded_forced_constraints",
        "ambiguity_check",
        "competing_output_rejection_reason",
        "uniquely_forced_reason",
    ],
    "partial_candidate_descriptor": [],
}


def build_controlled_answer_candidate_generator_input_v1(
    task_id: str,
    train_examples: list,
    test_input_descriptor: dict,
    forced_constraints: list | None = None,
    train_forced_transformations: list | None = None,
    object_graph_correspondences: list | None = None,
    invariant_preserving_transformations: list | None = None,
    relation_first_rewrites: list | None = None,
    composed_transform_candidates: list | None = None,
    explicit_candidate_grammars: list | None = None,
    unresolved_rival_grammars: list | None = None,
    unsupported_assumption_list: list | None = None,
    helper_diagnostics: dict | None = None,
    _requests_hidden_test: bool = False,
    _requests_public_arc_answer: bool = False,
) -> dict:
    return {
        "task_id": task_id,
        "train_examples": train_examples or [],
        "test_input_descriptor": test_input_descriptor or {},
        "forced_constraints": forced_constraints or [],
        "train_forced_transformations": train_forced_transformations or [],
        "object_graph_correspondences": object_graph_correspondences or [],
        "invariant_preserving_transformations": invariant_preserving_transformations or [],
        "relation_first_rewrites": relation_first_rewrites or [],
        "composed_transform_candidates": composed_transform_candidates or [],
        "explicit_candidate_grammars": explicit_candidate_grammars or [],
        "unresolved_rival_grammars": unresolved_rival_grammars or [],
        "unsupported_assumption_list": unsupported_assumption_list or [],
        "helper_diagnostics": helper_diagnostics or {},
        "_requests_hidden_test": _requests_hidden_test,
        "_requests_public_arc_answer": _requests_public_arc_answer,
    }


def generate_controlled_answer_candidates_v1(generator_input: dict) -> dict:
    metrics = _build_metrics()
    candidates: list[dict] = []
    blocking_reason = None
    generation_status = "none"

    if generator_input.get("_requests_hidden_test"):
        blocking_reason = "hidden_test_request_blocked"
        metrics["hidden_test_request_blocked_count"] += 1
        metrics["candidate_generation_blocked_count"] += 1
    elif generator_input.get("_requests_public_arc_answer"):
        blocking_reason = "public_answer_request_blocked"
        metrics["public_answer_request_blocked_count"] += 1
        metrics["candidate_generation_blocked_count"] += 1
    else:
        metrics["candidate_generation_attempt_count"] += 1
        candidates, blocking_in_generate = _generate_candidates(generator_input)

        if "unresolved_rival" in blocking_in_generate:
            metrics["unresolved_rival_blocked_count"] += 1
        if "ambiguous_correspondence" in blocking_in_generate:
            metrics["ambiguous_correspondence_blocked_count"] += 1
        if "unforced_invariant" in blocking_in_generate:
            metrics["unforced_invariant_blocked_count"] += 1
        if "mdl_only_choice" in blocking_in_generate:
            metrics["mdl_only_choice_blocked_count"] += 1
        if "unsupported_assumption" in blocking_in_generate:
            metrics["unsupported_assumption_blocked_count"] += 1

        if blocking_in_generate:
            blocking_reason = "candidate_generation_blocked"
            metrics["candidate_generation_blocked_count"] += 1

        metrics["candidate_generated_count"] = len(candidates)
        metrics.update(_summarize_candidate_metrics(candidates))
        generation_status = "generated" if candidates else "blocked"

    return {
        "task_id": generator_input.get("task_id"),
        "candidates": candidates,
        "blocking_reason": blocking_reason,
        "generation_status": generation_status,
        "metrics": metrics,
        "requires_ledger_review": True,
        "generator_grants_deservedness": False,
        "generator_outputs_final_answer": False,
        "candidate_treated_as_final_answer": False,
        "ledger_review_required": True,
        "rehearsal_candidate_generation_allowed": True,
        "rehearsal_counts_toward_threshold": False,
        "fresh_holdout_counts": True,
        "fresh_holdout_requires_no_leakage": True,
        "holdout_answers_must_not_train": True,
        "candidate_generated": len(candidates) > 0,
        "candidate_blocked": blocking_reason is not None,
        "missing_constraint_that_blocked": blocking_reason,
        "antilaundering_laws": ANTILAUNDERING_LAWS,
    }


def _build_metrics() -> dict:
    return {
        "candidate_generation_attempt_count": 0,
        "candidate_generated_count": 0,
        "candidate_generation_blocked_count": 0,
        "candidate_requires_ledger_review_count": 0,
        "safe_failure_required_count": 0,
        "unsupported_assumption_blocked_count": 0,
        "unresolved_rival_blocked_count": 0,
        "ambiguous_correspondence_blocked_count": 0,
        "unforced_invariant_blocked_count": 0,
        "mdl_only_choice_blocked_count": 0,
        "hidden_test_request_blocked_count": 0,
        "public_answer_request_blocked_count": 0,
        "candidate_treated_as_final_answer_count": 0,
        "ledger_review_required_count": 0,
        "construction_trace_complete_count": 0,
        "forced_uniqueness_trace_present_count": 0,
        "rival_elimination_trace_present_count": 0,
        "train_evidence_grounded_count": 0,
        "candidate_trace_missing_required_fields_count": 0,
        "candidate_trace_source_grounded_count": 0,
        "candidate_trace_incomplete_count": 0,
        "memorization_risk_flag_count": 0,
    }


def _generate_candidates(generator_input: dict) -> tuple[list[dict], list[str]]:
    candidates = []
    trace_count = 0
    task_id = generator_input.get("task_id", "unknown")
    blocking_reasons = []

    unresolved_rivals = generator_input.get("unresolved_rival_grammars", [])
    ambiguous_correspondences = generator_input.get("object_graph_correspondences", [])
    unforced_invariants = generator_input.get("invariant_preserving_transformations", [])
    mdl_only_grammars = generator_input.get("explicit_candidate_grammars", [])
    unsupported_assumptions_in_input = generator_input.get("unsupported_assumption_list", [])

    if len(unresolved_rivals) > 1:
        blocking_reasons.append("unresolved_rival")

    for corr in ambiguous_correspondences:
        if corr.get("mapping_type") == "ambiguous" or corr.get("ambiguous_with"):
            blocking_reasons.append("ambiguous_correspondence")
            break

    for inv in unforced_invariants:
        if not inv.get("train_supported", False):
            blocking_reasons.append("unforced_invariant")
            break

    for grammar in mdl_only_grammars:
        if grammar.get("mdl_only") and not grammar.get("rules_from_train"):
            blocking_reasons.append("mdl_only_choice")
            break

    if unsupported_assumptions_in_input:
        blocking_reasons.append("unsupported_assumption")

    if blocking_reasons:
        return [], blocking_reasons

    construction_sources = [
        ("train_forced_transformations", "train_forced_transformation_candidate", "train_forced_transformation"),
        ("object_graph_correspondences", "object_correspondence_candidate", "object_correspondence"),
        ("invariant_preserving_transformations", "invariant_preserving_candidate", "invariant_preserving"),
        ("relation_first_rewrites", "relation_first_rewrite_candidate", "relation_first_rewrite"),
        ("composed_transform_candidates", "composed_transform_candidate", "composed_transform"),
        ("explicit_candidate_grammars", "explicit_grammar_candidate", "explicit_grammar"),
    ]

    for input_key, mode, source_constraint in construction_sources:
        for operations in generator_input.get(input_key, []):
            if not _mode_is_eligible(mode, operations):
                continue
            candidates.append(
                _build_candidate(
                    task_id=task_id,
                    mode=mode,
                    operations=operations,
                    source_constraint=source_constraint,
                    trace_count=trace_count,
                    generator_input=generator_input,
                )
            )
            trace_count += 1

    if not candidates:
        candidates.append(_build_partial_candidate(task_id, trace_count, generator_input))

    return candidates, blocking_reasons


def _mode_is_eligible(mode: str, operations: dict) -> bool:
    if mode == "train_forced_transformation_candidate":
        return operations.get("train_supported") is True
    if mode == "object_correspondence_candidate":
        return operations.get("train_supported") is True
    if mode == "invariant_preserving_candidate":
        return operations.get("train_supported") is True
    if mode == "composed_transform_candidate":
        return operations.get("all_components_train_supported") is True
    if mode == "explicit_grammar_candidate":
        return True
    return True


def _build_candidate(
    task_id: str,
    mode: str,
    operations: dict,
    source_constraint: str,
    trace_count: int,
    generator_input: dict,
) -> dict:
    source_train_ids = _derive_source_train_ids(generator_input, operations)
    synthetic_local_train_ids = _listify(operations.get("synthetic_local_train_ids"))
    unsupported_assumptions = _listify(operations.get("unsupported_assumptions"))
    unresolved_rivals = _derive_unresolved_rivals(generator_input, operations)
    helper_output_as_evidence = False
    rehearsal_repeat_as_evidence = False
    mdl_only_support = bool(operations.get("mdl_only", False) and not operations.get("rules_from_train", False))

    train_grounded_transformation_rule = _derive_transformation_rule(mode, operations)
    train_grounded_forced_constraints = _derive_train_grounded_forced_constraints(mode, generator_input, operations)
    train_evidence_grounded = bool(
        source_train_ids
        and train_grounded_transformation_rule
        and train_grounded_forced_constraints
        and _mode_has_train_support(mode, operations)
    )
    construction_trace_source_grounded = bool(source_train_ids or synthetic_local_train_ids)
    ambiguity_check = _derive_ambiguity_check(generator_input, operations, unresolved_rivals)

    rival_grammars = _derive_rival_grammars(generator_input, operations)
    surviving_grammar = _derive_surviving_grammar(operations, unresolved_rivals)
    rival_outputs_considered = _listify(operations.get("rival_outputs_considered"))
    rejected_rival_reasons = _derive_rejected_rival_reasons(operations, rival_grammars)
    rival_elimination_trace = _derive_rival_elimination_trace(
        operations=operations,
        rival_grammars=rival_grammars,
        rejected_rival_reasons=rejected_rival_reasons,
        unresolved_rivals=unresolved_rivals,
    )
    surviving_grammar_train_evidence = _derive_surviving_grammar_train_evidence(
        operations=operations,
        surviving_grammar=surviving_grammar,
        train_evidence_grounded=train_evidence_grounded,
    )

    forced_uniqueness_trace_present = bool(
        train_evidence_grounded
        and construction_trace_source_grounded
        and ambiguity_check == "clear"
        and not unsupported_assumptions
        and not unresolved_rivals
        and (not rival_grammars or rival_elimination_trace)
    )

    competing_output_rejection_reason = _derive_competing_output_rejection_reason(
        mode=mode,
        operations=operations,
        forced_uniqueness_trace_present=forced_uniqueness_trace_present,
        rival_grammars=rival_grammars,
    )
    uniquely_forced_reason = _derive_uniquely_forced_reason(
        mode=mode,
        operations=operations,
        forced_uniqueness_trace_present=forced_uniqueness_trace_present,
    )

    if not competing_output_rejection_reason or not uniquely_forced_reason:
        forced_uniqueness_trace_present = False

    surviving_grammar_uniquely_forces_output = bool(
        surviving_grammar
        and surviving_grammar_train_evidence
        and rival_elimination_trace
        and forced_uniqueness_trace_present
    )

    candidate = {
        "candidate_id": f"{task_id}_cand_{trace_count}",
        "task_id": task_id,
        "construction_mode": mode,
        "output_shape_descriptor": operations.get("output_shape", {}),
        "object_operations": _listify(operations.get("object_operations")),
        "color_operations": _listify(operations.get("color_operations")),
        "spatial_operations": _listify(operations.get("spatial_operations")),
        "relation_operations": _listify(operations.get("relation_operations")),
        "invariant_preservation_claims": _listify(operations.get("invariant_claims")),
        "object_correspondence_claims": _derive_object_correspondence_claims(operations),
        "source_constraints": [source_constraint],
        "unsupported_assumptions": unsupported_assumptions,
        "unresolved_rivals": unresolved_rivals,
        "requires_ledger_review": True,
        "treated_as_final_answer": False,
        "candidate_treated_as_final_answer": False,
        "generation_status": "generated",
        "block_reason": None,
        "construction_trace_source_grounded": construction_trace_source_grounded,
        "train_evidence_grounded": train_evidence_grounded,
        "forced_uniqueness_trace_present": forced_uniqueness_trace_present,
        "source_train_ids": source_train_ids,
        "source_train_example_ids": list(source_train_ids),
        "synthetic_local_train_ids": synthetic_local_train_ids,
        "train_grounded_transformation_rule": train_grounded_transformation_rule,
        "train_grounded_forced_constraints": train_grounded_forced_constraints,
        "forced_constraints_tied_to_train_evidence": list(train_grounded_forced_constraints),
        "ambiguity_check": ambiguity_check,
        "competing_output_rejection_reason": competing_output_rejection_reason,
        "competing_outputs_rejected_reason": competing_output_rejection_reason,
        "uniquely_forced_reason": uniquely_forced_reason,
        "helper_output_as_evidence": helper_output_as_evidence,
        "rehearsal_repeat_as_evidence": rehearsal_repeat_as_evidence,
        "mdl_only_support": mdl_only_support,
        "rival_grammars": rival_grammars,
        "surviving_grammar": surviving_grammar,
        "rival_elimination_trace": rival_elimination_trace,
        "rival_elimination_trace_present": bool(rival_elimination_trace),
        "surviving_grammar_train_evidence": surviving_grammar_train_evidence,
        "rival_outputs_considered": rival_outputs_considered,
        "rejected_rival_reasons": rejected_rival_reasons,
        "surviving_grammar_uniquely_forces_output": surviving_grammar_uniquely_forces_output,
    }

    construction_trace = _build_construction_trace(
        trace_count=trace_count,
        source_constraint=source_constraint,
        operations=operations,
        candidate=candidate,
    )
    candidate["construction_trace"] = construction_trace
    candidate["missing_required_trace_fields"] = _missing_required_trace_fields(candidate)
    candidate["construction_trace_complete"] = (
        mode != "partial_candidate_descriptor" and not candidate["missing_required_trace_fields"]
    )
    return candidate


def _build_partial_candidate(task_id: str, trace_count: int, generator_input: dict) -> dict:
    unsupported = _listify(generator_input.get("unsupported_assumption_list"))
    unresolved_rivals = _listify(generator_input.get("unresolved_rival_grammars"))
    missing_fields = list(_TRACE_REQUIRED_FIELDS_BY_MODE["train_forced_transformation_candidate"])
    return {
        "candidate_id": f"{task_id}_cand_partial_{trace_count}",
        "task_id": task_id,
        "construction_mode": "partial_candidate_descriptor",
        "output_shape_descriptor": {},
        "object_operations": [],
        "color_operations": [],
        "spatial_operations": [],
        "relation_operations": [],
        "invariant_preservation_claims": [],
        "object_correspondence_claims": [],
        "source_constraints": [],
        "unsupported_assumptions": unsupported,
        "unresolved_rivals": unresolved_rivals,
        "construction_trace": [],
        "construction_trace_complete": False,
        "construction_trace_source_grounded": False,
        "train_evidence_grounded": False,
        "forced_uniqueness_trace_present": False,
        "source_train_ids": [],
        "source_train_example_ids": [],
        "synthetic_local_train_ids": [],
        "train_grounded_transformation_rule": "",
        "train_grounded_forced_constraints": [],
        "forced_constraints_tied_to_train_evidence": [],
        "ambiguity_check": "unresolved",
        "competing_output_rejection_reason": "",
        "competing_outputs_rejected_reason": "",
        "uniquely_forced_reason": "",
        "helper_output_as_evidence": False,
        "rehearsal_repeat_as_evidence": False,
        "mdl_only_support": False,
        "rival_grammars": [],
        "surviving_grammar": None,
        "rival_elimination_trace": [],
        "rival_elimination_trace_present": False,
        "surviving_grammar_train_evidence": "",
        "rival_outputs_considered": [],
        "rejected_rival_reasons": [],
        "surviving_grammar_uniquely_forces_output": False,
        "requires_ledger_review": True,
        "treated_as_final_answer": False,
        "candidate_treated_as_final_answer": False,
        "generation_status": "partial",
        "block_reason": "insufficient_train_evidence",
        "missing_required_trace_fields": missing_fields,
    }


def _summarize_candidate_metrics(candidates: list[dict]) -> dict:
    return {
        "candidate_requires_ledger_review_count": sum(1 for c in candidates if c.get("requires_ledger_review") is True),
        "candidate_treated_as_final_answer_count": sum(1 for c in candidates if c.get("candidate_treated_as_final_answer") is True),
        "ledger_review_required_count": sum(1 for c in candidates if c.get("requires_ledger_review") is True),
        "construction_trace_complete_count": sum(1 for c in candidates if c.get("construction_trace_complete") is True),
        "forced_uniqueness_trace_present_count": sum(1 for c in candidates if c.get("forced_uniqueness_trace_present") is True),
        "rival_elimination_trace_present_count": sum(1 for c in candidates if c.get("rival_elimination_trace_present") is True),
        "train_evidence_grounded_count": sum(1 for c in candidates if c.get("train_evidence_grounded") is True),
        "candidate_trace_missing_required_fields_count": sum(1 for c in candidates if c.get("missing_required_trace_fields")),
        "candidate_trace_source_grounded_count": sum(1 for c in candidates if c.get("construction_trace_source_grounded") is True),
        "candidate_trace_incomplete_count": sum(1 for c in candidates if c.get("construction_trace_complete") is not True),
        "memorization_risk_flag_count": 0,
    }


def _derive_source_train_ids(generator_input: dict, operations: dict) -> list[str]:
    explicit = _listify(operations.get("source_train_ids")) or _listify(operations.get("source_train_example_ids"))
    if explicit:
        return explicit
    train_examples = generator_input.get("train_examples", [])
    if not train_examples:
        return []
    if _mode_has_train_support("", operations) or operations.get("rules_from_train"):
        return [f"train_{idx + 1}" for idx, _ in enumerate(train_examples)]
    return []


def _derive_transformation_rule(mode: str, operations: dict) -> str:
    explicit = operations.get("train_grounded_transformation_rule") or operations.get("transformation_rule")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    operation_name = operations.get("operation_name")
    grammar_id = operations.get("grammar_id")
    rewrite_id = operations.get("rewrite_id")
    correspondence_id = operations.get("correspondence_id")
    invariant_type = operations.get("invariant_type")
    if mode == "train_forced_transformation_candidate" and operations.get("train_supported"):
        operation_label = operation_name or "train-supported transformation"
        return f"Train examples support {operation_label}."
    if mode == "object_correspondence_candidate" and operations.get("train_supported") and correspondence_id:
        return f"Train examples support correspondence {correspondence_id}."
    if mode == "invariant_preserving_candidate" and operations.get("train_supported") and invariant_type:
        return f"Train examples preserve invariant {invariant_type}."
    if mode == "relation_first_rewrite_candidate" and rewrite_id:
        return f"Train examples support relation rewrite {rewrite_id}."
    if mode == "composed_transform_candidate" and operations.get("all_components_train_supported"):
        return "Train examples support the composed transformation chain."
    if mode == "explicit_grammar_candidate" and operations.get("rules_from_train"):
        grammar_label = grammar_id or "the surviving grammar"
        return f"Train examples support grammar {grammar_label}."
    return ""


def _derive_train_grounded_forced_constraints(mode: str, generator_input: dict, operations: dict) -> list[str]:
    explicit = _listify(operations.get("train_grounded_forced_constraints")) or _listify(
        operations.get("forced_constraints_tied_to_train_evidence")
    )
    if explicit:
        return explicit

    base_constraints = _listify(generator_input.get("forced_constraints"))
    if base_constraints and (_mode_has_train_support(mode, operations) or operations.get("rules_from_train")):
        return base_constraints

    derived_constraints = []
    if mode == "object_correspondence_candidate" and operations.get("correspondence_id"):
        derived_constraints.append(f"Correspondence {operations['correspondence_id']} is train-supported.")
    if mode == "relation_first_rewrite_candidate" and operations.get("rewrite_id"):
        derived_constraints.append(f"Rewrite {operations['rewrite_id']} is constrained by train examples.")
    if mode == "invariant_preserving_candidate" and operations.get("invariant_type"):
        derived_constraints.append(f"Invariant {operations['invariant_type']} is preserved across train examples.")
    if mode == "explicit_grammar_candidate" and operations.get("rules_from_train"):
        grammar_label = operations.get("grammar_id", "surviving_grammar")
        derived_constraints.append(f"Grammar {grammar_label} is supported by train-derived rules.")
    if mode == "composed_transform_candidate" and operations.get("all_components_train_supported"):
        derived_constraints.append("Every composed transformation component is supported by train examples.")
    if mode == "train_forced_transformation_candidate" and operations.get("train_supported") and operations.get("operation_name"):
        derived_constraints.append(f"Operation {operations['operation_name']} is supported by train examples.")
    return derived_constraints


def _derive_ambiguity_check(generator_input: dict, operations: dict, unresolved_rivals: list[str]) -> str | bool:
    if operations.get("mapping_type") == "ambiguous" or operations.get("ambiguous_with"):
        return "unresolved"
    if unresolved_rivals:
        return "unresolved"
    if generator_input.get("unsupported_assumption_list") or operations.get("unsupported_assumptions"):
        return "unresolved"
    return "clear"


def _derive_rival_grammars(generator_input: dict, operations: dict) -> list[str]:
    return _listify(operations.get("rival_grammars")) or _listify(generator_input.get("unresolved_rival_grammars"))


def _derive_surviving_grammar(operations: dict, unresolved_rivals: list[str]) -> str | None:
    explicit = operations.get("surviving_grammar")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    grammar_id = operations.get("grammar_id")
    if grammar_id and not unresolved_rivals:
        return grammar_id
    return None


def _derive_rival_elimination_trace(
    operations: dict,
    rival_grammars: list[str],
    rejected_rival_reasons: list[str],
    unresolved_rivals: list[str],
) -> list[dict]:
    explicit = operations.get("rival_elimination_trace")
    if isinstance(explicit, list) and explicit:
        return explicit
    if not rival_grammars or unresolved_rivals or not rejected_rival_reasons:
        return []
    trace = []
    for grammar, reason in zip(rival_grammars, rejected_rival_reasons, strict=False):
        trace.append({"rival_grammar": grammar, "reason": reason})
    return trace


def _derive_surviving_grammar_train_evidence(operations: dict, surviving_grammar: str | None, train_evidence_grounded: bool) -> str:
    explicit = operations.get("surviving_grammar_train_evidence")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if surviving_grammar and train_evidence_grounded:
        return f"Train examples support surviving grammar {surviving_grammar}."
    return ""


def _derive_rejected_rival_reasons(operations: dict, rival_grammars: list[str]) -> list[str]:
    explicit = operations.get("rejected_rival_reasons")
    if isinstance(explicit, list):
        return explicit
    if not rival_grammars:
        return []
    rule = operations.get("train_grounded_transformation_rule") or operations.get("operation_name") or "train evidence"
    return [f"Rejected {grammar} because it conflicts with {rule}." for grammar in rival_grammars]


def _derive_competing_output_rejection_reason(
    mode: str,
    operations: dict,
    forced_uniqueness_trace_present: bool,
    rival_grammars: list[str],
) -> str:
    explicit = operations.get("competing_output_rejection_reason") or operations.get("competing_outputs_rejected_reason")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if not forced_uniqueness_trace_present:
        return ""
    anchor = operations.get("operation_name") or operations.get("grammar_id") or mode
    if rival_grammars:
        return f"Train-grounded trace rejects rival outputs inconsistent with {anchor}."
    return f"Train-grounded constraints reject competing outputs inconsistent with {anchor}."


def _derive_uniquely_forced_reason(mode: str, operations: dict, forced_uniqueness_trace_present: bool) -> str:
    explicit = operations.get("uniquely_forced_reason")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if not forced_uniqueness_trace_present:
        return ""
    anchor = operations.get("operation_name") or operations.get("grammar_id") or mode
    return f"Available train-grounded constraints uniquely force the candidate through {anchor}."


def _derive_object_correspondence_claims(operations: dict) -> list[Any]:
    explicit = operations.get("correspondence_claims")
    if isinstance(explicit, list):
        return explicit
    if operations.get("correspondence_id"):
        return [operations["correspondence_id"]]
    return []


def _build_construction_trace(trace_count: int, source_constraint: str, operations: dict, candidate: dict) -> list[dict]:
    return [{
        "step_id": trace_count,
        "source_helper": operations.get("source_helper", "local_generator"),
        "source_constraint": source_constraint,
        "operation": operations.get("operation_name", "transform"),
        "train_support": _mode_has_train_support("", operations),
        "assumption_status": "blocked" if candidate["unsupported_assumptions"] else "forced",
        "rival_impact": "unresolved" if candidate["unresolved_rivals"] else "none",
        "ledger_relevance": "required",
        "evidence_status": "train_explicit" if candidate["train_evidence_grounded"] else "insufficient",
        "source_train_ids": list(candidate["source_train_ids"]),
        "synthetic_local_train_ids": list(candidate["synthetic_local_train_ids"]),
        "train_grounded_transformation_rule": candidate["train_grounded_transformation_rule"],
        "train_grounded_forced_constraints": list(candidate["train_grounded_forced_constraints"]),
        "forced_constraints_tied_to_train_evidence": list(candidate["forced_constraints_tied_to_train_evidence"]),
        "ambiguity_check": candidate["ambiguity_check"],
        "competing_output_rejection_reason": candidate["competing_output_rejection_reason"],
        "uniquely_forced_reason": candidate["uniquely_forced_reason"],
    }]


def _missing_required_trace_fields(candidate: dict) -> list[str]:
    mode = candidate.get("construction_mode", "partial_candidate_descriptor")
    required = list(_TRACE_REQUIRED_FIELDS_BY_MODE.get(mode, []))
    missing = []

    for field in required:
        if field == "construction_trace" and not candidate.get("construction_trace"):
            missing.append(field)
        elif field == "construction_trace_source_grounded" and candidate.get(field) is not True:
            missing.append(field)
        elif field == "train_evidence_grounded" and candidate.get(field) is not True:
            missing.append(field)
        elif field == "forced_uniqueness_trace_present" and candidate.get(field) is not True:
            missing.append(field)
        elif field == "source_train_ids" and not (candidate.get("source_train_ids") or candidate.get("synthetic_local_train_ids")):
            missing.append(field)
        elif field == "train_grounded_transformation_rule" and not candidate.get(field):
            missing.append(field)
        elif field == "train_grounded_forced_constraints" and not candidate.get(field):
            missing.append(field)
        elif field == "ambiguity_check" and candidate.get(field) not in {"clear", "resolved", False}:
            missing.append(field)
        elif field == "competing_output_rejection_reason" and not candidate.get(field):
            missing.append(field)
        elif field == "uniquely_forced_reason" and not candidate.get(field):
            missing.append(field)

    if mode == "explicit_grammar_candidate" and candidate.get("rival_grammars"):
        if not candidate.get("surviving_grammar"):
            missing.append("surviving_grammar")
        if not candidate.get("rival_elimination_trace"):
            missing.append("rival_elimination_trace")
        if not candidate.get("surviving_grammar_train_evidence"):
            missing.append("surviving_grammar_train_evidence")
        if candidate.get("surviving_grammar_uniquely_forces_output") is not True:
            missing.append("surviving_grammar_uniquely_forces_output")

    return missing


def _derive_unresolved_rivals(generator_input: dict, operations: dict) -> list[str]:
    operation_rivals = _listify(operations.get("unresolved_rivals"))
    input_rivals = _listify(generator_input.get("unresolved_rival_grammars"))
    return list(dict.fromkeys(operation_rivals + input_rivals))


def _mode_has_train_support(mode: str, operations: dict) -> bool:
    return bool(
        operations.get("train_supported")
        or operations.get("all_components_train_supported")
        or operations.get("rules_from_train")
        or mode == "relation_first_rewrite_candidate"
    )


def _listify(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def summarize_controlled_answer_candidate_generation_v1(result: dict) -> dict:
    metrics = result.get("metrics", {})
    summary = f"""Controlled Answer Candidate Generator Summary
=================================================
Task: {result.get('task_id')}
Generation status: {result.get('generation_status')}
Blocking reason: {result.get('blocking_reason', 'none')}

Candidates generated: {metrics.get('candidate_generated_count', 0)}
Candidates blocked: {metrics.get('candidate_generation_blocked_count', 0)}

Ledger relationship:
- Requires ledger review: {result.get('requires_ledger_review')}
- Generator grants deservedness: {result.get('generator_grants_deservedness')}
- Generator outputs final answer: {result.get('generator_outputs_final_answer')}
"""
    return {"summary": summary, "result": result}


GENERATOR_GRANTS_DESERVEDNESS = False
GENERATOR_OUTPUTS_FINAL_ANSWER = False
REQUIRES_LEDGER_REVIEW = True
CANDIDATE_TREATED_AS_FINAL_ANSWER = False
