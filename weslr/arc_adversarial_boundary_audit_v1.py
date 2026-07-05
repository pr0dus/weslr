"""ARC-AGI-2 Adversarial Boundary Audit V1.

Audit-only module that classifies adversarial family behavior in the
synthetic discovery benchmark.  No solver repair, no public ARC data,
no Kaggle interaction.

The audit helper:
- detects adversarial families from task metadata
- classifies each family's intended vs actual behavior
- checks whether the solver packet leaks expected_output
- detects fallback masking (fallback identity matching identity expected output)
- produces a JSON-safe metadata report

This module is deterministic, side-effect-free, and metadata-only.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

ADVERSARIAL_FAMILY_NAMES_V1 = frozenset({
    "inconsistent_train_examples",
    "ambiguous_multiple_rules",
    "unsupported_primitive_chain",
    "near_match_one_cell",
    "same_palette_wrong_geometry",
    "same_geometry_wrong_recolor",
    "count_tie_ambiguity",
})

INTENDED_ROLE_V1: dict[str, str] = {
    "inconsistent_train_examples": "rejection_expected",
    "ambiguous_multiple_rules": "rejection_expected",
    "unsupported_primitive_chain": "rejection_expected",
    "near_match_one_cell": "exact_match_required",
    "same_palette_wrong_geometry": "over_acceptance_probe",
    "same_geometry_wrong_recolor": "over_acceptance_probe",
    "count_tie_ambiguity": "ambiguity_sensitive",
}

RISK_LABEL_V1: dict[str, str] = {
    "inconsistent_train_examples": "over_acceptance_risk",
    "ambiguous_multiple_rules": "over_acceptance_risk",
    "unsupported_primitive_chain": "over_acceptance_risk",
    "near_match_one_cell": "over_acceptance_risk",
    "same_palette_wrong_geometry": "over_acceptance_risk",
    "same_geometry_wrong_recolor": "over_acceptance_risk",
    "count_tie_ambiguity": "ambiguous_label_risk",
}


def is_adversarial_family(family_label: str) -> bool:
    """Return True if the family name is a known adversarial family."""
    return family_label in ADVERSARIAL_FAMILY_NAMES_V1


def classify_adversarial_family(
    family_label: str,
    *,
    generated: int = 0,
    solved: int = 0,
    rejected: int = 0,
    fallback_only: int = 0,
    malformed: int = 0,
    exception: int = 0,
    expected_behavior: str = "reject",
    actual_behavior: str = "unknown",
    identity_expected: bool = False,
    fallback_identity_match: bool = False,
) -> dict[str, Any]:
    """Classify a single adversarial family's audit result."""
    intended_role = INTENDED_ROLE_V1.get(family_label, "unknown")
    risk = RISK_LABEL_V1.get(family_label, "benchmark_definition_risk")

    if fallback_identity_match and identity_expected:
        risk = "fallback_masking_risk"

    if actual_behavior == "solved" and expected_behavior == "reject":
        pass_fail = "fail"
    elif actual_behavior == "rejected" and expected_behavior == "reject":
        pass_fail = "pass"
    elif actual_behavior == "solved" and expected_behavior == "solve":
        pass_fail = "pass"
    elif actual_behavior == "rejected" and expected_behavior == "solve":
        pass_fail = "fail"
    else:
        pass_fail = "unknown"

    recommended_action = "keep"
    if risk == "fallback_masking_risk":
        recommended_action = "revise_generator_output"
    elif risk == "over_acceptance_risk" and pass_fail == "fail":
        recommended_action = "revise_generator_output_or_solver_boundary_repair"
    elif risk == "ambiguous_label_risk":
        recommended_action = "keep_or_split"

    return {
        "family": family_label,
        "intended_role": intended_role,
        "expected_behavior": expected_behavior,
        "actual_behavior": actual_behavior,
        "pass_fail": pass_fail,
        "risk": risk,
        "recommended_next_action": recommended_action,
        "generated_count": generated,
        "solved_count": solved,
        "rejected_count": rejected,
        "fallback_only_count": fallback_only,
        "malformed_count": malformed,
        "exception_count": exception,
        "identity_expected": identity_expected,
        "fallback_identity_match": fallback_identity_match,
    }


def _eval_to_dict(evaluation: Any) -> dict[str, Any]:
    """Convert evaluation result to dict, handling dataclass and dict inputs."""
    if isinstance(evaluation, Mapping):
        return dict(evaluation)
    if hasattr(evaluation, "to_json_safe_dict"):
        return evaluation.to_json_safe_dict()
    if hasattr(evaluation, "__dict__"):
        return dict(evaluation.__dict__)
    return {}


def audit_adversarial_families_from_evaluation(
    evaluation: Any,
    tasks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the full adversarial audit report from evaluation results and task definitions."""
    evaluation = _eval_to_dict(evaluation)
    per_family_generated: dict[str, int] = dict(evaluation.get("per_family_generated") or {})
    per_family_solved: dict[str, int] = dict(evaluation.get("per_family_solved") or {})
    per_family_failed: dict[str, int] = dict(evaluation.get("per_family_failed") or {})
    failure_categories: dict[str, int] = dict(evaluation.get("failure_categories") or {})
    task_summaries: list[dict[str, Any]] = list(evaluation.get("task_summaries") or [])

    # Build per-adversarial-family stats
    family_audit_rows: list[dict[str, Any]] = []
    adv_rejection_pass = int(evaluation.get("adversarial_rejection_pass", 0))
    adv_rejection_fail = int(evaluation.get("adversarial_rejection_fail", 0))

    # Collect identity and fallback info from tasks
    identity_expected_families: set[str] = set()
    fallback_identity_match_families: set[str] = set()
    identity_solver_match_families: set[str] = set()

    task_lookup: dict[str, Mapping[str, Any]] = {
        str(t.get("task_id", "")): t for t in tasks
    }

    for ts in task_summaries:
        tid = str(ts.get("task_id", ""))
        task = task_lookup.get(tid)
        if task is None:
            continue
        family = str(task.get("family_label", ""))
        if not is_adversarial_family(family):
            continue
        expected_output = task.get("expected_output")
        test_input = task.get("test_input")
        is_identity = expected_output == test_input
        if is_identity:
            identity_expected_families.add(family)
        # Check if this was a fallback-only solve that matched via identity
        if ts.get("exact_match") and ts.get("fallback_only"):
            if is_identity:
                fallback_identity_match_families.add(family)
        # Check if solver (non-fallback) solved via identity match
        if ts.get("exact_match") and not ts.get("fallback_only"):
            if is_identity:
                identity_solver_match_families.add(family)

    for family in sorted(ADVERSARIAL_FAMILY_NAMES_V1):
        generated = int(per_family_generated.get(family, 0))
        solved = int(per_family_solved.get(family, 0))
        failed = int(per_family_failed.get(family, 0))
        fb_only = int(failure_categories.get("fallback_only", 0)) if family in per_family_failed else 0
        # fallback_only is global, estimate per family from task summaries
        fam_summaries = [ts for ts in task_summaries if str(task_lookup.get(str(ts.get("task_id", "")), {}).get("family_label", "")) == family]
        fb_only_family = sum(1 for ts in fam_summaries if ts.get("fallback_only"))
        malformed_family = sum(1 for ts in fam_summaries if ts.get("failure_category") == "malformed")
        exception_family = sum(1 for ts in fam_summaries if ts.get("failure_category") == "exception")

        if solved > 0:
            actual_behavior = "solved"
        elif failed > 0 and solved == 0:
            actual_behavior = "rejected"
        else:
            actual_behavior = "unknown"

        expected_behavior = "reject"
        identity_expected = family in identity_expected_families
        fallback_identity_match = family in fallback_identity_match_families

        row = classify_adversarial_family(
            family,
            generated=generated,
            solved=solved,
            rejected=failed,
            fallback_only=fb_only_family,
            malformed=malformed_family,
            exception=exception_family,
            expected_behavior=expected_behavior,
            actual_behavior=actual_behavior,
            identity_expected=identity_expected,
            fallback_identity_match=fallback_identity_match,
        )
        family_audit_rows.append(row)

    # Expected-output isolation check
    expected_output_isolated = True
    for task in tasks:
        family = str(task.get("family_label", ""))
        if not is_adversarial_family(family):
            continue
        # The solver packet should NOT contain expected_output
        # We verify by checking the build function's output shape
        # (This is a structural check, not a runtime check)
        meta = task.get("metadata") if isinstance(task.get("metadata"), Mapping) else {}
        if "expected_output" in task and task.get("expected_output") is not None:
            # This is fine — the task definition has it, but the solver packet must not
            pass

    # Check solver packet isolation by verifying the build function
    try:
        from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_solver_packet_v1
        for task in tasks:
            family = str(task.get("family_label", ""))
            if not is_adversarial_family(family):
                continue
            packet = build_arc_synthetic_solver_packet_v1(task)
            if "expected_output" in packet:
                expected_output_isolated = False
                break
    except Exception:
        expected_output_isolated = False

    # Fallback masking detection
    fallback_masking_detected = len(fallback_identity_match_families) > 0
    identity_solver_over_acceptance_detected = len(identity_solver_match_families) > 0

    return {
        "schema_version": "ArcAdversarialBoundaryAuditV1",
        "adversarial_rejection_pass": adv_rejection_pass,
        "adversarial_rejection_fail": adv_rejection_fail,
        "family_audit_rows": family_audit_rows,
        "identity_expected_families": sorted(identity_expected_families),
        "fallback_identity_match_families": sorted(fallback_identity_match_families),
        "identity_solver_match_families": sorted(identity_solver_match_families),
        "fallback_masking_detected": fallback_masking_detected,
        "identity_solver_over_acceptance_detected": identity_solver_over_acceptance_detected,
        "expected_output_isolated": expected_output_isolated,
        "exact_two_output_pass": bool(evaluation.get("exact_two_output_pass", False)),
    }


def audit_to_json(audit: Mapping[str, Any]) -> str:
    """Serialize audit report to JSON string (JSON-safe, metadata-only)."""
    return json.dumps(audit, sort_keys=True, default=str)


__all__ = [
    "ADVERSARIAL_FAMILY_NAMES_V1",
    "INTENDED_ROLE_V1",
    "RISK_LABEL_V1",
    "is_adversarial_family",
    "classify_adversarial_family",
    "audit_adversarial_families_from_evaluation",
    "audit_to_json",
]