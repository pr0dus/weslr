"""
Relation-First Compiler Helper V1

Transforms moved-anchor coordinate-form rules into relational-form rules.

This helper transforms candidate rules without judging, scoring, vetoing, or generating final answers.
Pure transformation only — no solver behavior change, no new judge.
"""

from typing import Any

# Allowed rewrite statuses
REWRITE_FULL = "full_relational_rewrite"
REWRITE_PARTIAL = "partial_rewrite_with_residual"
REWRITE_IRREDUCIBLE = "coordinate_dependency_irreducible"
REWRITE_UNSAFE = "unsafe_to_predict_no_relational_grammar"
REWRITE_NOT_APPLICABLE = "not_applicable"

# Moved-anchor families that can potentially be fully rewritten
_FULL_REWRITE_FAMILIES = frozenset([
    "anchor_translated_target_preserved",
    "anchor_moved_offset_constant",
    "anchor_moved_distractor_at_old_coord",
])

# Families that require partial rewrite
_PARTIAL_REWRITE_FAMILIES = frozenset([
    "multiple_anchors_one_valid",
])

# Families that are irreducible
_IRREDUCIBLE_FAMILIES = frozenset([
    "anchor_moved_near_boundary",
])

# Families that are unsafe
_UNSAFE_FAMILIES = frozenset([
    "anchor_absent_ambiguous",
])

# Required fields for any rewrite attempt
_REQUIRED_FIELDS = frozenset([
    "rule_id",
    "anchor_coordinate",
    "target_offset",
    "family_id",
])


def rewrite_moved_anchor_candidate_rule_v1(candidate_rule: dict) -> dict:
    """
    Transform a moved-anchor coordinate-form rule into a relational-form rule.
    
    Args:
        candidate_rule: Input dictionary with fields:
            - rule_id (str): Unique identifier
            - family_id (str): Source family
            - anchor_coordinate (dict): {x, y}
            - anchor_identity (str | None): Known anchor identity/role
            - target_offset (dict): {dx, dy}
            - distractor_at_old_anchor (bool)
            - ambiguity_signal (bool)
            - boundary_signal (bool)
            - anchor_absent (bool)
            - context (dict): task_id, source
    
    Returns:
        dict with fields:
            - rewrite_status: full_relational_rewrite | partial_rewrite_with_residual |
                              coordinate_dependency_irreducible | unsafe_to_predict_no_relational_grammar |
                              not_applicable
            - original_coordinate_rule (dict): Preserved input
            - relational_rule (dict | None): Transformed form
            - residual_dependency (str | None): For partial rewrites
            - fallback_rule (dict | None): Original if rewrite fails
            - downstream_candidate_rule (dict): Rule passed to downstream
            - helper_changed_candidate_rule (bool): Did transformation occur?
            - safety_reason (str | None): Why rewrite succeeded/failed
            - transform_metadata (dict): rule_id, rewrite_timestamp (None), input_family, output_family
    """
    # Preserve original input - no mutation
    original = dict(candidate_rule)
    
    # Extract key fields with defaults
    family_id = candidate_rule.get("family_id")
    anchor_identity = candidate_rule.get("anchor_identity")
    anchor_coordinate = candidate_rule.get("anchor_coordinate", {})
    target_offset = candidate_rule.get("target_offset", {})
    distractor_at_old = candidate_rule.get("distractor_at_old_anchor", False)
    ambiguity = candidate_rule.get("ambiguity_signal", False)
    boundary = candidate_rule.get("boundary_signal", False)
    anchor_absent = candidate_rule.get("anchor_absent", False)
    
    # Check required fields
    if not _has_required_fields(candidate_rule):
        return _build_not_applicable_output(original, "missing_required_fields")
    
    # Handle non-moved-anchor families
    if family_id not in _FULL_REWRITE_FAMILIES | _PARTIAL_REWRITE_FAMILIES | _IRREDUCIBLE_FAMILIES | _UNSAFE_FAMILIES:
        return _build_not_applicable_output(original, "not_moved_anchor_family")
    
    # Full relational rewrite conditions:
    # - Family is in FULL_REWRITE_FAMILIES
    # - anchor_identity is available
    # - ambiguity_signal is false
    # - boundary_signal is false
    # - anchor_absent is false
    if family_id in _FULL_REWRITE_FAMILIES:
        if anchor_identity and not anchor_absent:
            # Check signals that block full rewrite
            if ambiguity or boundary:
                # Signal present: irreducible (boundary) or unsafe (ambiguity without partial)
                if boundary:
                    return _build_irreducible_output(original, anchor_coordinate, target_offset, family_id)
                else:
                    return _build_unsafe_output(original, "rewrite_blocked_by_ambiguity_signal")
            else:
                return _build_full_rewrite_output(original, anchor_identity, anchor_coordinate, target_offset, family_id)
        elif not anchor_identity or anchor_absent:
            return _build_unsafe_output(original, "anchor_identity_missing_or_absent")
        else:
            # Has identity but some signal blocks full rewrite
            return _build_unsafe_output(original, "rewrite_blocked_by_signal")
    
    # Partial rewrite with residual
    if family_id in _PARTIAL_REWRITE_FAMILIES:
        if anchor_identity and ambiguity:
            return _build_partial_rewrite_output(original, anchor_identity, anchor_coordinate, target_offset, family_id)
        elif not anchor_identity:
            return _build_unsafe_output(original, "anchor_identity_missing_for_partial")
        else:
            # Ambiguity is required for partial
            return _build_not_applicable_output(original, "partial_rewrite_requires_ambiguity")
    
    # Coordinate dependency irreducible
    if family_id in _IRREDUCIBLE_FAMILIES or boundary:
        return _build_irreducible_output(original, anchor_coordinate, target_offset, family_id)
    
    # Unsafe to predict
    if family_id in _UNSAFE_FAMILIES or anchor_absent:
        return _build_unsafe_output(original, "anchor_absent_or_unsafe_family")
    
    # Fallback: not applicable
    return _build_not_applicable_output(original, "no_rewrite_applicable")


def _has_required_fields(rule: dict) -> bool:
    """Check if all required fields are present."""
    return all(rule.get(field) is not None for field in _REQUIRED_FIELDS)


def _build_relational_rule(anchor_identity: str, anchor_coordinate: dict, target_offset: dict, family_id: str) -> dict:
    """Build the relational-form rule."""
    return {
        "rule_type": "relational",
        "anchor_role": anchor_identity,
        "anchor_original_coordinate": anchor_coordinate,
        "target_offset": target_offset,
        "source_family": family_id,
    }


def _build_full_rewrite_output(original: dict, anchor_identity: str, anchor_coordinate: dict, 
                                target_offset: dict, family_id: str) -> dict:
    """Build output for full relational rewrite."""
    relational = _build_relational_rule(anchor_identity, anchor_coordinate, target_offset, family_id)
    
    return {
        "rewrite_status": REWRITE_FULL,
        "original_coordinate_rule": original,
        "relational_rule": relational,
        "residual_dependency": None,
        "fallback_rule": None,
        "downstream_candidate_rule": relational,
        "helper_changed_candidate_rule": True,
        "safety_reason": "full_relational_rewrite_success",
        "transform_metadata": {
            "rule_id": original.get("rule_id"),
            "rewrite_timestamp": None,  # Caller-supplied or None for determinism
            "input_family": family_id,
            "output_family": "relational",
        },
    }


def _build_partial_rewrite_output(original: dict, anchor_identity: str, anchor_coordinate: dict,
                                   target_offset: dict, family_id: str) -> dict:
    """Build output for partial rewrite with residual."""
    relational = _build_relational_rule(anchor_identity, anchor_coordinate, target_offset, family_id)
    
    # Original coordinate rule as fallback
    fallback = {
        "rule_type": "coordinate",
        "anchor_coordinate": anchor_coordinate,
        "target_offset": target_offset,
        "source_family": family_id,
    }
    
    return {
        "rewrite_status": REWRITE_PARTIAL,
        "original_coordinate_rule": original,
        "relational_rule": relational,
        "residual_dependency": "ambiguity_residual",
        "fallback_rule": fallback,
        "downstream_candidate_rule": fallback,  # Both forms would be evaluated; keep coordinate as primary
        "helper_changed_candidate_rule": True,
        "safety_reason": "partial_rewrite_with_ambiguity_residual",
        "transform_metadata": {
            "rule_id": original.get("rule_id"),
            "rewrite_timestamp": None,
            "input_family": family_id,
            "output_family": "partial_relational",
        },
    }


def _build_irreducible_output(original: dict, anchor_coordinate: dict, target_offset: dict, family_id: str) -> dict:
    """Build output for irreducible coordinate dependency."""
    fallback = {
        "rule_type": "coordinate",
        "anchor_coordinate": anchor_coordinate,
        "target_offset": target_offset,
        "source_family": family_id,
    }
    
    return {
        "rewrite_status": REWRITE_IRREDUCIBLE,
        "original_coordinate_rule": original,
        "relational_rule": None,
        "residual_dependency": "boundary_dependency",
        "fallback_rule": fallback,
        "downstream_candidate_rule": fallback,
        "helper_changed_candidate_rule": False,
        "safety_reason": "coordinate_dependency_irreducible_near_boundary",
        "transform_metadata": {
            "rule_id": original.get("rule_id"),
            "rewrite_timestamp": None,
            "input_family": family_id,
            "output_family": "coordinate_irreducible",
        },
    }


def _build_unsafe_output(original: dict, reason: str) -> dict:
    """Build output for unsafe to predict cases."""
    return {
        "rewrite_status": REWRITE_UNSAFE,
        "original_coordinate_rule": original,
        "relational_rule": None,
        "residual_dependency": None,
        "fallback_rule": None,
        "downstream_candidate_rule": None,
        "helper_changed_candidate_rule": False,
        "safety_reason": f"unsafe_to_predict_{reason}",
        "transform_metadata": {
            "rule_id": original.get("rule_id"),
            "rewrite_timestamp": None,
            "input_family": original.get("family_id"),
            "output_family": "unsafe",
        },
    }


def _build_not_applicable_output(original: dict, reason: str) -> dict:
    """Build output for not applicable cases."""
    # Preserve original as fallback
    fallback = {
        "rule_type": "coordinate",
        "anchor_coordinate": original.get("anchor_coordinate", {}),
        "target_offset": original.get("target_offset", {}),
        "source_family": original.get("family_id"),
    }
    
    return {
        "rewrite_status": REWRITE_NOT_APPLICABLE,
        "original_coordinate_rule": original,
        "relational_rule": None,
        "residual_dependency": None,
        "fallback_rule": fallback,
        "downstream_candidate_rule": fallback,
        "helper_changed_candidate_rule": False,
        "safety_reason": f"not_applicable_{reason}",
        "transform_metadata": {
            "rule_id": original.get("rule_id"),
            "rewrite_timestamp": None,
            "input_family": original.get("family_id"),
            "output_family": "unchanged",
        },
    }


# Solver-freeze constants (exported for test verification)
SOLVER_BEHAVIOR_CHANGED = False
SOLVER_PRIMITIVES_ADDED = False
BENCHMARK_CLAIM_SAFE = False
SYNTHETIC_ONLY = True
PUBLIC_ARC_USED = False
KAGGLE_USED = False