"""WESLR AI audit finding helpers V1.

Safe, in-memory finding/evidence envelopes for future operator-reviewed AI audit
observations. Findings are non-official evidence containers, not final truth,
not a runner, not a scoring engine, and not a live-system test. This module does
not call models, evaluate answers, use answer keys, copy protected items, claim
official scores, persist state, or modify runtime/chat/voice behavior.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any


FINDING_SCHEMA_VERSION = "ai_audit_finding_v1"
FINDING_COLLECTION_SCHEMA_VERSION = "ai_audit_finding_collection_v1"
ALLOWED_FINDING_TYPES = {
    "provenance_honesty",
    "continuity_claim",
    "memory_boundary",
    "tool_use_claim",
    "authority_resistance",
    "self_improvement_claim",
    "calibration",
    "other",
}
ALLOWED_VERDICTS = {
    "supported",
    "unsupported",
    "overclaimed",
    "inconclusive",
    "not_observed",
    "needs_more_evidence",
}
ALLOWED_SOURCES = {"manual_review_only", "dry_observation_only"}
FORBIDDEN_FINDING_FIELDS = {
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
    "internal_audit_score",
    "protected_test_item",
    "protected_prompt",
    "hidden_prompt",
}


@dataclass
class AIAuditFindingSafetyFlagsV1:
    protected_item_present: bool = False
    answer_key_present: bool = False
    official_score_claimed: bool = False
    clinical_validity_claimed: bool = False
    benchmark_tuning: bool = False
    model_output_included: bool = False
    runtime_behavior_change: bool = False
    executable_marker: bool = False


@dataclass
class AIAuditFindingV1:
    schema_version: str = FINDING_SCHEMA_VERSION
    finding_id: str = ""
    plan_id: str = ""
    target_name: str = "unknown_target"
    target_ref: str = ""
    probe_id: str = ""
    claim_category: str = "unknown"
    probe_category: str = "unknown"
    finding_type: str = "other"
    verdict: str = "inconclusive"
    evidence_refs: list[str] = field(default_factory=list)
    reviewer_notes: str = ""
    safety_flags: dict[str, bool] = field(default_factory=dict)
    source: str = "manual_review_only"
    executable: bool = False
    scoring_engine: bool = False
    official_score_claimed: bool = False
    answer_key_free: bool = True
    protected_item_free: bool = True
    non_official: bool = True
    non_clinical: bool = True
    benchmark_tuning: bool = False


def _default_safety_flags() -> dict[str, bool]:
    return asdict(AIAuditFindingSafetyFlagsV1())


def _stable_finding_id(plan_id: str, probe_id: str, finding_type: str, verdict: str) -> str:
    seed = "|".join([plan_id, probe_id, finding_type, verdict])
    return "weslr_ai_audit_finding_v1_" + sha256(seed.encode("utf-8")).hexdigest()[:12]


def _find_forbidden_fields(value: Any, path: str = "finding") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_FINDING_FIELDS:
                issues.append(f"forbidden finding field: {nested_path}")
            issues.extend(_find_forbidden_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden_fields(nested, f"{path}[{index}]"))
    return issues


def _plan_probe_lookup(plan: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(plan, dict):
        return {}
    selected_ids = [str(probe_id) for probe_id in plan.get("selected_probe_ids", [])]
    categories = list(plan.get("probe_categories", []))
    claim_categories = list(plan.get("claim_categories", []))
    lookup: dict[str, dict[str, Any]] = {}
    for index, probe_id in enumerate(selected_ids):
        lookup[probe_id] = {
            "probe_category": categories[index] if len(categories) == len(selected_ids) else "unknown",
            "claim_category": claim_categories[index] if len(claim_categories) == len(selected_ids) else "unknown",
        }
    return lookup


def create_ai_audit_finding_v1(
    *,
    plan_id: str,
    probe_id: str,
    verdict: str,
    finding_type: str = "other",
    target_name: str = "unknown_target",
    target_ref: str = "",
    claim_category: str = "unknown",
    probe_category: str = "unknown",
    evidence_refs: list[str] | None = None,
    reviewer_notes: str = "",
    source: str = "manual_review_only",
    finding_id: str | None = None,
) -> dict[str, Any]:
    """Create a deterministic, non-executing AI audit finding envelope."""
    item = AIAuditFindingV1(
        finding_id=finding_id or _stable_finding_id(plan_id, probe_id, finding_type, verdict),
        plan_id=plan_id,
        target_name=target_name,
        target_ref=target_ref,
        probe_id=probe_id,
        claim_category=claim_category,
        probe_category=probe_category,
        finding_type=finding_type,
        verdict=verdict,
        evidence_refs=list(evidence_refs or []),
        reviewer_notes=reviewer_notes,
        safety_flags=_default_safety_flags(),
        source=source,
    )
    return asdict(item)


def validate_ai_audit_finding_v1(finding: dict[str, Any], *, plan: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate a finding envelope without execution, scoring, or persistence."""
    issues: list[str] = []
    if not isinstance(finding, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["finding must be a dict"]}

    for field_name in ("finding_id", "plan_id", "probe_id", "finding_type", "verdict", "source"):
        if not str(finding.get(field_name, "")).strip():
            issues.append(f"missing {field_name}")

    if finding.get("finding_type") not in ALLOWED_FINDING_TYPES:
        issues.append("invalid finding_type")
    if finding.get("verdict") not in ALLOWED_VERDICTS:
        issues.append("invalid verdict")
    if finding.get("source") not in ALLOWED_SOURCES:
        issues.append("invalid source")
    if finding.get("executable") is not False:
        issues.append("finding executable must be False")
    if finding.get("scoring_engine") is not False:
        issues.append("finding scoring_engine must be False")
    if finding.get("official_score_claimed") is not False:
        issues.append("finding official_score_claimed must be False")
    if finding.get("answer_key_free") is not True:
        issues.append("finding answer_key_free must be True")
    if finding.get("protected_item_free") is not True:
        issues.append("finding protected_item_free must be True")
    if finding.get("non_official") is not True:
        issues.append("finding non_official must be True")
    if finding.get("non_clinical") is not True:
        issues.append("finding non_clinical must be True")
    if finding.get("benchmark_tuning") is not False:
        issues.append("finding benchmark_tuning must be False")

    safety_flags = finding.get("safety_flags") or {}
    prohibited_flags = {
        "protected_item_present": "protected item present",
        "answer_key_present": "answer key present",
        "official_score_claimed": "official score claimed",
        "clinical_validity_claimed": "clinical validity claimed",
        "benchmark_tuning": "benchmark tuning",
        "model_output_included": "model output included",
        "runtime_behavior_change": "runtime behavior change",
        "executable_marker": "executable marker",
    }
    for flag_name, label in prohibited_flags.items():
        if safety_flags.get(flag_name) is True:
            issues.append(label)

    if plan is not None:
        if not isinstance(plan, dict):
            issues.append("plan must be a dict")
        else:
            if finding.get("plan_id") != plan.get("plan_id"):
                issues.append("finding plan_id does not match plan")
            selected_ids = {str(probe_id) for probe_id in plan.get("selected_probe_ids", [])}
            if finding.get("probe_id") not in selected_ids:
                issues.append("finding probe_id not present in plan")

    issues.extend(_find_forbidden_fields(finding))

    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "finding_id": finding.get("finding_id", ""),
        "plan_id": finding.get("plan_id", ""),
        "probe_id": finding.get("probe_id", ""),
        "verdict": finding.get("verdict", "unknown"),
        "finding_type": finding.get("finding_type", "other"),
        "protected_items_copied": safety_flags.get("protected_item_present", False) or finding.get("protected_item_free") is not True,
        "answer_keys_used": safety_flags.get("answer_key_present", False) or finding.get("answer_key_free") is not True,
        "official_score_claimed": safety_flags.get("official_score_claimed", False) or finding.get("official_score_claimed") is not False,
        "benchmark_tuning_performed": safety_flags.get("benchmark_tuning", False) or finding.get("benchmark_tuning") is not False,
        "runtime_behavior_changed": safety_flags.get("runtime_behavior_change", False),
    }


def summarize_ai_audit_findings_v1(
    findings: list[dict[str, Any]],
    *,
    plan: dict[str, Any] | None = None,
    validate: bool = True,
) -> dict[str, Any]:
    """Return redacted/count-only summary of finding envelopes."""
    finding_list = deepcopy(list(findings or []))
    verdict_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    probe_category_counts: dict[str, int] = {}
    invalid_count = 0
    protected_items_copied = False
    answer_keys_used = False
    official_score_claimed = False
    benchmark_tuning_performed = False
    runtime_behavior_changed = False

    for finding in finding_list:
        verdict = str(finding.get("verdict", "unknown"))
        finding_type = str(finding.get("finding_type", "other"))
        probe_category = str(finding.get("probe_category", "unknown"))
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        type_counts[finding_type] = type_counts.get(finding_type, 0) + 1
        probe_category_counts[probe_category] = probe_category_counts.get(probe_category, 0) + 1
        if validate:
            result = validate_ai_audit_finding_v1(finding, plan=plan)
            if not result["valid"]:
                invalid_count += 1
            protected_items_copied = protected_items_copied or result["protected_items_copied"]
            answer_keys_used = answer_keys_used or result["answer_keys_used"]
            official_score_claimed = official_score_claimed or result["official_score_claimed"]
            benchmark_tuning_performed = benchmark_tuning_performed or result["benchmark_tuning_performed"]
            runtime_behavior_changed = runtime_behavior_changed or result["runtime_behavior_changed"]

    return {
        "schema_version": "ai_audit_findings_summary_v1",
        "redacted_count_only": True,
        "finding_count": len(finding_list),
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "finding_type_counts": dict(sorted(type_counts.items())),
        "probe_category_counts": dict(sorted(probe_category_counts.items())),
        "invalid_count": invalid_count,
        "safety_status": "safe_findings" if invalid_count == 0 else "invalid_findings_present",
        "protected_items_copied": protected_items_copied,
        "answer_keys_used": answer_keys_used,
        "official_score_claimed": official_score_claimed,
        "benchmark_tuning_performed": benchmark_tuning_performed,
        "runtime_behavior_changed": runtime_behavior_changed,
    }


def build_ai_audit_finding_collection_v1(
    findings: list[dict[str, Any]],
    *,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an in-memory finding collection with validation and grouping metadata."""
    finding_list = deepcopy(list(findings or []))
    issues: list[str] = []
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    by_plan_id: dict[str, int] = {}
    by_target_name: dict[str, int] = {}
    by_verdict: dict[str, int] = {}

    for finding in finding_list:
        finding_id = str(finding.get("finding_id", "")).strip()
        if not finding_id:
            issues.append("missing finding_id")
        elif finding_id in seen_ids:
            duplicate_ids.add(finding_id)
        seen_ids.add(finding_id)
        validation = validate_ai_audit_finding_v1(finding, plan=plan)
        issues.extend(validation["issues"])
        plan_id = str(finding.get("plan_id", "unknown"))
        target_name = str(finding.get("target_name", "unknown_target"))
        verdict = str(finding.get("verdict", "unknown"))
        by_plan_id[plan_id] = by_plan_id.get(plan_id, 0) + 1
        by_target_name[target_name] = by_target_name.get(target_name, 0) + 1
        by_verdict[verdict] = by_verdict.get(verdict, 0) + 1

    for finding_id in sorted(duplicate_ids):
        issues.append(f"duplicate finding_id: {finding_id}")

    summary = summarize_ai_audit_findings_v1(finding_list, plan=plan, validate=True)
    return {
        "schema_version": FINDING_COLLECTION_SCHEMA_VERSION,
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_allowed": False,
        "scoring_engine": False,
        "finding_count": len(finding_list),
        "findings": finding_list,
        "duplicate_finding_ids": sorted(duplicate_ids),
        "group_counts": {
            "by_plan_id": dict(sorted(by_plan_id.items())),
            "by_target_name": dict(sorted(by_target_name.items())),
            "by_verdict": dict(sorted(by_verdict.items())),
        },
        "summary": summary,
        "validation": {"valid": not issues, "redacted_count_only": True, "issues": issues},
    }
