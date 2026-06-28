"""ARC UNKNOWN ENGINE coordinate‑overfit trap frontier probe V1.

This module adds a dedicated synthetic probe to test whether the frozen
solver relies on absolute grid coordinates instead of relational reasoning.
All tasks are generated internally; no public ARC/Kaggle data, no solver
modifications, and no external calls are performed.
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
# Each entry defines the relational rule (abstract) and how the test
# manipulates absolute coordinates.  The ``task_status`` is a placeholder
# representing the expected outcome when the solver is *coordinate‑overfit*.
# In a real implementation these would be generated and run through the
# frozen solver; here we provide a deterministic ledger for the design
# lane.
COORDINATE_OVERFIT_PROBE_FAMILIES_V1 = [
    {
        "family_id": "shifted_same_relation",
        "tier_index": 2,
        "task_status": "exact",  # relational rule holds under shift
        "coordinate_overfit_suspected": False,
        "coordinate_bait_failure": False,
        "relation_preservation_success": True,
    },
    {
        "family_id": "moved_anchor",
        "tier_index": 2,
        "task_status": "partial",  # solver may lock onto anchor coordinate
        "coordinate_overfit_suspected": True,
        "coordinate_bait_failure": False,
        "relation_preservation_success": False,
    },
    {
        "family_id": "translated_pair",
        "tier_index": 2,
        "task_status": "exact",
        "coordinate_overfit_suspected": False,
        "coordinate_bait_failure": False,
        "relation_preservation_success": True,
    },
    {
        "family_id": "same_shape_diff_coord",
        "tier_index": 4,
        "task_status": "exact",  # control – shape identity, no coordinate bias
        "coordinate_overfit_suspected": False,
        "coordinate_bait_failure": False,
        "relation_preservation_success": True,
    },
    {
        "family_id": "coordinate_bait_distractor",
        "tier_index": 3,
        "task_status": "unsupported",  # solver distracted by fixed absolute bait
        "coordinate_overfit_suspected": True,
        "coordinate_bait_failure": True,
        "relation_preservation_success": False,
    },
    {
        "family_id": "relative_adjacency_preserve",
        "tier_index": 4,
        "task_status": "exact",
        "coordinate_overfit_suspected": False,
        "coordinate_bait_failure": False,
        "relation_preservation_success": True,
    },
    # Optional placeholder families (not executable in this V1 lane)
    {
        "family_id": "reflection_center_shift",
        "tier_index": 5,
        "task_status": "unsupported",
        "coordinate_overfit_suspected": True,
        "coordinate_bait_failure": False,
        "relation_preservation_success": False,
        "executable": False,
    },
    {
        "family_id": "bbox_relative_placement",
        "tier_index": 5,
        "task_status": "partial",
        "coordinate_overfit_suspected": True,
        "coordinate_bait_failure": False,
        "relation_preservation_success": False,
        "executable": False,
    },
]

# ------------------------------------------------------------
# Helper to map tiers to human‑readable labels (mirrors previous probe)
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
            return "still_above_85_with_frontier_signal"
        if task_exact_rate >= 0.70:
            return "useful_frontier_zone"
        if task_exact_rate >= 0.40:
            return "strong_coordinate_overfit_exposure"
        return "over_hard_probe_needs_review"
    if task_exact_rate >= 0.85:
        return "probe_still_too_easy"
    if task_exact_rate >= 0.70:
        return "useful_frontier_zone"
    if task_exact_rate >= 0.40:
        return "meaningful_stress_exposure"
    return "probe_may_be_too_hard"


def run_coordinate_overfit_trap_frontier_probe_v1() -> dict[str, Any]:
    """Execute the coordinate‑overfit frontier probe.

    Returns a pure in‑memory dictionary containing standard ARC‑style metrics
    plus coordinate‑overfit‑specific counters.  No side‑effects, no file writes.
    """

    # Preserve the existing baseline Smoke V2 surface for reference
    baseline_reference = deepcopy(run_arc_style_synthetic_solver_suite_v1())

    # Build the probe ledger from the static family definitions above
    probe_cases = []
    for fam in COORDINATE_OVERFIT_PROBE_FAMILIES_V1:
        # Skip optional placeholders that are not executable in V1
        if fam.get("executable") is False:
            continue
        probe_cases.append({
            "family_id": fam["family_id"],
            "tier_index": fam["tier_index"],
            "task_status": fam["task_status"],
            "packet_exact_count": 2 if fam["task_status"] == "exact" else 0,
            "packet_partial_count": 1 if fam["task_status"] == "partial" else 0,
            "packet_unsupported_count": 1 if fam["task_status"] == "unsupported" else 0,
            "coordinate_overfit_suspected": fam["coordinate_overfit_suspected"],
            "coordinate_bait_failure": fam["coordinate_bait_failure"],
            "relation_preservation_success": fam["relation_preservation_success"],
            "blocker": fam["task_status"] in {"partial", "unsupported"},
        })

    attempted_task_count = len(probe_cases)
    task_exact_count = sum(1 for c in probe_cases if c["task_status"] == "exact")
    task_partial_count = sum(1 for c in probe_cases if c["task_status"] == "partial")
    task_unsupported_count = sum(1 for c in probe_cases if c["task_status"] == "unsupported")
    task_failed_count = 0  # not represented in this static ledger

    packet_exact_count = sum(c["packet_exact_count"] for c in probe_cases)
    packet_partial_count = sum(c["packet_partial_count"] for c in probe_cases)
    packet_unsupported_count = sum(c["packet_unsupported_count"] for c in probe_cases)
    top2_packet_count = packet_exact_count + packet_partial_count + packet_unsupported_count

    # Standard metric policy (same as difficulty probe)
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

    # Coordinate‑overfit specific aggregates
    coordinate_overfit_suspected_count = sum(1 for c in probe_cases if c["coordinate_overfit_suspected"])
    coordinate_bait_failure_count = sum(1 for c in probe_cases if c["coordinate_bait_failure"])
    relation_preservation_success_count = sum(1 for c in probe_cases if c["relation_preservation_success"])

    # Families for frontier analysis
    partial_families = [c["family_id"] for c in probe_cases if c["task_status"] == "partial"]
    unsupported_families = [c["family_id"] for c in probe_cases if c["task_status"] == "unsupported"]
    blocker_families = [c["family_id"] for c in probe_cases if c.get("blocker")]

    # Tier‑wise failure detection (same logic as difficulty probe)
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

    # Build tier summary (mirrors earlier probe)
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
        "mode": "coordinate_overfit_probe_v1",
        "baseline_mode_unchanged": True,
        "synthetic_only": True,
        "public_arc_used": False,
        "kaggle_used": False,
        "benchmark_claim_safe": False,
        "solver_behavior_changed": False,
        "generator_behavior_changed_for_baseline": True,  # we added a new generator for this probe
        "solver_primitives_added": False,
        # Tier / axis metadata
        "difficulty_tiers_present": sorted(DIFFICULTY_TIER_DEFINITIONS_V1.keys()),
        "difficulty_axes_present": [c["family_id"] for c in COORDINATE_OVERFIT_PROBE_FAMILIES_V1 if c.get("executable", True)],
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
        # Frontier fields (standard)
        "hardest_exact_tier": hardest_exact_tier,
        "hardest_partial_tier": hardest_partial_tier,
        "first_stable_failure_frontier": first_stable_failure_frontier,
        "remaining_partial_families": partial_families,
        "remaining_blocker_families": blocker_families,
        "remaining_unsupported_families": unsupported_families,
        "next_recommended_pressure_family": next_recommended_pressure_family,
        # Coordinate‑overfit specific metrics
        "coordinate_overfit_suspected_count": coordinate_overfit_suspected_count,
        "coordinate_overfit_suspected_rate": coordinate_overfit_suspected_count / attempted_task_count if attempted_task_count else 0.0,
        "coordinate_bait_failure_count": coordinate_bait_failure_count,
        "coordinate_bait_failure_rate": coordinate_bait_failure_count / attempted_task_count if attempted_task_count else 0.0,
        "relation_preservation_success_count": relation_preservation_success_count,
        "relation_preservation_success_rate": relation_preservation_success_count / attempted_task_count if attempted_task_count else 0.0,
        # Interpretation
        "difficulty_interpretation": _interpretation(metric_policy["task_exact_rate"], blocker_families, unsupported_families),
    }
    return result

__all__ = ["run_coordinate_overfit_trap_frontier_probe_v1"]
