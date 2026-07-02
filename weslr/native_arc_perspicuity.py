"""WESLR Native ARC Evidence-Driven Perspicuity Ranking.

Upgrades the static 7-dimensional perspicuity scoring with evidence-driven
features from the 120 semantic pilot, candidate probes, promotion pipeline,
and strategic task-space analysis.

This module is metadata-only and deterministic:
- No oracle or solver implementations
- No primitive promotion
- No candidate counted as solved
- No runtime/chat/UI/provider paths
- No .weslr IO
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from weslr.native_arc_candidate_generator import (
    generate_candidates,
    PerspicuityScore,
    CandidateFamily,
)
from weslr.native_arc_language_schema import (
    PrimitiveContract,
    PromotionStage,
)

# ---------------------------------------------------------------------------
# BH80 accepted primitives (for duplicate-risk assessment)
# ---------------------------------------------------------------------------

BH80_ACCEPTED_PRIMITIVES: Set[str] = {
    "count", "count_objects", "count_or_pattern", "crop", "crop_object",
    "extract", "extract_boundary", "extract_changed_region", "extract_object",
    "fill_region", "isolate_largest", "mirror_object", "normalize_position",
    "pattern_output", "place_back", "recolor", "recolor_boundary",
    "remove_noise", "rotate", "transform",
}

PROMOTED_PRIMITIVES: Set[str] = {"color_invert"}

# ---------------------------------------------------------------------------
# Candidate probe mapping (from T120_101–T120_110)
# ---------------------------------------------------------------------------

CANDIDATE_PROBE_TASKS: Dict[str, Dict[str, str]] = {
    "mask_border_only":       {"task_id": "T120_101", "chain": "extract→mask_border_only→recolor", "family": "mask_algebra"},
    "geom_flip_vertical":     {"task_id": "T120_102", "chain": "isolate_largest→geom_flip_vertical→recolor", "family": "geometry_transform"},
    "topo_fill_holes":        {"task_id": "T120_103", "chain": "topo_fill_holes→extract→recolor", "family": "topology_transform"},
    "constr_draw_rect_around": {"task_id": "T120_104", "chain": "constr_draw_rect_around→recolor→crop", "family": "construction_transform"},
    "color_swap_1_2":         {"task_id": "T120_105", "chain": "color_swap_1_2→extract→rotate", "family": "color_transform"},
    "sel_leftmost":           {"task_id": "T120_106", "chain": "sel_leftmost→recolor→rotate", "family": "object_selector"},
    "pat_row_alternate":      {"task_id": "T120_107", "chain": "extract→pat_row_alternate→recolor", "family": "pattern_transform"},
    "cond_if_holes_fill":     {"task_id": "T120_108", "chain": "cond_if_holes_fill→recolor→crop", "family": "conditional_transform"},
    "rel_swap_positions":     {"task_id": "T120_109", "chain": "rel_swap_positions→recolor→transform", "family": "relation_transform"},
    "mask_complement":        {"task_id": "T120_110", "chain": "mask_complement→extract_boundary→recolor", "family": "mask_algebra"},
}

# ---------------------------------------------------------------------------
# Evidence-driven feature definitions
# ---------------------------------------------------------------------------

@dataclass
class EvidenceFeatures:
    """Evidence-driven features for a candidate primitive."""

    # Static perspicuity (from existing scoring)
    static_perspicuity: float

    # Probe evidence
    has_probe_task: bool               # appears in T120_101–T120_110
    probe_task_id: Optional[str]        # which probe task
    probe_chain: Optional[str]          # what 3-step chain it appears in

    # Promotion cost estimates (0.0 = trivial, 1.0 = very hard)
    oracle_complexity: float            # estimated oracle implementation complexity
    solver_complexity: float            # estimated solver implementation complexity
    promotion_difficulty: float         # overall promotion pipeline difficulty

    # Task-space expansion value (0.0 = low, 1.0 = high)
    task_space_value: float             # how much new task variety this enables
    new_family: bool                    # introduces a genuinely new transform family
    expected_denominator_gain: int      # how many new scored tasks this could add

    # Risk factors (0.0 = low risk, 1.0 = high risk)
    duplicate_risk: float               # similarity to existing BH80/promoted primitives
    regression_risk: float              # risk of breaking BH80 or 120 scored results
    shortcut_risk: float                # risk of being trivially shortcut-table

    # Strategic
    is_promoted: bool                   # already promoted
    recommendation: str                 # "promote_now" | "defer" | "discard"
    reason_codes: List[str]             # explainable reasons for recommendation


@dataclass
class EvidenceDrivenScore:
    """Full evidence-driven perspicuity score for a candidate."""

    primitive_id: str
    family: str
    human_summary: str
    static_score: PerspicuityScore
    evidence: EvidenceFeatures

    @property
    def total(self) -> float:
        """Weighted total score combining static and evidence-driven features."""
        e = self.evidence
        # Weights:
        # - static perspicuity: 25%
        # - probe availability: 10%
        # - low promotion difficulty: 20%
        # - task-space value: 20%
        # - low duplicate risk: 10%
        # - low regression risk: 10%
        # - low shortcut risk: 5%
        weights = {
            "static": 0.25,
            "probe": 0.10,
            "promotion_ease": 0.20,
            "task_space": 0.20,
            "non_duplicate": 0.10,
            "non_regression": 0.10,
            "non_shortcut": 0.05,
        }

        static_component = e.static_perspicuity
        probe_component = 1.0 if e.has_probe_task else 0.3
        promotion_ease = 1.0 - e.promotion_difficulty
        task_space = e.task_space_value
        non_duplicate = 1.0 - e.duplicate_risk
        non_regression = 1.0 - e.regression_risk
        non_shortcut = 1.0 - e.shortcut_risk

        return (
            weights["static"] * static_component +
            weights["probe"] * probe_component +
            weights["promotion_ease"] * promotion_ease +
            weights["task_space"] * task_space +
            weights["non_duplicate"] * non_duplicate +
            weights["non_regression"] * non_regression +
            weights["non_shortcut"] * non_shortcut
        )


# ---------------------------------------------------------------------------
# Duplicate risk assessment
# ---------------------------------------------------------------------------

# Semantic similarity map: candidate → most similar BH80/promoted primitive
SEMANTIC_SIMILARITY: Dict[str, Tuple[str, float]] = {
    # object_selector family
    "sel_leftmost":         ("extract", 0.5),      # selects one object, similar to extract
    "sel_topmost":          ("extract", 0.5),
    "sel_smallest":         ("extract", 0.5),
    "sel_most_holes":       ("extract", 0.4),
    "sel_edge_touch":       ("extract", 0.4),
    # mask_algebra family
    "mask_union":           ("fill_region", 0.3),   # fills regions, different semantics
    "mask_intersect":       ("extract_boundary", 0.4),
    "mask_complement":      ("recolor", 0.3),       # inverts mask, somewhat like recolor
    "mask_border_only":     ("extract_boundary", 0.6),  # border extraction, high similarity
    # color_transform family
    "color_swap_1_2":       ("recolor", 0.5),       # color remapping, similar to recolor
    "color_gradient":       ("fill_region", 0.3),
    "color_invert":         ("recolor", 0.4),       # already promoted
    "color_dominant":       ("recolor", 0.5),
    # geometry_transform family
    "geom_scale_2x":        ("crop", 0.2),          # dimension change, but different direction
    "geom_translate_center": ("normalize_position", 0.7),  # very similar to normalize_position
    "geom_flip_vertical":   ("transform", 0.6),     # flip, similar to transform (which is vertical flip)
    # topology_transform family
    "topo_merge_objects":   ("fill_region", 0.3),
    "topo_fill_holes":      ("fill_region", 0.4),   # fills, different target
    "topo_split_at_gap":    ("extract", 0.2),
    # relation_transform family
    "rel_align_centroids":  ("normalize_position", 0.6),
    "rel_swap_positions":   ("place_back", 0.3),
    "rel_order_by_size":    ("normalize_position", 0.3),
    # construction_transform family
    "constr_draw_rect_around": ("extract_boundary", 0.4),
    "constr_extend_pattern":   ("pattern_output", 0.5),
    "constr_connect_line":     ("fill_region", 0.2),
    "constr_copy_to_pos":      ("place_back", 0.4),
    # pattern_transform family
    "pat_row_alternate":    ("pattern_output", 0.6),  # pattern, similar to pattern_output
    "pat_block_repeat":     ("pattern_output", 0.5),
    "pat_color_cycle":      ("pattern_output", 0.4),
    # conditional_transform family
    "cond_if_holes_fill":   ("fill_region", 0.4),
    "cond_if_multi_count":  ("count_or_pattern", 0.5),
    "cond_if_edge_clip":    ("crop", 0.4),
}


def _compute_duplicate_risk(primitive_id: str) -> float:
    """Compute duplicate risk for a candidate.

    Returns 0.0 (no risk) to 1.0 (high risk of being a duplicate).
    """
    if primitive_id in PROMOTED_PRIMITIVES:
        return 0.0  # already promoted, not a candidate anymore

    sim = SEMANTIC_SIMILARITY.get(primitive_id)
    if sim is None:
        return 0.3  # default moderate risk if unknown
    _similar_to, similarity = sim
    return similarity


# ---------------------------------------------------------------------------
# Oracle/solver complexity estimation
# ---------------------------------------------------------------------------

COMPLEXITY_ESTIMATES: Dict[str, Tuple[float, float]] = {
    # primitive_id: (oracle_complexity, solver_complexity)
    # 0.1 = trivial (< 10 lines), 0.3 = easy (< 30 lines), 0.5 = moderate, 0.7 = hard, 0.9 = very hard
    "sel_leftmost":         (0.2, 0.3),
    "sel_topmost":          (0.2, 0.3),
    "sel_smallest":         (0.3, 0.4),
    "sel_most_holes":       (0.4, 0.5),
    "sel_edge_touch":       (0.3, 0.4),
    "mask_union":           (0.3, 0.4),
    "mask_intersect":       (0.3, 0.4),
    "mask_complement":      (0.2, 0.3),
    "mask_border_only":     (0.2, 0.3),
    "color_swap_1_2":       (0.1, 0.2),
    "color_gradient":       (0.5, 0.6),
    "color_invert":         (0.1, 0.1),  # already promoted
    "color_dominant":       (0.3, 0.4),
    "geom_scale_2x":        (0.5, 0.6),
    "geom_translate_center": (0.3, 0.4),
    "geom_flip_vertical":   (0.1, 0.2),
    "topo_merge_objects":   (0.5, 0.6),
    "topo_fill_holes":      (0.3, 0.4),
    "topo_split_at_gap":    (0.6, 0.7),
    "rel_align_centroids":  (0.4, 0.5),
    "rel_swap_positions":   (0.5, 0.6),
    "rel_order_by_size":    (0.6, 0.7),
    "constr_draw_rect_around": (0.2, 0.3),
    "constr_extend_pattern":   (0.5, 0.6),
    "constr_connect_line":     (0.4, 0.5),
    "constr_copy_to_pos":      (0.3, 0.4),
    "pat_row_alternate":      (0.2, 0.3),
    "pat_block_repeat":       (0.4, 0.5),
    "pat_color_cycle":        (0.4, 0.5),
    "cond_if_holes_fill":     (0.4, 0.5),
    "cond_if_multi_count":    (0.5, 0.6),
    "cond_if_edge_clip":      (0.3, 0.4),
}


def _estimate_promotion_difficulty(oracle_complexity: float, solver_complexity: float) -> float:
    """Estimate overall promotion pipeline difficulty (0.0 = trivial, 1.0 = very hard)."""
    # Average of oracle and solver complexity, with a small bump for testing/anti-cheat overhead
    base = (oracle_complexity + solver_complexity) / 2.0
    overhead = 0.1  # anti-cheat + regression testing overhead
    return min(1.0, base + overhead)


# ---------------------------------------------------------------------------
# Task-space expansion value
# ---------------------------------------------------------------------------

# Families already represented in BH80/promoted primitives
EXISTING_FAMILIES_REPRESENTED: Set[str] = {
    "extraction", "geometric", "color", "counting", "noise_removal",
    "positioning", "boundary", "cropping", "pattern", "fill",
}

# Which families each candidate introduces
CANDIDATE_FAMILY_NOVELTY: Dict[str, bool] = {
    # object_selector: introduces object selection by property — new family
    "sel_leftmost": True, "sel_topmost": True, "sel_smallest": True,
    "sel_most_holes": True, "sel_edge_touch": True,
    # mask_algebra: introduces mask operations — new family
    "mask_union": True, "mask_intersect": True, "mask_complement": True, "mask_border_only": True,
    # color_transform: color space operations — partially new (recolor exists)
    "color_swap_1_2": False, "color_gradient": True, "color_invert": False, "color_dominant": False,
    # geometry_transform: geometric — partially overlaps with rotate/transform/crop
    "geom_scale_2x": True, "geom_translate_center": False, "geom_flip_vertical": False,
    # topology_transform: topology changes — new family
    "topo_merge_objects": True, "topo_fill_holes": True, "topo_split_at_gap": True,
    # relation_transform: multi-object relations — new family
    "rel_align_centroids": True, "rel_swap_positions": True, "rel_order_by_size": True,
    # construction_transform: drawing/constructing — new family
    "constr_draw_rect_around": True, "constr_extend_pattern": True,
    "constr_connect_line": True, "constr_copy_to_pos": True,
    # pattern_transform: pattern generation — partially overlaps with pattern_output
    "pat_row_alternate": False, "pat_block_repeat": True, "pat_color_cycle": True,
    # conditional_transform: conditional execution — new family
    "cond_if_holes_fill": True, "cond_if_multi_count": True, "cond_if_edge_clip": True,
}


def _compute_task_space_value(primitive_id: str, is_new_family: bool) -> Tuple[float, int]:
    """Compute task-space expansion value and expected denominator gain.

    Returns (task_space_value 0.0-1.0, expected_new_scored_tasks).
    """
    if primitive_id in PROMOTED_PRIMITIVES:
        return 0.0, 0  # already promoted, no new tasks

    # New families add more task variety
    family_bonus = 0.3 if is_new_family else 0.0

    # Base value from having a probe task (proven composable)
    probe_bonus = 0.2 if primitive_id in CANDIDATE_PROBE_TASKS else 0.0

    # Base value from being Grid→Grid (most composable)
    base = 0.4 + family_bonus + probe_bonus

    # Expected new scored tasks: if promoted, the probe task becomes scored
    # plus potential new tasks in 3-step chains
    expected_gain = 10 if primitive_id in CANDIDATE_PROBE_TASKS else 5

    return min(1.0, base), expected_gain


# ---------------------------------------------------------------------------
# Regression risk assessment
# ---------------------------------------------------------------------------

def _compute_regression_risk(primitive_id: str, duplicate_risk: float) -> float:
    """Compute regression risk (0.0 = safe, 1.0 = high risk to BH80/120)."""
    if primitive_id in PROMOTED_PRIMITIVES:
        return 0.0  # already promoted, no regression risk

    # High duplicate risk means higher regression risk (could shadow existing primitive)
    reg = duplicate_risk * 0.5

    # Candidates that modify grid dimensions add structural risk
    dimension_changers = {"geom_scale_2x", "topo_split_at_gap", "constr_extend_pattern"}
    if primitive_id in dimension_changers:
        reg += 0.2

    # Candidates that affect object connectivity add risk
    connectivity_changers = {"topo_merge_objects", "topo_split_at_gap", "rel_swap_positions"}
    if primitive_id in connectivity_changers:
        reg += 0.1

    return min(1.0, reg)


# ---------------------------------------------------------------------------
# Recommendation engine
# ---------------------------------------------------------------------------

def _make_recommendation(
    primitive_id: str,
    total_score: float,
    evidence: EvidenceFeatures,
) -> Tuple[str, List[str]]:
    """Produce a recommendation and reason codes for a candidate.

    Returns (recommendation, reason_codes).
    recommendation is one of: "promote_now", "defer", "discard"
    """
    reasons: List[str] = []

    if evidence.is_promoted:
        return "already_promoted", ["already_promoted", "color_invert is fully promoted"]

    # Discard conditions
    if evidence.shortcut_risk > 0.7:
        reasons.append("high_shortcut_risk")
    if evidence.duplicate_risk > 0.7:
        reasons.append("high_duplicate_risk_near_existing_primitive")
    if evidence.task_space_value < 0.3:
        reasons.append("low_task_space_value")

    if reasons and total_score < 0.5:
        return "discard", reasons

    # Defer conditions
    if evidence.promotion_difficulty > 0.6:
        reasons.append("high_promotion_difficulty")
    if evidence.regression_risk > 0.5:
        reasons.append("high_regression_risk")
    if not evidence.has_probe_task:
        reasons.append("no_probe_task_yet")

    if reasons and total_score < 0.65:
        return "defer", reasons

    # Promote now conditions
    reasons_pos: List[str] = []
    if evidence.has_probe_task:
        reasons_pos.append("has_probe_task_in_120_suite")
    if evidence.task_space_value > 0.6:
        reasons_pos.append(f"high_task_space_value={evidence.task_space_value:.2f}")
    if evidence.promotion_difficulty < 0.4:
        reasons_pos.append(f"low_promotion_difficulty={evidence.promotion_difficulty:.2f}")
    if evidence.new_family:
        reasons_pos.append("introduces_new_transform_family")
    if evidence.duplicate_risk < 0.5:
        reasons_pos.append(f"low_duplicate_risk={evidence.duplicate_risk:.2f}")
    if evidence.regression_risk < 0.3:
        reasons_pos.append(f"low_regression_risk={evidence.regression_risk:.2f}")
    if evidence.oracle_complexity < 0.3:
        reasons_pos.append(f"simple_oracle_impl={evidence.oracle_complexity:.2f}")

    all_reasons = reasons + reasons_pos
    if not all_reasons:
        all_reasons.append("neutral_candidate")

    if total_score >= 0.65 and evidence.promotion_difficulty < 0.5:
        return "promote_now", all_reasons

    if total_score >= 0.55:
        return "defer", all_reasons + ["borderline_score_defer_for_now"]

    return "discard", all_reasons + ["low_score"]


# ---------------------------------------------------------------------------
# Main ranking function
# ---------------------------------------------------------------------------

def compute_evidence_driven_ranking() -> List[EvidenceDrivenScore]:
    """Compute evidence-driven perspicuity ranking for all candidates.

    Returns a list of EvidenceDrivenScore sorted by total score (descending).
    Deterministic: same input always produces same output.
    """
    candidates, families, static_scores = generate_candidates()

    # Build family lookup
    candidate_to_family: Dict[str, str] = {}
    for fam in families:
        for c in fam.candidates:
            candidate_to_family[c.primitive_id] = fam.family_id

    # Build human summary lookup
    candidate_to_summary: Dict[str, str] = {}
    for c in candidates:
        candidate_to_summary[c.primitive_id] = c.human_summary or "(no summary)"

    results: List[EvidenceDrivenScore] = []

    for c in candidates:
        pid = c.primitive_id
        family = candidate_to_family.get(pid, "unknown")
        summary = candidate_to_summary.get(pid, "(no summary)")
        static = static_scores[pid]

        is_promoted = pid in PROMOTED_PRIMITIVES
        has_probe = pid in CANDIDATE_PROBE_TASKS
        probe_info = CANDIDATE_PROBE_TASKS.get(pid, {})
        probe_task_id = probe_info.get("task_id") if has_probe else None
        probe_chain = probe_info.get("chain") if has_probe else None

        # Complexity estimates
        oracle_cx, solver_cx = COMPLEXITY_ESTIMATES.get(pid, (0.5, 0.5))
        promo_diff = _estimate_promotion_difficulty(oracle_cx, solver_cx)

        # Task-space value
        is_new_family = CANDIDATE_FAMILY_NOVELTY.get(pid, False)
        ts_value, exp_gain = _compute_task_space_value(pid, is_new_family)

        # Risk
        dup_risk = _compute_duplicate_risk(pid)
        reg_risk = _compute_regression_risk(pid, dup_risk)
        shortcut = static.shortcut_risk

        # Build evidence features
        evidence = EvidenceFeatures(
            static_perspicuity=static.total,
            has_probe_task=has_probe,
            probe_task_id=probe_task_id,
            probe_chain=probe_chain,
            oracle_complexity=oracle_cx,
            solver_complexity=solver_cx,
            promotion_difficulty=promo_diff,
            task_space_value=ts_value,
            new_family=is_new_family,
            expected_denominator_gain=exp_gain,
            duplicate_risk=dup_risk,
            regression_risk=reg_risk,
            shortcut_risk=shortcut,
            is_promoted=is_promoted,
            recommendation="",  # filled below
            reason_codes=[],     # filled below
        )

        # Build score
        score = EvidenceDrivenScore(
            primitive_id=pid,
            family=family,
            human_summary=summary,
            static_score=static,
            evidence=evidence,
        )

        # Make recommendation
        rec, reasons = _make_recommendation(pid, score.total, evidence)
        evidence.recommendation = rec
        evidence.reason_codes = reasons

        results.append(score)

    # Sort by total score descending (deterministic)
    results.sort(key=lambda s: (-s.total, s.primitive_id))
    return results


def get_top_n_recommendations(n: int = 10) -> List[Dict[str, Any]]:
    """Return top-N promotion recommendations as serializable dicts."""
    rankings = compute_evidence_driven_ranking()
    top = [r for r in rankings if not r.evidence.is_promoted][:n]
    return [
        {
            "rank": i + 1,
            "primitive_id": r.primitive_id,
            "family": r.family,
            "human_summary": r.human_summary,
            "total_score": round(r.total, 4),
            "recommendation": r.evidence.recommendation,
            "reason_codes": r.evidence.reason_codes,
            "risk_flags": {
                "duplicate_risk": round(r.evidence.duplicate_risk, 2),
                "regression_risk": round(r.evidence.regression_risk, 2),
                "shortcut_risk": round(r.evidence.shortcut_risk, 2),
            },
            "promotion_difficulty": round(r.evidence.promotion_difficulty, 2),
            "oracle_complexity": round(r.evidence.oracle_complexity, 2),
            "solver_complexity": round(r.evidence.solver_complexity, 2),
            "task_space_value": round(r.evidence.task_space_value, 2),
            "new_family": r.evidence.new_family,
            "expected_denominator_gain": r.evidence.expected_denominator_gain,
            "has_probe_task": r.evidence.has_probe_task,
            "probe_task_id": r.evidence.probe_task_id,
            "probe_chain": r.evidence.probe_chain,
        }
        for i, r in enumerate(top)
    ]


def get_batch_2_reassessment() -> Dict[str, Any]:
    """Reassess the proposed Batch 2 candidates with evidence-driven ranking.

    Returns a dict with the reassessment results.
    """
    original_batch_2 = ["mask_border_only", "geom_flip_vertical", "topo_fill_holes", "constr_draw_rect_around"]
    rankings = compute_evidence_driven_ranking()

    # Find original batch 2 in rankings
    original_assessment: Dict[str, Dict[str, Any]] = {}
    for r in rankings:
        if r.primitive_id in original_batch_2:
            original_assessment[r.primitive_id] = {
                "rank": next(i for i, rr in enumerate(rankings) if rr.primitive_id == r.primitive_id) + 1,
                "total_score": round(r.total, 4),
                "recommendation": r.evidence.recommendation,
                "reason_codes": r.evidence.reason_codes,
                "oracle_complexity": round(r.evidence.oracle_complexity, 2),
                "solver_complexity": round(r.evidence.solver_complexity, 2),
                "promotion_difficulty": round(r.evidence.promotion_difficulty, 2),
                "task_space_value": round(r.evidence.task_space_value, 2),
                "duplicate_risk": round(r.evidence.duplicate_risk, 2),
                "regression_risk": round(r.evidence.regression_risk, 2),
            }

    # Find top 4 promote_now candidates
    promote_now = [
        r for r in rankings
        if r.evidence.recommendation == "promote_now" and not r.evidence.is_promoted
    ][:4]

    recommended_batch: List[Dict[str, Any]] = []
    for r in promote_now:
        recommended_batch.append({
            "primitive_id": r.primitive_id,
            "family": r.family,
            "total_score": round(r.total, 4),
            "reason_codes": r.evidence.reason_codes,
            "oracle_complexity": round(r.evidence.oracle_complexity, 2),
            "solver_complexity": round(r.evidence.solver_complexity, 2),
        })

    # Determine if original batch should be revised
    original_in_top4 = all(
        any(r.primitive_id == pid for r in promote_now[:4])
        for pid in original_batch_2
    )

    return {
        "original_batch_2": original_batch_2,
        "original_assessment": original_assessment,
        "recommended_batch_2": recommended_batch,
        "original_in_top4": original_in_top4,
        "revision_needed": not original_in_top4,
        "all_rankings_count": len(rankings),
    }


def get_ranking_summary() -> Dict[str, Any]:
    """Return a summary of the full ranking."""
    rankings = compute_evidence_driven_ranking()
    return {
        "total_candidates": len(rankings),
        "promoted": sum(1 for r in rankings if r.evidence.is_promoted),
        "promote_now": sum(1 for r in rankings if r.evidence.recommendation == "promote_now"),
        "defer": sum(1 for r in rankings if r.evidence.recommendation == "defer"),
        "discard": sum(1 for r in rankings if r.evidence.recommendation == "discard"),
        "already_promoted": sum(1 for r in rankings if r.evidence.recommendation == "already_promoted"),
        "candidates_with_probes": sum(1 for r in rankings if r.evidence.has_probe_task),
        "new_family_candidates": sum(1 for r in rankings if r.evidence.new_family),
    }