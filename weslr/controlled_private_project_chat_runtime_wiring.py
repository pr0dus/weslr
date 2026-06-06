"""Metadata-only helpers for controlled private project-chat runtime wiring.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It consumes bounded project-chat request metadata only, runs the closed
helper chain in private/local dry-run mode only, and produces internal
result metadata only.

It does not perform public chat, answer delivery, provider/model/search/tool
calls, live retrieval, persistence, `.weslr` IO, UI/Nova behavior, or any
public/user-facing behavior.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from weslr.project_chat_assembly_orchestration_packet import (
    build_project_chat_assembly_packet_v1,
    validate_project_chat_assembly_packet_v1,
)
from weslr.project_chat_runtime_boundary_helpers import (
    build_project_chat_runtime_boundary_packet_v1,
    validate_project_chat_runtime_boundary_packet_v1,
)
from weslr.project_chat_runtime_shell_dry_run_consumer import (
    build_project_chat_runtime_shell_dry_run_consumer_packet_v1,
    validate_project_chat_runtime_shell_dry_run_consumer_packet_v1,
)

HELPER_TYPE_V1 = "weslr_controlled_private_project_chat_runtime_wiring_v1"
SCHEMA_VERSION_V1 = "controlled_private_project_chat_runtime_wiring_v1"

PRIVATE_RUNTIME_MODES_V1 = (
    "private_local_only",
)

ALLOWED_RUNTIME_BOUNDARY_DECISIONS_V1 = (
    "require_owner_approval_before_runtime_wiring",
    "preserve_metadata_only",
)

FORBIDDEN_VISIBLE_PHRASES_V1 = (
    "unknown engine",
    "raw transcript",
    "raw prompt",
    "raw message",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "internal mechanism",
    "secret",
    "confidential",
    "live chat",
    "live chat output",
    "tool executed",
    "i executed",
    "i searched your private data",
    "i saved this project",
    "i remember this",
    "answer delivery",
    "send to user",
    "reply to user",
    "public readiness",
    "certified",
    "proof",
    "proven",
    "solved",
    "benchmark",
    "legal certainty",
    "medical certainty",
    "financial certainty",
    "professional certainty",
    "guaranteed",
    "cognitive engine",
    "cognitive research run",
    "runtime authority",
    "final answer authority",
    "retrieval truth authority",
)

_DEFAULT_FALSE_BOOL_FIELDS = (
    "answer_delivery_requested",
    "public_user_facing_mode_requested",
    "provider_model_search_tool_requested",
    "persistence_requested",
    "weslr_io_requested",
    "retrieval_requested",
    "live_retrieval_requested",
    "model_call_requested",
    "provider_call_requested",
    "search_call_requested",
    "tool_call_requested",
)

_DEFAULT_CONTROL_FLAGS = {field: False for field in _DEFAULT_FALSE_BOOL_FIELDS}


def allowed_controlled_private_project_chat_runtime_modes_v1() -> tuple[str, ...]:
    return PRIVATE_RUNTIME_MODES_V1



def allowed_controlled_private_project_chat_runtime_boundary_decisions_v1() -> tuple[str, ...]:
    return ALLOWED_RUNTIME_BOUNDARY_DECISIONS_V1



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
    blob = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()



def _normalize_refs(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))



def _normalize_flags(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))



def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    raw = _as_mapping(value)
    payload: dict[str, bool] = {}
    for field in (
        "runtime_wiring_authority",
        "chat_responder_authority",
        "live_chat_output_authority",
        "answer_delivery_authority",
        "final_answer_generation_authority",
        "retrieval_execution_authority",
        "provider_call_authority",
        "model_call_authority",
        "search_call_authority",
        "tool_execution_authority",
        "external_action_authority",
        "storage_database_authority",
        "weslr_io_authority",
        "ui_nova_behavior_authority",
        "public_user_facing_authority",
        "hidden_memory_authority",
        "hidden_project_state_authority",
        "private_mechanism_disclosure_authority",
        "cross_user_leakage_authority",
        "public_product_readiness_authority",
        "autonomous_self_improvement_authority",
        "cognitive_engine_authority",
    ):
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



def _slugify_v1(value: Any) -> str:
    import re

    text = _safe_str(value).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "value"



def _find_forbidden_hits_v1(*values: Any) -> list[str]:
    hits: list[str] = []
    for value in values:
        text = _safe_str(value).lower()
        for phrase in FORBIDDEN_VISIBLE_PHRASES_V1:
            if phrase in text:
                hits.append(phrase)
    return _dedupe(hits)



def _base_request_metadata() -> dict[str, Any]:
    return {
        "request_id": "request-001",
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "user_intent_class": "project-chat",
        "private_runtime_mode": "private_local_only",
        "owner_approval_metadata": {
            "owner_approval_required": True,
            "owner_approval_granted": True,
            "owner_approval_ref": "approval-001",
            "operator_visible_summary": "owner approval granted for private local runtime wiring only",
        },
        "answer_delivery_requested": False,
        "public_user_facing_mode_requested": False,
        "provider_model_search_tool_requested": False,
        "persistence_requested": False,
        "weslr_io_requested": False,
        "retrieval_requested": False,
        "live_retrieval_requested": False,
        "model_call_requested": False,
        "provider_call_requested": False,
        "search_call_requested": False,
        "tool_call_requested": False,
        "approval_refs": ["approval-001"],
        "operator_visibility_refs": ["operator-001"],
        "uncertainty_flags": [],
        "stale_state_flags": [],
        "contradiction_flags": [],
        "missing_evidence_flags": [],
        "privacy_flags": [],
        "limitations": [],
        "denied_authority": {
            "runtime_wiring_authority": False,
            "chat_responder_authority": False,
            "live_chat_output_authority": False,
            "answer_delivery_authority": False,
            "final_answer_generation_authority": False,
            "retrieval_execution_authority": False,
            "provider_call_authority": False,
            "model_call_authority": False,
            "search_call_authority": False,
            "tool_execution_authority": False,
            "external_action_authority": False,
            "storage_database_authority": False,
            "weslr_io_authority": False,
            "ui_nova_behavior_authority": False,
            "public_user_facing_authority": False,
            "hidden_memory_authority": False,
            "hidden_project_state_authority": False,
            "private_mechanism_disclosure_authority": False,
            "cross_user_leakage_authority": False,
            "public_product_readiness_authority": False,
            "autonomous_self_improvement_authority": False,
            "cognitive_engine_authority": False,
        },
        "user_visible_status": "private local runtime wiring metadata only",
        "operator_visible_summary": "private/local runtime wiring request; metadata only",
    }



def _base_assembly_metadata(request: Mapping[str, Any]) -> dict[str, Any]:
    project_id = _safe_str(request.get("project_id")) or "project-001"
    owner_user_scope = _safe_str(request.get("owner_user_scope")) or "owner-user"
    tenant_account_scope = _safe_str(request.get("tenant_account_scope")) or "tenant-a"
    source_scope = _safe_str(request.get("source_scope")) or "project_metadata_only"
    user_intent_class = _safe_str(request.get("user_intent_class")) or "project-chat"
    return {
        "project_id": project_id,
        "owner_user_scope": owner_user_scope,
        "tenant_account_scope": tenant_account_scope,
        "source_scope": source_scope,
        "user_intent_class": user_intent_class,
        "user_request_metadata": {
            "request_id": _safe_str(request.get("request_id")) or "request-001",
            "message_ref": "message-001",
            "message_status": "metadata only",
            "user_visible_status": "metadata only",
            "operator_visible_summary": "message intake metadata only",
        },
        "project_context_metadata": {
            "project_state_refs": ["project-state-001"],
            "memory_state_refs": ["memory-state-001"],
            "continuity_state_refs": ["continuity-state-001"],
            "gap_analysis_refs": ["gap-001"],
            "approval_refs": _normalize_refs(request.get("approval_refs")) or ["approval-001"],
            "user_visible_status": "evidence grounded answer",
            "operator_visible_summary": "evidence grounded; metadata only",
        },
        "retrieval_need_metadata": {
            "retrieval_need_class": "project_metadata_retrieval_needed",
            "retrieval_status": "metadata only",
        },
        "evidence_packet_metadata": [
            {
                "project_id": project_id,
                "owner_user_scope": owner_user_scope,
                "tenant_account_scope": tenant_account_scope,
                "source_scope": source_scope,
                "retrieval_request_id": _safe_str(request.get("request_id")) or "request-001",
                "retrieval_need_class": "project_metadata_retrieval_needed",
                "retrieval_adapter": "ProjectStateMetadataAdapter",
                "source_type": "project_metadata",
                "source_ref": "project-metadata-001",
                "source_title": "project metadata only",
                "source_timestamp": "2026-06-06T14:00:00Z",
                "retrieved_at_marker": "metadata_only",
                "freshness_label": "fresh_current",
                "relevance_label": "high_relevance",
                "confidence_label": "high_confidence",
                "verification_status": "metadata_only",
                "privacy_label": "public",
                "privacy_sensitivity": "low",
                "query_redaction_status": "not_required",
                "evidence_summary": "evidence packet metadata only",
            }
        ],
        "answer_plan_metadata": {
            "project_id": project_id,
            "owner_user_scope": owner_user_scope,
            "tenant_account_scope": tenant_account_scope,
            "source_scope": source_scope,
            "user_intent_class": user_intent_class,
            "answer_mode": "evidence_grounded_answer",
            "allowed_answer_scope": "approved_evidence_packet",
            "answer_status": "plan_valid_metadata_only",
            "evidence_packet_refs": ["evidence-001"],
            "user_visible_status": "evidence grounded answer",
            "operator_visible_summary": "evidence grounded; metadata only",
        },
        "final_answer_packet_metadata": {
            "controlled_answer_text_proposal": "Internal controlled answer candidate: evidence-grounded and bounded by citations.",
        },
    }



def _build_request_packet(request: Mapping[str, Any]) -> dict[str, Any]:
    request_packet = {
        "schema_version": _safe_str(request.get("schema_version")) or SCHEMA_VERSION_V1,
        "request_id": _safe_str(request.get("request_id")) or "request-001",
        "project_id": _safe_str(request.get("project_id")) or "project-001",
        "owner_user_scope": _safe_str(request.get("owner_user_scope")) or "owner-user",
        "tenant_account_scope": _safe_str(request.get("tenant_account_scope")) or "tenant-a",
        "source_scope": _safe_str(request.get("source_scope")) or "project_metadata_only",
        "user_intent_class": _safe_str(request.get("user_intent_class")) or "project-chat",
        "private_runtime_mode": _safe_str(request.get("private_runtime_mode")) or "private_local_only",
        "owner_approval_metadata": _as_mapping(request.get("owner_approval_metadata")) or {
            "owner_approval_required": True,
            "owner_approval_granted": True,
            "owner_approval_ref": "approval-001",
            "operator_visible_summary": "owner approval granted for private local runtime wiring only",
        },
        "answer_delivery_requested": _safe_bool(request.get("answer_delivery_requested", False)),
        "public_user_facing_mode_requested": _safe_bool(request.get("public_user_facing_mode_requested", False)),
        "provider_model_search_tool_requested": _safe_bool(request.get("provider_model_search_tool_requested", False)),
        "persistence_requested": _safe_bool(request.get("persistence_requested", False)),
        "weslr_io_requested": _safe_bool(request.get("weslr_io_requested", False)),
        "retrieval_requested": _safe_bool(request.get("retrieval_requested", False)),
        "live_retrieval_requested": _safe_bool(request.get("live_retrieval_requested", False)),
        "model_call_requested": _safe_bool(request.get("model_call_requested", False)),
        "provider_call_requested": _safe_bool(request.get("provider_call_requested", False)),
        "search_call_requested": _safe_bool(request.get("search_call_requested", False)),
        "tool_call_requested": _safe_bool(request.get("tool_call_requested", False)),
        "approval_refs": _normalize_refs(request.get("approval_refs")) or ["approval-001"],
        "operator_visibility_refs": _normalize_refs(request.get("operator_visibility_refs")) or ["operator-001"],
        "uncertainty_flags": _normalize_flags(request.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(request.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(request.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(request.get("missing_evidence_flags")),
        "privacy_flags": _normalize_flags(request.get("privacy_flags")),
        "limitations": _normalize_flags(request.get("limitations")),
        "denied_authority": _normalize_denied_authority(request.get("denied_authority")),
        "user_visible_status": _safe_str(request.get("user_visible_status")) or "private local runtime wiring metadata only",
        "operator_visible_summary": _safe_str(request.get("operator_visible_summary")) or "private/local runtime wiring request; metadata only",
        "helper_type": HELPER_TYPE_V1,
    }
    if not request_packet["request_id"]:
        digest_source = {k: v for k, v in request_packet.items() if k not in {"request_id", "operator_visible_summary"}}
        request_packet["request_id"] = f"controlled-private-runtime-request-{_stable_digest(digest_source)[:16]}"
    return request_packet



def build_controlled_private_project_chat_runtime_request_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    request = _base_request_metadata()
    request.update({k: v for k, v in data.items() if k != "assembly_packet_metadata"})
    request_packet = _build_request_packet(request)

    assembly_source = data.get("assembly_packet_metadata")
    if isinstance(assembly_source, Mapping):
        assembly_packet = build_project_chat_assembly_packet_v1(assembly_source)
    else:
        assembly_packet = build_project_chat_assembly_packet_v1(_base_assembly_metadata(request_packet))

    request_packet["assembly_packet_metadata"] = assembly_packet
    request_packet["safe_metadata"] = {
        "request_summary": "controlled private runtime wiring request packet",
        "private_runtime_mode": request_packet["private_runtime_mode"],
        "owner_approval_required": True,
        "answer_delivery_requested": request_packet["answer_delivery_requested"],
        "public_user_facing_mode_requested": request_packet["public_user_facing_mode_requested"],
        "provider_model_search_tool_requested": request_packet["provider_model_search_tool_requested"],
        "persistence_requested": request_packet["persistence_requested"],
        "weslr_io_requested": request_packet["weslr_io_requested"],
        "retrieval_requested": request_packet["retrieval_requested"],
    }
    return request_packet



def _default_user_visible_status(blocked: bool) -> str:
    if blocked:
        return "Controlled private runtime wiring is blocked."
    return "Controlled private runtime wiring metadata only."



def _default_operator_visible_summary(request_packet: Mapping[str, Any], blocked: bool, boundary_validation: Mapping[str, Any]) -> str:
    return (
        f"{_safe_str(request_packet.get('private_runtime_mode'))} | "
        f"{_safe_str(boundary_validation.get('boundary_decision'))} | "
        f"blocked={blocked} | "
        f"approval={_safe_bool(_as_mapping(request_packet.get('owner_approval_metadata')).get('owner_approval_granted'))}"
    )



def _request_validation(candidate: Mapping[str, Any]) -> list[str]:
    blocked_labels: list[str] = []

    for field in ("request_id", "project_id", "owner_user_scope", "tenant_account_scope", "source_scope", "user_intent_class", "private_runtime_mode"):
        if not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    if candidate.get("private_runtime_mode") not in PRIVATE_RUNTIME_MODES_V1:
        blocked_labels.append("unknown_private_runtime_mode")

    owner_approval = _as_mapping(candidate.get("owner_approval_metadata"))
    if not owner_approval:
        blocked_labels.append("missing_owner_approval_metadata")
    if owner_approval.get("owner_approval_required") is not True:
        blocked_labels.append("owner_approval_required_must_be_true")
    if owner_approval.get("owner_approval_granted") is not True:
        blocked_labels.append("owner_approval_granted_must_be_true")

    for field in _DEFAULT_FALSE_BOOL_FIELDS:
        if candidate.get(field) is True:
            blocked_labels.append(f"{field}_must_be_false")

    if _safe_bool(candidate.get("answer_delivery_requested")):
        blocked_labels.append("answer_delivery_requested_must_be_false")
    if _safe_bool(candidate.get("public_user_facing_mode_requested")):
        blocked_labels.append("public_user_facing_mode_requested_must_be_false")
    if _safe_bool(candidate.get("provider_model_search_tool_requested")):
        blocked_labels.append("provider_model_search_tool_requested_must_be_false")
    if _safe_bool(candidate.get("persistence_requested")):
        blocked_labels.append("persistence_requested_must_be_false")
    if _safe_bool(candidate.get("weslr_io_requested")):
        blocked_labels.append("weslr_io_requested_must_be_false")

    if _safe_bool(candidate.get("retrieval_requested")) or _safe_bool(candidate.get("live_retrieval_requested")):
        blocked_labels.append("retrieval_requested_without_preapproved_metadata")

    for phrase in _find_forbidden_hits_v1(candidate.get("user_visible_status"), candidate.get("operator_visible_summary")):
        blocked_labels.append(f"forbidden_phrase_{_slugify_v1(phrase)}")

    return _dedupe(blocked_labels)



def _build_chain(candidate: Mapping[str, Any]) -> dict[str, Any]:
    assembly_packet = _as_mapping(candidate.get("assembly_packet_metadata"))
    if not assembly_packet:
        assembly_packet = build_project_chat_assembly_packet_v1(_base_assembly_metadata(candidate))
    else:
        assembly_packet = build_project_chat_assembly_packet_v1(assembly_packet)
    assembly_validation = validate_project_chat_assembly_packet_v1(assembly_packet)

    dry_run_consumer_packet = build_project_chat_runtime_shell_dry_run_consumer_packet_v1({"assembly_packet_metadata": assembly_packet})
    dry_run_consumer_validation = validate_project_chat_runtime_shell_dry_run_consumer_packet_v1(dry_run_consumer_packet)

    runtime_boundary_packet = build_project_chat_runtime_boundary_packet_v1({"dry_run_consumer_packet_metadata": dry_run_consumer_packet})
    runtime_boundary_validation = validate_project_chat_runtime_boundary_packet_v1(runtime_boundary_packet)

    answer_plan_validation = _as_mapping(assembly_validation.get("answer_plan_validation"))
    final_answer_validation = _as_mapping(assembly_validation.get("final_answer_validation"))
    evidence_validations = assembly_validation.get("evidence_validations", [])
    if not isinstance(evidence_validations, list):
        evidence_validations = []

    blocked_labels: list[str] = []
    blocked_labels.extend(_request_validation(candidate))
    blocked_labels.extend(_normalize_flags(assembly_validation.get("blocked_labels")))
    blocked_labels.extend(_normalize_flags(dry_run_consumer_validation.get("blocked_labels")))
    blocked_labels.extend(_normalize_flags(runtime_boundary_validation.get("blocked_labels")))

    if runtime_boundary_validation.get("blocked") or runtime_boundary_validation.get("boundary_status") not in {"owner_approval_required", "boundary_valid_metadata_only"}:
        blocked_labels.append("runtime_boundary_decision_not_allowed")
    if runtime_boundary_validation.get("boundary_decision") not in ALLOWED_RUNTIME_BOUNDARY_DECISIONS_V1:
        blocked_labels.append("runtime_boundary_decision_not_allowed")

    if _safe_bool(_as_mapping(candidate.get("owner_approval_metadata")).get("owner_approval_granted")) is not True:
        blocked_labels.append("owner_approval_not_granted")

    if any(_safe_bool(validation.get("blocked")) for validation in evidence_validations if isinstance(validation, Mapping)):
        blocked_labels.append("invalid_or_blocked_evidence_metadata")
    if answer_plan_validation.get("blocked"):
        blocked_labels.append("invalid_answer_plan_metadata")
    if final_answer_validation.get("blocked"):
        blocked_labels.append("invalid_final_answer_metadata")

    if _safe_bool(candidate.get("answer_delivery_requested")):
        blocked_labels.append("answer_delivery_requested_must_be_false")
    if _safe_bool(candidate.get("public_user_facing_mode_requested")):
        blocked_labels.append("public_user_facing_mode_requested_must_be_false")
    if _safe_bool(candidate.get("provider_model_search_tool_requested")):
        blocked_labels.append("provider_model_search_tool_requested_must_be_false")
    if _safe_bool(candidate.get("persistence_requested")):
        blocked_labels.append("persistence_requested_must_be_false")
    if _safe_bool(candidate.get("weslr_io_requested")):
        blocked_labels.append("weslr_io_requested_must_be_false")

    if dry_run_consumer_validation.get("blocked"):
        blocked_labels.append("dry_run_consumer_blocked")
    if assembly_validation.get("blocked"):
        blocked_labels.append("assembly_blocked")

    blocked_labels = _dedupe(blocked_labels)
    blocked = bool(blocked_labels)

    result_status = "blocked" if blocked else "controlled_private_runtime_valid_metadata_only"

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "request_packet": candidate,
        "request_id": candidate["request_id"],
        "project_id": candidate["project_id"],
        "owner_user_scope": candidate["owner_user_scope"],
        "tenant_account_scope": candidate["tenant_account_scope"],
        "source_scope": candidate["source_scope"],
        "private_runtime_mode": candidate["private_runtime_mode"],
        "owner_approval_metadata": candidate["owner_approval_metadata"],
        "assembly_packet_metadata": assembly_packet,
        "assembly_validation": assembly_validation,
        "dry_run_consumer_packet_metadata": dry_run_consumer_packet,
        "dry_run_consumer_validation": dry_run_consumer_validation,
        "runtime_boundary_packet_metadata": runtime_boundary_packet,
        "runtime_boundary_validation": runtime_boundary_validation,
        "answer_plan_metadata": _as_mapping(assembly_packet.get("answer_plan_metadata")),
        "answer_plan_validation": answer_plan_validation,
        "final_answer_packet_metadata": _as_mapping(assembly_validation.get("final_answer_packet_metadata")),
        "final_answer_validation": final_answer_validation,
        "evidence_validations": evidence_validations,
        "blocked_state": _as_mapping(runtime_boundary_validation.get("blocked_state")),
        "missing_evidence_state": _as_mapping(runtime_boundary_validation.get("missing_evidence_state")),
        "conflict_state": _as_mapping(runtime_boundary_validation.get("conflict_state")),
        "approval_state": _as_mapping(runtime_boundary_validation.get("approval_state")),
        "provenance_chain": _as_mapping(runtime_boundary_validation.get("provenance_chain")),
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "controlled_private_runtime_status": result_status,
        "user_visible_status": _default_user_visible_status(blocked),
        "operator_visible_summary": _default_operator_visible_summary(candidate, blocked, runtime_boundary_validation),
        "safe_metadata": {
            "result_summary": result_status,
            "private_runtime_mode": candidate["private_runtime_mode"],
            "owner_approval_required": True,
            "owner_approval_granted": _safe_bool(_as_mapping(candidate.get("owner_approval_metadata")).get("owner_approval_granted")),
            "answer_delivery_requested": _safe_bool(candidate.get("answer_delivery_requested")),
            "public_user_facing_mode_requested": _safe_bool(candidate.get("public_user_facing_mode_requested")),
            "provider_model_search_tool_requested": _safe_bool(candidate.get("provider_model_search_tool_requested")),
            "persistence_requested": _safe_bool(candidate.get("persistence_requested")),
            "weslr_io_requested": _safe_bool(candidate.get("weslr_io_requested")),
            "retrieval_requested": _safe_bool(candidate.get("retrieval_requested")),
            "runtime_boundary_decision": _safe_str(runtime_boundary_validation.get("boundary_decision")),
        },
    }



def validate_controlled_private_project_chat_runtime_request_v1(packet: Any) -> dict[str, Any]:
    candidate = build_controlled_private_project_chat_runtime_request_v1(packet)
    chain = _build_chain(candidate)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "request_packet": candidate,
        **chain,
    }



def run_controlled_private_project_chat_runtime_dry_run_v1(packet: Any) -> dict[str, Any]:
    return _build_chain(build_controlled_private_project_chat_runtime_request_v1(packet))



def summarize_controlled_private_project_chat_runtime_result_v1(packet: Any) -> dict[str, Any]:
    result = run_controlled_private_project_chat_runtime_dry_run_v1(packet)
    summary_text = (
        f"{_safe_str(result.get('controlled_private_runtime_status'))} | "
        f"boundary={_safe_str(_as_mapping(result.get('runtime_boundary_validation')).get('boundary_decision'))} | "
        f"assembly={_safe_str(_as_mapping(result.get('assembly_validation')).get('assembly_status'))} | "
        f"blocked={result.get('blocked')}"
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "request_id": result.get("request_id"),
        "project_id": result.get("project_id"),
        "summary_text": summary_text,
        "controlled_private_runtime_status": result.get("controlled_private_runtime_status"),
        "blocked": result.get("blocked"),
        "blocked_labels": result.get("blocked_labels", []),
        "operator_visible_summary": result.get("operator_visible_summary"),
        "safe_metadata": result.get("safe_metadata", {}),
    }



def to_controlled_private_project_chat_runtime_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def build_initial_controlled_private_project_chat_runtime_examples_v1() -> list[dict[str, Any]]:
    valid = run_controlled_private_project_chat_runtime_dry_run_v1({})
    blocked = run_controlled_private_project_chat_runtime_dry_run_v1(
        {
            "answer_delivery_requested": True,
            "public_user_facing_mode_requested": True,
            "provider_model_search_tool_requested": True,
            "persistence_requested": True,
            "weslr_io_requested": True,
        }
    )
    return [
        to_controlled_private_project_chat_runtime_json_safe_v1(valid),
        to_controlled_private_project_chat_runtime_json_safe_v1(blocked),
    ]


__all__ = [
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "PRIVATE_RUNTIME_MODES_V1",
    "ALLOWED_RUNTIME_BOUNDARY_DECISIONS_V1",
    "allowed_controlled_private_project_chat_runtime_modes_v1",
    "allowed_controlled_private_project_chat_runtime_boundary_decisions_v1",
    "build_controlled_private_project_chat_runtime_request_v1",
    "validate_controlled_private_project_chat_runtime_request_v1",
    "run_controlled_private_project_chat_runtime_dry_run_v1",
    "summarize_controlled_private_project_chat_runtime_result_v1",
    "to_controlled_private_project_chat_runtime_json_safe_v1",
    "build_initial_controlled_private_project_chat_runtime_examples_v1",
]
