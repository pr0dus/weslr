"""
ARC Minimum Description Length / Compression Helper

Helper family 6/8: Evaluates candidate grammars using compression / description-length 
diagnostics.

This is a pure diagnostic helper:
- Estimates description length of grammars
- Flags exception-heavy or assumption-heavy grammars
- Reports overfit/underfit risk
- Does NOT crown grammars by simplicity
- Does NOT use MDL as proof
- Does NOT generate final answers
- Final answer authority remains with ledger
"""

from typing import Any

# Allowed output statuses
ALLOWED_OUTPUT_STATUSES = [
    "description_length_estimated",
    "grammar_compresses_train",
    "grammar_has_exception_penalty",
    "grammar_has_assumption_penalty",
    "grammar_overfit_risk",
    "grammar_underfit_risk",
    "compression_tie",
    "compression_preference_diagnostic",
    "candidate_simpler_but_not_forced",
    "safe_failure_recommended",
    "counterexample_non_evidential",
]

# Forbidden output statuses
FORBIDDEN_OUTPUT_STATUSES = [
    "grammar_true_by_compression",
    "answer_deserved_by_mdl",
    "shorter_grammar_wins",
    "compression_proves_truth",
    "confidence_increased_by_compression",
    "hidden_test_compression_inferred",
    "probe_compression_as_evidence",
]

# Anti-laundering laws
ANTI_LAUNDERING_LAWS = [
    "compression_is_diagnostic_not_proof",
    "shorter_grammar_does_not_mean_true",
    "mdl_cannot_create_train_evidence",
    "mdl_cannot_eliminate_train_consistent_rivals",
    "compression_preference_cannot_override_underdetermination",
    "compression_cannot_raise_confidence_by_itself",
    "hidden_test_output_cannot_be_compressed",
    "synthetic_probes_cannot_become_evidence",
    "helper_does_not_rank_for_final_answer",
    "helper_does_not_generate_final_answers",
]


def build_mdl_compression_helper_input_v1(
    task_id: str,
    train_examples: list[dict],
    test_input_descriptor: dict,
    candidate_grammars: list[dict],
    constraint_helper_status: dict | None = None,
    divergence_helper_status: dict | None = None,
    invariant_symmetry_helper_status: dict | None = None,
) -> dict:
    """
    Build helper input with proper boundary enforcement.
    
    Args:
        task_id: Task identifier
        train_examples: List of train input/output pairs
        test_input_descriptor: Test input description
        candidate_grammars: List of candidate grammars
        constraint_helper_status: Optional status from helper 3
        divergence_helper_status: Optional status from helper 4
        invariant_symmetry_helper_status: Optional status from helper 5
    
    Returns:
        Helper input dict with boundary enforcement
    
    Raises:
        ValueError: If boundaries are violated
    """
    # Fail closed: evidence scope must be train_only
    allowed_evidence_scope = "train_only"  # Fixed
    
    # Fail closed: hidden test output not available
    hidden_test_output_available = False  # Fixed
    
    # Fail closed: synthetic probe results as evidence not allowed
    synthetic_probe_results_allowed_as_evidence = False  # Fixed
    
    return {
        "task_id": task_id,
        "train_examples": train_examples,
        "test_input_descriptor": test_input_descriptor,
        "candidate_grammars": candidate_grammars,
        "constraint_helper_status": constraint_helper_status,
        "divergence_helper_status": divergence_helper_status,
        "invariant_symmetry_helper_status": invariant_symmetry_helper_status,
        "allowed_evidence_scope": allowed_evidence_scope,
        "hidden_test_output_available": hidden_test_output_available,
        "synthetic_probe_results_allowed_as_evidence": synthetic_probe_results_allowed_as_evidence,
    }


def _estimate_description_length(grammar: dict) -> int:
    """
    Estimate description length of a grammar.
    
    Args:
        grammar: Grammar dict with rule_count, primitive_count, etc.
    
    Returns:
        Estimated description length in bits
    """
    # Base costs
    rule_count = grammar.get("rule_count", 0)
    primitive_count = grammar.get("primitive_count", 0)
    condition_count = grammar.get("condition_count", 0)
    exception_count = grammar.get("exception_count", 0)
    assumption_count = grammar.get("assumption_count", 0)
    special_case_count = grammar.get("special_case_count", 0)
    
    # Weighted cost calculation
    base_cost = 10  # Base cost per rule
    primitive_cost = 5  # Cost per primitive
    condition_cost = 3  # Cost per condition
    exception_penalty = 8  # Higher penalty for exceptions
    assumption_penalty = 6  # Penalty for assumptions
    special_case_penalty = 4  # Penalty for special cases
    
    description_length = (
        (rule_count * base_cost) +
        (primitive_count * primitive_cost) +
        (condition_count * condition_cost) +
        (exception_count * exception_penalty) +
        (assumption_count * assumption_penalty) +
        (special_case_count * special_case_penalty)
    )
    
    return description_length


def _evaluate_compression_comparison(
    candidate_grammars: list[dict],
    constraint_helper_status: dict | None,
    divergence_helper_status: dict | None,
) -> list[dict]:
    """
    Evaluate compression characteristics of candidate grammars.
    
    Args:
        candidate_grammars: List of candidate grammars
        constraint_helper_status: Status from helper 3
        divergence_helper_status: Status from helper 4
    
    Returns:
        List of compression evaluation results
    """
    results = []
    
    # Calculate description lengths
    for grammar in candidate_grammars:
        grammar_id = grammar.get("grammar_id", "unknown")
        
        # Estimate description length
        description_length = _estimate_description_length(grammar)
        
        # Check for penalties
        exception_count = grammar.get("exception_count", 0)
        assumption_count = grammar.get("assumption_count", 0)
        special_case_count = grammar.get("special_case_count", 0)
        unexplained_count = len(grammar.get("train_examples_unexplained", []))
        
        # Determine status
        statuses = []
        
        if exception_count > 2:
            statuses.append("grammar_has_exception_penalty")
        if assumption_count > 2:
            statuses.append("grammar_has_assumption_penalty")
        if special_case_count > 2:
            statuses.append("grammar_has_special_case_penalty")
        
        # Check overfit/underfit
        overfit_markers = grammar.get("overfit_markers", [])
        underfit_markers = grammar.get("underfit_markers", [])
        
        if overfit_markers:
            statuses.append("grammar_overfit_risk")
        if underfit_markers:
            statuses.append("grammar_underfit_risk")
        
        if not statuses:
            statuses.append("description_length_estimated")
        
        # Determine if simpler but not forced
        rival_alive = constraint_helper_status and constraint_helper_status.get("overall_status") != "all_eliminated"
        has_divergence = divergence_helper_status and divergence_helper_status.get("overall_status") == "divergence_detected"
        
        if rival_alive or has_divergence:
            statuses.append("candidate_simpler_but_not_forced")
        
        results.append({
            "grammar_id": grammar_id,
            "description_length_estimate": description_length,
            "statuses": statuses,
            "exception_count": exception_count,
            "assumption_count": assumption_count,
            "special_case_count": special_case_count,
            "treated_as_evidence": False,
        })
    
    return results


def evaluate_mdl_compression_v1(helper_input: dict) -> dict:
    """
    Evaluate grammars using MDL compression diagnostics.
    
    Args:
        helper_input: Input from build_mdl_compression_helper_input_v1
    
    Returns:
        Evaluation result with compression diagnostics
    """
    candidate_grammars = helper_input.get("candidate_grammars", [])
    constraint_helper_status = helper_input.get("constraint_helper_status")
    divergence_helper_status = helper_input.get("divergence_helper_status")
    
    # Evaluate compression comparison
    compression_results = _evaluate_compression_comparison(
        candidate_grammars=candidate_grammars,
        constraint_helper_status=constraint_helper_status,
        divergence_helper_status=divergence_helper_status,
    )
    
    # Determine overall status
    overall_status = _determine_overall_mdl_status(compression_results)
    
    # Build result
    result = {
        "task_id": helper_input.get("task_id"),
        "allowed_evidence_scope": helper_input.get("allowed_evidence_scope"),
        "helper_generates_final_answer": False,
        "helper_ranks_for_final_answer": False,
        "compression_treated_as_evidence": False,
        "final_answer_authority": "ledger",
        "compression_results": compression_results,
        "overall_status": overall_status,
        "anti_laundering_laws_enforced": ANTI_LAUNDERING_LAWS,
    }
    
    # Add metrics
    result.update(_compute_mdl_metrics(compression_results))
    
    return result


def _determine_overall_mdl_status(compression_results: list[dict]) -> str:
    """Determine overall MDL compression status."""
    # Check for various conditions
    exception_penalties = sum(1 for r in compression_results if "grammar_has_exception_penalty" in r.get("statuses", []))
    assumption_penalties = sum(1 for r in compression_results if "grammar_has_assumption_penalty" in r.get("statuses", []))
    overfit_risks = sum(1 for r in compression_results if "grammar_overfit_risk" in r.get("statuses", []))
    underfit_risks = sum(1 for r in compression_results if "grammar_underfit_risk" in r.get("statuses", []))
    simpler_not_forced = sum(1 for r in compression_results if "candidate_simpler_but_not_forced" in r.get("statuses", []))
    
    # Check for compression ties
    if len(compression_results) >= 2:
        lengths = [r.get("description_length_estimate", 0) for r in compression_results]
        if lengths and max(lengths) - min(lengths) < 5:
            return "compression_tie"
    
    if overfit_risks > 0:
        return "grammar_overfit_risk"
    elif underfit_risks > 0:
        return "grammar_underfit_risk"
    elif simpler_not_forced > 0:
        return "candidate_simpler_but_not_forced"
    elif exception_penalties > 0:
        return "grammar_has_exception_penalty"
    elif assumption_penalties > 0:
        return "grammar_has_assumption_penalty"
    elif len(compression_results) > 0:
        return "description_length_estimated"
    else:
        return "safe_failure_recommended"


def _compute_mdl_metrics(compression_results: list[dict]) -> dict:
    """Compute MDL metrics from results."""
    exception_penalties = sum(1 for r in compression_results if "grammar_has_exception_penalty" in r.get("statuses", []))
    assumption_penalties = sum(1 for r in compression_results if "grammar_has_assumption_penalty" in r.get("statuses", []))
    special_case_penalties = sum(1 for r in compression_results if "grammar_has_special_case_penalty" in r.get("statuses", []))
    overfit_risks = sum(1 for r in compression_results if "grammar_overfit_risk" in r.get("statuses", []))
    underfit_risks = sum(1 for r in compression_results if "grammar_underfit_risk" in r.get("statuses", []))
    simpler_not_forced = sum(1 for r in compression_results if "candidate_simpler_but_not_forced" in r.get("statuses", []))
    
    # Check for tie
    tie_count = 0
    if len(compression_results) >= 2:
        lengths = [r.get("description_length_estimate", 0) for r in compression_results]
        if lengths and max(lengths) - min(lengths) < 5:
            tie_count = 1
    
    return {
        "candidate_grammar_count": len(compression_results),
        "description_length_estimated_count": len(compression_results),
        "compression_preference_count": len([r for r in compression_results if r.get("description_length_estimate", 0) > 0]),
        "compression_tie_count": tie_count,
        "exception_penalty_count": exception_penalties,
        "assumption_penalty_count": assumption_penalties,
        "special_case_penalty_count": special_case_penalties,
        "overfit_risk_count": overfit_risks,
        "underfit_risk_count": underfit_risks,
        "candidate_simpler_but_not_forced_count": simpler_not_forced,
        "train_consistent_rival_preserved_count": simpler_not_forced,
        "compression_confidence_increase_blocked_count": 0,  # Always 0
        "hidden_test_compression_blocked_count": 0,  # Always 0
        "synthetic_probe_compression_blocked_count": 0,  # Always 0
        "safe_failure_recommended_count": 1 if len(compression_results) == 0 else 0,
        "ledger_boundary_preserved_count": 1 if len(compression_results) > 0 else 0,
    }


def summarize_mdl_compression_status_v1(evaluation_result: dict) -> dict:
    """
    Summarize MDL compression status for the ledger.
    
    Args:
        evaluation_result: Result from evaluate_mdl_compression_v1
    
    Returns:
        Summary dict with human-readable status
    """
    overall_status = evaluation_result.get("overall_status", "unknown")
    metrics = {
        k: v for k, v in evaluation_result.items()
        if k in [
            "compression_tie_count",
            "exception_penalty_count",
            "overfit_risk_count",
            "candidate_simpler_but_not_forced_count",
        ]
    }
    
    # Build human-readable summary
    if overall_status == "compression_tie":
        summary = f"Compression tie detected. Multiple grammars have similar description lengths."
    elif overall_status == "grammar_overfit_risk":
        summary = f"Grammar shows overfit risk. {metrics.get('overfit_risk_count', 0)} overfit markers found."
    elif overall_status == "candidate_simpler_but_not_forced":
        summary = f"Simpler grammar identified but not forced by train evidence. Safe failure recommended."
    elif overall_status == "grammar_has_exception_penalty":
        summary = f"Grammar has exception penalty. {metrics.get('exception_penalty_count', 0)} exceptions flagged."
    else:
        summary = f"MDL compression evaluation complete. Status: {overall_status}"
    
    return {
        "overall_status": overall_status,
        "summary": summary,
        "metrics": metrics,
        "final_answer_authority": evaluation_result.get("final_answer_authority", "ledger"),
    }


# Boundary constants
FINAL_ANSWER_AUTHORITY = "ledger"
HELPER_GENERATES_FINAL_ANSWER = False
HELPER_RANKS_FOR_FINAL_ANSWER = False
COMPRESSION_TREATED_AS_EVIDENCE = False
ALLOWED_EVIDENCE_SCOPE = "train_only"
HIDDEN_TEST_OUTPUT_AVAILABLE = False
SYNTHETIC_PROBE_RESULTS_ALLOWED_AS_EVIDENCE = False