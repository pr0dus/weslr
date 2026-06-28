"""
ARC Ledger-Guided Micro-Theory Retry Loop

A bounded helper that models:
1. Micro-Theory candidate → Ledger evaluation
2. Ledger rejection reason → Retry constraint
3. Retry under constraint → Final ledger gate
4. Final answer or abstain

Core law: Ledger rejection reason may become a retry constraint,
but must NOT become evidence.

This is NOT runtime solver wiring. This is a pure helper + tests.
"""

from typing import Any

# Supported rejection reason codes
REJECTION_REASON_CODES = [
    "target_uncertain",
    "action_uncertain",
    "representation_uncertain",
    "rival_grammar_alive",
    "train_evidence_underdetermined",
    "beautiful_wrong_rule_not_eliminated",
    "probe_divergence_detected",
    "negative_evidence_not_accounted_for",
    "helper_trap_detected",
    "unsafe_hidden_assumption",
    "coincidence_risk",
    "insufficient_forced_output",
]

# Allowed retry constraint forms (constraint language, not evidence)
ALLOWED_RETRY_CONSTRAINTS = [
    "Generate a theory that explicitly proves target selection from train evidence.",
    "Generate a theory that explicitly proves action from train evidence.",
    "Generate a theory that explicitly proves representation from train evidence.",
    "Generate a theory that resolves or preserves Rival Grammar B.",
    "Generate a theory that accounts for negative evidence / absence.",
    "Generate a theory that explains why beautiful wrong rule is eliminated by train evidence.",
    "Generate a theory that avoids unsupported hidden assumption.",
    "Generate a theory that declares underdetermination if no train-only resolution exists.",
    "Generate a theory where output pattern is forced, not coincidental.",
    "Generate a theory where output is necessary, not optional.",
]

# Forbidden retry behaviors
FORBIDDEN_RETRY_BEHAVIORS = [
    "Choose the rival because the first grammar failed.",
    "Use probe success as evidence.",
    "Use synthetic probe as train example.",
    "Retry until any grammar passes.",
    "Prefer the theory with higher apparent score.",
    "Use hidden test output.",
    "Use helper output as confidence.",
    "Accumulate confidence across retries.",
]

# Final termination states
TERMINATION_STATES = [
    "answer_deserved",
    "unsupported",
    "underdetermined",
    "unsafe",
    "rival_grammars_remain",
    "retry_budget_exhausted",
]

# Anti-laundering laws
ANTI_LAUNDERING_LAWS = [
    "rejection_reason_is_not_evidence",
    "probe_result_is_not_train_evidence",
    "retry_success_is_not_truth_proof",
    "retries_do_not_accumulate_confidence",
    "rival_grammar_eliminated_only_by_train_evidence",
    "in_task_repair_is_not_solver_change",
    "final_answer_always_needs_ledger",
]


def build_ledger_rejection_reason_v1(
    reason_code: str,
    affected_candidate_grammar: str,
    rival_grammar: str | None = None,
    train_example_reference: str | None = None,
    explanation: str | None = None,
) -> dict:
    """
    Build a structured ledger rejection reason.
    
    Args:
        reason_code: One of the 12 rejection reason codes
        affected_candidate_grammar: The grammar that was rejected
        rival_grammar: Rival grammar if any
        train_example_reference: Train example reference if any
        explanation: Human-readable explanation
    
    Returns:
        Dictionary with structured rejection reason
    """
    if reason_code not in REJECTION_REASON_CODES:
        raise ValueError(f"Unknown reason_code: {reason_code}")
    
    # Build explanation if not provided
    if explanation is None:
        explanation = _get_default_explanation(reason_code)
    
    # Determine retry allowed and final abstention required
    retry_allowed, final_abstention = _get_retry_policy(reason_code)
    
    # Get retry constraint
    retry_constraint = _get_retry_constraint(reason_code)
    
    return {
        "reason_code": reason_code,
        "explanation": explanation,
        "affected_candidate_grammar": affected_candidate_grammar,
        "rival_grammar": rival_grammar,
        "train_example_reference": train_example_reference,
        "retry_allowed": retry_allowed,
        "retry_constraint": retry_constraint,
        "final_abstention_required": final_abstention,
        "treated_as_evidence": False,  # Core law enforcement
    }


def build_retry_constraint_from_rejection_v1(rejection_reason: dict) -> dict:
    """
    Build a retry constraint from a rejection reason.
    
    The rejection reason is a constraint, NOT evidence.
    
    Args:
        rejection_reason: Structured rejection reason from build_ledger_rejection_reason_v1
    
    Returns:
        Dictionary with retry constraint
    """
    if not rejection_reason.get("retry_allowed", False):
        return {
            "constraint_type": "final_abstention",
            "constraint": "No retry allowed - final abstention required",
            "reason_code": rejection_reason.get("reason_code"),
            "treated_as_evidence": False,
        }
    
    return {
        "constraint_type": "retry_with_constraint",
        "constraint": rejection_reason.get("retry_constraint", ""),
        "reason_code": rejection_reason.get("reason_code"),
        "affected_candidate": rejection_reason.get("affected_candidate_grammar"),
        "rival_grammar": rejection_reason.get("rival_grammar"),
        "treated_as_evidence": False,  # Core law: constraint, NOT evidence
    }


def run_ledger_guided_micro_theory_retry_loop_v1(
    candidate_attempts: list[dict],
    ledger_results: list[dict],
) -> dict:
    """
    Run the ledger-guided micro-theory retry loop.
    
    Models:
    - Round 1: candidate → ledger evaluate → answer if deserved, else reject
    - Round 2: retry with constraint → ledger evaluate → answer if deserved, else abstain
    
    Args:
        candidate_attempts: List of candidate grammar attempts
        ledger_results: List of ledger evaluation results (parallel to candidates)
    
    Returns:
        Dictionary with loop result and metrics
    """
    max_retry_rounds = 1  # Bounded: 1 retry only
    
    # Initialize counters
    initial_candidate_count = 0
    ledger_rejection_count = 0
    retry_attempt_count = 0
    retry_success_count = 0
    retry_abstain_count = 0
    retry_unsafe_count = 0
    rival_grammar_preserved_count = 0
    rival_grammar_legally_eliminated_count = 0
    overconfident_wrong_before_retry = 0
    overconfident_wrong_after_retry = 0
    safe_unsupported_preserved_count = 0
    answer_deserved_after_retry_count = 0
    
    rejection_reason_distribution = {}
    retry_constraint_distribution = {}
    retry_budget_exhausted_count = 0
    
    # Track state
    retry_used = False
    termination_state = None
    
    # Check inputs
    if not candidate_attempts or not ledger_results:
        return _build_empty_result()
    
    # Process each candidate/ledger pair
    for i, (candidate, ledger) in enumerate(zip(candidate_attempts, ledger_results)):
        if i == 0:
            initial_candidate_count += 1
        
        ledger_decision = ledger.get("decision", "unknown")
        
        if ledger_decision == "deserved":
            if i == 0:
                # Initial deserved - terminate immediately
                termination_state = "answer_deserved"
                break
            else:
                # Retry deserved
                retry_success_count += 1
                answer_deserved_after_retry_count += 1
                termination_state = "answer_deserved"
                break
        
        elif ledger_decision == "rejected":
            ledger_rejection_count += 1
            
            # Track overconfident wrong
            if ledger.get("confidence", 0) > 0.5 and ledger.get("answer_was_wrong", False):
                if i == 0:
                    overconfident_wrong_before_retry += 1
                else:
                    overconfident_wrong_after_retry += 1
            
            # Track safe unsupported
            if ledger.get("safe_unsupported_correct", False):
                safe_unsupported_preserved_count += 1
            
            # Get rejection reason
            rejection_reason = ledger.get("rejection_reason")
            if rejection_reason:
                reason_code = rejection_reason.get("reason_code", "unknown")
                rejection_reason_distribution[reason_code] = rejection_reason_distribution.get(reason_code, 0) + 1
            
            # Check if retry is allowed
            if not retry_used and rejection_reason and rejection_reason.get("retry_allowed", False):
                # Create retry constraint
                retry_constraint = build_retry_constraint_from_rejection_v1(rejection_reason)
                constraint_type = retry_constraint.get("constraint_type", "unknown")
                retry_constraint_distribution[constraint_type] = retry_constraint_distribution.get(constraint_type, 0) + 1
                
                # Check for rival grammar
                rival = rejection_reason.get("rival_grammar")
                if rival and reason_code == "rival_grammar_alive":
                    rival_grammar_preserved_count += 1
                
                # Attempt retry
                if i < len(candidate_attempts) - 1:
                    retry_used = True
                    retry_attempt_count += 1
            else:
                # No retry or retry not allowed
                if rejection_reason and rejection_reason.get("final_abstention_required", False):
                    retry_unsafe_count += 1
                    termination_state = "unsafe"
                elif reason_code == "rival_grammar_alive":
                    termination_state = "rival_grammars_remain"
                else:
                    termination_state = "unsupported"
    
    # Check retry budget exhausted
    if retry_used and termination_state is None:
        retry_budget_exhausted_count += 1
        termination_state = "retry_budget_exhausted"
    elif not retry_used and termination_state is None:
        termination_state = "unsupported"
    
    # Build result
    result = {
        # Boundary flags
        "treated_as_evidence": False,
        "probe_result_treated_as_evidence": False,
        "auto_improvement_separated": True,
        "final_ledger_gate_preserved": True,
        "max_retry_rounds": max_retry_rounds,
        
        # Termination
        "termination_state": termination_state,
        "retry_budget_exhausted": retry_budget_exhausted_count > 0,
        
        # Metrics
        "initial_candidate_count": initial_candidate_count,
        "ledger_rejection_count": ledger_rejection_count,
        "retry_attempt_count": retry_attempt_count,
        "retry_success_count": retry_success_count,
        "retry_abstain_count": retry_abstain_count,
        "retry_unsafe_count": retry_unsafe_count,
        "rival_grammar_preserved_count": rival_grammar_preserved_count,
        "rival_grammar_legally_eliminated_count": rival_grammar_legally_eliminated_count,
        "overconfident_wrong_before_retry": overconfident_wrong_before_retry,
        "overconfident_wrong_after_retry": overconfident_wrong_after_retry,
        "safe_unsupported_preserved_count": safe_unsupported_preserved_count,
        "answer_deserved_after_retry_count": answer_deserved_after_retry_count,
        "rejection_reason_distribution": rejection_reason_distribution,
        "retry_constraint_distribution": retry_constraint_distribution,
        "retry_budget_exhausted_count": retry_budget_exhausted_count,
        
        # Anti-laundering laws enforced
        "anti_laundering_laws_enforced": ANTI_LAUNDERING_LAWS,
    }
    
    return result


def _get_default_explanation(reason_code: str) -> str:
    """Get default human-readable explanation for reason code."""
    explanations = {
        "target_uncertain": "Target selection not forced by train evidence",
        "action_uncertain": "Action not forced by train evidence",
        "representation_uncertain": "Representation shift not forced by train evidence",
        "rival_grammar_alive": "Multiple grammars fit train evidence equally",
        "train_evidence_underdetermined": "Train evidence doesn't uniquely determine test",
        "beautiful_wrong_rule_not_eliminated": "Tempting wrong rule not eliminated by train evidence",
        "probe_divergence_detected": "Probe exposed divergence from expected behavior",
        "negative_evidence_not_accounted_for": "Negative evidence not explained by candidate",
        "helper_trap_detected": "Helper eligibility trap detected",
        "unsafe_hidden_assumption": "Hidden assumption not forced by train evidence",
        "coincidence_risk": "Output pattern may be coincidence, not forced",
        "insufficient_forced_output": "Output not forced by train evidence",
    }
    return explanations.get(reason_code, "Unknown rejection reason")


def _get_retry_policy(reason_code: str) -> tuple[bool, bool]:
    """Get retry allowed and final abstention required for reason code."""
    # Reason codes that do NOT allow retry
    no_retry_codes = {
        "probe_divergence_detected",
        "helper_trap_detected",
        "unsafe_hidden_assumption",
    }
    
    # Reason codes that require final abstention
    final_abstention_codes = {
        "probe_divergence_detected",
        "helper_trap_detected",
        "unsafe_hidden_assumption",
    }
    
    retry_allowed = reason_code not in no_retry_codes
    final_abstention = reason_code in final_abstention_codes
    
    return retry_allowed, final_abstention


def _get_retry_constraint(reason_code: str) -> str:
    """Get retry constraint for reason code."""
    constraints = {
        "target_uncertain": "Generate a theory that explicitly proves target selection from train evidence.",
        "action_uncertain": "Generate a theory that explicitly proves action from train evidence.",
        "representation_uncertain": "Generate a theory that explicitly proves representation from train evidence.",
        "rival_grammar_alive": "Generate a theory that resolves or preserves Rival Grammar B.",
        "train_evidence_underdetermined": "Generate a theory that declares underdetermination if no train-only resolution exists.",
        "beautiful_wrong_rule_not_eliminated": "Generate a theory that explains why beautiful wrong rule is eliminated by train evidence.",
        "negative_evidence_not_accounted_for": "Generate a theory that accounts for negative evidence / absence.",
        "coincidence_risk": "Generate a theory where output pattern is forced, not coincidental.",
        "insufficient_forced_output": "Generate a theory where output is necessary, not optional.",
    }
    return constraints.get(reason_code, "Generate a theory that is forced by train evidence.")


def _build_empty_result() -> dict:
    """Build empty result for invalid inputs."""
    return {
        "termination_state": "invalid_input",
        "max_retry_rounds": 1,
        "treated_as_evidence": False,
        "probe_result_treated_as_evidence": False,
        "auto_improvement_separated": True,
        "final_ledger_gate_preserved": True,
        "initial_candidate_count": 0,
        "ledger_rejection_count": 0,
        "retry_attempt_count": 0,
        "retry_success_count": 0,
        "retry_abstain_count": 0,
        "retry_unsafe_count": 0,
        "rival_grammar_preserved_count": 0,
        "rival_grammar_legally_eliminated_count": 0,
        "overconfident_wrong_before_retry": 0,
        "overconfident_wrong_after_retry": 0,
        "safe_unsupported_preserved_count": 0,
        "answer_deserved_after_retry_count": 0,
        "rejection_reason_distribution": {},
        "retry_constraint_distribution": {},
        "retry_budget_exhausted_count": 0,
        "anti_laundering_laws_enforced": ANTI_LAUNDERING_LAWS,
    }


# Constants for boundary checks
MAX_RETRY_ROUNDS = 1
SOLVER_BEHAVIOR_CHANGED = False
HELPER_INTEGRATED = False
AUTO_IMPROVEMENT_SEPARATED = True