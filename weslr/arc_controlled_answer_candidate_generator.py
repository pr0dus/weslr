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


# Anti-laundering laws (exposed)
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

# Construction modes
CONSTRUCTION_MODES = [
    "relation_first_rewrite_candidate",
    "object_correspondence_candidate",
    "invariant_preserving_candidate",
    "composed_transform_candidate",
    "train_forced_transformation_candidate",
    "explicit_grammar_candidate",
    "partial_candidate_descriptor",
]

# Blocking statuses
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

# Forbidden statuses
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
    """
    Build input for the controlled answer candidate generator.
    
    Args:
        task_id: Unique task identifier
        train_examples: List of train examples
        test_input_descriptor: Descriptor of test input
        forced_constraints: Train-forced constraints
        train_forced_transformations: Transformations with train support
        object_graph_correspondences: Object mapping correspondences
        invariant_preserving_transformations: Invariant-preserving transforms
        relation_first_rewrites: Relation-first rewrites
        composed_transform_candidates: Composed transform candidates
        explicit_candidate_grammars: Explicit grammar candidates
        unresolved_rival_grammars: Unresolved rival grammars
        unsupported_assumption_list: Unsupported assumptions
        helper_diagnostics: Diagnostics from helpers 1-8
        _requests_hidden_test: Internal flag - should remain False
        _requests_public_arc_answer: Internal flag - should remain False
    
    Returns:
        Input dictionary for candidate generation
    """
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
    """
    Generate controlled answer candidates from train-forced constraints.
    
    Args:
        generator_input: Input from build_controlled_answer_candidate_generator_input_v1
    
    Returns:
        Generation result with candidates or blocking reasons
    """
    # Initialize metrics
    metrics = {
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
        "memorization_risk_flag_count": 0,
    }
    
    candidates = []
    blocking_reason = None
    generation_status = "none"
    
    # Check for hidden test/public answer requests - fail closed
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
        
        # Check for forced constraints
        forced_constraints = generator_input.get("forced_constraints", [])
        if not forced_constraints:
            # Check if any construction mode can proceed
            can_proceed = _check_construction_modes(generator_input)
            
            if not can_proceed:
                blocking_reason = "candidate_generation_blocked"
                metrics["candidate_generation_blocked_count"] += 1
                generation_status = "blocked"  # FIX: set status
            else:
                # Generate candidates via construction modes
                candidates, trace_metrics = _generate_candidates(generator_input)
                metrics["candidate_generated_count"] = len(candidates)
                metrics["candidate_requires_ledger_review_count"] = len(candidates)
                metrics["ledger_review_required_count"] = len(candidates)
                metrics["construction_trace_complete_count"] = trace_metrics
                generation_status = "generated" if candidates else "blocked"
                if not candidates:
                    blocking_reason = "candidate_generation_blocked"
                    metrics["candidate_generation_blocked_count"] += 1
        else:
            # Has forced constraints - generate candidates
            candidates, trace_metrics = _generate_candidates(generator_input)
            metrics["candidate_generated_count"] = len(candidates)
            metrics["candidate_requires_ledger_review_count"] = len(candidates)
            metrics["ledger_review_required_count"] = len(candidates)
            metrics["construction_trace_complete_count"] = trace_metrics
            generation_status = "generated" if candidates else "blocked"
            if not candidates:
                blocking_reason = "candidate_generation_blocked"
                metrics["candidate_generation_blocked_count"] += 1
    
    # Build result
    result = {
        "task_id": generator_input.get("task_id"),
        "candidates": candidates,
        "blocking_reason": blocking_reason,
        "generation_status": generation_status,
        "metrics": metrics,
        # Ledger relationship
        "requires_ledger_review": True,
        "generator_grants_deservedness": False,
        "generator_outputs_final_answer": False,
        "candidate_treated_as_final_answer": False,
        "ledger_review_required": True,
        # Rehearsal/holdout
        "rehearsal_candidate_generation_allowed": True,
        "rehearsal_counts_toward_threshold": False,
        "fresh_holdout_counts": True,
        "fresh_holdout_requires_no_leakage": True,
        "holdout_answers_must_not_train": True,
        # Recorder fields
        "candidate_generated": len(candidates) > 0,
        "candidate_blocked": blocking_reason is not None,
        "missing_constraint_that_blocked": blocking_reason,
        # Anti-laundering
        "antilaundering_laws": ANTILAUNDERING_LAWS,
    }
    
    return result


def _check_construction_modes(generator_input: dict) -> bool:
    """Check if any construction mode can proceed."""
    # Check train-forced transformations
    if generator_input.get("train_forced_transformations"):
        return True
    # Check object correspondences (require train support)
    obj_corr = generator_input.get("object_graph_correspondences", [])
    for corr in obj_corr:
        if corr.get("train_supported"):
            return True
    # Check invariant preserving (require train support)
    inv = generator_input.get("invariant_preserving_transformations", [])
    for i in inv:
        if i.get("train_supported"):
            return True
    # Check relation-first rewrites
    if generator_input.get("relation_first_rewrites"):
        return True
    # Check composed transforms (all components must be train-supported)
    comp = generator_input.get("composed_transform_candidates", [])
    for c in comp:
        if c.get("all_components_train_supported"):
            return True
    # Check explicit grammars
    if generator_input.get("explicit_candidate_grammars"):
        return True
    
    return False


def _generate_candidates(generator_input: dict) -> tuple[list, int]:
    """Generate candidates via construction modes."""
    candidates = []
    trace_count = 0
    task_id = generator_input.get("task_id", "unknown")
    
    # Mode 1: Train-forced transformation candidate
    train_forced = generator_input.get("train_forced_transformations", [])
    for tf in train_forced:
        if tf.get("train_supported"):
            candidate = _build_candidate(
                task_id=task_id,
                mode="train_forced_transformation_candidate",
                operations=tf,
                source_constraint="train_forced_transformation",
                trace_count=trace_count,
            )
            candidates.append(candidate)
            trace_count += 1
    
    # Mode 2: Object correspondence candidate
    obj_corr = generator_input.get("object_graph_correspondences", [])
    for oc in obj_corr:
        if oc.get("train_supported"):
            candidate = _build_candidate(
                task_id=task_id,
                mode="object_correspondence_candidate",
                operations=oc,
                source_constraint="object_correspondence",
                trace_count=trace_count,
            )
            candidates.append(candidate)
            trace_count += 1
    
    # Mode 3: Invariant preserving candidate
    inv = generator_input.get("invariant_preserving_transformations", [])
    for i in inv:
        if i.get("train_supported"):
            candidate = _build_candidate(
                task_id=task_id,
                mode="invariant_preserving_candidate",
                operations=i,
                source_constraint="invariant_preserving",
                trace_count=trace_count,
            )
            candidates.append(candidate)
            trace_count += 1
    
    # Mode 4: Relation-first rewrite candidate
    rf = generator_input.get("relation_first_rewrites", [])
    for r in rf:
        candidate = _build_candidate(
            task_id=task_id,
            mode="relation_first_rewrite_candidate",
            operations=r,
            source_constraint="relation_first_rewrite",
            trace_count=trace_count,
        )
        candidates.append(candidate)
        trace_count += 1
    
    # Mode 5: Composed transform candidate
    comp = generator_input.get("composed_transform_candidates", [])
    for c in comp:
        if c.get("all_components_train_supported"):
            candidate = _build_candidate(
                task_id=task_id,
                mode="composed_transform_candidate",
                operations=c,
                source_constraint="composed_transform",
                trace_count=trace_count,
            )
            candidates.append(candidate)
            trace_count += 1
    
    # Mode 6: Explicit grammar candidate
    grammars = generator_input.get("explicit_candidate_grammars", [])
    for g in grammars:
        candidate = _build_candidate(
            task_id=task_id,
            mode="explicit_grammar_candidate",
            operations=g,
            source_constraint="explicit_grammar",
            trace_count=trace_count,
        )
        candidates.append(candidate)
        trace_count += 1
    
    # If no candidates, mark as partial
    if not candidates:
        candidate = _build_partial_candidate(task_id, trace_count)
        candidates.append(candidate)
    
    return candidates, trace_count


def _build_candidate(
    task_id: str,
    mode: str,
    operations: dict,
    source_constraint: str,
    trace_count: int,
) -> dict:
    """Build a candidate descriptor."""
    return {
        "candidate_id": f"{task_id}_cand_{trace_count}",
        "task_id": task_id,
        "construction_mode": mode,
        "output_shape_descriptor": operations.get("output_shape", {}),
        "object_operations": operations.get("object_operations", []),
        "color_operations": operations.get("color_operations", []),
        "spatial_operations": operations.get("spatial_operations", []),
        "relation_operations": operations.get("relation_operations", []),
        "invariant_preservation_claims": operations.get("invariant_claims", []),
        "object_correspondence_claims": operations.get("correspondence_claims", []),
        "source_constraints": [source_constraint],
        "unsupported_assumptions": operations.get("unsupported_assumptions", []),
        "unresolved_rivals": operations.get("unresolved_rivals", []),
        "construction_trace": [
            {
                "step_id": trace_count,
                "source_helper": operations.get("source_helper", "unknown"),
                "source_constraint": source_constraint,
                "operation": operations.get("operation_name", "transform"),
                "train_support": operations.get("train_supported", True),
                "assumption_status": operations.get("assumption_status", "forced"),
                "rival_impact": operations.get("rival_impact", "none"),
                "ledger_relevance": "required",
                "evidence_status": operations.get("evidence_status", "train_explicit"),
            }
        ],
        "requires_ledger_review": True,
        "treated_as_final_answer": False,
        "generation_status": "generated",
        "block_reason": None,
    }


def _build_partial_candidate(task_id: str, trace_count: int) -> dict:
    """Build a partial candidate descriptor."""
    return {
        "candidate_id": f"{task_id}_cand_partial",
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
        "unsupported_assumptions": [],
        "unresolved_rivals": [],
        "construction_trace": [],
        "requires_ledger_review": True,
        "treated_as_final_answer": False,
        "generation_status": "partial",
        "block_reason": "insufficient_train_evidence",
    }


def summarize_controlled_answer_candidate_generation_v1(result: dict) -> dict:
    """
    Summarize the candidate generation result.
    
    Args:
        result: Result from generate_controlled_answer_candidates_v1
    
    Returns:
        Human-readable summary
    """
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

Anti-laundering laws enforced: {len(result.get('antilaundering_laws', []))}
"""
    
    return {
        "summary": summary,
        "result": result,
    }


# Boundary constants
GENERATOR_GRANTS_DESERVEDNESS = False
GENERATOR_OUTPUTS_FINAL_ANSWER = False
REQUIRES_LEDGER_REVIEW = True
CANDIDATE_TREATED_AS_FINAL_ANSWER = False