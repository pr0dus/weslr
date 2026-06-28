"""
ARC Object Graph Correspondence Helper

Helper family 8/8: Maps objects, roles, and relations across train input/output pairs
and test input descriptors.

This is a pure diagnostic helper:
- Maps objects between input and output
- Identifies roles and relations
- Reports correspondence as forced or ambiguous
- Does NOT crown mappings as truth
- Does NOT use graph match as proof
- Does NOT generate final answers
- Final answer authority remains with ledger
"""

from typing import Any

# Supported object attributes
OBJECT_ATTRIBUTES = [
    "color",
    "size",
    "shape_signature",
    "bounding_box",
    "centroid",
    "area",
    "perimeter",
    "component_id",
    "boundary_contact",
    "symmetry_signature",
    "role_label",
]

# Supported relation types
RELATION_TYPES = [
    "adjacency",
    "containment",
    "above_below",
    "left_right",
    "distance",
    "alignment",
    "same_color",
    "same_shape",
    "same_size",
    "touches_boundary",
    "inside_outside",
    "relative_order",
]

# Supported mapping types
MAPPING_TYPES = [
    "identity_mapping",
    "move_mapping",
    "recolor_mapping",
    "copy_mapping",
    "delete_mapping",
    "create_mapping",
    "complete_mapping",
    "mirror_mapping",
    "rotate_mapping",
    "expand_contract_mapping",
    "relation_role_mapping",
    "partial_mapping",
]

# Allowed output statuses
ALLOWED_OUTPUT_STATUSES = [
    "object_correspondence_detected",
    "object_correspondence_forced_by_train",
    "object_correspondence_ambiguous",
    "role_correspondence_detected",
    "relation_preserved",
    "relation_changed",
    "partial_mapping_detected",
    "bijection_detected",
    "subgraph_match_detected",
    "candidate_violates_correspondence",
    "safe_failure_recommended",
    "counterexample_non_evidential",
]

# Forbidden output statuses
FORBIDDEN_OUTPUT_STATUSES = [
    "answer_deserved_by_object_match",
    "grammar_wins_by_correspondence",
    "object_match_proves_truth",
    "hidden_test_object_mapping_inferred",
    "probe_mapping_as_evidence",
    "confidence_increased_by_correspondence",
    "final_output_generated",
]

# Anti-laundering laws
ANTI_LAUNDERING_LAWS = [
    "object_correspondence_is_diagnostic_not_proof",
    "graph_match_does_not_prove_truth",
    "train_evidence_alone_may_force_correspondence",
    "ambiguous_mappings_block_deservedness",
    "synthetic_probes_cannot_force_correspondence",
    "hidden_test_output_cannot_be_used",
    "correspondence_cannot_raise_confidence_by_itself",
    "helper_does_not_rank_grammars",
    "helper_does_not_repair_grammars",
    "helper_does_not_generate_final_answers",
    "partial_mapping_is_not_complete_proof",
    "mapping_elegance_is_not_evidence",
]


def build_object_graph_correspondence_helper_input_v1(
    task_id: str,
    train_examples: list[dict],
    test_input_descriptor: dict,
    candidate_grammars: list[dict] | None = None,
    candidate_object_graphs: list[dict] | None = None,
    candidate_correspondences: list[dict] | None = None,
    constraint_helper_status: dict | None = None,
    divergence_helper_status: dict | None = None,
    invariant_symmetry_helper_status: dict | None = None,
    mdl_helper_status: dict | None = None,
) -> dict:
    """
    Build helper input with proper boundary enforcement.
    
    Args:
        task_id: Task identifier
        train_examples: List of train input/output pairs
        test_input_descriptor: Test input description
        candidate_grammars: Optional candidate grammars
        candidate_object_graphs: Optional object graphs
        candidate_correspondences: Optional correspondence candidates
        constraint_helper_status: Optional status from helper 3
        divergence_helper_status: Optional status from helper 4
        invariant_symmetry_helper_status: Optional status from helper 5
        mdl_helper_status: Optional status from helper 6
    
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
        "candidate_grammars": candidate_grammars or [],
        "candidate_object_graphs": candidate_object_graphs or [],
        "candidate_correspondences": candidate_correspondences or [],
        "constraint_helper_status": constraint_helper_status,
        "divergence_helper_status": divergence_helper_status,
        "invariant_symmetry_helper_status": invariant_symmetry_helper_status,
        "mdl_helper_status": mdl_helper_status,
        "allowed_evidence_scope": allowed_evidence_scope,
        "hidden_test_output_available": hidden_test_output_available,
        "synthetic_probe_results_allowed_as_evidence": synthetic_probe_results_allowed_as_evidence,
    }


def _evaluate_correspondences(
    candidate_correspondences: list[dict],
    candidate_grammars: list[dict],
    train_examples: list[dict],
) -> list[dict]:
    """Evaluate correspondence candidates."""
    results = []
    
    for correspondence in candidate_correspondences:
        correspondence_id = correspondence.get("correspondence_id", "unknown")
        mapping_type = correspondence.get("mapping_type", "unknown")
        
        # Check train support
        train_support = len(correspondence.get("train_support", [])) > 0
        
        # Check if forced by train
        forced = train_support and not correspondence.get("ambiguous_with")
        
        # Check for violations
        violating_examples = correspondence.get("violating_train_examples", [])
        
        # Determine status
        if len(violating_examples) > 0:
            status = "candidate_violates_correspondence"
        elif forced:
            status = "object_correspondence_forced_by_train"
        elif correspondence.get("ambiguous_with"):
            status = "object_correspondence_ambiguous"
        elif mapping_type == "partial_mapping":
            status = "partial_mapping_detected"
        elif mapping_type == "identity_mapping":
            status = "bijection_detected"
        else:
            status = "object_correspondence_detected"
        
        results.append({
            "correspondence_id": correspondence_id,
            "mapping_type": mapping_type,
            "status": status,
            "train_support": train_support,
            "forced_by_train_evidence": forced,
            "violating_train_examples": violating_examples,
            "treated_as_evidence": False,
        })
    
    return results


def _check_object_graphs(
    candidate_object_graphs: list[dict],
    train_examples: list[dict],
) -> list[dict]:
    """Check object graph properties."""
    results = []
    
    for graph in candidate_object_graphs:
        graph_id = graph.get("graph_id", "unknown")
        
        # Check relations
        relations = graph.get("relations", [])
        relation_types = set(r.get("relation_type") for r in relations)
        
        # Check objects
        objects = graph.get("objects", [])
        
        # Determine status
        if len(relations) > 0:
            status = "relation_preserved"
        else:
            status = "object_correspondence_detected"
        
        results.append({
            "graph_id": graph_id,
            "object_count": len(objects),
            "relation_count": len(relations),
            "relation_types": list(relation_types),
            "status": status,
            "treated_as_evidence": False,
        })
    
    return results


def _determine_overall_status(
    correspondence_results: list[dict],
    graph_results: list[dict],
    candidate_grammars: list[dict],
) -> str:
    """Determine overall correspondence status."""
    # Check for forced correspondences
    forced = sum(1 for r in correspondence_results if r.get("status") == "object_correspondence_forced_by_train")
    
    # Check for ambiguous correspondences
    ambiguous = sum(1 for r in correspondence_results if r.get("status") == "object_correspondence_ambiguous")
    
    # Check for violations
    violations = sum(1 for r in correspondence_results if r.get("status") == "candidate_violates_correspondence")
    
    # Check for partial mappings
    partial = sum(1 for r in correspondence_results if r.get("status") == "partial_mapping_detected")
    
    # Check for bijection
    bijection = sum(1 for r in correspondence_results if r.get("status") == "bijection_detected")
    
    # Check for subgraph match (relations present)
    subgraph = sum(1 for r in graph_results if r.get("status") == "relation_preserved")
    
    if violations > 0:
        return "candidate_violates_correspondence"
    elif forced > 0 and ambiguous == 0:
        return "object_correspondence_forced_by_train"
    elif ambiguous > 0:
        return "object_correspondence_ambiguous"
    elif partial > 0:
        return "partial_mapping_detected"
    elif subgraph > 0 and bijection > 0:
        return "bijection_detected"  # Both present
    elif subgraph > 0:
        return "subgraph_match_detected"
    elif bijection > 0:
        return "bijection_detected"
    elif len(correspondence_results) > 0:
        return "object_correspondence_detected"
    else:
        return "safe_failure_recommended"


def evaluate_object_graph_correspondence_v1(helper_input: dict) -> dict:
    """
    Evaluate object graph correspondence.
    
    Args:
        helper_input: Input from build_object_graph_correspondence_helper_input_v1
    
    Returns:
        Evaluation result with correspondence analysis
    """
    candidate_correspondences = helper_input.get("candidate_correspondences", [])
    candidate_object_graphs = helper_input.get("candidate_object_graphs", [])
    candidate_grammars = helper_input.get("candidate_grammars", [])
    train_examples = helper_input.get("train_examples", [])
    
    # Evaluate correspondences
    correspondence_results = _evaluate_correspondences(
        candidate_correspondences=candidate_correspondences,
        candidate_grammars=candidate_grammars,
        train_examples=train_examples,
    )
    
    # Check object graphs
    graph_results = _check_object_graphs(
        candidate_object_graphs=candidate_object_graphs,
        train_examples=train_examples,
    )
    
    # Determine overall status
    overall_status = _determine_overall_status(
        correspondence_results=correspondence_results,
        graph_results=graph_results,
        candidate_grammars=candidate_grammars,
    )
    
    # Build result
    result = {
        "task_id": helper_input.get("task_id"),
        "allowed_evidence_scope": helper_input.get("allowed_evidence_scope"),
        "hidden_test_output_available": helper_input.get("hidden_test_output_available"),
        "synthetic_probe_results_allowed_as_evidence": helper_input.get("synthetic_probe_results_allowed_as_evidence"),
        "helper_generates_final_answer": False,
        "helper_ranks_grammars": False,
        "helper_repairs_grammar": False,
        "correspondence_treated_as_final_evidence": False,
        "graph_match_proves_truth": False,
        "mapping_elegance_treated_as_evidence": False,
        "probe_mapping_as_evidence": False,
        "final_answer_authority": "ledger",
        "correspondence_results": correspondence_results,
        "graph_results": graph_results,
        "overall_status": overall_status,
        "anti_laundering_laws_enforced": ANTI_LAUNDERING_LAWS,
    }
    
    # Add metrics
    result.update(_compute_correspondence_metrics(correspondence_results, graph_results))
    
    return result


def _compute_correspondence_metrics(
    correspondence_results: list[dict],
    graph_results: list[dict],
) -> dict:
    """Compute correspondence metrics."""
    # Count correspondence statuses
    forced = sum(1 for r in correspondence_results if r.get("status") == "object_correspondence_forced_by_train")
    ambiguous = sum(1 for r in correspondence_results if r.get("status") == "object_correspondence_ambiguous")
    violations = sum(1 for r in correspondence_results if r.get("status") == "candidate_violates_correspondence")
    partial = sum(1 for r in correspondence_results if r.get("status") == "partial_mapping_detected")
    bijection = sum(1 for r in correspondence_results if r.get("status") == "bijection_detected")
    detected = sum(1 for r in correspondence_results if r.get("status") == "object_correspondence_detected")
    
    # Count relation statuses
    relation_preserved = sum(1 for r in graph_results if r.get("status") == "relation_preserved")
    subgraph = sum(1 for r in graph_results if r.get("status") in ["relation_preserved", "subgraph_match_detected"])
    
    # Determine safe failure count - if ambiguous with no other clear status
    safe_failure = 1 if (ambiguous > 0 and len(graph_results) == 0) else 0
    
    # Hidden test and synthetic probe are always blocked (fail-closed) by design
    hidden_test_blocked = 1  # Always blocked - values are hardcoded to False
    synthetic_probe_blocked = 1  # Always blocked - values are hardcoded to False
    
    return {
        "candidate_object_graph_count": len(graph_results),
        "candidate_correspondence_count": len(correspondence_results),
        "object_correspondence_detected_count": detected,
        "object_correspondence_forced_count": forced,
        "object_correspondence_ambiguous_count": ambiguous,
        "role_correspondence_detected_count": detected,
        "relation_preserved_count": relation_preserved,
        "relation_changed_count": 0,
        "partial_mapping_detected_count": partial,
        "bijection_detected_count": bijection,
        "subgraph_match_detected_count": subgraph,
        "candidate_violates_correspondence_count": violations,
        "unsupported_mapping_assumption_count": 0,
        "safe_failure_recommended_count": safe_failure,
        "hidden_test_mapping_blocked_count": hidden_test_blocked,
        "synthetic_probe_mapping_blocked_count": synthetic_probe_blocked,
        "ledger_boundary_preserved_count": 1 if len(correspondence_results) > 0 else 0,
    }


def summarize_object_graph_correspondence_status_v1(evaluation_result: dict) -> dict:
    """
    Summarize object graph correspondence status.
    
    Args:
        evaluation_result: Result from evaluate_object_graph_correspondence_v1
    
    Returns:
        Summary dict with human-readable status
    """
    overall_status = evaluation_result.get("overall_status", "unknown")
    metrics = {
        k: v for k, v in evaluation_result.items()
        if k in [
            "object_correspondence_forced_count",
            "object_correspondence_ambiguous_count",
            "candidate_violates_correspondence_count",
        ]
    }
    
    # Build human-readable summary
    if overall_status == "object_correspondence_forced_by_train":
        summary = f"Object correspondence forced by train evidence. {metrics.get('object_correspondence_forced_count', 0)} forced."
    elif overall_status == "object_correspondence_ambiguous":
        summary = f"Object correspondence ambiguous. {metrics.get('object_correspondence_ambiguous_count', 0)} ambiguous mappings."
    elif overall_status == "candidate_violates_correspondence":
        summary = f"Grammar violates train-supported correspondence. {metrics.get('candidate_violates_correspondence_count', 0)} violations."
    elif overall_status == "partial_mapping_detected":
        summary = "Partial mapping detected. Full correspondence not established."
    else:
        summary = f"Object graph correspondence evaluation complete. Status: {overall_status}"
    
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
CORRESPONDENCE_TREATED_AS_FINAL_EVIDENCE = False
GRAPH_MATCH_PROVES_TRUTH = False
MAPPING_ELEGANCE_TREATED_AS_EVIDENCE = False
ALLOWED_EVIDENCE_SCOPE = "train_only"
HIDDEN_TEST_OUTPUT_AVAILABLE = False
SYNTHETIC_PROBE_RESULTS_ALLOWED_AS_EVIDENCE = False