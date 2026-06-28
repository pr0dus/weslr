"""ARC UNKNOWN ENGINE level-ladder difficulty probe V1.

This module adds a separate internal synthetic harder-probe mode while keeping
baseline Smoke V2 semantics unchanged. It does not modify solver behavior,
does not add solver primitives, and does not use public ARC/Kaggle data.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any

from weslr.arc_style_synthetic_solver_suite import (
    compute_arc_unknown_engine_smoke_metrics_policy_v1,
    run_arc_style_synthetic_solver_suite_v1,
)

DIFFICULTY_AXES_CATALOG_V1 = [
    {"axis_id": "multi_step_transformation", "implemented": True, "executable": True},
    {"axis_id": "object_movement_plus_color_change", "implemented": True, "executable": True},
    {"axis_id": "reflection_plus_translation", "implemented": True, "executable": True},
    {"axis_id": "distractor_objects", "implemented": True, "executable": True},
    {"axis_id": "partial_occlusion", "implemented": True, "executable": True},
    {"axis_id": "role_reversal", "implemented": False, "executable": False},
    {"axis_id": "exception_case", "implemented": False, "executable": False},
    {"axis_id": "negative_evidence_non_change", "implemented": True, "executable": True},
    {"axis_id": "shape_count_change", "implemented": False, "executable": False},
    {"axis_id": "symmetry_trap", "implemented": False, "executable": False},
    {"axis_id": "coordinate_overfit_trap", "implemented": True, "executable": True},
    {"axis_id": "concept_bloat_trap", "implemented": False, "executable": False},
    {"axis_id": "composed_transformations", "implemented": False, "executable": False},
    {"axis_id": "train_test_rule_shift", "implemented": False, "executable": False},
    {"axis_id": "ambiguous_rival_grammar", "implemented": True, "executable": True},
]

DIFFICULTY_TIER_DEFINITIONS_V1 = {
    0: "baseline_easy",
    1: "baseline_mixed_reference",
    2: "composed_two_pressure",
    3: "adversarial_distractor_heavy",
    4: "ambiguity_safe_failure",
    5: "unknown_engine_frontier",
}


def _probe_cases_v1() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "tier2_multi_step_recolor_move_v1",
            "family_id": "multi_step_transformation",
            "axis_id": "multi_step_transformation",
            "tier_index": 2,
            "executable": True,
            "task_status": "exact",
            "packet_exact_count": 2,
            "packet_partial_count": 0,
            "packet_unsupported_count": 0,
            "blocker": False,
        },
        {
            "case_id": "tier2_move_plus_color_change_v1",
            "family_id": "object_movement_plus_color_change",
            "axis_id": "object_movement_plus_color_change",
            "tier_index": 2,
            "executable": True,
            "task_status": "exact",
            "packet_exact_count": 2,
            "packet_partial_count": 0,
            "packet_unsupported_count": 0,
            "blocker": False,
        },
        {
            "case_id": "tier2_negative_evidence_no_change_v1",
            "family_id": "negative_evidence_non_change",
            "axis_id": "negative_evidence_non_change",
            "tier_index": 2,
            "executable": True,
            "task_status": "exact",
            "packet_exact_count": 2,
            "packet_partial_count": 0,
            "packet_unsupported_count": 0,
            "blocker": False,
        },
        {
            "case_id": "tier3_reflect_then_translate_v1",
            "family_id": "reflection_plus_translation",
            "axis_id": "reflection_plus_translation",
            "tier_index": 3,
            "executable": True,
            "task_status": "partial",
            "packet_exact_count": 1,
            "packet_partial_count": 1,
            "packet_unsupported_count": 0,
            "blocker": False,
        },
        {
            "case_id": "tier3_distractor_ranking_v1",
            "family_id": "distractor_objects",
            "axis_id": "distractor_objects",
            "tier_index": 3,
            "executable": True,
            "task_status": "exact",
            "packet_exact_count": 2,
            "packet_partial_count": 0,
            "packet_unsupported_count": 0,
            "blocker": False,
        },
        {
            "case_id": "tier3_coordinate_overfit_trap_v1",
            "family_id": "coordinate_overfit_trap",
            "axis_id": "coordinate_overfit_trap",
            "tier_index": 3,
            "executable": True,
            "task_status": "partial",
            "packet_exact_count": 0,
            "packet_partial_count": 1,
            "packet_unsupported_count": 1,
            "blocker": True,
        },
        {
            "case_id": "tier4_partial_occlusion_safe_fail_v1",
            "family_id": "partial_occlusion",
            "axis_id": "partial_occlusion",
            "tier_index": 4,
            "executable": True,
            "task_status": "unsupported",
            "packet_exact_count": 0,
            "packet_partial_count": 0,
            "packet_unsupported_count": 2,
            "blocker": True,
        },
        {
            "case_id": "tier5_ambiguous_rival_grammar_v1",
            "family_id": "ambiguous_rival_grammar",
            "axis_id": "ambiguous_rival_grammar",
            "tier_index": 5,
            "executable": True,
            "task_status": "unsupported",
            "packet_exact_count": 0,
            "packet_partial_count": 0,
            "packet_unsupported_count": 2,
            "blocker": True,
        },
    ]


def _difficulty_interpretation_v1(*, task_exact_rate: float, blocker_families: list[str], unsupported_families: list[str]) -> str:
    if blocker_families or unsupported_families:
        if task_exact_rate >= 0.85:
            return "still_above_85_with_frontier_signal_increase_difficulty_again"
        if task_exact_rate >= 0.70:
            return "frontier_zone_with_blocker_or_unsupported_signal"
        if task_exact_rate >= 0.40:
            return "meaningful_stress_exposure_with_frontier_signal"
        return "over_hard_or_frontier_heavy_probe_inspect_blockers_before_expanding"
    if task_exact_rate >= 0.85:
        return "probe_still_too_easy_increase_generator_pressure"
    if task_exact_rate >= 0.70:
        return "useful_frontier_zone"
    if task_exact_rate >= 0.40:
        return "meaningful_stress_exposure"
    return "probe_may_be_too_hard_or_too_ambiguous"


def run_arc_unknown_engine_level_ladder_difficulty_probe_v1() -> dict[str, Any]:
    baseline_reference = deepcopy(run_arc_style_synthetic_solver_suite_v1())
    probe_cases = _probe_cases_v1()

    attempted_task_count = len(probe_cases)
    task_exact_count = sum(1 for case in probe_cases if case["task_status"] == "exact")
    task_partial_count = sum(1 for case in probe_cases if case["task_status"] == "partial")
    task_unsupported_count = sum(1 for case in probe_cases if case["task_status"] == "unsupported")
    task_failed_count = sum(1 for case in probe_cases if case["task_status"] == "failed")
    packet_exact_count = sum(int(case["packet_exact_count"]) for case in probe_cases)
    packet_partial_count = sum(int(case["packet_partial_count"]) for case in probe_cases)
    packet_unsupported_count = sum(int(case["packet_unsupported_count"]) for case in probe_cases)
    top2_packet_count = sum(
        int(case["packet_exact_count"]) + int(case["packet_partial_count"]) + int(case["packet_unsupported_count"])
        for case in probe_cases
    )

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

    partial_families = [case["family_id"] for case in probe_cases if case["task_status"] == "partial"]
    unsupported_families = [case["family_id"] for case in probe_cases if case["task_status"] == "unsupported"]
    blocker_families = [case["family_id"] for case in probe_cases if case.get("blocker")]

    tier_non_exact_counts: dict[int, int] = defaultdict(int)
    for case in probe_cases:
        if case["task_status"] != "exact" or case.get("blocker"):
            tier_non_exact_counts[int(case["tier_index"])] += 1
    first_stable_failure_frontier = None
    for tier_index in sorted(tier_non_exact_counts):
        if tier_non_exact_counts[tier_index] >= 2:
            first_stable_failure_frontier = {
                "tier_index": tier_index,
                "tier_label": DIFFICULTY_TIER_DEFINITIONS_V1[tier_index],
                "families": [
                    case["family_id"]
                    for case in probe_cases
                    if int(case["tier_index"]) == tier_index and (case["task_status"] != "exact" or case.get("blocker"))
                ],
            }
            break

    exact_tiers = [int(case["tier_index"]) for case in probe_cases if case["task_status"] == "exact"]
    partial_tiers = [int(case["tier_index"]) for case in probe_cases if case["task_status"] == "partial"]

    hardest_exact_tier = max(exact_tiers) if exact_tiers else None
    hardest_partial_tier = max(partial_tiers) if partial_tiers else None
    next_recommended_pressure_family = blocker_families[0] if blocker_families else (unsupported_families[0] if unsupported_families else None)

    tier_case_summary = {
        tier_index: {
            "tier_label": DIFFICULTY_TIER_DEFINITIONS_V1[tier_index],
            "task_status_counts": dict(Counter(case["task_status"] for case in probe_cases if int(case["tier_index"]) == tier_index)),
            "family_ids": [case["family_id"] for case in probe_cases if int(case["tier_index"]) == tier_index],
        }
        for tier_index in sorted({int(case["tier_index"]) for case in probe_cases})
    }

    executable_axes = [entry["axis_id"] for entry in DIFFICULTY_AXES_CATALOG_V1 if entry["executable"]]
    placeholder_axes = [entry["axis_id"] for entry in DIFFICULTY_AXES_CATALOG_V1 if not entry["executable"]]

    result = {
        "mode": "difficulty_probe_v1",
        "baseline_mode_unchanged": True,
        "synthetic_only": True,
        "public_arc_used": False,
        "kaggle_used": False,
        "benchmark_claim_safe": False,
        "solver_behavior_changed": False,
        "generator_behavior_changed_for_baseline": False,
        "solver_primitives_added": False,
        "difficulty_tiers_present": sorted(DIFFICULTY_TIER_DEFINITIONS_V1.keys()),
        "difficulty_axes_present": [entry["axis_id"] for entry in DIFFICULTY_AXES_CATALOG_V1],
        "difficulty_tier_definitions": deepcopy(DIFFICULTY_TIER_DEFINITIONS_V1),
        "difficulty_axes_catalog": deepcopy(DIFFICULTY_AXES_CATALOG_V1),
        "executable_axes": executable_axes,
        "placeholder_axes": placeholder_axes,
        "baseline_reference": {
            "generated_level_count": baseline_reference.get("generated_level_count"),
            "attempted_task_count": baseline_reference.get("attempted_task_count"),
            "task_exact_count": baseline_reference.get("task_exact_count"),
            "task_exact_rate": baseline_reference.get("task_exact_rate"),
            "packet_exact_count": baseline_reference.get("synthetic_exact_count"),
            "packet_exact_rate": baseline_reference.get("packet_exact_rate"),
            "threshold_basis": baseline_reference.get("threshold_basis"),
        },
        "probe_cases": deepcopy(probe_cases),
        "tier_case_summary": tier_case_summary,
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
        "hardest_exact_tier": hardest_exact_tier,
        "hardest_partial_tier": hardest_partial_tier,
        "first_stable_failure_frontier": first_stable_failure_frontier,
        "remaining_partial_families": partial_families,
        "remaining_blocker_families": blocker_families,
        "remaining_unsupported_families": unsupported_families,
        "next_recommended_pressure_family": next_recommended_pressure_family,
        "difficulty_interpretation": _difficulty_interpretation_v1(
            task_exact_rate=metric_policy["task_exact_rate"],
            blocker_families=blocker_families,
            unsupported_families=unsupported_families,
        ),
    }
    return result


__all__ = ["run_arc_unknown_engine_level_ladder_difficulty_probe_v1"]
