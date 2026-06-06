"""Metadata-only helpers for the private local Project Chat entrypoint.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It consumes bounded owner-only project-chat request metadata, delegates to the
controlled private runtime dry-run helper only, and produces internal result
metadata only.

It does not perform public chat, website chat, answer delivery, live retrieval,
provider/model/search/tool calls, persistence, `.weslr` IO, UI/Nova behavior,
or any public/user-facing behavior.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from weslr.controlled_private_project_chat_runtime_wiring import (
    build_controlled_private_project_chat_runtime_request_v1,
    run_controlled_private_project_chat_runtime_dry_run_v1,
)

HELPER_TYPE_V1 = "weslr_private_local_project_chat_entrypoint_v1"
SCHEMA_VERSION_V1 = "private_local_project_chat_entrypoint_v1"
ENTRYPOINT_MODE_V1 = "private_local_cli_test"
ALLOWED_OWNER_MODES_V1 = (
    "private_local_cli_test",
)

FORBIDDEN_VISIBLE_PHRASES_V1 = (
    "public chat",
    "website chat",
    "50-user",
    "production deployment",
    "answer delivery",
    "live retrieval",
    "model call",
    "provider call",
    "search call",
    "tool call",
    "persistence",
    ".weslr",
    "ui",
    "nova",
    "chat responder",
    "website",
    "public/user-facing",
    "public user-facing",
    "open registration",
    "website chat",
)

_DEFAULT_FALSE_FLAGS = (
    "public_user_facing_mode_requested",
    "answer_delivery_requested",
    "provider_model_search_tool_requested",
    "provider_call_requested",
    "model_call_requested",
    "search_call_requested",
    "tool_call_requested",
    "persistence_requested",
    "weslr_io_requested",
    "retrieval_requested",
    "live_retrieval_requested",
)


def allowed_private_local_project_chat_entrypoint_modes_v1() -> tuple[str, ...]:
    return ALLOWED_OWNER_MODES_V1



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



def _coalesce_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    elif payload is not None:
        data["payload"] = payload
    data.update(overrides)
    return data



def _normalize_list(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))



def _normalize_flags(value: Any) -> list[str]:
    return _dedupe(_safe_list(value))



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
        "request_id": "entrypoint-request-001",
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "user_intent_class": "project-chat",
        "entrypoint_mode": ENTRYPOINT_MODE_V1,
        "owner_approval_metadata": {
            "owner_approval_required": True,
            "owner_approval_granted": True,
            "owner_approval_ref": "approval-001",
            "operator_visible_summary": "owner approval granted for private local entrypoint request only",
        },
        "public_user_facing_mode_requested": False,
        "answer_delivery_requested": False,
        "provider_model_search_tool_requested": False,
        "provider_call_requested": False,
        "model_call_requested": False,
        "search_call_requested": False,
        "tool_call_requested": False,
        "persistence_requested": False,
        "weslr_io_requested": False,
        "retrieval_requested": False,
        "live_retrieval_requested": False,
        "approval_refs": ["approval-001"],
        "operator_visibility_refs": ["operator-001"],
        "uncertainty_flags": [],
        "stale_state_flags": [],
        "contradiction_flags": [],
        "missing_evidence_flags": [],
        "limitations": [],
        "blocked_labels": [],
        "provenance_refs": ["entrypoint-provenance-001"],
        "user_visible_status": "private local project chat entrypoint metadata only",
        "operator_visible_summary": "private local entrypoint request; metadata only",
    }



def _default_user_visible_status(blocked: bool) -> str:
    return "Private local project chat entrypoint is blocked." if blocked else "Private local project chat entrypoint metadata only."



def _default_operator_visible_summary(candidate: Mapping[str, Any], blocked: bool, runtime_result: Mapping[str, Any]) -> str:
    return (
        f"{_safe_str(candidate.get('entrypoint_mode'))} | "
        f"runtime={_safe_str(runtime_result.get('controlled_private_runtime_status'))} | "
        f"blocked={blocked} | "
        f"approval={_safe_bool(_as_mapping(candidate.get('owner_approval_metadata')).get('owner_approval_granted'))}"
    )



def _build_request_packet(request: Mapping[str, Any]) -> dict[str, Any]:
    packet = {
        "schema_version": _safe_str(request.get("schema_version")) or SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "request_id": _safe_str(request.get("request_id")) or "entrypoint-request-001",
        "project_id": _safe_str(request.get("project_id")) or "project-001",
        "owner_user_scope": _safe_str(request.get("owner_user_scope")) or "owner-user",
        "tenant_account_scope": _safe_str(request.get("tenant_account_scope")) or "tenant-a",
        "source_scope": _safe_str(request.get("source_scope")) or "project_metadata_only",
        "user_intent_class": _safe_str(request.get("user_intent_class")) or "project-chat",
        "entrypoint_mode": _safe_str(request.get("entrypoint_mode")) or ENTRYPOINT_MODE_V1,
        "owner_approval_metadata": _as_mapping(request.get("owner_approval_metadata")) or {
            "owner_approval_required": True,
            "owner_approval_granted": True,
            "owner_approval_ref": "approval-001",
            "operator_visible_summary": "owner approval granted for private local entrypoint request only",
        },
        "public_user_facing_mode_requested": _safe_bool(request.get("public_user_facing_mode_requested", False)),
        "answer_delivery_requested": _safe_bool(request.get("answer_delivery_requested", False)),
        "provider_model_search_tool_requested": _safe_bool(request.get("provider_model_search_tool_requested", False)),
        "provider_call_requested": _safe_bool(request.get("provider_call_requested", False)),
        "model_call_requested": _safe_bool(request.get("model_call_requested", False)),
        "search_call_requested": _safe_bool(request.get("search_call_requested", False)),
        "tool_call_requested": _safe_bool(request.get("tool_call_requested", False)),
        "persistence_requested": _safe_bool(request.get("persistence_requested", False)),
        "weslr_io_requested": _safe_bool(request.get("weslr_io_requested", False)),
        "retrieval_requested": _safe_bool(request.get("retrieval_requested", False)),
        "live_retrieval_requested": _safe_bool(request.get("live_retrieval_requested", False)),
        "approval_refs": _normalize_list(request.get("approval_refs")) or ["approval-001"],
        "operator_visibility_refs": _normalize_list(request.get("operator_visibility_refs")) or ["operator-001"],
        "uncertainty_flags": _normalize_flags(request.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(request.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(request.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(request.get("missing_evidence_flags")),
        "limitations": _normalize_flags(request.get("limitations")),
        "blocked_labels": _normalize_flags(request.get("blocked_labels")),
        "provenance_refs": _normalize_list(request.get("provenance_refs")) or ["entrypoint-provenance-001"],
        "user_visible_status": _safe_str(request.get("user_visible_status")) or "private local project chat entrypoint metadata only",
        "operator_visible_summary": _safe_str(request.get("operator_visible_summary")) or "private local entrypoint request; metadata only",
    }
    if not packet["request_id"]:
        digest_source = {k: v for k, v in packet.items() if k != "request_id"}
        packet["request_id"] = f"private-local-entrypoint-{_stable_digest(digest_source)[:16]}"
    return packet



def build_private_local_project_chat_entrypoint_request_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    request = _base_request_metadata()
    request.update(data)
    if "assembly_packet_metadata" not in request:
        request["assembly_packet_metadata"] = data.get("assembly_packet_metadata")
    return _build_request_packet(request)



def _validate_request(candidate: Mapping[str, Any]) -> list[str]:
    blocked_labels: list[str] = []

    for field in ("request_id", "project_id", "owner_user_scope", "tenant_account_scope", "source_scope", "user_intent_class", "entrypoint_mode"):
        if not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    if candidate.get("entrypoint_mode") not in ALLOWED_OWNER_MODES_V1:
        blocked_labels.append("unknown_entrypoint_mode")

    owner_approval = _as_mapping(candidate.get("owner_approval_metadata"))
    if not owner_approval:
        blocked_labels.append("missing_owner_approval_metadata")
    if owner_approval.get("owner_approval_required") is not True:
        blocked_labels.append("owner_approval_required_must_be_true")
    if owner_approval.get("owner_approval_granted") is not True:
        blocked_labels.append("owner_approval_granted_must_be_true")

    for field in _DEFAULT_FALSE_FLAGS:
        if candidate.get(field) is True:
            blocked_labels.append(f"{field}_must_be_false")

    if _safe_bool(candidate.get("public_user_facing_mode_requested")):
        blocked_labels.append("public_user_facing_mode_requested_must_be_false")
    if _safe_bool(candidate.get("answer_delivery_requested")):
        blocked_labels.append("answer_delivery_requested_must_be_false")
    if _safe_bool(candidate.get("provider_model_search_tool_requested")):
        blocked_labels.append("provider_model_search_tool_requested_must_be_false")
    if _safe_bool(candidate.get("provider_call_requested")):
        blocked_labels.append("provider_call_requested_must_be_false")
    if _safe_bool(candidate.get("model_call_requested")):
        blocked_labels.append("model_call_requested_must_be_false")
    if _safe_bool(candidate.get("search_call_requested")):
        blocked_labels.append("search_call_requested_must_be_false")
    if _safe_bool(candidate.get("tool_call_requested")):
        blocked_labels.append("tool_call_requested_must_be_false")
    if _safe_bool(candidate.get("persistence_requested")):
        blocked_labels.append("persistence_requested_must_be_false")
    if _safe_bool(candidate.get("weslr_io_requested")):
        blocked_labels.append("weslr_io_requested_must_be_false")
    if _safe_bool(candidate.get("retrieval_requested")) or _safe_bool(candidate.get("live_retrieval_requested")):
        blocked_labels.append("retrieval_requested_without_preapproved_metadata")

    for phrase in _find_forbidden_hits_v1(candidate.get("user_visible_status"), candidate.get("operator_visible_summary")):
        blocked_labels.append(f"forbidden_phrase_{phrase.replace(' ', '_')}")

    return _dedupe(blocked_labels)



def _ensure_runtime_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    runtime_request = build_controlled_private_project_chat_runtime_request_v1(candidate)
    return run_controlled_private_project_chat_runtime_dry_run_v1(runtime_request)



def _build_result(candidate: Mapping[str, Any]) -> dict[str, Any]:
    runtime_result = _ensure_runtime_candidate(candidate)
    runtime_validation = _as_mapping(runtime_result.get("safe_metadata"))
    blocked_labels: list[str] = []
    blocked_labels.extend(_validate_request(candidate))
    blocked_labels.extend(_normalize_flags(candidate.get("blocked_labels")))
    blocked_labels.extend(_normalize_flags(runtime_result.get("blocked_labels")))
    blocked = bool(blocked_labels) or _safe_bool(runtime_result.get("blocked"))
    blocked_labels = _dedupe(blocked_labels)

    result_status = "blocked" if blocked else "private_local_entrypoint_valid_metadata_only"
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "entrypoint_request_packet": candidate,
        "request_id": candidate["request_id"],
        "project_id": candidate["project_id"],
        "owner_user_scope": candidate["owner_user_scope"],
        "tenant_account_scope": candidate["tenant_account_scope"],
        "source_scope": candidate["source_scope"],
        "entrypoint_mode": candidate["entrypoint_mode"],
        "owner_approval_metadata": candidate["owner_approval_metadata"],
        "controlled_private_runtime_result": runtime_result,
        "controlled_private_runtime_status": _safe_str(runtime_result.get("controlled_private_runtime_status")),
        "assembly_validation": _as_mapping(runtime_result.get("assembly_validation")),
        "dry_run_consumer_validation": _as_mapping(runtime_result.get("dry_run_consumer_validation")),
        "runtime_boundary_validation": _as_mapping(runtime_result.get("runtime_boundary_validation")),
        "answer_plan_validation": _as_mapping(runtime_result.get("answer_plan_validation")),
        "final_answer_validation": _as_mapping(runtime_result.get("final_answer_validation")),
        "evidence_validations": runtime_result.get("evidence_validations", []),
        "blocked_state": _as_mapping(runtime_result.get("blocked_state")),
        "missing_evidence_state": _as_mapping(runtime_result.get("missing_evidence_state")),
        "conflict_state": _as_mapping(runtime_result.get("conflict_state")),
        "approval_state": _as_mapping(runtime_result.get("approval_state")),
        "provenance_chain": _as_mapping(runtime_result.get("provenance_chain")),
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "entrypoint_status": result_status,
        "user_visible_status": _default_user_visible_status(blocked),
        "operator_visible_summary": _default_operator_visible_summary(candidate, blocked, runtime_result),
        "safe_metadata": {
            "entrypoint_mode": candidate["entrypoint_mode"],
            "owner_approval_required": True,
            "owner_approval_granted": _safe_bool(_as_mapping(candidate.get("owner_approval_metadata")).get("owner_approval_granted")),
            "public_user_facing_mode_requested": _safe_bool(candidate.get("public_user_facing_mode_requested")),
            "answer_delivery_requested": _safe_bool(candidate.get("answer_delivery_requested")),
            "provider_model_search_tool_requested": _safe_bool(candidate.get("provider_model_search_tool_requested")),
            "provider_call_requested": _safe_bool(candidate.get("provider_call_requested")),
            "model_call_requested": _safe_bool(candidate.get("model_call_requested")),
            "search_call_requested": _safe_bool(candidate.get("search_call_requested")),
            "tool_call_requested": _safe_bool(candidate.get("tool_call_requested")),
            "persistence_requested": _safe_bool(candidate.get("persistence_requested")),
            "weslr_io_requested": _safe_bool(candidate.get("weslr_io_requested")),
            "runtime_boundary_decision": _safe_str(_as_mapping(runtime_result.get("runtime_boundary_validation")).get("boundary_decision")),
            "runtime_validation_summary": runtime_validation,
        },
    }



def validate_private_local_project_chat_entrypoint_request_v1(packet: Any) -> dict[str, Any]:
    candidate = build_private_local_project_chat_entrypoint_request_v1(packet)
    result = _build_result(candidate)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "entrypoint_request_packet": candidate,
        **result,
    }



def run_private_local_project_chat_entrypoint_dry_run_v1(packet: Any) -> dict[str, Any]:
    return _build_result(build_private_local_project_chat_entrypoint_request_v1(packet))



def summarize_private_local_project_chat_entrypoint_result_v1(packet: Any) -> dict[str, Any]:
    result = run_private_local_project_chat_entrypoint_dry_run_v1(packet)
    summary_text = (
        f"{_safe_str(result.get('entrypoint_status'))} | "
        f"runtime={_safe_str(result.get('controlled_private_runtime_status'))} | "
        f"blocked={result.get('blocked')}"
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "request_id": result.get("request_id"),
        "project_id": result.get("project_id"),
        "summary_text": summary_text,
        "entrypoint_status": result.get("entrypoint_status"),
        "blocked": result.get("blocked"),
        "blocked_labels": result.get("blocked_labels", []),
        "operator_visible_summary": result.get("operator_visible_summary"),
        "safe_metadata": result.get("safe_metadata", {}),
    }



def to_private_local_project_chat_entrypoint_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def build_initial_private_local_project_chat_entrypoint_examples_v1() -> list[dict[str, Any]]:
    valid = run_private_local_project_chat_entrypoint_dry_run_v1({})
    blocked = run_private_local_project_chat_entrypoint_dry_run_v1(
        {
            "public_user_facing_mode_requested": True,
            "answer_delivery_requested": True,
            "provider_model_search_tool_requested": True,
            "provider_call_requested": True,
            "search_call_requested": True,
            "tool_call_requested": True,
            "persistence_requested": True,
            "weslr_io_requested": True,
        }
    )
    return [
        to_private_local_project_chat_entrypoint_json_safe_v1(valid),
        to_private_local_project_chat_entrypoint_json_safe_v1(blocked),
    ]


__all__ = [
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "ENTRYPOINT_MODE_V1",
    "ALLOWED_OWNER_MODES_V1",
    "allowed_private_local_project_chat_entrypoint_modes_v1",
    "build_private_local_project_chat_entrypoint_request_v1",
    "validate_private_local_project_chat_entrypoint_request_v1",
    "run_private_local_project_chat_entrypoint_dry_run_v1",
    "summarize_private_local_project_chat_entrypoint_result_v1",
    "to_private_local_project_chat_entrypoint_json_safe_v1",
    "build_initial_private_local_project_chat_entrypoint_examples_v1",
]
