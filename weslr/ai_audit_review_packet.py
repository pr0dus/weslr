"""WESLR AI audit review packet helpers V1.

Safe, in-memory review packet/dossier helpers that combine a dry audit plan,
manual/dry findings, redacted summaries, and safety validation for operator
review. A review packet is not a runner, not a scoring engine, not a benchmark
report, not a certification, and not a live-system test.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any

from weslr.ai_audit_findings import summarize_ai_audit_findings_v1, validate_ai_audit_finding_v1
from weslr.ai_audit_plan import summarize_ai_audit_plan_v1, validate_ai_audit_plan_v1


REVIEW_PACKET_SCHEMA_VERSION = "ai_audit_review_packet_v1"
ALLOWED_OPERATOR_REVIEW_STATUSES = {"pending_review", "reviewed"}
ALLOWED_OPERATOR_DECISIONS = {
    "none",
    "needs_more_evidence",
    "accepted_as_observation",
    "rejected_insufficient_evidence",
    "archive_review_only",
}
FORBIDDEN_PACKET_FIELDS = {
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
    "certification",
    "certified",
    "official_benchmark_result",
    "protected_test_item",
    "protected_prompt",
    "hidden_prompt",
}


@dataclass
class AIAuditReviewPacketV1:
    schema_version: str = REVIEW_PACKET_SCHEMA_VERSION
    packet_id: str = ""
    plan_id: str = ""
    target_summary: dict[str, Any] = field(default_factory=dict)
    selected_probe_count: int = 0
    finding_count: int = 0
    finding_summary: dict[str, Any] = field(default_factory=dict)
    plan_summary: dict[str, Any] = field(default_factory=dict)
    validation_status: dict[str, Any] = field(default_factory=dict)
    safety_boundaries: dict[str, Any] = field(default_factory=dict)
    operator_review_status: str = "pending_review"
    operator_decision: str = "none"
    operator_decision_notes: str = ""
    execution_status: str = "dry_review_only"
    executable: bool = False
    scoring_engine: bool = False
    automated_grading: bool = False
    answer_evaluation: bool = False
    non_official: bool = True
    non_clinical: bool = True
    non_benchmark_report: bool = True
    in_memory_only: bool = True


def _stable_packet_id(plan_id: str, finding_ids: list[str]) -> str:
    seed = "|".join([plan_id, *sorted(finding_ids)])
    return "weslr_ai_audit_review_packet_v1_" + sha256(seed.encode("utf-8")).hexdigest()[:12]


def _default_safety_boundaries() -> dict[str, Any]:
    return {
        "execution_allowed": False,
        "runner_created": False,
        "external_model_calls": False,
        "real_system_testing": False,
        "scoring_engine": False,
        "automated_grading": False,
        "answer_evaluation": False,
        "protected_item_free": True,
        "answer_key_free": True,
        "official_score_claimed": False,
        "certification_claimed": False,
        "official_benchmark_claimed": False,
        "clinical_validity_claimed": False,
        "benchmark_tuning": False,
        "runtime_behavior_change": False,
        "in_memory_only": True,
    }


def _find_forbidden_packet_fields(value: Any, path: str = "packet") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_PACKET_FIELDS:
                issues.append(f"forbidden review packet field: {nested_path}")
            issues.extend(_find_forbidden_packet_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden_packet_fields(nested, f"{path}[{index}]"))
    return issues


def build_ai_audit_review_packet_v1(
    plan: dict[str, Any],
    findings: list[dict[str, Any]],
    *,
    operator_review_status: str = "pending_review",
    operator_decision: str = "none",
    operator_decision_notes: str = "",
) -> dict[str, Any]:
    """Build a safe in-memory review packet from a dry plan and dry findings."""
    plan_copy = deepcopy(plan)
    finding_copies = deepcopy(list(findings or []))
    finding_ids = [str(finding.get("finding_id", "")) for finding in finding_copies]
    plan_id = str(plan_copy.get("plan_id", ""))
    plan_summary = summarize_ai_audit_plan_v1(plan_copy)
    finding_summary = summarize_ai_audit_findings_v1(finding_copies, plan=plan_copy, validate=True)
    packet = asdict(
        AIAuditReviewPacketV1(
            packet_id=_stable_packet_id(plan_id, finding_ids),
            plan_id=plan_id,
            target_summary={
                "redacted_count_only": True,
                "target_name": plan_summary.get("target_name", "unknown_target"),
                "target_kind": plan_summary.get("target_kind", "unknown"),
            },
            selected_probe_count=int(plan_summary.get("selected_probe_count", 0)),
            finding_count=len(finding_copies),
            finding_summary=finding_summary,
            plan_summary=plan_summary,
            safety_boundaries=_default_safety_boundaries(),
            operator_review_status=operator_review_status,
            operator_decision=operator_decision,
            operator_decision_notes=operator_decision_notes,
        )
    )
    packet["validation_status"] = validate_ai_audit_review_packet_v1(packet, plan=plan_copy, findings=finding_copies)
    return packet


def validate_ai_audit_review_packet_v1(
    packet: dict[str, Any],
    *,
    plan: dict[str, Any] | None = None,
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate a review packet without execution, grading, scoring, or persistence."""
    issues: list[str] = []
    if not isinstance(packet, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["packet must be a dict"]}

    if not str(packet.get("packet_id", "")).strip():
        issues.append("missing packet_id")
    if not str(packet.get("plan_id", "")).strip():
        issues.append("missing plan_id")
    if packet.get("execution_status") not in {"dry_review_only", "not_executable"}:
        issues.append("packet execution_status must be dry_review_only or not_executable")
    if packet.get("executable") is not False:
        issues.append("packet executable must be False")
    if packet.get("scoring_engine") is not False:
        issues.append("packet scoring_engine must be False")
    if packet.get("automated_grading") is not False:
        issues.append("packet automated_grading must be False")
    if packet.get("answer_evaluation") is not False:
        issues.append("packet answer_evaluation must be False")
    if packet.get("non_official") is not True:
        issues.append("packet non_official must be True")
    if packet.get("non_clinical") is not True:
        issues.append("packet non_clinical must be True")
    if packet.get("non_benchmark_report") is not True:
        issues.append("packet non_benchmark_report must be True")
    if packet.get("in_memory_only") is not True:
        issues.append("packet in_memory_only must be True")
    if packet.get("operator_review_status") not in ALLOWED_OPERATOR_REVIEW_STATUSES:
        issues.append("invalid operator_review_status")
    if packet.get("operator_decision") not in ALLOWED_OPERATOR_DECISIONS:
        issues.append("invalid operator_decision")

    for key, expected in _default_safety_boundaries().items():
        if (packet.get("safety_boundaries") or {}).get(key) is not expected:
            issues.append(f"safety boundary {key} must be {expected}")

    finding_summary = packet.get("finding_summary") or {}
    if finding_summary.get("redacted_count_only") is not True:
        issues.append("finding summary must be redacted/count-only")
    plan_summary = packet.get("plan_summary") or {}
    if plan_summary.get("redacted_count_only") is not True:
        issues.append("plan summary must be redacted/count-only")

    if plan is not None:
        plan_validation = validate_ai_audit_plan_v1(plan)
        if not plan_validation.get("valid", False):
            issues.append("plan is invalid")
        if packet.get("plan_id") != plan.get("plan_id"):
            issues.append("packet plan_id does not match plan")

    if findings is not None:
        for finding in findings:
            finding_validation = validate_ai_audit_finding_v1(finding, plan=plan)
            if not finding_validation.get("valid", False):
                issues.append(f"invalid finding: {finding.get('finding_id', '')}")
            if finding.get("plan_id") != packet.get("plan_id"):
                issues.append(f"finding plan_id mismatch: {finding.get('finding_id', '')}")

    issues.extend(_find_forbidden_packet_fields(packet))

    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "packet_id": packet.get("packet_id", ""),
        "plan_id": packet.get("plan_id", ""),
        "executable": bool(packet.get("executable", True)),
        "operator_review_status": packet.get("operator_review_status", "unknown"),
        "operator_decision": packet.get("operator_decision", "unknown"),
        "protected_items_copied": finding_summary.get("protected_items_copied", False),
        "answer_keys_used": finding_summary.get("answer_keys_used", False),
        "official_score_claimed": finding_summary.get("official_score_claimed", False),
        "certification_claimed": False,
        "official_benchmark_claimed": False,
        "benchmark_tuning_performed": finding_summary.get("benchmark_tuning_performed", False),
        "runtime_behavior_changed": finding_summary.get("runtime_behavior_changed", False),
    }


def summarize_ai_audit_review_packet_v1(packet: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted/count-only operator review packet summary."""
    validation = validate_ai_audit_review_packet_v1(packet)
    target_summary = packet.get("target_summary", {}) if isinstance(packet, dict) else {}
    finding_summary = packet.get("finding_summary", {}) if isinstance(packet, dict) else {}
    return {
        "schema_version": "ai_audit_review_packet_summary_v1",
        "redacted_count_only": True,
        "target_name": target_summary.get("target_name", "unknown_target"),
        "target_kind": target_summary.get("target_kind", "unknown"),
        "selected_probe_count": packet.get("selected_probe_count", 0) if isinstance(packet, dict) else 0,
        "finding_count": packet.get("finding_count", 0) if isinstance(packet, dict) else 0,
        "verdict_counts": dict(finding_summary.get("verdict_counts", {})),
        "finding_type_counts": dict(finding_summary.get("finding_type_counts", {})),
        "safety_status": "safe_review_packet" if validation["valid"] else "invalid_review_packet",
        "validation_valid": validation["valid"],
        "issue_count": len(validation["issues"]),
        "operator_review_status": packet.get("operator_review_status", "unknown") if isinstance(packet, dict) else "unknown",
        "operator_decision": packet.get("operator_decision", "unknown") if isinstance(packet, dict) else "unknown",
        "executable": bool(packet.get("executable", True)) if isinstance(packet, dict) else True,
    }


def set_ai_audit_review_packet_decision_v1(
    packet: dict[str, Any],
    decision: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Return a copy of packet with in-memory operator decision placeholders updated."""
    if decision not in ALLOWED_OPERATOR_DECISIONS:
        raise ValueError("invalid operator decision")
    updated = deepcopy(packet)
    updated["operator_decision"] = decision
    updated["operator_review_status"] = "pending_review" if decision == "none" else "reviewed"
    if notes is not None:
        updated["operator_decision_notes"] = notes
    updated["validation_status"] = validate_ai_audit_review_packet_v1(updated)
    return updated
