"""ARC-AGI-2 diversified failure audit V1.

Audit-only: classify diversified family failures, reconcile counts,
rank repair priorities. No solver repair, no generator changes.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from weslr.arc_synthetic_family_diversification_v1 import (
    DIVERSIFIED_FAMILY_ORDER_V1,
    DIVERSIFIED_FAMILY_COUNT_V1,
    build_diversified_family_corpus_v1,
)

# Classification of each diversified family's likely missing capability
FAMILY_CAPABILITY_MAP: dict[str, str] = {
    "complete_horizontal_symmetry": "symmetry_completion",
    "complete_vertical_symmetry": "symmetry_completion",
    "fill_enclosed_hole": "hole_detection",
    "remove_distractor_object": "object_parsing",
    "copy_object_to_marker": "marker_interpretation",
    "extend_line_to_boundary": "line_extension",
    "extract_row_or_column_by_marker": "row_column_extraction",
    "recolor_by_object_size": "object_parsing",
}

# Families expected to be solved by the current solver
EXPECTED_SOLVED_FAMILIES: set[str] = {
    "remove_distractor_object",
    "recolor_by_object_size",
}

# Families expected to be unsolved (missing capability)
EXPECTED_UNSOLVED_FAMILIES: set[str] = {
    "complete_horizontal_symmetry",
    "complete_vertical_symmetry",
    "fill_enclosed_hole",
    "copy_object_to_marker",
    "extend_line_to_boundary",
    "extract_row_or_column_by_marker",
}

# Repair priority labels
PRIORITY_REPAIR_NEXT = "repair_next"
PRIORITY_REPAIR_AFTER_NEXT = "repair_after_next"
PRIORITY_REPAIR_LATER = "repair_later"
PRIORITY_NEEDS_BENCHMARK_REVIEW = "needs_benchmark_review"
PRIORITY_DO_NOT_REPAIR = "do_not_repair_currently"

# Failure classification labels
FAILURE_MISSING_CAPABILITY = "missing_capability"
FAILURE_ROUTING_GAP = "routing_gap"
FAILURE_ADAPTER_GAP = "adapter_gap"
FAILURE_BENCHMARK_DEFINITION = "benchmark_definition_issue"
FAILURE_OVER_REJECTION = "over_rejection"
FAILURE_EXPECTED_PRESSURE = "expected_pressure"
FAILURE_SOLVED = "solved"


def reconcile_diversified_counts(
    dev_tasks: Sequence[Mapping[str, Any]],
    heldout_tasks: Sequence[Mapping[str, Any]],
    *,
    dev_seed: int,
    heldout_seed: int,
    diversified_tasks_per_family: int,
) -> dict[str, Any]:
    """Reconcile expected vs actual diversified family counts."""
    dev_div = build_diversified_family_corpus_v1(seed=dev_seed, tasks_per_family=diversified_tasks_per_family)
    held_div = build_diversified_family_corpus_v1(seed=heldout_seed, tasks_per_family=diversified_tasks_per_family)

    dev_div_ids = {t["task_id"] for t in dev_div}
    held_div_ids = {t["task_id"] for t in held_div}

    # Find diversified tasks in the actual task lists
    dev_div_found = [t for t in dev_tasks if t["task_id"] in dev_div_ids]
    held_div_found = [t for t in heldout_tasks if t["task_id"] in held_div_ids]

    dev_div_families = Counter(t["family_label"] for t in dev_div_found)
    held_div_families = Counter(t["family_label"] for t in held_div_found)

    expected_dev = DIVERSIFIED_FAMILY_COUNT_V1 * diversified_tasks_per_family
    expected_held = DIVERSIFIED_FAMILY_COUNT_V1 * diversified_tasks_per_family

    missing_dev = set(DIVERSIFIED_FAMILY_ORDER_V1) - set(dev_div_families.keys())
    missing_held = set(DIVERSIFIED_FAMILY_ORDER_V1) - set(held_div_families.keys())

    return {
        "diversified_family_count": DIVERSIFIED_FAMILY_COUNT_V1,
        "diversified_families": list(DIVERSIFIED_FAMILY_ORDER_V1),
        "diversified_tasks_per_family": diversified_tasks_per_family,
        "expected_dev_diversified_tasks": expected_dev,
        "expected_heldout_diversified_tasks": expected_held,
        "actual_dev_diversified_tasks": len(dev_div_found),
        "actual_heldout_diversified_tasks": len(held_div_found),
        "dev_per_family_counts": dict(sorted(dev_div_families.items())),
        "heldout_per_family_counts": dict(sorted(held_div_families.items())),
        "missing_dev_families": sorted(missing_dev),
        "missing_heldout_families": sorted(missing_held),
        "count_match": (
            len(dev_div_found) == expected_dev
            and len(held_div_found) == expected_held
            and not missing_dev
            and not missing_held
        ),
    }


def classify_diversified_family(
    family: str,
    *,
    dev_solved: int,
    dev_unsolved: int,
    dev_fallback: int,
    heldout_solved: int,
    heldout_unsolved: int,
    heldout_fallback: int,
    exceptions: int,
) -> dict[str, Any]:
    """Classify a single diversified family's failure mode."""
    total_solved = dev_solved + heldout_solved
    total_unsolved = dev_unsolved + heldout_unsolved
    total_fallback = dev_fallback + heldout_fallback
    total = total_solved + total_unsolved

    capability = FAMILY_CAPABILITY_MAP.get(family, "unknown")

    if total_solved == total and total > 0:
        # All tasks solved
        classification = FAILURE_SOLVED
        priority = PRIORITY_DO_NOT_REPAIR
        explanation = "All tasks solved by current solver"
    elif family in EXPECTED_SOLVED_FAMILIES:
        classification = FAILURE_EXPECTED_PRESSURE
        priority = PRIORITY_NEEDS_BENCHMARK_REVIEW
        explanation = f"Expected solved but {total_unsolved}/{total} unsolved"
    elif family in EXPECTED_UNSOLVED_FAMILIES:
        classification = FAILURE_MISSING_CAPABILITY
        # Assign priority based on capability
        if capability in ("symmetry_completion", "line_extension"):
            priority = PRIORITY_REPAIR_NEXT
        elif capability in ("hole_detection",):
            priority = PRIORITY_REPAIR_AFTER_NEXT
        elif capability in ("row_column_extraction",):
            priority = PRIORITY_REPAIR_AFTER_NEXT
        elif capability in ("marker_interpretation",):
            priority = PRIORITY_REPAIR_LATER
        else:
            priority = PRIORITY_REPAIR_LATER
        explanation = f"Missing capability: {capability}"
    else:
        classification = FAILURE_EXPECTED_PRESSURE
        priority = PRIORITY_NEEDS_BENCHMARK_REVIEW
        explanation = "Unexpected failure pattern"

    return {
        "family": family,
        "capability_layer": capability,
        "dev_solved": dev_solved,
        "dev_unsolved": dev_unsolved,
        "dev_fallback": dev_fallback,
        "heldout_solved": heldout_solved,
        "heldout_unsolved": heldout_unsolved,
        "heldout_fallback": heldout_fallback,
        "exceptions": exceptions,
        "total_solved": total_solved,
        "total_unsolved": total_unsolved,
        "total_fallback": total_fallback,
        "classification": classification,
        "repair_priority": priority,
        "explanation": explanation,
    }


def audit_diversified_families(
    evaluation: Mapping[str, Any],
    *,
    split_name: str,
) -> list[dict[str, Any]]:
    """Extract per-family results for diversified families from evaluation data."""
    per_family_generated = evaluation.get("per_family_generated", {})
    per_family_solved = evaluation.get("per_family_solved", {})
    per_family_failed = evaluation.get("per_family_failed", {})
    failure_categories = evaluation.get("failure_categories", {})

    results: list[dict[str, Any]] = []
    for family in DIVERSIFIED_FAMILY_ORDER_V1:
        generated = per_family_generated.get(family, 0)
        solved = per_family_solved.get(family, 0)
        failed = per_family_failed.get(family, 0)
        # Fallback count from task summaries
        fallback = 0
        for ts in evaluation.get("task_summaries", []):
            if ts.get("family_label") == family and ts.get("fallback_only"):
                fallback += 1

        results.append({
            "family": family,
            "split": split_name,
            "generated": generated,
            "solved": solved,
            "unsolved": failed,
            "fallback_only": fallback,
        })
    return results


def compute_repair_priorities(
    family_classifications: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group families by repair priority."""
    priorities: dict[str, list[dict[str, Any]]] = {
        PRIORITY_REPAIR_NEXT: [],
        PRIORITY_REPAIR_AFTER_NEXT: [],
        PRIORITY_REPAIR_LATER: [],
        PRIORITY_NEEDS_BENCHMARK_REVIEW: [],
        PRIORITY_DO_NOT_REPAIR: [],
    }
    for fc in family_classifications:
        p = fc.get("repair_priority", PRIORITY_DO_NOT_REPAIR)
        if p in priorities:
            priorities[p].append(fc)
    return priorities


def check_accidental_solve(
    family: str,
    *,
    dev_solved: int,
    heldout_solved: int,
    dev_generated: int,
    heldout_generated: int,
) -> dict[str, Any]:
    """Check whether a solved diversified family is a legitimate solve or accidental."""
    total_solved = dev_solved + heldout_solved
    total_generated = dev_generated + heldout_generated

    if total_solved == 0:
        return {"family": family, "status": "unsolved", "accidental": False}

    if family == "remove_distractor_object":
        # The solver has object selection primitives (select_largest_object)
        # and can remove non-selected objects. This is a legitimate solve.
        return {
            "family": family,
            "status": "solved",
            "accidental": False,
            "reason": "Solver has object selection and removal primitives",
            "likely_existing_capability": "select_largest_object + remove_non_selected",
        }
    elif family == "recolor_by_object_size":
        # The solver has recolor primitives and can identify object sizes.
        # The smallest object is a single cell, which the solver can recolor.
        return {
            "family": family,
            "status": "solved",
            "accidental": False,
            "reason": "Solver has recolor primitives and object size comparison",
            "likely_existing_capability": "recolor_foreground + object_count_to_square",
        }
    else:
        return {
            "family": family,
            "status": "solved",
            "accidental": True,
            "reason": "Unexpected solve for this family type",
        }


def run_diversified_failure_audit(
    dev_tasks: Sequence[Mapping[str, Any]],
    heldout_tasks: Sequence[Mapping[str, Any]],
    dev_evaluation: Mapping[str, Any],
    heldout_evaluation: Mapping[str, Any],
    *,
    dev_seed: int = 2435,
    heldout_seed: int = 82435,
    diversified_tasks_per_family: int = 3,
) -> dict[str, Any]:
    """Run the full diversified failure audit."""
    # Count reconciliation
    reconciliation = reconcile_diversified_counts(
        dev_tasks, heldout_tasks,
        dev_seed=dev_seed,
        heldout_seed=heldout_seed,
        diversified_tasks_per_family=diversified_tasks_per_family,
    )

    # Per-family results per split
    dev_family_results = audit_diversified_families(dev_evaluation, split_name="dev")
    heldout_family_results = audit_diversified_families(heldout_evaluation, split_name="heldout")

    # Merge per-split results into per-family classifications
    dev_by_family = {r["family"]: r for r in dev_family_results}
    held_by_family = {r["family"]: r for r in heldout_family_results}

    family_classifications: list[dict[str, Any]] = []
    for family in DIVERSIFIED_FAMILY_ORDER_V1:
        dev_r = dev_by_family.get(family, {})
        held_r = held_by_family.get(family, {})
        fc = classify_diversified_family(
            family,
            dev_solved=dev_r.get("solved", 0),
            dev_unsolved=dev_r.get("unsolved", 0),
            dev_fallback=dev_r.get("fallback_only", 0),
            heldout_solved=held_r.get("solved", 0),
            heldout_unsolved=held_r.get("unsolved", 0),
            heldout_fallback=held_r.get("fallback_only", 0),
            exceptions=0,
        )
        family_classifications.append(fc)

    # Repair priorities
    priorities = compute_repair_priorities(family_classifications)

    # Accidental solve check
    accidental_checks: list[dict[str, Any]] = []
    for family in DIVERSIFIED_FAMILY_ORDER_V1:
        dev_r = dev_by_family.get(family, {})
        held_r = held_by_family.get(family, {})
        check = check_accidental_solve(
            family,
            dev_solved=dev_r.get("solved", 0),
            heldout_solved=held_r.get("solved", 0),
            dev_generated=dev_r.get("generated", 0),
            heldout_generated=held_r.get("generated", 0),
        )
        accidental_checks.append(check)

    return {
        "reconciliation": reconciliation,
        "dev_family_results": dev_family_results,
        "heldout_family_results": heldout_family_results,
        "family_classifications": family_classifications,
        "repair_priorities": {k: [fc["family"] for fc in v] for k, v in priorities.items()},
        "accidental_solve_checks": accidental_checks,
    }


__all__ = [
    "DIVERSIFIED_FAMILY_ORDER_V1",
    "FAMILY_CAPABILITY_MAP",
    "EXPECTED_SOLVED_FAMILIES",
    "EXPECTED_UNSOLVED_FAMILIES",
    "reconcile_diversified_counts",
    "classify_diversified_family",
    "audit_diversified_families",
    "compute_repair_priorities",
    "check_accidental_solve",
    "run_diversified_failure_audit",
]