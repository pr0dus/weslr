"""WESLR AI audit planning scaffold V1.

Safe, in-memory planning helpers for arranging WESLR-native synthetic AI audit
probes before a future operator-reviewed evaluation. This module creates dry
plans only: it does not execute probes, call models/advisors, score systems,
evaluate answers, use protected items, use answer keys, claim official scores,
or modify runtime/chat/voice behavior.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any

from weslr.ai_audit_probe_inventory import (
    build_ai_audit_synthetic_probe_set_v1,
    load_ai_audit_synthetic_probe_inventory_v1,
    validate_ai_audit_synthetic_probe_selection_v1,
)


PLAN_SCHEMA_VERSION = "ai_audit_plan_v1"
TARGET_SCHEMA_VERSION = "ai_audit_target_descriptor_v1"
PLAN_EXECUTION_STATUS = "dry_plan_only"
NON_EXECUTABLE_STATUS = "not_executable"

FORBIDDEN_PLAN_FIELDS = {
    "answer",
    "answers",
    "answer_key",
    "answer_keys",
    "model_output",
    "model_outputs",
    "score",
    "scores",
    "official_score",
    "official_scores",
    "clinical_score",
    "iq_score",
    "benchmark_score",
    "result_label",
    "internal_audit_score",
}


@dataclass
class AIAuditTargetDescriptorV1:
    schema_version: str = TARGET_SCHEMA_VERSION
    target_name: str = "unknown_target"
    target_kind: str = "unknown"
    claimed_capabilities: list[str] = field(default_factory=list)
    audit_reason: str = "operator-requested review preparation"
    operator_notes: str = ""
    source_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    created_by: str = "WESLR"
    created_for: str = "operator_review"


@dataclass
class AIAuditPlanV1:
    schema_version: str = PLAN_SCHEMA_VERSION
    plan_id: str = ""
    target: dict[str, Any] = field(default_factory=dict)
    selected_probe_ids: list[str] = field(default_factory=list)
    probe_categories: list[str] = field(default_factory=list)
    claim_categories: list[str] = field(default_factory=list)
    filters_used: dict[str, Any] = field(default_factory=dict)
    safety_boundaries: dict[str, Any] = field(default_factory=dict)
    execution_status: str = PLAN_EXECUTION_STATUS
    executable: bool = False
    dry_plan_only: bool = True
    synthetic_weslr_native: bool = True
    non_official: bool = True
    no_scores: bool = True
    no_answers: bool = True
    no_model_outputs: bool = True
    validation: dict[str, Any] = field(default_factory=dict)


def create_ai_audit_target_descriptor_v1(
    *,
    target_name: str,
    target_kind: str = "unknown",
    claimed_capabilities: list[str] | None = None,
    audit_reason: str = "operator-requested review preparation",
    operator_notes: str = "",
    source_refs: list[str] | None = None,
    provenance_refs: list[str] | None = None,
    created_by: str = "WESLR",
    created_for: str = "operator_review",
) -> dict[str, Any]:
    """Create a plain in-memory target descriptor for audit planning only."""
    return asdict(
        AIAuditTargetDescriptorV1(
            target_name=target_name,
            target_kind=target_kind,
            claimed_capabilities=list(claimed_capabilities or []),
            audit_reason=audit_reason,
            operator_notes=operator_notes,
            source_refs=list(source_refs or []),
            provenance_refs=list(provenance_refs or []),
            created_by=created_by,
            created_for=created_for,
        )
    )


def _stable_plan_id(target: dict[str, Any], selected_probe_ids: list[str]) -> str:
    seed = "|".join([str(target.get("target_name", "unknown_target")), *selected_probe_ids])
    return "weslr_ai_audit_plan_v1_" + sha256(seed.encode("utf-8")).hexdigest()[:12]


def _default_safety_boundaries() -> dict[str, Any]:
    return {
        "execution_allowed": False,
        "runner_created": False,
        "external_model_calls": False,
        "real_system_testing": False,
        "answer_evaluation": False,
        "protected_item_free": True,
        "answer_key_free": True,
        "official_score_claimed": False,
        "clinical_validity_claimed": False,
        "benchmark_tuning": False,
        "runtime_behavior_change": False,
        "synthetic_weslr_native": True,
        "non_official": True,
    }


def _canonical_probe_lookup(inventory: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    probes = load_ai_audit_synthetic_probe_inventory_v1() if inventory is None else deepcopy(list(inventory))
    return {str(probe.get("probe_id", "")): probe for probe in probes if probe.get("probe_id")}


def _ordered_selected_ids(selected_probe_ids: list[str], inventory: list[dict[str, Any]] | None = None) -> list[str]:
    canonical = _canonical_probe_lookup(inventory)
    selected = set(selected_probe_ids)
    return [probe_id for probe_id in sorted(canonical.keys()) if probe_id in selected]


def _categories_for_probe_ids(selected_probe_ids: list[str], field_name: str, inventory: list[dict[str, Any]] | None = None) -> list[str]:
    canonical = _canonical_probe_lookup(inventory)
    return sorted({str(canonical[probe_id].get(field_name, "unknown")) for probe_id in selected_probe_ids if probe_id in canonical})


def _find_forbidden_plan_fields(value: Any, path: str = "plan") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_PLAN_FIELDS:
                issues.append(f"forbidden plan field: {nested_path}")
            issues.extend(_find_forbidden_plan_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden_plan_fields(nested, f"{path}[{index}]"))
    return issues


def validate_ai_audit_plan_v1(plan: dict[str, Any], *, inventory: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Validate a dry AI audit plan without executing probes or scoring anything."""
    issues: list[str] = []
    if not isinstance(plan, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["plan must be a dict"]}

    target = plan.get("target")
    if not isinstance(target, dict):
        issues.append("missing target descriptor")
    else:
        if not str(target.get("target_name", "")).strip():
            issues.append("missing target_name")
        if not str(target.get("target_kind", "")).strip():
            issues.append("missing target_kind")

    selected_probe_ids = list(plan.get("selected_probe_ids") or [])
    if not selected_probe_ids:
        issues.append("missing selected_probe_ids")
    selection_validation = validate_ai_audit_synthetic_probe_selection_v1(selected_probe_ids, inventory=inventory)
    issues.extend(selection_validation.get("issues", []))

    if plan.get("executable") is not False:
        issues.append("plan executable must be False")
    if plan.get("dry_plan_only") is not True:
        issues.append("plan dry_plan_only must be True")
    if plan.get("execution_status") not in {PLAN_EXECUTION_STATUS, NON_EXECUTABLE_STATUS}:
        issues.append("plan execution_status must be dry_plan_only or not_executable")
    if plan.get("synthetic_weslr_native") is not True:
        issues.append("plan synthetic_weslr_native must be True")
    if plan.get("non_official") is not True:
        issues.append("plan non_official must be True")
    if plan.get("no_scores") is not True:
        issues.append("plan no_scores must be True")
    if plan.get("no_answers") is not True:
        issues.append("plan no_answers must be True")
    if plan.get("no_model_outputs") is not True:
        issues.append("plan no_model_outputs must be True")

    safety_boundaries = plan.get("safety_boundaries") or {}
    for key, expected in _default_safety_boundaries().items():
        if safety_boundaries.get(key) is not expected:
            issues.append(f"safety boundary {key} must be {expected}")

    issues.extend(_find_forbidden_plan_fields(plan))

    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "selected_probe_count": len(selected_probe_ids),
        "selection_validation": selection_validation,
        "executable": bool(plan.get("executable", True)),
        "dry_plan_only": plan.get("dry_plan_only") is True,
        "synthetic_weslr_native": plan.get("synthetic_weslr_native") is True,
        "non_official": plan.get("non_official") is True,
        "protected_items_copied": selection_validation.get("protected_items_copied", False),
        "answer_keys_used": selection_validation.get("answer_keys_used", False),
        "official_score_claimed": selection_validation.get("official_score_claimed", False),
        "benchmark_tuning_performed": selection_validation.get("benchmark_tuning_performed", False),
        "runtime_behavior_changed": selection_validation.get("runtime_behavior_changed", False),
    }


def build_ai_audit_plan_v1(
    *,
    target: dict[str, Any] | None = None,
    target_name: str = "unknown_target",
    target_kind: str = "unknown",
    claimed_capabilities: list[str] | None = None,
    audit_reason: str = "operator-requested review preparation",
    selected_probe_ids: list[str] | None = None,
    probe_categories: str | list[str] | tuple[str, ...] | set[str] | None = None,
    claim_categories: str | list[str] | tuple[str, ...] | set[str] | None = None,
    limit: int | None = None,
    inventory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic dry AI audit plan from selected synthetic probes."""
    target_descriptor = deepcopy(target) if target is not None else create_ai_audit_target_descriptor_v1(
        target_name=target_name,
        target_kind=target_kind,
        claimed_capabilities=claimed_capabilities,
        audit_reason=audit_reason,
    )

    if selected_probe_ids is None:
        probe_set = build_ai_audit_synthetic_probe_set_v1(
            limit=limit,
            probe_categories=probe_categories,
            claim_categories=claim_categories,
            references_only=True,
            inventory=inventory,
        )
        candidate_ids = list(probe_set["probe_ids"])
    else:
        candidate_ids = [str(probe_id) for probe_id in selected_probe_ids]
        if limit is not None:
            candidate_ids = candidate_ids[:limit]

    selection_validation = validate_ai_audit_synthetic_probe_selection_v1(candidate_ids, inventory=inventory)
    if not selection_validation.get("valid", False):
        return {
            "valid": False,
            "redacted_count_only": True,
            "plan": None,
            "validation": {"valid": False, "issues": list(selection_validation.get("issues", [])), "selection_validation": selection_validation},
        }

    ordered_ids = _ordered_selected_ids(candidate_ids, inventory=inventory)
    plan = asdict(
        AIAuditPlanV1(
            plan_id=_stable_plan_id(target_descriptor, ordered_ids),
            target=target_descriptor,
            selected_probe_ids=ordered_ids,
            probe_categories=_categories_for_probe_ids(ordered_ids, "probe_category", inventory=inventory),
            claim_categories=_categories_for_probe_ids(ordered_ids, "claim_category", inventory=inventory),
            filters_used={
                "probe_categories": sorted(list(probe_categories)) if isinstance(probe_categories, (set, list, tuple)) else probe_categories,
                "claim_categories": sorted(list(claim_categories)) if isinstance(claim_categories, (set, list, tuple)) else claim_categories,
                "limit": limit,
                "explicit_probe_ids": selected_probe_ids is not None,
            },
            safety_boundaries=_default_safety_boundaries(),
            validation=selection_validation,
        )
    )
    plan_validation = validate_ai_audit_plan_v1(plan, inventory=inventory)
    plan["validation"] = plan_validation
    return {"valid": plan_validation["valid"], "redacted_count_only": True, "plan": plan, "validation": plan_validation}


def summarize_ai_audit_plan_v1(plan: dict[str, Any], *, inventory: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return a redacted/count-only summary of a dry AI audit plan."""
    validation = validate_ai_audit_plan_v1(plan, inventory=inventory)
    selected_probe_ids = list(plan.get("selected_probe_ids") or []) if isinstance(plan, dict) else []
    target = plan.get("target", {}) if isinstance(plan, dict) else {}
    return {
        "schema_version": "ai_audit_plan_summary_v1",
        "redacted_count_only": True,
        "target_name": target.get("target_name", "unknown_target") if isinstance(target, dict) else "unknown_target",
        "target_kind": target.get("target_kind", "unknown") if isinstance(target, dict) else "unknown",
        "selected_probe_count": len(selected_probe_ids),
        "probe_categories": list(plan.get("probe_categories", [])) if isinstance(plan, dict) else [],
        "claim_categories": list(plan.get("claim_categories", [])) if isinstance(plan, dict) else [],
        "executable": bool(plan.get("executable", True)) if isinstance(plan, dict) else True,
        "dry_plan_only": plan.get("dry_plan_only") is True if isinstance(plan, dict) else False,
        "validation_valid": validation["valid"],
        "issue_count": len(validation["issues"]),
        "safety_status": "safe_dry_plan" if validation["valid"] else "invalid_plan",
        "protected_items_copied": validation.get("protected_items_copied", False),
        "answer_keys_used": validation.get("answer_keys_used", False),
        "official_score_claimed": validation.get("official_score_claimed", False),
        "benchmark_tuning_performed": validation.get("benchmark_tuning_performed", False),
        "runtime_behavior_changed": validation.get("runtime_behavior_changed", False),
    }
