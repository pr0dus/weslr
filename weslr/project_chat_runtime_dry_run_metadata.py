"""Metadata-only helpers for WESLR project-chat runtime dry-run V1."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from weslr.project_chat_answer_plan_metadata_helpers import (
    DENIED_AUTHORITY_FIELDS_V1 as ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_answer_plan_v1,
    validate_project_chat_answer_plan_v1,
)

HELPER_TYPE_V1 = "weslr_project_chat_runtime_dry_run_metadata_v1"
SCHEMA_VERSION_V1 = "project_chat_runtime_dry_run_metadata_v1"

DRY_RUN_STAGES_V1 = (
    "message_intake",
    "project_context_resolution",
    "memory_context_resolution",
    "continuity_state_resolution",
    "gap_analysis_candidate_resolution",
    "retrieval_need_resolution",
    "evidence_packet_resolution",
    "tool_lane_candidate_resolution",
    "answer_plan_metadata_resolution",
    "final_answer_generation_boundary",
    "operator_observability_event",
    "optional_persistence_candidate",
    "user_confirmation_or_correction",
)

DRY_RUN_STATUSES_V1 = (
    "dry_run_valid_metadata_only",
    "clarification_required",
    "approval_required",
    "operator_review_required",
    "blocked",
    "invalid",
)

DRY_RUN_DECISIONS_V1 = (
    "proceed_to_answer_plan_metadata",
    "ask_clarifying_question",
    "request_user_approval",
    "request_operator_review",
    "block_due_to_boundary",
    "block_due_to_missing_evidence",
    "block_due_to_contradiction",
    "block_due_to_stale_or_invalidated_state",
    "block_due_to_tool_execution_boundary",
    "block_due_to_persistence_boundary",
    "block_due_to_private_mechanism_boundary",
)

_DEFAULT_FALSE_DENIED_AUTHORITY = {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1}


def allowed_project_chat_runtime_dry_run_stages_v1() -> tuple[str, ...]:
    return DRY_RUN_STAGES_V1


def allowed_project_chat_runtime_dry_run_statuses_v1() -> tuple[str, ...]:
    return DRY_RUN_STATUSES_V1


def allowed_project_chat_runtime_dry_run_decisions_v1() -> tuple[str, ...]:
    return DRY_RUN_DECISIONS_V1


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        items = [value]
    elif isinstance(value, Mapping):
        items = list(value.keys())
    else:
        try:
            items = list(value)
        except TypeError:
            items = [value]
    return [_safe_str(item) for item in items if _safe_str(item)]


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_str(value)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    safe_payload = _json_safe(payload)
    blob = json.dumps(safe_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_refs(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))


def _normalize_flags(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))


def _normalize_stage_results(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    results: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            results.append({str(key): _json_safe(val) for key, val in item.items()})
        else:
            results.append({"stage": _safe_str(item), "status": "invalid", "decision": "invalid"})
    return results


def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    payload = dict(_DEFAULT_FALSE_DENIED_AUTHORITY)
    raw = _as_mapping(value)
    for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1:
        payload[field] = _safe_bool(raw.get(field, False))
    return payload


def _coalesce_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    elif payload is not None:
        data["payload"] = payload
    data.update(overrides)
    return data


def _is_unknown(value: str) -> bool:
    return not value or value not in DRY_RUN_STAGES_V1


def _default_user_visible_status(dry_run: Mapping[str, Any]) -> str:
    status = _safe_str(dry_run.get("dry_run_status"))
    decision = _safe_str(dry_run.get("dry_run_decision"))
    if status == "blocked" or decision.startswith("block_due_to_"):
        return "dry-run blocked"
    if status == "operator_review_required" or decision == "request_operator_review":
        return "operator review required"
    if status == "approval_required" or decision == "request_user_approval":
        return "approval required"
    if status == "clarification_required" or decision == "ask_clarifying_question":
        return "clarification needed"
    return "dry-run metadata only"


def _default_operator_visible_summary(dry_run: Mapping[str, Any]) -> str:
    stage_count = len(_safe_list(dry_run.get("stage_results")))
    return (
        f"{_safe_str(dry_run.get('dry_run_decision'))} | "
        f"{_safe_str(dry_run.get('dry_run_status'))} | "
        f"stages={stage_count} | "
        f"retrieval={_safe_str(dry_run.get('retrieval_need_class'))}"
    )


def _build_default_answer_plan_payload(dry_run: Mapping[str, Any]) -> dict[str, Any]:
    mode = "clarifying_question"
    scope = "current_message_only"
    status = "clarification_required"
    decision = _safe_str(dry_run.get("dry_run_decision"))
    retrieval_need = _safe_str(dry_run.get("retrieval_need_class"))
    if decision == "proceed_to_answer_plan_metadata":
        if retrieval_need in {"project_metadata_only", "none", ""}:
            mode = "project_start_guidance"
            scope = "project_metadata_only"
            status = "plan_valid_metadata_only"
        elif retrieval_need == "approved_evidence_packet":
            mode = "evidence_grounded_answer"
            scope = "approved_evidence_packet"
            status = "plan_valid_metadata_only"
        elif retrieval_need == "tool_lane_candidate_only":
            mode = "tool_request_boundary_response"
            scope = "tool_lane_candidate_only"
            status = "plan_valid_metadata_only"
        else:
            mode = "uncertain_or_missing_evidence_answer"
            scope = "approved_project_context"
            status = "plan_valid_metadata_only"
    return {
        "project_id": _safe_str(dry_run.get("project_id")),
        "owner_user_scope": _safe_str(dry_run.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(dry_run.get("tenant_account_scope")),
        "source_scope": _safe_str(dry_run.get("source_scope")),
        "user_intent_class": _safe_str(dry_run.get("user_intent_class")),
        "answer_mode": mode,
        "allowed_answer_scope": scope,
        "answer_status": status,
        "evidence_packet_refs": _normalize_refs(dry_run.get("evidence_packet_refs")),
        "project_state_refs": _normalize_refs(dry_run.get("project_state_refs")),
        "memory_state_refs": _normalize_refs(dry_run.get("memory_state_refs")),
        "continuity_state_refs": _normalize_refs(dry_run.get("continuity_state_refs")),
        "gap_analysis_refs": _normalize_refs(dry_run.get("gap_analysis_refs")),
        "tool_lane_candidate_refs": _normalize_refs(dry_run.get("tool_lane_candidate_refs")),
        "operator_visibility_refs": _normalize_refs(dry_run.get("operator_visibility_refs")),
        "approval_refs": _normalize_refs(dry_run.get("approval_refs")),
        "user_visible_status": _safe_str(dry_run.get("user_visible_status")) or _default_user_visible_status(dry_run),
        "operator_visible_summary": _safe_str(dry_run.get("operator_visible_summary")) or "dry-run answer-plan metadata",
        "denied_authority": _normalize_denied_authority(dry_run.get("denied_authority")),
    }


def _build_status_probe_answer_plan(dry_run: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "project_id": _safe_str(dry_run.get("project_id")) or "project-001",
        "owner_user_scope": _safe_str(dry_run.get("owner_user_scope")) or "owner-user",
        "tenant_account_scope": _safe_str(dry_run.get("tenant_account_scope")) or "tenant-a",
        "source_scope": _safe_str(dry_run.get("source_scope")) or "project_metadata_only",
        "user_intent_class": _safe_str(dry_run.get("user_intent_class")) or "project-chat",
        "answer_mode": "clarifying_question",
        "allowed_answer_scope": "current_message_only",
        "answer_status": "clarification_required",
        "user_visible_status": _safe_str(dry_run.get("user_visible_status")) or "clarification needed",
        "operator_visible_summary": _safe_str(dry_run.get("operator_visible_summary")) or "dry-run status probe",
        "denied_authority": dict(_DEFAULT_FALSE_DENIED_AUTHORITY),
    }


def _stage_result(stage: str, status: str, decision: str, **extra: Any) -> dict[str, Any]:
    result = {
        "stage": stage,
        "status": status,
        "decision": decision,
    }
    result.update(extra)
    return result


def build_project_chat_runtime_dry_run_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)

    dry_run = {
        "schema_version": _safe_str(data.get("schema_version")) or SCHEMA_VERSION_V1,
        "dry_run_id": _safe_str(data.get("dry_run_id")),
        "project_id": _safe_str(data.get("project_id")),
        "owner_user_scope": _safe_str(data.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(data.get("tenant_account_scope")),
        "source_scope": _safe_str(data.get("source_scope")),
        "user_intent_class": _safe_str(data.get("user_intent_class")),
        "dry_run_status": _safe_str(data.get("dry_run_status")),
        "dry_run_decision": _safe_str(data.get("dry_run_decision")),
        "stage_results": _normalize_stage_results(data.get("stage_results")),
        "project_state_refs": _normalize_refs(data.get("project_state_refs")),
        "memory_state_refs": _normalize_refs(data.get("memory_state_refs")),
        "continuity_state_refs": _normalize_refs(data.get("continuity_state_refs")),
        "gap_analysis_refs": _normalize_refs(data.get("gap_analysis_refs")),
        "retrieval_need_class": _safe_str(data.get("retrieval_need_class")),
        "evidence_packet_refs": _normalize_refs(data.get("evidence_packet_refs")),
        "tool_lane_candidate_refs": _normalize_refs(data.get("tool_lane_candidate_refs")),
        "answer_plan_ref": _safe_str(data.get("answer_plan_ref")),
        "answer_plan_metadata": _as_mapping(data.get("answer_plan_metadata")),
        "operator_visibility_refs": _normalize_refs(data.get("operator_visibility_refs")),
        "approval_refs": _normalize_refs(data.get("approval_refs")),
        "uncertainty_flags": _normalize_flags(data.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(data.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(data.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(data.get("missing_evidence_flags")),
        "privacy_flags": _normalize_flags(data.get("privacy_flags")),
        "persistence_candidate_refs": _normalize_refs(data.get("persistence_candidate_refs")),
        "blocked_authority": _safe_str(data.get("blocked_authority")),
        "limitations": _normalize_flags(data.get("limitations")),
        "user_visible_status": _safe_str(data.get("user_visible_status")),
        "operator_visible_summary": _safe_str(data.get("operator_visible_summary")),
        "denied_authority": _normalize_denied_authority(data.get("denied_authority")),
        "helper_type": HELPER_TYPE_V1,
        "raw_content_stored": False,
    }

    if not dry_run["dry_run_id"]:
        digest_source = {k: v for k, v in dry_run.items() if k not in {"dry_run_id", "operator_visible_summary", "user_visible_status"}}
        dry_run["dry_run_id"] = f"project-chat-runtime-dry-run-{_stable_digest(digest_source)[:16]}"

    if not dry_run["answer_plan_ref"]:
        dry_run["answer_plan_ref"] = f"answer-plan-ref-{dry_run['dry_run_id']}"

    if not dry_run["stage_results"]:
        dry_run["stage_results"] = []

    if not dry_run["dry_run_status"]:
        dry_run["dry_run_status"] = "dry_run_valid_metadata_only"
    if not dry_run["dry_run_decision"]:
        dry_run["dry_run_decision"] = "proceed_to_answer_plan_metadata"

    answer_plan_payload = data.get("answer_plan_metadata") if isinstance(data.get("answer_plan_metadata"), Mapping) else data.get("answer_plan_payload")
    if isinstance(answer_plan_payload, Mapping):
        answer_plan_candidate = build_project_chat_answer_plan_v1(answer_plan_payload)
    else:
        answer_plan_candidate = build_project_chat_answer_plan_v1(_build_default_answer_plan_payload(dry_run))

    answer_plan_validation = validate_project_chat_answer_plan_v1(answer_plan_candidate)
    dry_run["answer_plan_metadata"] = answer_plan_validation["answer_plan"]
    dry_run["answer_plan_validation"] = answer_plan_validation
    if not dry_run["answer_plan_ref"]:
        dry_run["answer_plan_ref"] = f"answer-plan-ref-{answer_plan_validation['answer_plan_id']}"

    if not data.get("stage_results"):
        stage_results = [
            _stage_result(
                "message_intake",
                "passed" if dry_run["project_id"] and dry_run["owner_user_scope"] and dry_run["tenant_account_scope"] and dry_run["source_scope"] and dry_run["user_intent_class"] else "invalid",
                "ask_clarifying_question" if dry_run["dry_run_status"] == "clarification_required" else "proceed_to_answer_plan_metadata",
                project_id=dry_run["project_id"],
            ),
            _stage_result(
                "project_context_resolution",
                "resolved" if dry_run["project_id"] and dry_run["source_scope"] else "blocked",
                "proceed_to_answer_plan_metadata",
                project_state_refs=dry_run["project_state_refs"],
            ),
            _stage_result(
                "memory_context_resolution",
                "resolved",
                "proceed_to_answer_plan_metadata",
                memory_state_refs=dry_run["memory_state_refs"],
            ),
            _stage_result(
                "continuity_state_resolution",
                "stale_or_invalidated" if dry_run["stale_state_flags"] else "resolved",
                "block_due_to_stale_or_invalidated_state" if dry_run["stale_state_flags"] else "proceed_to_answer_plan_metadata",
                continuity_state_refs=dry_run["continuity_state_refs"],
            ),
            _stage_result(
                "gap_analysis_candidate_resolution",
                "resolved" if dry_run["gap_analysis_refs"] else "resolved",
                "proceed_to_answer_plan_metadata",
                gap_analysis_refs=dry_run["gap_analysis_refs"],
            ),
            _stage_result(
                "retrieval_need_resolution",
                "approval_required" if dry_run["retrieval_need_class"] in {"external_private", "private", "external"} and not dry_run["approval_refs"] else "resolved",
                "request_user_approval" if dry_run["retrieval_need_class"] in {"external_private", "private", "external"} and not dry_run["approval_refs"] else "proceed_to_answer_plan_metadata",
                retrieval_need_class=dry_run["retrieval_need_class"],
            ),
            _stage_result(
                "evidence_packet_resolution",
                "blocked_missing_evidence" if (_safe_str(answer_plan_candidate.get("answer_mode")) == "evidence_grounded_answer" or dry_run["retrieval_need_class"] == "approved_evidence_packet") and not dry_run["evidence_packet_refs"] else "resolved",
                "block_due_to_missing_evidence" if (_safe_str(answer_plan_candidate.get("answer_mode")) == "evidence_grounded_answer" or dry_run["retrieval_need_class"] == "approved_evidence_packet") and not dry_run["evidence_packet_refs"] else "proceed_to_answer_plan_metadata",
                evidence_packet_refs=dry_run["evidence_packet_refs"],
            ),
            _stage_result(
                "tool_lane_candidate_resolution",
                "candidate_only" if dry_run["tool_lane_candidate_refs"] else "resolved",
                "proceed_to_answer_plan_metadata",
                tool_lane_candidate_refs=dry_run["tool_lane_candidate_refs"],
            ),
            _stage_result(
                "answer_plan_metadata_resolution",
                "invalid" if answer_plan_validation["blocked"] else "resolved",
                "proceed_to_answer_plan_metadata" if not answer_plan_validation["blocked"] else "block_due_to_boundary",
                answer_plan_ref=dry_run["answer_plan_ref"],
                answer_plan_validation=answer_plan_validation,
            ),
            _stage_result(
                "final_answer_generation_boundary",
                "blocked_boundary",
                "block_due_to_boundary",
                note="final answer generation is not executed",
            ),
            _stage_result(
                "operator_observability_event",
                "resolved",
                "request_operator_review" if dry_run["operator_visibility_refs"] else "proceed_to_answer_plan_metadata",
                operator_visibility_refs=dry_run["operator_visibility_refs"],
            ),
            _stage_result(
                "optional_persistence_candidate",
                "blocked" if _safe_bool(data.get("persistence_candidate_requested")) or _normalize_refs(data.get("persistence_candidate_refs")) else "resolved",
                "block_due_to_persistence_boundary" if _safe_bool(data.get("persistence_candidate_requested")) or _normalize_refs(data.get("persistence_candidate_refs")) else "proceed_to_answer_plan_metadata",
                persistence_candidate_refs=_normalize_refs(data.get("persistence_candidate_refs")),
            ),
            _stage_result(
                "user_confirmation_or_correction",
                "clarification_required" if dry_run["dry_run_status"] == "clarification_required" else "resolved",
                "ask_clarifying_question" if dry_run["dry_run_status"] == "clarification_required" else "proceed_to_answer_plan_metadata",
            ),
        ]
        dry_run["stage_results"] = stage_results

    probe_validation = validate_project_chat_answer_plan_v1(_build_status_probe_answer_plan(dry_run))
    dry_run["status_probe_validation"] = probe_validation

    return dry_run


def validate_project_chat_runtime_dry_run_v1(dry_run: Any) -> dict[str, Any]:
    candidate = build_project_chat_runtime_dry_run_v1(dry_run)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "dry_run_id",
        "project_id",
        "owner_user_scope",
        "tenant_account_scope",
        "source_scope",
        "user_intent_class",
        "dry_run_status",
        "dry_run_decision",
        "stage_results",
        "retrieval_need_class",
        "answer_plan_ref",
        "answer_plan_metadata",
        "user_visible_status",
    )
    for field in required_fields:
        if not _safe_str(candidate.get(field)) and field != "stage_results":
            blocked_labels.append(f"missing_{field}")
        if field == "stage_results" and not isinstance(candidate.get(field), list):
            blocked_labels.append("missing_stage_results")

    stage_names = [item.get("stage", "") for item in candidate.get("stage_results", []) if isinstance(item, Mapping)]
    for stage in stage_names:
        if stage not in DRY_RUN_STAGES_V1:
            blocked_labels.append(f"unknown_stage_{stage or 'missing'}")

    status = _safe_str(candidate.get("dry_run_status"))
    decision = _safe_str(candidate.get("dry_run_decision"))
    if status not in DRY_RUN_STATUSES_V1:
        blocked_labels.append("unknown_dry_run_status")
    if decision not in DRY_RUN_DECISIONS_V1:
        blocked_labels.append("unknown_dry_run_decision")

    evidence_refs = _normalize_refs(candidate.get("evidence_packet_refs"))
    retrieval_need = _safe_str(candidate.get("retrieval_need_class"))
    approval_refs = _normalize_refs(candidate.get("approval_refs"))
    contradiction_flags = _normalize_flags(candidate.get("contradiction_flags"))
    stale_state_flags = _normalize_flags(candidate.get("stale_state_flags"))
    missing_evidence_flags = _normalize_flags(candidate.get("missing_evidence_flags"))
    privacy_flags = _normalize_flags(candidate.get("privacy_flags"))
    denied = _as_mapping(candidate.get("denied_authority"))

    if retrieval_need in {"approved_evidence_packet"} and not evidence_refs:
        blocked_labels.append("missing_evidence_packet_refs")
    if retrieval_need in {"external_private", "private", "external"} and not approval_refs:
        blocked_labels.append("missing_approval_refs")
    if retrieval_need in {"external_private", "private", "external"} and not approval_refs and decision != "request_user_approval":
        blocked_labels.append("external_private_retrieval_requires_approval")
    if contradiction_flags and decision != "ask_clarifying_question":
        blocked_labels.append("contradiction_requires_resolution")
    if stale_state_flags and decision != "ask_clarifying_question":
        blocked_labels.append("stale_state_requires_clarification_or_block")
    if missing_evidence_flags and decision != "ask_clarifying_question":
        blocked_labels.append("missing_evidence_requires_clarification_or_block")
    if _normalize_refs(candidate.get("tool_lane_candidate_refs")) and decision == "block_due_to_tool_execution_boundary":
        blocked_labels.append("tool_lane_must_remain_candidate_only")
    if _normalize_refs(candidate.get("persistence_candidate_refs")):
        blocked_labels.append("persistence_boundary_must_block")

    for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1:
        if field not in denied:
            blocked_labels.append(f"missing_denied_authority_{field}")
        elif _safe_bool(denied.get(field, False)):
            blocked_labels.append(f"denied_authority_asserted_{field}")

    for item in candidate.get("stage_results", []):
        if not isinstance(item, Mapping):
            blocked_labels.append("invalid_stage_result_shape")
            continue
        stage_name = _safe_str(item.get("stage"))
        stage_status = _safe_str(item.get("status"))
        stage_decision = _safe_str(item.get("decision"))
        if stage_name not in DRY_RUN_STAGES_V1:
            blocked_labels.append(f"unknown_stage_{stage_name or 'missing'}")
        if not stage_status:
            blocked_labels.append(f"missing_stage_status_{stage_name or 'missing'}")
        if not stage_decision:
            blocked_labels.append(f"missing_stage_decision_{stage_name or 'missing'}")

    answer_plan_validation = _as_mapping(candidate.get("answer_plan_validation"))
    if answer_plan_validation.get("blocked"):
        blocked_labels.append("answer_plan_metadata_invalid")
    probe_validation = _as_mapping(candidate.get("status_probe_validation"))
    if probe_validation.get("blocked"):
        blocked_labels.append("user_visible_status_forbidden_phrase")

    user_visible_status = _safe_str(candidate.get("user_visible_status"))
    if not user_visible_status:
        blocked_labels.append("missing_user_visible_status")
    if "Unknown Engine" in user_visible_status:
        blocked_labels.append("unknown_engine_in_user_visible_status")
    if any(marker in user_visible_status for marker in (
        "chat" + "_" + "responder",
        "respond_chat",
        "generate_chat",
        "chat" + "_" + "ui",
        "dia" + "logue",
        "main" + ".py",
        "." + "weslr",
        "hidden prompt",
        "system prompt",
        "private mechanism",
        "internal mechanism",
        "internal scoring",
        "tool executed",
        "I executed",
        "I searched your private data",
        "I saved this project",
        "I remember this",
        "SearXNG proves",
        "the web confirms",
        "truth authority",
        "final answer authority",
        "runtime authority",
        "mutation authority",
        "memory authority",
        "tool execution authority",
        "storage authority",
        "public readiness",
        "certified intelligence",
        "autonomous self-improvement",
    )):
        blocked_labels.append("private_mechanism_or_authority_wording_in_user_visible_status")

    valid = not blocked_labels
    if not valid:
        dry_run_status = "invalid"
    else:
        dry_run_status = status
        if decision in {"ask_clarifying_question"}:
            dry_run_status = "clarification_required"
        elif decision in {"request_user_approval"}:
            dry_run_status = "approval_required"
        elif decision in {"request_operator_review"}:
            dry_run_status = "operator_review_required"
        elif decision.startswith("block_due_to_"):
            dry_run_status = "blocked"
        elif decision == "proceed_to_answer_plan_metadata":
            dry_run_status = "dry_run_valid_metadata_only"

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "dry_run": candidate,
        "dry_run_id": candidate["dry_run_id"],
        "dry_run_status": dry_run_status,
        "dry_run_decision": decision,
        "valid_metadata_only": valid,
        "blocked": not valid,
        "blocked_labels": blocked_labels,
        "validation_notes": blocked_labels[:],
        "user_visible_status": user_visible_status,
        "operator_visible_summary": _safe_str(candidate.get("operator_visible_summary")),
        "denied_authority": dict(denied),
        "retrieval_need_class": retrieval_need,
        "answer_plan_validation": answer_plan_validation,
    }
    if not valid and dry_run_status == "invalid":
        result["dry_run"]["dry_run_status"] = "invalid"
    return result


def classify_project_chat_runtime_dry_run_v1(dry_run: Any) -> dict[str, Any]:
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    candidate = validation["dry_run"]
    decision = _safe_str(validation.get("dry_run_decision"))
    status = _safe_str(validation.get("dry_run_status"))

    if validation["blocked"]:
        classification = "blocked"
    elif status == "invalid":
        classification = "invalid"
    elif decision == "ask_clarifying_question":
        classification = "clarification_required"
    elif decision == "request_user_approval":
        classification = "approval_required"
    elif decision == "request_operator_review":
        classification = "operator_review_required"
    elif decision == "proceed_to_answer_plan_metadata":
        classification = "proceed_to_answer_plan_metadata"
    else:
        classification = "metadata_only"

    if candidate.get("missing_evidence_flags") and classification == "proceed_to_answer_plan_metadata":
        classification = "blocked"
    if candidate.get("contradiction_flags") and classification == "proceed_to_answer_plan_metadata":
        classification = "blocked"
    if candidate.get("stale_state_flags") and classification == "proceed_to_answer_plan_metadata":
        classification = "blocked"

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "classification": classification,
        "dry_run_status": validation["dry_run_status"],
        "dry_run_decision": decision,
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "needs_approval": classification == "approval_required",
        "needs_operator_review": classification == "operator_review_required",
        "needs_clarification": classification == "clarification_required",
        "answer_plan_ref": candidate["answer_plan_ref"],
    }


def summarize_project_chat_runtime_dry_run_v1(dry_run: Any) -> dict[str, Any]:
    candidate = build_project_chat_runtime_dry_run_v1(dry_run)
    validation = validate_project_chat_runtime_dry_run_v1(candidate)
    summary_text = (
        f"{_safe_str(validation.get('dry_run_decision'))} | "
        f"{_safe_str(validation.get('dry_run_status'))} | "
        f"retrieval={_safe_str(candidate.get('retrieval_need_class'))} | "
        f"stages={len(candidate.get('stage_results', []))} | "
        f"blocked={validation['blocked']}"
    )
    safe_user_visible_status = _default_user_visible_status(candidate)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "dry_run_id": candidate["dry_run_id"],
        "summary_text": summary_text,
        "dry_run_status": validation["dry_run_status"],
        "dry_run_decision": validation["dry_run_decision"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "stage_count": len(candidate.get("stage_results", [])),
        "retrieval_need_class": _safe_str(candidate.get("retrieval_need_class")),
        "user_visible_status": safe_user_visible_status if validation["blocked"] else _safe_str(candidate.get("user_visible_status")),
        "operator_visible_summary": _safe_str(candidate.get("operator_visible_summary")),
    }


def to_project_chat_runtime_dry_run_json_safe_v1(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): to_project_chat_runtime_dry_run_json_safe_v1(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_project_chat_runtime_dry_run_json_safe_v1(item) for item in value]
    if isinstance(value, tuple):
        return [to_project_chat_runtime_dry_run_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        return [to_project_chat_runtime_dry_run_json_safe_v1(item) for item in sorted(value, key=lambda item: _safe_str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_str(value)


def build_initial_project_chat_runtime_dry_run_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_project_chat_runtime_dry_run_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "current_message_only",
                "user_intent_class": "clarification",
                "dry_run_status": "clarification_required",
                "dry_run_decision": "ask_clarifying_question",
                "user_visible_status": "clarification needed",
                "operator_visible_summary": "dry-run clarification; metadata only",
                "retrieval_need_class": "none",
            }
        ),
        build_project_chat_runtime_dry_run_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-start",
                "dry_run_status": "dry_run_valid_metadata_only",
                "dry_run_decision": "proceed_to_answer_plan_metadata",
                "user_visible_status": "dry-run metadata only",
                "retrieval_need_class": "project_metadata_only",
            }
        ),
        build_project_chat_runtime_dry_run_v1(
            {
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "approved_evidence_packet",
                "user_intent_class": "evidence-grounded",
                "dry_run_status": "dry_run_valid_metadata_only",
                "dry_run_decision": "proceed_to_answer_plan_metadata",
                "retrieval_need_class": "approved_evidence_packet",
                "evidence_packet_refs": ["evidence-001"],
                "user_visible_status": "dry-run metadata only",
            }
        ),
    ]
    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "DRY_RUN_STAGES_V1",
    "DRY_RUN_STATUSES_V1",
    "DRY_RUN_DECISIONS_V1",
    "allowed_project_chat_runtime_dry_run_stages_v1",
    "allowed_project_chat_runtime_dry_run_statuses_v1",
    "allowed_project_chat_runtime_dry_run_decisions_v1",
    "build_project_chat_runtime_dry_run_v1",
    "validate_project_chat_runtime_dry_run_v1",
    "classify_project_chat_runtime_dry_run_v1",
    "summarize_project_chat_runtime_dry_run_v1",
    "to_project_chat_runtime_dry_run_json_safe_v1",
    "build_initial_project_chat_runtime_dry_run_examples_v1",
]
