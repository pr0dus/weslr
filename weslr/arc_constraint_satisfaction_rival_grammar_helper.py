"""
ARC Constraint Satisfaction / Rival Grammar Helper

Helper family 3/8: Treats candidate grammars as constraints and checks 
which grammars remain legally compatible with train examples.

This is a pure diagnostic helper:
- Evaluates constraint satisfaction against train examples only
- Reports consistent/eliminated/rival_alive/underdetermined
- Does NOT choose final answers
- Does NOT rank grammars
- Does NOT repair grammars
- Does NOT use probes as evidence
- Final answer authority remains with ledger
"""

from typing import Any

# Allowed output statuses
ALLOWED_OUTPUT_STATUSES = [
    "grammar_consistent",
    "grammar_eliminated_by_train_evidence",
    "rival_grammar_alive",
    "all_grammars_eliminated",
    "underdetermined",
    "candidate_deserved_if_unique_and_forced",
    "candidate_not_deserved",
]

# Forbidden output statuses
FORBIDDEN_OUTPUT_STATUSES = [
    "grammar_best",
    "grammar_more_beautiful",
    "grammar_probably_right",
    "grammar_wins_by_probe",
    "grammar_wins_by_helper",
    "grammar_wins_by_score",
    "answer_deserved_without_train_forcing",
]

# Anti-laundering laws
ANTI_LAUNDERING_LAWS = [
    "train_evidence_only_eliminates_grammars",
    "synthetic_probes_cannot_eliminate_grammars",
    "consistency_is_not_proof_of_truth",
    "uniqueness_must_be_forced_by_train_evidence",
    "helper_does_not_rank_grammars",
    "helper_does_not_create_evidence",
    "helper_does_not_repair_grammar",
    "helper_does_not_generate_final_answers",
]


def build_constraint_helper_input_v1(
    task_id: str,
    train_examples: list[dict],
    test_input_descriptor: dict,
    candidate_grammars: list[dict],
    candidate_predictions: list[dict],
    ledger_rejection_context: dict | None = None,
) -> dict:
    """
    Build helper input with proper boundary enforcement.
    
    Args:
        task_id: Task identifier
        train_examples: List of train input/output pairs
        test_input_descriptor: Test input description
        candidate_grammars: List of candidate grammars
        candidate_predictions: List of predictions for each candidate
        ledger_rejection_context: Optional rejection context from ledger
    
    Returns:
        Helper input dict with boundary enforcement
    
    Raises:
        ValueError: If boundaries are violated
    """
    # Fail closed: allowed_evidence_scope must be train_only
    allowed_evidence_scope = "train_only"  # Fixed by design
    
    # Fail closed: hidden test output must not be available
    if ledger_rejection_context and ledger_rejection_context.get("hidden_test_output_available", False):
        raise ValueError("hidden_test_output_available must be False")
    
    # Fail closed: synthetic probes must not be used as evidence
    if ledger_rejection_context and ledger_rejection_context.get("synthetic_probe_results_used", False):
        raise ValueError("synthetic_probe_results_allowed must be False")
    
    return {
        "task_id": task_id,
        "train_examples": train_examples,
        "test_input_descriptor": test_input_descriptor,
        "candidate_grammars": candidate_grammars,
        "candidate_predictions": candidate_predictions,
        "ledger_rejection_context": ledger_rejection_context,
        "allowed_evidence_scope": allowed_evidence_scope,
        "hidden_test_output_available": False,
        "synthetic_probe_results_allowed": False,
    }


def evaluate_candidate_grammar_constraints_v1(helper_input: dict) -> dict:
    """
    Evaluate candidate grammars against train constraints.
    
    Args:
        helper_input: Input from build_constraint_helper_input_v1
    
    Returns:
        Evaluation result with constraint statuses
    """
    train_examples = helper_input.get("train_examples", [])
    candidate_grammars = helper_input.get("candidate_grammars", [])
    candidate_predictions = helper_input.get("candidate_predictions", [])
    
    # Initialize results
    grammar_results = []
    
    # Evaluate each candidate grammar
    for i, grammar in enumerate(candidate_grammars):
        prediction = candidate_predictions[i] if i < len(candidate_predictions) else {}
        
        result = _evaluate_single_grammar(
            grammar=grammar,
            prediction=prediction,
            train_examples=train_examples,
        )
        grammar_results.append(result)
    
    # Determine overall status
    overall_status = _determine_overall_status(grammar_results)
    
    # Build result
    result = {
        "task_id": helper_input.get("task_id"),
        "allowed_evidence_scope": helper_input.get("allowed_evidence_scope"),
        "helper_generates_final_answer": False,
        "helper_ranks_grammars": False,
        "helper_repairs_grammar": False,
        "final_answer_authority": "ledger",
        "grammar_results": grammar_results,
        "overall_status": overall_status,
        "anti_laundering_laws_enforced": ANTI_LAUNDERING_LAWS,
    }
    
    # Add metrics
    result.update(_compute_metrics(grammar_results))
    
    return result


def _evaluate_single_grammar(
    grammar: dict,
    prediction: dict,
    train_examples: list[dict],
) -> dict:
    """Evaluate a single grammar against train examples."""
    grammar_id = grammar.get("grammar_id", "unknown")
    assumptions = grammar.get("assumptions", [])
    
    # Check consistency with train examples
    consistency_failures = []
    for train_ex in train_examples:
        train_in = train_ex.get("input")
        train_out = train_ex.get("output")
        
        pred_out = prediction.get("output")
        
        # Simple check: does prediction match train output?
        if pred_out != train_out:
            consistency_failures.append({
                "train_input": train_in,
                "train_output": train_out,
                "predicted_output": pred_out,
                "failure_type": "train_io_mismatch",
            })
    
    # Check for unsupported assumptions
    unsupported_assumption = any(
        a.get("supported_by_train", True) is False for a in assumptions
    )
    
    # Determine status
    if len(consistency_failures) > 0:
        status = "grammar_eliminated_by_train_evidence"
        elimination_reason = "train_io_mismatch"
    elif unsupported_assumption:
        status = "candidate_not_deserved"
        elimination_reason = "unsupported_assumption"
    else:
        status = "grammar_consistent"
        elimination_reason = None
    
    return {
        "grammar_id": grammar_id,
        "status": status,
        "elimination_reason": elimination_reason,
        "consistency_failures": consistency_failures,
        "contradiction_count": len(consistency_failures),
    }


def _determine_overall_status(grammar_results: list[dict]) -> str:
    """Determine overall status from individual grammar results."""
    consistent = [g for g in grammar_results if g.get("status") == "grammar_consistent"]
    eliminated = [g for g in grammar_results if g.get("status") == "grammar_eliminated_by_train_evidence"]
    not_deserved = [g for g in grammar_results if g.get("status") == "candidate_not_deserved"]
    
    if len(grammar_results) == 0:
        return "all_grammars_eliminated"
    
    if len(consistent) == 0:
        return "all_grammars_eliminated"
    
    # Multiple consistent grammars = rival grammars alive
    if len(consistent) > 1:
        return "rival_grammar_alive"
    
    # Exactly one grammar consistent
    if len(consistent) == 1:
        if len(eliminated) + len(not_deserved) == len(grammar_results) - 1:
            # This is forced by train evidence (all rivals eliminated)
            return "candidate_deserved_if_unique_and_forced"
        else:
            # Only one grammar exists, so it's unique
            return "candidate_deserved_if_unique_and_forced"
    
    return "underdetermined"


def _compute_metrics(grammar_results: list[dict]) -> dict:
    """Compute metrics from grammar results."""
    consistent = [g for g in grammar_results if g.get("status") == "grammar_consistent"]
    eliminated = [g for g in grammar_results if g.get("status") == "grammar_eliminated_by_train_evidence"]
    not_deserved = [g for g in grammar_results if g.get("status") == "candidate_not_deserved"]
    rivals = len(consistent) if len(consistent) > 1 else 0
    
    # Count contradictions
    contradiction_count = sum(g.get("contradiction_count", 0) for g in grammar_results)
    
    # Count train-only eliminations
    train_only_elimination = len([g for g in eliminated if g.get("elimination_reason") == "train_io_mismatch"])
    
    return {
        "candidate_grammar_count": len(grammar_results),
        "grammar_consistent_count": len(consistent),
        "grammar_eliminated_count": len(eliminated),
        "rival_grammar_alive_count": rivals,
        "underdetermined_count": 1 if len(consistent) > 1 else 0,
        "all_eliminated_count": 1 if len(consistent) == 0 else 0,
        "forced_unique_candidate_count": 1 if len(consistent) == 1 and len(eliminated) + len(not_deserved) > 0 else 0,
        "unsupported_assumption_count": len(not_deserved),
        "contradiction_count": contradiction_count,
        "train_only_elimination_count": train_only_elimination,
        "synthetic_probe_elimination_attempt_blocked_count": 0,  # Always 0 - probes can't eliminate
        "deserved_candidate_count": len(consistent),
        "candidate_not_deserved_count": len(not_deserved),
    }


def summarize_rival_grammar_constraint_status_v1(evaluation_result: dict) -> dict:
    """
    Summarize the constraint status for the ledger.
    
    Args:
        evaluation_result: Result from evaluate_candidate_grammar_constraints_v1
    
    Returns:
        Summary dict with human-readable status
    """
    overall_status = evaluation_result.get("overall_status", "unknown")
    metrics = {
        k: v for k, v in evaluation_result.items()
        if k in [
            "candidate_grammar_count",
            "grammar_consistent_count",
            "grammar_eliminated_count",
            "rival_grammar_alive_count",
            "underdetermined_count",
            "all_eliminated_count",
            "forced_unique_candidate_count",
        ]
    }
    
    # Build human-readable summary
    if overall_status == "candidate_deserved_if_unique_and_forced":
        summary = "Exactly one grammar is consistent with all train examples and rivals are eliminated. This grammar is forced by train evidence."
    elif overall_status == "rival_grammar_alive":
        summary = f"{metrics.get('grammar_consistent_count', 0)} grammars remain consistent with train evidence. Output is underdetermined."
    elif overall_status == "all_grammars_eliminated":
        summary = "No grammar is consistent with train evidence. No candidate deserves forward application."
    elif overall_status == "underdetermined":
        summary = "Train evidence does not uniquely determine the output. Multiple grammars remain viable."
    else:
        summary = f"Constraint evaluation complete. Status: {overall_status}"
    
    return {
        "overall_status": overall_status,
        "summary": summary,
        "metrics": metrics,
        "final_answer_authority": evaluation_result.get("final_answer_authority", "ledger"),
    }


# Boundary constants
FINAL_ANSWER_AUTHORITY = "ledger"
HELPER_GENERATES_FINAL_ANSWER = False
HELPER_RANKS_GRAMMARS = False
HELPER_REPAIRS_GRAMMAR = False
ALLOWED_EVIDENCE_SCOPE = "train_only"
HIDDEN_TEST_OUTPUT_AVAILABLE = False
SYNTHETIC_PROBE_RESULTS_ALLOWED = False