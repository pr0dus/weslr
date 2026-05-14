"""WESLR AI audit operator review surface helpers V1.

Read-only, in-memory helpers for operator inspection of AI audit review packets,
redacted reports, and derived cards. This surface is not a runner, not a scoring
engine, not runtime wiring, and not persistence.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any

from weslr.ai_audit_report import summarize_ai_audit_review_packet_v1, validate_ai_audit_redacted_report_v1
from weslr.ai_audit_review_packet import summarize_ai_audit_review_packet_v1 as summarize_packet_v1, validate_ai_audit_review_packet_v1


REVIEW_SURFACE_SCHEMA_VERSION = "ai_audit_operator_review_card_v1"
FORBIDDEN_CARD_FIELDS = {
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


@dataclass
class AIAuditOperatorReviewCardV1:
    schema_version: str = REVIEW_SURFACE_SCHEMA_VERSION
    card_id: str = ""
    source_type: str = "unknown"
    target_name: str = "unknown_target"
    target_kind: str = "unknown"
    plan_id: str = ""
    packet_id: str = ""
    report_id: str = ""
    total_probes: int = 0
    total_findings: int = 0
    verdict_counts: dict[str, int] = field(default_factory=dict)
    finding_type_counts: dict[str, int] = field(default_factory=dict)
    operator_review_status: str = "unknown"
    operator_decision: str = "unknown"
    safety_status: str = "unknown"
    validation_status: str = "unknown"
    execution_status: str = "dry_review_only"
    executable: bool = False
    scoring_engine: bool = False
    report_persistence: bool = False
    in_memory_only: bool = True
    redacted_count_only: bool = True


def _stable_card_id(source_type: str, plan_id: str, packet_id: str = "", report_id: str = "") -> str:
    seed = "|".join([source_type, plan_id, packet_id, report_id])
    return "weslr_ai_audit_review_card_v1_" + sha256(seed.encode("utf-8")).hexdigest()[:12]


def _source_type(item: dict[str, Any]) -> str:
    schema = str(item.get("schema_version", ""))
    if schema == "ai_audit_review_packet_v1" or "finding_summary" in item:
        return "review_packet"
    if schema == "ai_audit_redacted_report_v1" or "report_id" in item:
        return "redacted_report"
    if schema == REVIEW_SURFACE_SCHEMA_VERSION or "card_id" in item:
        return "review_card"
    return "unknown"


def _find_forbidden_card_fields(value: Any, path: str = "card") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_CARD_FIELDS:
                issues.append(f"forbidden review card field: {nested_path}")
            issues.extend(_find_forbidden_card_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden_card_fields(nested, f"{path}[{index}]"))
    return issues


def build_ai_audit_operator_review_card_v1(packet_or_report: dict[str, Any]) -> dict[str, Any]:
    """Build a redacted operator review card from a review packet or report."""
    item = deepcopy(packet_or_report)
    source_type = _source_type(item)
    if source_type == "review_packet":
        summary = summarize_packet_v1(item)
        validation = validate_ai_audit_review_packet_v1(item)
        packet_id = str(item.get("packet_id", ""))
        report_id = ""
        total_probes = int(summary.get("selected_probe_count", 0))
        total_findings = int(summary.get("finding_count", 0))
    elif source_type == "redacted_report":
        validation = validate_ai_audit_redacted_report_v1(item)
        summary = {
            "target_name": (item.get("target_summary") or {}).get("target_name", "unknown_target"),
            "target_kind": (item.get("target_summary") or {}).get("target_kind", "unknown"),
            "verdict_counts": dict(item.get("verdict_counts", {})),
            "finding_type_counts": dict(item.get("finding_type_counts", {})),
            "operator_review_status": item.get("operator_review_status", "unknown"),
            "operator_decision": item.get("operator_decision", "unknown"),
            "safety_status": "safe_review_packet" if validation.get("valid") else "invalid_review_packet",
            "validation_valid": validation.get("valid", False),
        }
        packet_id = str(item.get("packet_id", ""))
        report_id = str(item.get("report_id", ""))
        total_probes = int(item.get("total_selected_probes", 0))
        total_findings = int(item.get("total_findings", 0))
    elif source_type == "review_card":
        return deepcopy(item)
    else:
        summary = {}
        validation = {"valid": False, "issues": ["unknown source type"]}
        packet_id = str(item.get("packet_id", ""))
        report_id = str(item.get("report_id", ""))
        total_probes = int(item.get("total_probes", 0) or 0)
        total_findings = int(item.get("total_findings", 0) or 0)

    plan_id = str(item.get("plan_id", ""))
    card = asdict(
        AIAuditOperatorReviewCardV1(
            card_id=_stable_card_id(source_type, plan_id, packet_id, report_id),
            source_type=source_type,
            target_name=str(summary.get("target_name", "unknown_target")),
            target_kind=str(summary.get("target_kind", "unknown")),
            plan_id=plan_id,
            packet_id=packet_id,
            report_id=report_id,
            total_probes=total_probes,
            total_findings=total_findings,
            verdict_counts=dict(summary.get("verdict_counts", {})),
            finding_type_counts=dict(summary.get("finding_type_counts", {})),
            operator_review_status=str(summary.get("operator_review_status", "unknown")),
            operator_decision=str(summary.get("operator_decision", "unknown")),
            safety_status=str(summary.get("safety_status", "unknown")),
            validation_status="valid" if validation.get("valid") else "invalid",
            execution_status=str(item.get("execution_status", "dry_review_only")),
        )
    )
    card_validation = validate_ai_audit_operator_review_card_v1(card)
    card["validation_status"] = "valid" if card_validation["valid"] else "invalid"
    return card


def validate_ai_audit_operator_review_card_v1(card: dict[str, Any]) -> dict[str, Any]:
    """Validate a redacted operator review card."""
    issues: list[str] = []
    if not isinstance(card, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["card must be a dict"]}
    for field_name in ("card_id", "source_type", "target_name", "target_kind", "plan_id", "total_probes", "total_findings"):
        if field_name not in card or card.get(field_name) in (None, ""):
            issues.append(f"missing {field_name}")
    if card.get("execution_status") not in {"dry_review_only", "not_executable"}:
        issues.append("card execution_status must be dry_review_only or not_executable")
    if card.get("executable") is not False:
        issues.append("card executable must be False")
    if card.get("scoring_engine") is not False:
        issues.append("card scoring_engine must be False")
    if card.get("report_persistence") is not False:
        issues.append("card report_persistence must be False")
    if card.get("in_memory_only") is not True:
        issues.append("card in_memory_only must be True")
    if card.get("redacted_count_only") is not True:
        issues.append("card redacted_count_only must be True")
    issues.extend(_find_forbidden_card_fields(card))
    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "card_id": card.get("card_id", ""),
        "source_type": card.get("source_type", "unknown"),
        "safety_status": card.get("safety_status", "unknown"),
        "validation_status": card.get("validation_status", "unknown"),
        "executable": bool(card.get("executable", True)),
        "answer_keys_used": False,
        "official_score_claimed": False,
        "certification_claimed": False,
        "official_benchmark_claimed": False,
        "protected_items_copied": False,
        "runtime_behavior_changed": False,
    }


def build_ai_audit_operator_review_list_v1(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a deterministic redacted operator review list from packets/reports/cards."""
    cards = [build_ai_audit_operator_review_card_v1(item) for item in deepcopy(list(items or []))]
    cards = sorted(cards, key=lambda card: (str(card.get("target_name", "")), str(card.get("plan_id", "")), str(card.get("card_id", ""))))
    status_counts: dict[str, int] = {}
    decision_counts: dict[str, int] = {}
    for card in cards:
        status = str(card.get("operator_review_status", "unknown"))
        decision = str(card.get("operator_decision", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
    return {
        "schema_version": "ai_audit_operator_review_list_v1",
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": "dry_review_only",
        "executable": False,
        "card_count": len(cards),
        "cards": cards,
        "summary": {
            "redacted_count_only": True,
            "card_count": len(cards),
            "operator_review_status_counts": dict(sorted(status_counts.items())),
            "operator_decision_counts": dict(sorted(decision_counts.items())),
        },
    }


def filter_ai_audit_operator_review_cards_v1(
    cards: list[dict[str, Any]],
    *,
    target_kind: str | None = None,
    operator_review_status: str | None = None,
    operator_decision: str | None = None,
    validation_status: str | None = None,
    safety_status: str | None = None,
    min_findings: int | None = None,
) -> list[dict[str, Any]]:
    """Filter redacted cards deterministically without mutating inputs."""
    selected = []
    for card in deepcopy(list(cards or [])):
        if target_kind is not None and card.get("target_kind") != target_kind:
            continue
        if operator_review_status is not None and card.get("operator_review_status") != operator_review_status:
            continue
        if operator_decision is not None and card.get("operator_decision") != operator_decision:
            continue
        if validation_status is not None and card.get("validation_status") != validation_status:
            continue
        if safety_status is not None and card.get("safety_status") != safety_status:
            continue
        if min_findings is not None and int(card.get("total_findings", 0)) < min_findings:
            continue
        selected.append(card)
    return sorted(selected, key=lambda card: (str(card.get("target_name", "")), str(card.get("plan_id", "")), str(card.get("card_id", ""))))


def render_ai_audit_operator_review_surface_markdown_v1(cards_or_list: list[dict[str, Any]] | dict[str, Any]) -> str:
    """Render a deterministic redacted Markdown overview for operator inspection."""
    if isinstance(cards_or_list, dict) and "cards" in cards_or_list:
        review_list = deepcopy(cards_or_list)
    else:
        review_list = build_ai_audit_operator_review_list_v1(list(cards_or_list or []))
    cards = list(review_list.get("cards", []))
    lines = [
        "# AI Audit Operator Review Surface",
        "",
        "## Summary",
        f"- Cards: {len(cards)}",
        "- Mode: read-only, dry review only, not executable",
        "",
        "## Cards",
    ]
    if not cards:
        lines.append("- none")
    for card in cards:
        lines.extend(
            [
                f"- Card: {card.get('card_id', 'unknown')}",
                f"  - Target: {card.get('target_name', 'unknown_target')} ({card.get('target_kind', 'unknown')})",
                f"  - Source: {card.get('source_type', 'unknown')}",
                f"  - Plan: {card.get('plan_id', '')}",
                f"  - Probes: {card.get('total_probes', 0)}; Findings: {card.get('total_findings', 0)}",
                f"  - Review: {card.get('operator_review_status', 'unknown')} / {card.get('operator_decision', 'unknown')}",
                f"  - Safety: {card.get('safety_status', 'unknown')}; Validation: {card.get('validation_status', 'unknown')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Boundaries",
            "- No model calls, no runner, no scoring engine, no answer evaluation.",
            "- No protected material, no answer keys, no official scoring or certification claims.",
            "",
            "## Non-execution Disclaimer",
            "- This review surface is read-only operator review infrastructure.",
            "- Cards are not official benchmark reports and not certification claims.",
            "- Findings remain evidence containers, not final truth.",
        ]
    )
    return "\n".join(lines) + "\n"
