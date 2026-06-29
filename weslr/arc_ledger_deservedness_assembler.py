"""
ARC Ledger Deservedness Assembler

The assembler receives candidate descriptors from the controlled answer candidate generator
plus helper diagnostics, then decides whether a candidate deserves ledger approval.

Core law:
A candidate can become deserved only from its own candidate-level, trace-grounded train evidence.
Task-level context may inform review, but it may not independently create deservedness.

Repeated rehearsal cannot create deservedness.
Helper output cannot become evidence.
MDL/elegance alone cannot create deservedness.
The assembler decides deservedness, but does not emit public/final answers.
"""

from typing import Any


# Anti-laundering laws (exposed)
ANTILAUNDERING_LAWS = [
    "train_evidence_is_the_only_source_of_deservedness",
    "helper_output_is_diagnostic_not_evidence",
    "candidate_generation_is_not_deservedness",
    "every_candidate_requires_ledger_review",
    "unresolved_rivals_block_deservedness",
    "output_affecting_ambiguity_requires_safe_failure",
    "mdl_elegance_alone_cannot_deserve",
    "repeated_rehearsal_cannot_deserve",
    "hidden_test_output_cannot_be_used",
    "public_arc_answers_cannot_be_used",
    "partial_candidates_cannot_be_complete_answers",
    "assembler_does_not_emit_public_final_answers",
]

# Allowed decisions
ALLOWED_DECISIONS = [
    "candidate_deserved",
    "candidate_not_deserved",
    "safe_failure_required",
    "needs_candidate_generation",
    "rival_grammar_unresolved",
    "forced_unique_output_available",
    "insufficient_train_evidence",
]

# Forbidden decisions/statuses
FORBIDDEN_STATUSES = [
    "final_answer_emitted",
    "public_answer_generated",
    "official_arc_claim",
    "deserved_by_rehearsal",
    "deserved_by_mdl_only",
    "deserved_by_helper_preference",
    "deserved_with_unresolved_rivals",
    "deserved_with_hidden_test_output",
    "deserved_with_public_arc_answer",
]

_FORBIDDEN_SCORING_KEYS = {
    "synthetic_expected_answer_for_scoring_only",
    "expected_output",
    "expected_answer",
    "post_ledger_scoring_result",
    "deserved_exact_result",
    "deserved_but_wrong_result",
    "scoring_result",
}

_SAFE_FAILURE_REASON_TO_METRIC = {
    "insufficient_train_evidence": "safe_failure_from_insufficient_evidence_count",
    "incomplete_construction_trace": "safe_failure_from_incomplete_trace_count",
    "unresolved_rivals": "safe_failure_from_unresolved_rival_count",
}


def build_ledger_deservedness_assembler_input_v1(
    task_id: str,
    candidate_descriptors: list,
    helper_diagnostics: dict | None = None,
    candidate_grammars: list | None = None,
    forced_constraints: list | None = None,
    train_evidence_support: dict | None = None,
    unresolved_rival_grammars: list | None = None,
    ambiguity_flags: dict | None = None,
    invariant_symmetry_findings: list | None = None,
    object_correspondence_findings: list | None = None,
    mdl_diagnostics: dict | None = None,
    divergence_findings: list | None = None,
    constraint_findings: list | None = None,
    rehearsal_context: dict | None = None,
    group_id: str | None = None,
    expected_frontier_failure: str | None = None,
    rival_context_hint: bool = False,
    evidence_scope: str = "train_only",
    hidden_test_output_available: bool = False,
    public_arc_answer_available: bool = False,
) -> dict:
    """Build input for the ledger deservedness assembler."""
    return {
        "task_id": task_id,
        "candidate_descriptors": candidate_descriptors or [],
        "helper_diagnostics": helper_diagnostics or {},
        "candidate_grammars": candidate_grammars or [],
        "forced_constraints": forced_constraints or [],
        "train_evidence_support": train_evidence_support or {},
        "unresolved_rival_grammars": unresolved_rival_grammars or [],
        "ambiguity_flags": ambiguity_flags or {},
        "invariant_symmetry_findings": invariant_symmetry_findings or [],
        "object_correspondence_findings": object_correspondence_findings or [],
        "mdl_diagnostics": mdl_diagnostics or {},
        "divergence_findings": divergence_findings or [],
        "constraint_findings": constraint_findings or [],
        "rehearsal_context": rehearsal_context or {},
        "group_id": group_id,
        "expected_frontier_failure": expected_frontier_failure,
        "rival_context_hint": rival_context_hint,
        "evidence_scope": evidence_scope,
        "hidden_test_output_available": hidden_test_output_available,
        "public_arc_answer_available": public_arc_answer_available,
    }


def evaluate_ledger_deservedness_v1(assembler_input: dict) -> dict:
    """Evaluate whether candidates deserve ledger approval."""
    metrics = _build_metrics()

    evidence_scope = assembler_input.get("evidence_scope", "train_only")
    hidden_test_available = assembler_input.get("hidden_test_output_available", False)
    public_arc_available = assembler_input.get("public_arc_answer_available", False)

    if evidence_scope != "train_only":
        return _build_fail_closed_result(assembler_input, "evidence_scope_not_train_only", metrics)

    if hidden_test_available:
        metrics["hidden_test_blocked_count"] += 1
        return _build_fail_closed_result(assembler_input, "hidden_test_output_available", metrics)

    if public_arc_available:
        metrics["public_arc_answer_blocked_count"] += 1
        return _build_fail_closed_result(assembler_input, "public_arc_answer_available", metrics)

    if _contains_forbidden_scoring_content(assembler_input):
        return _build_fail_closed_result(assembler_input, "scoring_answer_leakage_detected", metrics)

    candidates = assembler_input.get("candidate_descriptors", [])
    if not candidates:
        metrics["needs_candidate_generation_count"] += 1
        return _build_result(
            assembler_input,
            decision="needs_candidate_generation",
            metrics=metrics,
            traces=[_build_trace("no_candidates", "system", "candidate_descriptors", False, "required", "none")],
            candidate_results=[],
        )

    evaluation_results = []
    safe_failure_reasons: list[str] = []
    any_deserved = False
    forced_unique_output_available = False

    for candidate in candidates:
        metrics["candidate_review_count"] += 1
        result = _evaluate_candidate(candidate, assembler_input, metrics)
        evaluation_results.append(result)

        if candidate.get("requires_ledger_review") is True:
            metrics["ledger_review_required_count"] += 1
        if candidate.get("construction_trace_complete") is True:
            metrics["construction_trace_complete_count"] += 1
        if candidate.get("forced_uniqueness_trace_present") is True:
            metrics["forced_uniqueness_trace_present_count"] += 1
        if candidate.get("rival_elimination_trace_present") is True:
            metrics["rival_elimination_trace_present_count"] += 1
        if candidate.get("train_evidence_grounded") is True:
            metrics["train_evidence_grounded_count"] += 1

        if result["decision"] == "candidate_deserved":
            any_deserved = True
            forced_unique_output_available = (
                forced_unique_output_available or result.get("forced_unique_output_available", False)
            )
            metrics["candidate_deserved_count"] += 1
        else:
            metrics["candidate_not_deserved_count"] += 1
            if result.get("safe_failure_reason"):
                safe_failure_reasons.append(result["safe_failure_reason"])

        if result.get("unresolved_rivals_present"):
            metrics["rival_unresolved_count"] += 1

    if any_deserved:
        decision = "candidate_deserved"
        if forced_unique_output_available:
            metrics["forced_unique_output_count"] += 1
    else:
        decision = "safe_failure_required"
        metrics["safe_failure_required_count"] += 1
        for reason in set(safe_failure_reasons):
            metric_name = _SAFE_FAILURE_REASON_TO_METRIC.get(reason)
            if metric_name:
                metrics[metric_name] += 1

    rehearsal_context = assembler_input.get("rehearsal_context", {})
    rehearsal_count = rehearsal_context.get("repeat_count", 0)
    memorization_risk = rehearsal_context.get("memorization_risk", "none")
    fresh_holdout_confirmed = rehearsal_context.get("fresh_holdout_confirmed", False)

    return {
        "task_id": assembler_input.get("task_id"),
        "decision": decision,
        "candidate_results": evaluation_results,
        "metrics": metrics,
        "final_answer_emitted": False,
        "public_claim_allowed": False,
        "official_arc_claim_allowed": False,
        "runtime_wiring_changed": False,
        "helper_output_as_evidence": False,
        "rehearsal_repeat_as_evidence": False,
        "ledger_decision_only": True,
        "rehearsal_repeat_count": rehearsal_count,
        "memorization_risk_flag": memorization_risk,
        "fresh_holdout_confirmed": fresh_holdout_confirmed,
        "rehearsal_does_not_create_deservedness": True,
        "fresh_holdout_may_count": True,
        "antilaundering_laws": ANTILAUNDERING_LAWS,
    }


def _build_metrics() -> dict:
    return {
        "candidate_review_count": 0,
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
        "hidden_test_blocked_count": 0,
        "public_arc_answer_blocked_count": 0,
        "helper_output_as_evidence_blocked_count": 0,
        "final_answer_emitted_count": 0,
        "public_claim_allowed_count": 0,
        "ledger_review_required_count": 0,
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


def _evaluate_candidate(candidate: dict, assembler_input: dict, metrics: dict) -> dict:
    traces: list[dict[str, Any]] = []

    if _contains_forbidden_scoring_content(candidate):
        traces.append(_build_trace("scoring_boundary_check", "system", "scoring_only_fields", False, "required", "violated"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if "requires_ledger_review" not in candidate or candidate.get("requires_ledger_review") is not True:
        traces.append(_build_trace("ledger_review_check", "system", "requires_ledger_review", False, "required", "violated"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if candidate.get("treated_as_final_answer") or candidate.get("candidate_treated_as_final_answer"):
        traces.append(_build_trace("final_answer_check", "system", "treated_as_final_answer", False, "required", "violated"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if candidate.get("helper_output_as_evidence"):
        metrics["helper_output_as_evidence_blocked_count"] += 1
        traces.append(_build_trace("helper_output_check", "helper", "helper_output_as_evidence", False, "required", "violated"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if candidate.get("rehearsal_repeat_as_evidence"):
        metrics["rehearsal_only_rejected_count"] += 1
        traces.append(_build_trace("rehearsal_check", "system", "rehearsal_repeat_as_evidence", False, "required", "violated"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if candidate.get("mdl_only_support") or candidate.get("elegance_only_support"):
        metrics["mdl_only_rejected_count"] += 1
        traces.append(_build_trace("mdl_check", "system", "mdl_only_support", False, "required", "violated"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if candidate.get("hidden_test_output_used") or candidate.get("public_arc_answer_used") or candidate.get("scoring_answer_used"):
        traces.append(_build_trace("external_answer_check", "system", "forbidden_answer_source", False, "required", "violated"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if candidate.get("generation_status") == "partial":
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("partial_candidate_check", "system", "generation_status", False, "required", "partial"))
        return _candidate_rejection(candidate, traces, "incomplete_construction_trace")

    unsupported = candidate.get("unsupported_assumptions", [])
    if unsupported:
        metrics["unsupported_assumption_rejected_count"] += 1
        traces.append(_build_trace("unsupported_assumption_check", "system", "unsupported_assumptions", False, "required", "present"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    rival_case = _is_rival_case(candidate, assembler_input)
    if rival_case:
        metrics["rival_context_detected_count"] += 1

    unresolved = candidate.get("unresolved_rivals", [])
    if unresolved:
        if rival_case:
            metrics["rival_context_missing_proof_count"] += 1
            metrics["rival_context_safe_failure_count"] += 1
            if candidate.get("construction_mode") == "train_forced_transformation_candidate":
                metrics["train_forced_rival_bypass_blocked_count"] += 1
        traces.append(_build_trace("unresolved_rival_check", "system", "unresolved_rivals", False, "required", "present"))
        return _candidate_rejection(candidate, traces, "unresolved_rivals", unresolved_rivals_present=True)

    ambiguity_flags = assembler_input.get("ambiguity_flags", {})
    output_affecting = bool(
        candidate.get("output_affecting_ambiguity")
        or candidate.get("ambiguity_check") == "output_affecting"
        or ambiguity_flags.get("affects_output", False)
    )
    if output_affecting:
        traces.append(_build_trace("ambiguity_check", "system", "output_affecting_ambiguity", False, "required", "present"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    trace = candidate.get("construction_trace") or []
    if not trace or candidate.get("construction_trace_complete") is not True:
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("construction_trace_check", "system", "construction_trace_complete", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "incomplete_construction_trace")

    if candidate.get("construction_trace_source_grounded") is not True:
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("source_grounding_check", "train", "construction_trace_source_grounded", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if candidate.get("train_evidence_grounded") is not True:
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("train_evidence_check", "train", "train_evidence_grounded", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if candidate.get("forced_uniqueness_trace_present") is not True:
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("forced_uniqueness_check", "train", "forced_uniqueness_trace_present", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if not _has_source_train_ids(candidate, trace):
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("train_source_id_check", "train", "source_train_example_ids", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if not _has_train_grounded_rule(candidate, trace):
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("train_rule_check", "train", "train_grounded_transformation_rule", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if not _has_train_grounded_forced_constraints(candidate, trace):
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("forced_constraints_check", "train", "forced_constraints_tied_to_train_evidence", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if not _has_ambiguity_check(candidate):
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("ambiguity_trace_check", "train", "ambiguity_check", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    competing_output_rejection_reason = candidate.get("competing_outputs_rejected_reason") or candidate.get("competing_output_rejection_reason")
    if not _has_nonempty_text(competing_output_rejection_reason):
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("competing_outputs_check", "train", "competing_outputs_rejected_reason", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if not _has_nonempty_text(candidate.get("uniquely_forced_reason")):
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace("uniquely_forced_check", "train", "uniquely_forced_reason", False, "required", "missing"))
        return _candidate_rejection(candidate, traces, "insufficient_train_evidence")

    if rival_case:
        rival_grammars = candidate.get("rival_grammars") or []
        surviving_grammar = candidate.get("surviving_grammar")
        rival_outputs_considered = candidate.get("rival_outputs_considered") or []
        rejected_rival_reasons = candidate.get("rejected_rival_reasons") or []
        if not _candidate_has_rival_proof(candidate):
            metrics["insufficient_train_evidence_count"] += 1
            metrics["rival_context_missing_proof_count"] += 1
            metrics["rival_context_safe_failure_count"] += 1
            if candidate.get("construction_mode") == "train_forced_transformation_candidate":
                metrics["train_forced_rival_bypass_blocked_count"] += 1
            missing_constraint = "rival_elimination_trace_present"
            if not rival_grammars:
                missing_constraint = "rival_grammars"
            elif not surviving_grammar:
                missing_constraint = "surviving_grammar"
            elif not rival_outputs_considered:
                missing_constraint = "rival_outputs_considered"
            elif not rejected_rival_reasons:
                missing_constraint = "rejected_rival_reasons"
            elif not _has_nonempty_text(candidate.get("surviving_grammar_train_evidence")):
                missing_constraint = "surviving_grammar_train_evidence"
            elif candidate.get("surviving_grammar_uniquely_forces_output") is not True:
                missing_constraint = "surviving_grammar_uniquely_forces_output"
            traces.append(_build_trace("rival_elimination_check", "train", missing_constraint, False, "required", "missing"))
            return _candidate_rejection(candidate, traces, "unresolved_rivals", unresolved_rivals_present=True)

    traces.append(_build_trace("candidate_deserved", "train", "candidate_level_trace_grounding", True, "required", "explicit"))
    return {
        "candidate_id": candidate.get("candidate_id"),
        "decision": "candidate_deserved",
        "reason": "candidate_level_forced_unique_train_grounded",
        "deservedness_traces": traces,
        "unresolved_rivals_present": False,
        "forced_unique_output_available": True,
        "safe_failure_reason": None,
    }


def _candidate_rejection(
    candidate: dict,
    traces: list[dict[str, Any]],
    safe_failure_reason: str,
    unresolved_rivals_present: bool = False,
) -> dict:
    reason = "candidate_not_deserved"
    if safe_failure_reason == "incomplete_construction_trace":
        reason = "incomplete_construction_trace"
    elif safe_failure_reason == "unresolved_rivals":
        reason = "unresolved_rivals"
    elif safe_failure_reason == "insufficient_train_evidence":
        reason = "insufficient_train_evidence"

    return {
        "candidate_id": candidate.get("candidate_id"),
        "decision": "candidate_not_deserved",
        "reason": reason,
        "deservedness_traces": traces,
        "unresolved_rivals_present": unresolved_rivals_present,
        "forced_unique_output_available": False,
        "safe_failure_reason": safe_failure_reason,
    }


def _contains_forbidden_scoring_content(value: Any) -> bool:
    if isinstance(value, dict):
        if _FORBIDDEN_SCORING_KEYS.intersection(value.keys()):
            return True
        return any(_contains_forbidden_scoring_content(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_scoring_content(v) for v in value)
    return False


def _has_source_train_ids(candidate: dict, trace: list[dict]) -> bool:
    if candidate.get("source_train_ids") or candidate.get("source_train_example_ids") or candidate.get("synthetic_local_train_ids"):
        return True
    for step in trace:
        if step.get("source_train_ids") or step.get("source_train_example_ids") or step.get("synthetic_local_train_ids"):
            return True
    return False


def _has_train_grounded_rule(candidate: dict, trace: list[dict]) -> bool:
    if _has_nonempty_text(candidate.get("train_grounded_transformation_rule")):
        return True
    for step in trace:
        if _has_nonempty_text(step.get("train_grounded_transformation_rule")):
            return True
    return False


def _has_train_grounded_forced_constraints(candidate: dict, trace: list[dict]) -> bool:
    constraints = candidate.get("forced_constraints_tied_to_train_evidence") or candidate.get("train_grounded_forced_constraints")
    if isinstance(constraints, list) and constraints:
        return True
    for step in trace:
        step_constraints = step.get("forced_constraints_tied_to_train_evidence") or step.get("train_grounded_forced_constraints")
        if isinstance(step_constraints, list) and step_constraints:
            return True
    return False


def _has_ambiguity_check(candidate: dict) -> bool:
    ambiguity_check = candidate.get("ambiguity_check")
    return ambiguity_check in {"clear", "resolved", False}


def _is_rival_case(candidate: dict, assembler_input: dict) -> bool:
    task_id = str(assembler_input.get("task_id") or candidate.get("task_id") or "")
    group_id = str(assembler_input.get("group_id") or "")
    expected_frontier_failure = str(assembler_input.get("expected_frontier_failure") or "")
    return bool(
        candidate.get("rival_grammar_case")
        or candidate.get("rival_context_detected") is True
        or candidate.get("rival_grammars")
        or candidate.get("surviving_grammar")
        or candidate.get("rival_elimination_trace_present") is True
        or candidate.get("unresolved_rivals")
        or assembler_input.get("unresolved_rival_grammars")
        or assembler_input.get("rival_context_hint") is True
        or "rival_grammar" in task_id
        or "rival_grammar" in group_id
        or "rival_grammar" in expected_frontier_failure
    )


def _candidate_has_rival_proof(candidate: dict) -> bool:
    return bool(
        candidate.get("rival_grammars")
        and candidate.get("surviving_grammar")
        and candidate.get("rival_elimination_trace")
        and candidate.get("rival_elimination_trace_present") is True
        and _has_nonempty_text(candidate.get("surviving_grammar_train_evidence"))
        and candidate.get("rival_outputs_considered")
        and candidate.get("rejected_rival_reasons")
        and candidate.get("surviving_grammar_uniquely_forces_output") is True
    )


def _has_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _build_trace(
    step_id: str,
    source: str,
    constraint: str,
    train_support: bool,
    decision_relevance: str,
    evidence_status: str,
) -> dict:
    return {
        "step_id": step_id,
        "source": source,
        "constraint": constraint,
        "train_support": train_support,
        "decision_relevance": decision_relevance,
        "evidence_status": evidence_status,
        "rival_status": "none",
        "ambiguity_status": "none",
        "conclusion": "checked",
    }


def _build_result(assembler_input: dict, decision: str, metrics: dict, traces: list, candidate_results: list) -> dict:
    return {
        "task_id": assembler_input.get("task_id"),
        "decision": decision,
        "candidate_results": candidate_results,
        "metrics": metrics,
        "deservedness_traces": traces,
        "final_answer_emitted": False,
        "public_claim_allowed": False,
        "official_arc_claim_allowed": False,
        "runtime_wiring_changed": False,
        "helper_output_as_evidence": False,
        "rehearsal_repeat_as_evidence": False,
        "ledger_decision_only": True,
        "rehearsal_repeat_count": 0,
        "memorization_risk_flag": "none",
        "fresh_holdout_confirmed": False,
        "rehearsal_does_not_create_deservedness": True,
        "fresh_holdout_may_count": True,
        "antilaundering_laws": ANTILAUNDERING_LAWS,
    }


def _build_fail_closed_result(assembler_input: dict, reason: str, metrics: dict) -> dict:
    return _build_result(
        assembler_input,
        decision="safe_failure_required",
        metrics=metrics,
        traces=[_build_trace("fail_closed", "system", reason, False, "required", "violated")],
        candidate_results=[],
    )


def summarize_ledger_deservedness_v1(result: dict) -> dict:
    """Summarize the ledger deservedness evaluation result."""
    metrics = result.get("metrics", {})

    summary = f"""Ledger Deservedness Assembler Summary
==========================================
Task: {result.get('task_id')}
Decision: {result.get('decision')}

Metrics:
- Candidates reviewed: {metrics.get('candidate_review_count', 0)}
- Candidates deserved: {metrics.get('candidate_deserved_count', 0)}
- Candidates not deserved: {metrics.get('candidate_not_deserved_count', 0)}
- Safe failures required: {metrics.get('safe_failure_required_count', 0)}
- Needs candidate generation: {metrics.get('needs_candidate_generation_count', 0)}
- Rival unresolved: {metrics.get('rival_unresolved_count', 0)}
- Forced unique output: {metrics.get('forced_unique_output_count', 0)}
- Insufficient evidence: {metrics.get('insufficient_train_evidence_count', 0)}

Ledger boundary:
- Final answer emitted: {result.get('final_answer_emitted')}
- Public claim allowed: {result.get('public_claim_allowed')}
- Helper output as evidence: {result.get('helper_output_as_evidence')}

Anti-laundering laws enforced: {len(result.get('antilaundering_laws', []))}
"""

    return {
        "summary": summary,
        "result": result,
    }


# Boundary constants
FINAL_ANSWER_EMITTED = False
PUBLIC_CLAIM_ALLOWED = False
OFFICIAL_ARC_CLAIM_ALLOWED = False
HELPER_OUTPUT_AS_EVIDENCE = False
LEDGER_DECISION_ONLY = True
