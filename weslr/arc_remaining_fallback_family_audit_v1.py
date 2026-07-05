"""ARC-AGI-2 remaining fallback family audit V1.

Audit-only module that classifies every unsolved/fallback family in the
synthetic benchmark as either a correct adversarial rejection or a real
solver gap.  No solver repair, no benchmark changes, no public ARC data.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

ADVERSARIAL_FAMILIES_V1: frozenset[str] = frozenset({
    "inconsistent_train_examples",
    "ambiguous_multiple_rules",
    "unsupported_primitive_chain",
    "near_match_one_cell",
    "same_palette_wrong_geometry",
    "same_geometry_wrong_recolor",
    "count_tie_ambiguity",
})

NORMAL_FAMILIES_V1: frozenset[str] = frozenset({
    "add_uniform_border",
    "count_objects_to_line",
    "crop_foreground_bbox",
    "crop_largest_object",
    "object_count_to_square",
    "recolor_foreground",
    "reflect_object_horizontal",
    "reflect_object_vertical",
    "rotate_object_180",
    "rotate_object_90",
    "scale_cells_integer",
    "select_largest_object",
    "swap_two_colors",
    "tile_grid",
    "translate_single_object",
    "crop_then_recolor",
    "crop_then_rotate_or_reflect",
    "crop_then_tile",
    "recolor_then_border",
    "select_then_recolor",
})


def is_adversarial(family_label: str) -> bool:
    return family_label in ADVERSARIAL_FAMILIES_V1


def is_normal(family_label: str) -> bool:
    return family_label in NORMAL_FAMILIES_V1


def classify_unsolved_family(
    family_label: str,
    *,
    generated: int = 0,
    solved: int = 0,
    unsolved: int = 0,
    fallback_only: int = 0,
    malformed: int = 0,
    exception: int = 0,
    failure_category: str | None = None,
    selected_families: list[str] | None = None,
) -> dict[str, Any]:
    """Classify a single family's unsolved status."""
    is_adv = is_adversarial(family_label)
    is_norm = is_normal(family_label)

    if is_adv:
        classification = "correct_adversarial_rejection"
        expected_unsolved = True
        repair_priority = "correct_rejection_not_failure"
        likely_layer = "correct_adversarial_rejection"
        dominant_issue = "adversarial task correctly rejected"
    elif is_norm:
        classification = "unexpected_normal_family_failure"
        expected_unsolved = False
        repair_priority = "repair_next"
        likely_layer = "unknown"
        dominant_issue = "normal family unexpectedly unsolved"
    else:
        classification = "unknown_family"
        expected_unsolved = True
        repair_priority = "benchmark_definition_review_needed"
        likely_layer = "unknown"
        dominant_issue = "family not in known sets"

    # Refine likely layer based on failure category and selected families
    if failure_category == "ambiguous_expected_rejection" and is_adv:
        likely_layer = "correct_adversarial_rejection"
    elif failure_category == "fallback_only":
        likely_layer = "universal_runner_fallback"
    elif failure_category == "wrong_family_selected":
        likely_layer = "family_discovery"
    elif failure_category == "discovery_missed_family":
        likely_layer = "primitive_discovery"
    elif failure_category == "family_discovered_not_executed":
        likely_layer = "composition_executor"
    elif failure_category == "candidate_wrong_output":
        likely_layer = "capability_execution"
    elif failure_category == "exception":
        likely_layer = "evaluator_exception"

    return {
        "family": family_label,
        "is_adversarial": is_adv,
        "is_normal": is_norm,
        "classification": classification,
        "expected_unsolved": expected_unsolved,
        "generated_count": generated,
        "solved_count": solved,
        "unsolved_count": unsolved,
        "fallback_only_count": fallback_only,
        "malformed_count": malformed,
        "exception_count": exception,
        "dominant_failure_category": failure_category or "none",
        "selected_families": selected_families or [],
        "likely_layer": likely_layer,
        "dominant_issue": dominant_issue,
        "repair_priority": repair_priority,
    }


def audit_remaining_families_from_evaluation(
    evaluation: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the full remaining-family audit from evaluation results."""
    per_family_generated: dict[str, int] = dict(evaluation.get("per_family_generated") or {})
    per_family_solved: dict[str, int] = dict(evaluation.get("per_family_solved") or {})
    per_family_failed: dict[str, int] = dict(evaluation.get("per_family_failed") or {})
    failure_categories: dict[str, int] = dict(evaluation.get("failure_categories") or {})
    task_summaries: list[dict[str, Any]] = list(evaluation.get("task_summaries") or [])

    # Build per-family stats
    family_stats: dict[str, dict[str, int]] = {}
    for ts in task_summaries:
        family = str(ts.get("family_label", ""))
        if family not in family_stats:
            family_stats[family] = {"generated": 0, "solved": 0, "unsolved": 0,
                                    "fallback_only": 0, "malformed": 0, "exception": 0}
        family_stats[family]["generated"] += 1
        if ts.get("exact_match"):
            family_stats[family]["solved"] += 1
        else:
            family_stats[family]["unsolved"] += 1
        if ts.get("fallback_only"):
            family_stats[family]["fallback_only"] += 1
        if ts.get("failure_category") == "exception":
            family_stats[family]["exception"] += 1

    # Build per-family failure categories
    family_failure_cats: dict[str, str] = {}
    family_selected: dict[str, list[str]] = {}
    for ts in task_summaries:
        family = str(ts.get("family_label", ""))
        if not ts.get("exact_match"):
            cat = ts.get("failure_category")
            if cat:
                family_failure_cats[family] = str(cat)
            sel = ts.get("selected_families", [])
            if sel:
                family_selected[family] = [str(s) for s in sel]

    rows: list[dict[str, Any]] = []
    correct_rejections: list[dict[str, Any]] = []
    real_failures: list[dict[str, Any]] = []
    fallback_expected: list[dict[str, Any]] = []
    fallback_unexpected: list[dict[str, Any]] = []

    for family in sorted(family_stats.keys()):
        stats = family_stats[family]
        # Only classify families that have unsolved tasks
        if stats["unsolved"] == 0:
            continue
        cat = family_failure_cats.get(family)
        sel = family_selected.get(family, [])
        row = classify_unsolved_family(
            family,
            generated=stats["generated"],
            solved=stats["solved"],
            unsolved=stats["unsolved"],
            fallback_only=stats["fallback_only"],
            malformed=stats["malformed"],
            exception=stats["exception"],
            failure_category=cat,
            selected_families=sel,
        )
        rows.append(row)

        if row["classification"] == "correct_adversarial_rejection":
            correct_rejections.append(row)
        elif row["classification"] == "unexpected_normal_family_failure":
            real_failures.append(row)

        if row["fallback_only_count"] > 0:
            if row["expected_unsolved"]:
                fallback_expected.append(row)
            else:
                fallback_unexpected.append(row)

    # Repair priority ranking
    repair_priorities: list[dict[str, Any]] = []
    for row in rows:
        if row["repair_priority"] in ("repair_next", "repair_later"):
            repair_priorities.append({
                "family": row["family"],
                "priority": row["repair_priority"],
                "unsolved_count": row["unsolved_count"],
                "likely_layer": row["likely_layer"],
                "dominant_issue": row["dominant_issue"],
            })

    return {
        "total_families_with_unsolved": len(rows),
        "correct_adversarial_rejections": len(correct_rejections),
        "unexpected_normal_family_failures": len(real_failures),
        "fallback_expected_count": len(fallback_expected),
        "fallback_unexpected_count": len(fallback_unexpected),
        "family_rows": rows,
        "correct_rejections": correct_rejections,
        "real_failures": real_failures,
        "fallback_expected": fallback_expected,
        "fallback_unexpected": fallback_unexpected,
        "repair_priorities": repair_priorities,
        "adversarial_rejection_pass": int(evaluation.get("adversarial_rejection_pass", 0)),
        "adversarial_rejection_fail": int(evaluation.get("adversarial_rejection_fail", 0)),
        "exact_two_output_pass": bool(evaluation.get("exact_two_output_pass", False)),
    }


__all__ = [
    "ADVERSARIAL_FAMILIES_V1",
    "NORMAL_FAMILIES_V1",
    "is_adversarial",
    "is_normal",
    "classify_unsolved_family",
    "audit_remaining_families_from_evaluation",
]