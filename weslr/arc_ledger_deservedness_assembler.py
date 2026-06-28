"""
ARC Ledger Deservedness Assembler

The assembler receives candidate descriptors from the controlled answer candidate generator
plus helper diagnostics, then decides whether a candidate deserves ledger approval.

Core law:
A candidate can become deserved only if train evidence plus diagnostics force a unique output
or a bounded top candidate under the local synthetic policy.

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
    evidence_scope: str = "train_only",
    hidden_test_output_available: bool = False,
    public_arc_answer_available: bool = False,
) -> dict:
    """
    Build input for the ledger deservedness assembler.
    
    Args:
        task_id: Unique task identifier
        candidate_descriptors: Candidates from controlled generator
        helper_diagnostics: Diagnostics from helpers
        candidate_grammars: Grammar candidates
        forced_constraints: Train-forced constraints
        train_evidence_support: Train evidence alignment
        unresolved_rival_grammars: Unresolved rival grammars
        ambiguity_flags: Ambiguity detected
        invariant_symmetry_findings: Invariant/symmetry findings
        object_correspondence_findings: Object mapping findings
        mdl_diagnostics: MDL signals
        divergence_findings: Counterexample results
        constraint_findings: Constraint satisfaction
        rehearsal_context: Rehearsal context (for policy check)
        evidence_scope: Must be "train_only"
        hidden_test_output_available: Must be False
        public_arc_answer_available: Must be False
    
    Returns:
        Input dictionary for assembler evaluation
    """
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
        "evidence_scope": evidence_scope,
        "hidden_test_output_available": hidden_test_output_available,
        "public_arc_answer_available": public_arc_answer_available,
    }


def evaluate_ledger_deservedness_v1(assembler_input: dict) -> dict:
    """
    Evaluate whether candidates deserve ledger approval.
    
    Args:
        assembler_input: Input from build_ledger_deservedness_assembler_input_v1
    
    Returns:
        Deservedness evaluation result
    """
    # Initialize metrics
    metrics = {
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
    }
    
    # Check fail-closed conditions first
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
    
    # Get candidates
    candidates = assembler_input.get("candidate_descriptors", [])
    
    # No candidates case
    if not candidates:
        metrics["needs_candidate_generation_count"] += 1
        return _build_result(
            assembler_input,
            decision="needs_candidate_generation",
            metrics=metrics,
            traces=[_build_trace("no_candidates", "system", "candidate_descriptors", False, "required", "none")],
        )
    
    # Evaluate each candidate
    evaluation_results = []
    unique_forced_output = False
    resolved_rivals = True
    
    for candidate in candidates:
        result = _evaluate_candidate(candidate, assembler_input, metrics)
        evaluation_results.append(result)
        
        if result.get("decision") == "candidate_deserved":
            metrics["candidate_deserved_count"] += 1
            if result.get("forced_unique_output_available"):
                unique_forced_output = True
        else:
            metrics["candidate_not_deserved_count"] += 1
        
        if result.get("unresolved_rivals_present"):
            resolved_rivals = False
    
    # Determine overall decision
    if metrics["candidate_deserved_count"] > 0 and unique_forced_output:
        overall_decision = "candidate_deserved"
        metrics["forced_unique_output_count"] += 1
    elif metrics["candidate_deserved_count"] > 0:
        overall_decision = "candidate_deserved"
    elif not resolved_rivals:
        overall_decision = "rival_grammar_unresolved"
        metrics["rival_unresolved_count"] += 1
    else:
        overall_decision = "candidate_not_deserved"
    
    # Check rehearsal context
    rehearsal_context = assembler_input.get("rehearsal_context", {})
    rehearsal_count = rehearsal_context.get("repeat_count", 0)
    memorization_risk = rehearsal_context.get("memorization_risk", "none")
    fresh_holdout_confirmed = rehearsal_context.get("fresh_holdout_confirmed", False)
    
    # Build result
    result = {
        "task_id": assembler_input.get("task_id"),
        "decision": overall_decision,
        "candidate_results": evaluation_results,
        "metrics": metrics,
        # Ledger boundary
        "final_answer_emitted": False,
        "public_claim_allowed": False,
        "official_arc_claim_allowed": False,
        "runtime_wiring_changed": False,
        "helper_output_as_evidence": False,
        "rehearsal_repeat_as_evidence": False,
        "ledger_decision_only": True,
        # Rehearsal relationship
        "rehearsal_repeat_count": rehearsal_count,
        "memorization_risk_flag": memorization_risk,
        "fresh_holdout_confirmed": fresh_holdout_confirmed,
        "rehearsal_does_not_create_deservedness": True,
        "fresh_holdout_may_count": True,
        # Anti-laundering
        "antilaundering_laws": ANTILAUNDERING_LAWS,
    }
    
    return result


def _evaluate_candidate(candidate: dict, assembler_input: dict, metrics: dict) -> dict:
    """Evaluate a single candidate."""
    traces = []
    decision = "candidate_not_deserved"
    forced_unique = False
    unresolved_rivals_present = False
    
    # Check: candidate requires ledger review
    if not candidate.get("requires_ledger_review", False):
        metrics["helper_output_as_evidence_blocked_count"] += 1
        traces.append(_build_trace(
            "ledger_review_check", "system", "requires_ledger_review", False, "required", "violated"
        ))
        return {
            "candidate_id": candidate.get("candidate_id"),
            "decision": "candidate_not_deserved",
            "reason": "bypassed_ledger_review",
            "deservedness_traces": traces,
            "unresolved_rivals_present": False,
            "forced_unique_output_available": False,
        }
    
    # Check: candidate not treated as final answer
    if candidate.get("treated_as_final_answer", False):
        traces.append(_build_trace(
            "final_answer_check", "system", "treated_as_final_answer", False, "required", "violated"
        ))
        return {
            "candidate_id": candidate.get("candidate_id"),
            "decision": "candidate_not_deserved",
            "reason": "treated_as_final_answer",
            "deservedness_traces": traces,
            "unresolved_rivals_present": False,
            "forced_unique_output_available": False,
        }
    
    # Check: partial candidate cannot be complete
    if candidate.get("generation_status") == "partial":
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace(
            "partial_check", "system", "generation_status", False, "required", "partial"
        ))
        return {
            "candidate_id": candidate.get("candidate_id"),
            "decision": "candidate_not_deserved",
            "reason": "partial_candidate",
            "deservedness_traces": traces,
            "unresolved_rivals_present": False,
            "forced_unique_output_available": False,
        }
    
    # Check: unsupported assumptions
    unsupported = candidate.get("unsupported_assumptions", [])
    if unsupported:
        metrics["unsupported_assumption_rejected_count"] += 1
        traces.append(_build_trace(
            "unsupported_check", "system", "unsupported_assumptions", False, "required", "present"
        ))
        return {
            "candidate_id": candidate.get("candidate_id"),
            "decision": "candidate_not_deserved",
            "reason": "unsupported_assumptions",
            "deservedness_traces": traces,
            "unresolved_rivals_present": False,
            "forced_unique_output_available": False,
        }
    
    # Check: unresolved rivals
    unresolved = candidate.get("unresolved_rivals", [])
    if unresolved:
        unresolved_rivals_present = True
        metrics["rival_unresolved_count"] += 1
        traces.append(_build_trace(
            "rival_check", "system", "unresolved_rivals", False, "required", "present"
        ))
        return {
            "candidate_id": candidate.get("candidate_id"),
            "decision": "candidate_not_deserved",
            "reason": "unresolved_rivals",
            "deservedness_traces": traces,
            "unresolved_rivals_present": True,
            "forced_unique_output_available": False,
        }
    
    # Check: MDL-only selection
    grammars = assembler_input.get("candidate_grammars", [])
    # Check if any grammar for this candidate is MDL-only without train evidence
    mdl_only_grammars = [g for g in grammars if g.get("mdl_only") and not g.get("rules_from_train")]
    if mdl_only_grammars:
        metrics["mdl_only_rejected_count"] += 1
        traces.append(_build_trace(
            "mdl_check", "system", "mdl_only", False, "required", "present"
        ))
        return {
            "candidate_id": candidate.get("candidate_id"),
            "decision": "candidate_not_deserved",
            "reason": "mdl_only_selection",
            "deservedness_traces": traces,
            "unresolved_rivals_present": False,
            "forced_unique_output_available": False,
        }
    
    # Check: output-affecting ambiguity requires safe failure
    ambiguity_flags = assembler_input.get("ambiguity_flags", {})
    output_affecting = ambiguity_flags.get("affects_output", False)
    if output_affecting:
        metrics["safe_failure_required_count"] += 1
        traces.append(_build_trace(
            "ambiguity_check", "system", "ambiguity_flags", False, "required", "output_affecting"
        ))
        return {
            "candidate_id": candidate.get("candidate_id"),
            "decision": "safe_failure_required",
            "reason": "output_affecting_ambiguity",
            "deservedness_traces": traces,
            "unresolved_rivals_present": False,
            "forced_unique_output_available": False,
        }
    
    # Check: rehearsal-only support
    rehearsal_context = assembler_input.get("rehearsal_context", {})
    rehearsal_repeat_count = rehearsal_context.get("repeat_count", 0)
    if rehearsal_repeat_count > 0 and not rehearsal_context.get("fresh_holdout_confirmed"):
        # Only rehearsal, no fresh confirmation
        metrics["rehearsal_only_rejected_count"] += 1
        traces.append(_build_trace(
            "rehearsal_check", "system", "rehearsal_only", False, "required", "present"
        ))
        return {
            "candidate_id": candidate.get("candidate_id"),
            "decision": "candidate_not_deserved",
            "reason": "rehearsal_only_support",
            "deservedness_traces": traces,
            "unresolved_rivals_present": False,
            "forced_unique_output_available": False,
        }
    
    # Check: forced constraints provide unique output
    forced_constraints = assembler_input.get("forced_constraints", [])
    train_evidence = assembler_input.get("train_evidence_support", {})
    
    if forced_constraints and train_evidence:
        # Train evidence + forced constraints = deserves
        forced_unique = True
        metrics["forced_unique_output_count"] += 1
        traces.append(_build_trace(
            "forced_check", "train", "forced_constraints", True, "required", "explicit"
        ))
        traces.append(_build_trace(
            "evidence_check", "train", "train_evidence_support", True, "required", "explicit"
        ))
        decision = "candidate_deserved"
    elif forced_constraints:
        # Has forced constraints but no train evidence
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace(
            "evidence_check", "train", "train_evidence_support", False, "required", "missing"
        ))
        decision = "insufficient_train_evidence"
    else:
        # No forced constraints
        metrics["insufficient_train_evidence_count"] += 1
        traces.append(_build_trace(
            "constraint_check", "system", "forced_constraints", False, "required", "missing"
        ))
        decision = "insufficient_train_evidence"
    
    return {
        "candidate_id": candidate.get("candidate_id"),
        "decision": decision,
        "deservedness_traces": traces,
        "unresolved_rivals_present": unresolved_rivals_present,
        "forced_unique_output_available": forced_unique,
    }


def _build_trace(step_id: str, source: str, constraint: str, train_support: bool, 
                 decision_relevance: str, evidence_status: str) -> dict:
    """Build a trace step."""
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


def _build_result(assembler_input: dict, decision: str, metrics: dict, traces: list) -> dict:
    """Build a result dictionary."""
    return {
        "task_id": assembler_input.get("task_id"),
        "decision": decision,
        "candidate_results": [],
        "metrics": metrics,
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
    """Build a fail-closed result."""
    return _build_result(
        assembler_input,
        decision="safe_failure_required",
        metrics=metrics,
        traces=[_build_trace("fail_closed", "system", reason, False, "required", "violated")],
    )


def summarize_ledger_deservedness_v1(result: dict) -> dict:
    """
    Summarize the ledger deservedness evaluation result.
    
    Args:
        result: Result from evaluate_ledger_deservedness_v1
    
    Returns:
        Human-readable summary
    """
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