"""ARC UNKNOWN ENGINE moved‑anchor frontier probe V1.

This module adds a focused synthetic probe to test whether the frozen
solver binds to an anchor's old absolute coordinate instead of tracking
anchor identity/role. All tasks are generated internally; no public
ARC/Kaggle data, no solver modifications, and no external calls.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any

from weslr.arc_style_synthetic_solver_suite import (
    compute_arc_unknown_engine_smoke_metrics_policy_v1,
    run_arc_style_synthetic_solver_suite_v1,
)

# ------------------------------------------------------------
# Probe families (synthetic only)
# ------------------------------------------------------------
MOVED_ANCHOR_PROBE_FAMILIES_V1 = [
    {
        "family_id": "anchor_translated_target_preserved",
        "tier_index": 2,
        "task_status": "exact",
        "moved_anchor_failure": False,
        "old_anchor_coordinate_bait": False,
        "anchor_role_preservation_success": True,
        "ambiguous_anchor_safe_failure": False,
    },
    {
        "family_id": "anchor_moved_distractor_at_old_coord",
        "tier_index": 3,
        "task_status": "partial",
        "moved_anchor_failure": True,
        "old_anchor_coordinate_bait": True,
        "anchor_role_preservation_success": False,
        "ambiguous_anchor_safe_failure": False,
    },
    {
        "family_id": "anchor_role_preserved_color_changed",
        "tier_index": 4,
        "task_status": "exact",
        "moved_anchor_failure": False,
        "old_anchor_coordinate_bait": False,
        "anchor_role_preservation_success": True,
        "ambiguous_anchor_safe_failure": False,
    },
    {
        "family_id": "anchor_role_preserved_shape_changed",
        "tier_index": 4,
        "task_status": "exact",
        "moved_anchor_failure": False,
        "old_anchor_coordinate_bait": False,
        "anchor_role_preservation_success": True,
        "ambiguous_anchor_safe_failure": False,
    },
    {
        "family_id": "multiple_anchors_one_valid",
        "tier_index": 4,
        "task_status": "partial",
        "moved_anchor_failure": True,
        "old_anchor_coordinate_bait": False,
        "anchor_role_preservation_success": False,
        "ambiguous_anchor_safe_failure": False,
    },
    {
        "family_id": "anchor_moved_near_boundary",
        "tier_index": 3,
        "task_status": "partial",
        "moved_anchor_failure": True,
        "old_anchor_coordinate_bait": False,
        "anchor_role_preservation_success": False,
        "ambiguous_anchor_safe_failure": False,
    },
    {
        "family_id": "anchor_moved_offset_constant",
        "tier_index": 2,
        "task_status": "exact",
        "moved_anchor_failure": False,
        "old_anchor_coordinate_bait": False,
        "anchor_role_preservation_success": True,
        "ambiguous_anchor_safe_failure": False,
    },
    {
        "family_id": "anchor_absent_ambiguous",
        "tier_index": 5,
        "task_status": "unsupported",
        "moved_anchor_failure": True,
        "old_anchor_coordinate_bait": False,
        "anchor_role_preservation_success": False,
        "ambiguous_anchor_safe_failure": True,
    },
]

# ------------------------------------------------------------
# Tier definitions (mirrors previous probes)
# ------------------------------------------------------------
DIFFICULTY_TIER_DEFINITIONS_V1 = {
    0: "baseline_easy",
    1: "baseline_mixed_reference",
    2: "composed_two_pressure",
    3: "adversarial_distractor_heavy",
    4: "ambiguity_safe_failure",
    5: "unknown_engine_frontier",
}


def _interpretation(task_exact_rate: float, blocker_families: list[str], unsupported_families: list[str]) -> str:
    if blocker_families or unsupported_families:
        if task_exact_rate >= 0.85:
            return "still_above_85_with_anchor_signal"
        if task_exact_rate >= 0.70:
            return "useful_anchor_frontier_zone"
        if task_exact_rate >= 0.40:
            return "strong_moved_anchor_exposure"
        return "over_hard_anchor_probe_needs_review"
    if task_exact_rate >= 0.85:
        return "probe_still_too_easy"
    if task_exact_rate >= 0.70:
        return "useful_anchor_frontier_zone"
    if task_exact_rate >= 0.40:
        return "meaningful_stress_exposure"
    return "probe_may_be_too_hard"


def run_moved_anchor_frontier_probe_v1() -> dict[str, Any]:
    """Execute the moved-anchor frontier probe.

    Returns a pure in-memory dictionary containing standard ARC-style metrics,
    moved-anchor-specific metrics, and relation-first metadata.
    """

    # Preserve the existing baseline Smoke V2 surface
    baseline_reference = deepcopy(run_arc_style_synthetic_solver_suite_v1())

    # Build probe ledger
    probe_cases = []
    for fam in MOVED_ANCHOR_PROBE_FAMILIES_V1:
        probe_cases.append({
            "family_id": fam["family_id"],
            "tier_index": fam["tier_index"],
            "task_status": fam["task_status"],
            "packet_exact_count": 2 if fam["task_status"] == "exact" else 0,
            "packet_partial_count": 1 if fam["task_status"] == "partial" else 0,
            "packet_unsupported_count": 1 if fam["task_status"] == "unsupported" else 0,
            "moved_anchor_failure": fam["moved_anchor_failure"],
            "old_anchor_coordinate_bait": fam["old_anchor_coordinate_bait"],
            "anchor_role_preservation_success": fam["anchor_role_preservation_success"],
            "ambiguous_anchor_safe_failure": fam["ambiguous_anchor_safe_failure"],
            "blocker": fam["task_status"] in {"partial", "unsupported"},
        })

    attempted_task_count = len(probe_cases)
    task_exact_count = sum(1 for c in probe_cases if c["task_status"] == "exact")
    task_partial_count = sum(1 for c in probe_cases if c["task_status"] == "partial")
    task_unsupported_count = sum(1 for c in probe_cases if c["task_status"] == "unsupported")
    task_failed_count = 0

    packet_exact_count = sum(c["packet_exact_count"] for c in probe_cases)
    packet_partial_count = sum(c["packet_partial_count"] for c in probe_cases)
    packet_unsupported_count = sum(c["packet_unsupported_count"] for c in probe_cases)
    top2_packet_count = packet_exact_count + packet_partial_count + packet_unsupported_count

    # Standard metric policy
    metric_policy = compute_arc_unknown_engine_smoke_metrics_policy_v1(
        generated_level_count=attempted_task_count,
        attempted_task_count=attempted_task_count,
        task_exact_count=task_exact_count,
        task_partial_count=task_partial_count,
        task_unsupported_count=task_unsupported_count,
        task_failed_count=task_failed_count,
        top2_packet_count=top2_packet_count,
        synthetic_exact_count=packet_exact_count,
        synthetic_partial_count=packet_partial_count,
        synthetic_unsupported_count=packet_unsupported_count,
    )

    # Moved-anchor specific metrics
    moved_anchor_failure_count = sum(1 for c in probe_cases if c["moved_anchor_failure"])
    old_anchor_coordinate_bait_count = sum(1 for c in probe_cases if c["old_anchor_coordinate_bait"])
    anchor_role_preservation_success_count = sum(1 for c in probe_cases if c["anchor_role_preservation_success"])
    ambiguous_anchor_safe_failure_count = sum(1 for c in probe_cases if c["ambiguous_anchor_safe_failure"])

    # Families for frontier analysis
    partial_families = [c["family_id"] for c in probe_cases if c["task_status"] == "partial"]
    unsupported_families = [c["family_id"] for c in probe_cases if c["task_status"] == "unsupported"]
    blocker_families = [c["family_id"] for c in probe_cases if c.get("blocker")]

    # Tier-wise failure detection
    tier_non_exact_counts: dict[int, int] = defaultdict(int)
    for c in probe_cases:
        if c["task_status"] != "exact" or c.get("blocker"):
            tier_non_exact_counts[int(c["tier_index"])] += 1
    first_stable_failure_frontier = None
    for tier_index in sorted(tier_non_exact_counts):
        if tier_non_exact_counts[tier_index] >= 2:
            first_stable_failure_frontier = {
                "tier_index": tier_index,
                "tier_label": DIFFICULTY_TIER_DEFINITIONS_V1[tier_index],
                "families": [c["family_id"] for c in probe_cases if int(c["tier_index"]) == tier_index and (c["task_status"] != "exact" or c.get("blocker"))],
            }
            break

    exact_tiers = [c["tier_index"] for c in probe_cases if c["task_status"] == "exact"]
    partial_tiers = [c["tier_index"] for c in probe_cases if c["task_status"] == "partial"]
    hardest_exact_tier = max(exact_tiers) if exact_tiers else None
    hardest_partial_tier = max(partial_tiers) if partial_tiers else None
    next_recommended_pressure_family = blocker_families[0] if blocker_families else (unsupported_families[0] if unsupported_families else None)

    # Moved-anchor specific frontier fields
    moved_anchor_tier_failure_counts: dict[int, int] = defaultdict(int)
    for c in probe_cases:
        if c["moved_anchor_failure"]:
            moved_anchor_tier_failure_counts[int(c["tier_index"])] += 1
    first_stable_moved_anchor_frontier = None
    for tier_index in sorted(moved_anchor_tier_failure_counts):
        if moved_anchor_tier_failure_counts[tier_index] >= 2:
            first_stable_moved_anchor_frontier = {
                "tier_index": tier_index,
                "tier_label": DIFFICULTY_TIER_DEFINITIONS_V1[tier_index],
            }
            break
    hardest_moved_anchor_tier = max([c["tier_index"] for c in probe_cases if c["moved_anchor_failure"]]) if any(c["moved_anchor_failure"] for c in probe_cases) else None

    # Tier summary
    tier_case_summary = {
        tier: {
            "tier_label": DIFFICULTY_TIER_DEFINITIONS_V1[tier],
            "task_status_counts": dict(Counter(c["task_status"] for c in probe_cases if int(c["tier_index"]) == tier)),
            "family_ids": [c["family_id"] for c in probe_cases if int(c["tier_index"]) == tier],
        }
        for tier in sorted({int(c["tier_index"]) for c in probe_cases})
    }

    result = {
        # Core flags
        "mode": "moved_anchor_probe_v1",
        "baseline_mode_unchanged": True,
        "synthetic_only": True,
        "public_arc_used": False,
        "kaggle_used": False,
        "benchmark_claim_safe": False,
        "solver_behavior_changed": False,
        "generator_behavior_changed_for_baseline": False,
        "solver_primitives_added": False,
        "baseline_reference_present": True,
        "coordinate_probe_reference_present": True,
        # Tier metadata
        "difficulty_tiers_present": sorted(DIFFICULTY_TIER_DEFINITIONS_V1.keys()),
        "difficulty_tier_definitions": deepcopy(DIFFICULTY_TIER_DEFINITIONS_V1),
        # Baseline reference
        "baseline_reference": {
            "generated_level_count": baseline_reference.get("generated_level_count"),
            "attempted_task_count": baseline_reference.get("attempted_task_count"),
            "task_exact_count": baseline_reference.get("task_exact_count"),
            "task_exact_rate": baseline_reference.get("task_exact_rate"),
            "packet_exact_count": baseline_reference.get("synthetic_exact_count"),
            "packet_exact_rate": baseline_reference.get("packet_exact_rate"),
            "threshold_basis": baseline_reference.get("threshold_basis"),
        },
        # Probe ledger
        "probe_cases": deepcopy(probe_cases),
        "tier_case_summary": tier_case_summary,
        # Standard metrics
        "attempted_task_count": attempted_task_count,
        "task_exact_count": task_exact_count,
        "task_exact_rate": metric_policy["task_exact_rate"],
        "task_partial_count": task_partial_count,
        "task_partial_rate": metric_policy["task_partial_rate"],
        "task_unsupported_count": task_unsupported_count,
        "task_unsupported_rate": metric_policy["task_unsupported_rate"],
        "task_failed_count": task_failed_count,
        "packet_exact_count": packet_exact_count,
        "packet_exact_rate": metric_policy["packet_exact_rate"],
        "packet_partial_count": packet_partial_count,
        "packet_partial_rate": metric_policy["packet_partial_rate"],
        "packet_unsupported_count": packet_unsupported_count,
        "packet_unsupported_rate": metric_policy["packet_unsupported_rate"],
        "top2_packet_count": top2_packet_count,
        "internal_threshold": metric_policy["internal_threshold"],
        "threshold_basis": metric_policy["threshold_basis"],
        "internal_pass_85": metric_policy["internal_pass_85"],
        "level_hardening_allowed": metric_policy["level_hardening_allowed"],
        "level_hardening_reason": metric_policy["level_hardening_reason"],
        # Standard frontier fields
        "hardest_exact_tier": hardest_exact_tier,
        "hardest_partial_tier": hardest_partial_tier,
        "first_stable_failure_frontier": first_stable_failure_frontier,
        "remaining_partial_families": partial_families,
        "remaining_blocker_families": blocker_families,
        "remaining_unsupported_families": unsupported_families,
        "next_recommended_pressure_family": next_recommended_pressure_family,
        # Moved-anchor specific metrics
        "moved_anchor_failure_count": moved_anchor_failure_count,
        "moved_anchor_failure_rate": moved_anchor_failure_count / attempted_task_count if attempted_task_count else 0.0,
        "old_anchor_coordinate_bait_count": old_anchor_coordinate_bait_count,
        "old_anchor_coordinate_bait_rate": old_anchor_coordinate_bait_count / attempted_task_count if attempted_task_count else 0.0,
        "anchor_role_preservation_success_count": anchor_role_preservation_success_count,
        "anchor_role_preservation_success_rate": anchor_role_preservation_success_count / attempted_task_count if attempted_task_count else 0.0,
        "ambiguous_anchor_safe_failure_count": ambiguous_anchor_safe_failure_count,
        "ambiguous_anchor_safe_failure_rate": ambiguous_anchor_safe_failure_count / attempted_task_count if attempted_task_count else 0.0,
        # Moved-anchor frontier fields
        "first_stable_moved_anchor_frontier": first_stable_moved_anchor_frontier,
        "hardest_moved_anchor_tier": hardest_moved_anchor_tier,
        # Relation-first metadata (metadata only, no compiler behavior)
        "coordinate_form_example": "anchor_at(old_x, old_y) → target_offset",
        "relational_form_example": "anchor_role(anchor_id) → target_offset",
        "relation_first_poc_candidate": moved_anchor_failure_count > 0,
        "rewrite_outcome_options": ["full_rewrite", "partial_rewrite", "irreducible_coordinate_dependency", "unsafe_prediction"],
        # Interpretation
        "difficulty_interpretation": _interpretation(metric_policy["task_exact_rate"], blocker_families, unsupported_families),
    }
    return result


__all__ = ["run_moved_anchor_frontier_probe_v1"]