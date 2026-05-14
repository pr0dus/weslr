"""WESLR AI audit redacted report helpers V1.

Safe, non-executing helpers for turning an AI audit review packet into an
operator-readable redacted report structure and Markdown rendering. Reports are
not runners, not scoring engines, not official benchmark reports, not clinical
claims, and not certification claims. Helpers do not persist files or modify
runtime/chat/voice behavior.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any

from weslr.ai_audit_review_packet import summarize_ai_audit_review_packet_v1, validate_ai_audit_review_packet_v1


REPORT_SCHEMA_VERSION = "ai_audit_redacted_report_v1"
FORBIDDEN_REPORT_FIELDS = {
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
    "reviewer_notes",
}
FORBIDDEN_RENDER_TEXT = {
    "answer_key",
    "official_score",
    "official score",
    "iq score",
    "clinical score",
    "certification claim",
    "protected test item",
    "hidden prompt",
    "reviewer_notes",
}


@dataclass
class AIAuditRedactedReportV1:
    schema_version: str = REPORT_SCHEMA_VERSION
    report_id: str = ""
    packet_id: str = ""
    plan_id: str = ""
    target_summary: dict[str, Any] = field(default_factory=dict)
    audit_scope_summary: dict[str, Any] = field(default_factory=dict)
    total_selected_probes: int = 0
    total_findings: int = 0
    verdict_counts: dict[str, int] = field(default_factory=dict)
    finding_type_counts: dict[str, int] = field(default_factory=dict)
    safety_boundaries: dict[str, Any] = field(default_factory=dict)
    validation_status: dict[str, Any] = field(default_factory=dict)
    operator_review_status: str = "pending_review"
    operator_decision: str = "none"
    disclaimer: dict[str, bool] = field(default_factory=dict)
    in_memory_only: bool = True
    report_persistence: bool = False
    executable: bool = False
    scoring_engine: bool = False


def _stable_report_id(packet_id: str, plan_id: str) -> str:
    return "weslr_ai_audit_redacted_report_v1_" + sha256(f"{packet_id}|{plan_id}".encode("utf-8")).hexdigest()[:12]


def _default_disclaimer() -> dict[str, bool]:
    return {
        "non_official": True,
        "non_clinical": True,
        "non_certification": True,
        "synthetic_weslr_native": True,
        "dry_review_only": True,
        "not_executable": True,
        "not_benchmark_report": True,
        "findings_are_evidence_containers_not_final_truth": True,
    }


def _default_safety_boundaries() -> dict[str, Any]:
    return {
        "execution_allowed": False,
        "runner_created": False,
        "model_calls": False,
        "scoring_engine": False,
        "automated_grading": False,
        "answer_evaluation": False,
        "report_persistence": False,
        "protected_item_free": True,
        "answer_key_free": True,
        "official_score_claimed": False,
        "certification_claimed": False,
        "official_benchmark_claimed": False,
        "clinical_validity_claimed": False,
        "runtime_behavior_change": False,
    }


def _find_forbidden_report_fields(value: Any, path: str = "report") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_REPORT_FIELDS:
                issues.append(f"forbidden report field: {nested_path}")
            issues.extend(_find_forbidden_report_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden_report_fields(nested, f"{path}[{index}]"))
    return issues


def build_ai_audit_redacted_report_v1(packet: dict[str, Any]) -> dict[str, Any]:
    """Build a redacted, in-memory report structure from a review packet."""
    packet_copy = deepcopy(packet)
    packet_summary = summarize_ai_audit_review_packet_v1(packet_copy)
    packet_validation = validate_ai_audit_review_packet_v1(packet_copy)
    packet_id = str(packet_copy.get("packet_id", ""))
    plan_id = str(packet_copy.get("plan_id", ""))
    report = asdict(
        AIAuditRedactedReportV1(
            report_id=_stable_report_id(packet_id, plan_id),
            packet_id=packet_id,
            plan_id=plan_id,
            target_summary={
                "redacted_count_only": True,
                "target_name": packet_summary.get("target_name", "unknown_target"),
                "target_kind": packet_summary.get("target_kind", "unknown"),
            },
            audit_scope_summary={
                "redacted_count_only": True,
                "scope": "operator_review_of_synthetic_weslr_native_ai_audit_packet",
                "dry_review_only": True,
                "not_executable": True,
            },
            total_selected_probes=int(packet_summary.get("selected_probe_count", 0)),
            total_findings=int(packet_summary.get("finding_count", 0)),
            verdict_counts=dict(packet_summary.get("verdict_counts", {})),
            finding_type_counts=dict(packet_summary.get("finding_type_counts", {})),
            safety_boundaries=_default_safety_boundaries(),
            validation_status={
                "redacted_count_only": True,
                "packet_valid": packet_validation.get("valid", False),
                "report_valid": False,
                "packet_issue_count": len(packet_validation.get("issues", [])),
            },
            operator_review_status=str(packet_summary.get("operator_review_status", "unknown")),
            operator_decision=str(packet_summary.get("operator_decision", "unknown")),
            disclaimer=_default_disclaimer(),
        )
    )
    validation = validate_ai_audit_redacted_report_v1(report)
    report["validation_status"]["report_valid"] = validation["valid"]
    report["validation_status"]["report_issue_count"] = len(validation["issues"])
    return report


def validate_ai_audit_redacted_report_v1(report: dict[str, Any]) -> dict[str, Any]:
    """Validate a redacted report structure without rendering or persistence side effects."""
    issues: list[str] = []
    if not isinstance(report, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["report must be a dict"]}

    for field_name in ("report_id", "packet_id", "plan_id", "target_summary", "audit_scope_summary"):
        if field_name not in report or report.get(field_name) in (None, "", {}):
            issues.append(f"missing {field_name}")

    disclaimer = report.get("disclaimer") or {}
    for key, expected in _default_disclaimer().items():
        if disclaimer.get(key) is not expected:
            issues.append(f"disclaimer {key} must be {expected}")

    if report.get("executable") is not False:
        issues.append("report executable must be False")
    if report.get("scoring_engine") is not False:
        issues.append("report scoring_engine must be False")
    if report.get("in_memory_only") is not True:
        issues.append("report in_memory_only must be True")
    if report.get("report_persistence") is not False:
        issues.append("report_persistence must be False")

    for key, expected in _default_safety_boundaries().items():
        if (report.get("safety_boundaries") or {}).get(key) is not expected:
            issues.append(f"safety boundary {key} must be {expected}")

    target_summary = report.get("target_summary") or {}
    audit_scope_summary = report.get("audit_scope_summary") or {}
    if target_summary.get("redacted_count_only") is not True:
        issues.append("target summary must be redacted/count-only")
    if audit_scope_summary.get("redacted_count_only") is not True:
        issues.append("audit scope summary must be redacted/count-only")

    issues.extend(_find_forbidden_report_fields(report))

    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "report_id": report.get("report_id", ""),
        "packet_id": report.get("packet_id", ""),
        "plan_id": report.get("plan_id", ""),
        "executable": bool(report.get("executable", True)),
        "non_official": disclaimer.get("non_official") is True,
        "non_clinical": disclaimer.get("non_clinical") is True,
        "non_certification": disclaimer.get("non_certification") is True,
        "protected_items_copied": False,
        "answer_keys_used": False,
        "official_score_claimed": False,
        "certification_claimed": False,
        "official_benchmark_claimed": False,
        "runtime_behavior_changed": False,
    }


def render_ai_audit_redacted_report_markdown_v1(report: dict[str, Any]) -> str:
    """Render a deterministic redacted Markdown report without writing files."""
    safe_report = to_ai_audit_redacted_report_json_safe_v1(report)
    target = safe_report.get("target_summary", {})
    verdict_counts = safe_report.get("verdict_counts", {})
    finding_type_counts = safe_report.get("finding_type_counts", {})
    disclaimer = safe_report.get("disclaimer", {})

    def bullet_counts(counts: dict[str, int]) -> list[str]:
        if not counts:
            return ["- none: 0"]
        return [f"- {key}: {counts[key]}" for key in sorted(counts)]

    lines = [
        "# AI Audit Review Report",
        "",
        "## Target",
        f"- Name: {target.get('target_name', 'unknown_target')}",
        f"- Kind: {target.get('target_kind', 'unknown')}",
        "",
        "## Scope",
        f"- Selected synthetic probes: {safe_report.get('total_selected_probes', 0)}",
        f"- Findings: {safe_report.get('total_findings', 0)}",
        "- Mode: dry review only; not executable",
        "",
        "## Findings Summary",
        "### Verdict Counts",
        *bullet_counts(verdict_counts),
        "",
        "### Finding Type Counts",
        *bullet_counts(finding_type_counts),
        "",
        "## Safety / Boundary Notes",
        "- No model calls, no runner, no scoring engine, no answer evaluation.",
        "- Redacted/count-only report; raw reviewer notes and protected material are omitted.",
        "",
        "## Operator Review Status",
        f"- Review status: {safe_report.get('operator_review_status', 'unknown')}",
        f"- Decision: {safe_report.get('operator_decision', 'unknown')}",
        "",
        "## Disclaimer",
        f"- Non-official: {disclaimer.get('non_official') is True}",
        f"- Non-clinical: {disclaimer.get('non_clinical') is True}",
        f"- Non-certification: {disclaimer.get('non_certification') is True}",
        f"- Synthetic WESLR-native: {disclaimer.get('synthetic_weslr_native') is True}",
        f"- Dry review only: {disclaimer.get('dry_review_only') is True}",
        f"- Not executable: {disclaimer.get('not_executable') is True}",
        "- Findings are evidence containers, not final truth.",
    ]
    return "\n".join(lines) + "\n"


def to_ai_audit_redacted_report_json_safe_v1(report: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe redacted report copy without writing to disk."""
    safe = deepcopy(report)
    for forbidden in FORBIDDEN_REPORT_FIELDS:
        safe.pop(forbidden, None)
    return safe
