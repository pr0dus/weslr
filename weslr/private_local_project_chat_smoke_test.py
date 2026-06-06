"""Metadata-only helpers for the private local Project Chat smoke test.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It consumes bounded owner-only private/local smoke-test metadata, delegates
to the private local Project Chat entrypoint helper only, and produces
internal smoke-test result metadata only.

It does not perform public chat, website chat, answer delivery, live
retrieval, provider/model/search/tool calls, persistence, `.weslr` IO,
UI/Nova behavior, or any public/user-facing behavior.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from weslr.private_local_project_chat_entrypoint import (
    build_private_local_project_chat_entrypoint_request_v1,
    run_private_local_project_chat_entrypoint_dry_run_v1,
)

HELPER_TYPE_V1 = "weslr_private_local_project_chat_smoke_test_v1"
SCHEMA_VERSION_V1 = "private_local_project_chat_smoke_test_v1"
SMOKE_TEST_MODE_V1 = "owner_only_private_local_smoke_test"
ALLOWED_SMOKE_TEST_MODES_V1 = (
    "owner_only_private_local_smoke_test",
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
    "public user-facing",
    "public/user-facing",
    "open registration",
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


def allowed_private_local_project_chat_smoke_test_modes_v1() -> tuple[str, ...]:
    return ALLOWED_SMOKE_TEST_MODES_V1



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



def _base_case_metadata() -> dict[str, Any]:
    return {
        "case_id": "smoke-case-001",
        "request_id": "smoke-request-001",
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "user_intent_class": "project-chat",
        "smoke_test_mode": SMOKE_TEST_MODE_V1,
        "owner_approval_metadata_supplied": False,
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
        "provenance_refs": ["smoke-test-provenance-001"],
        "user_visible_status": "private local project chat smoke test metadata only",
        "operator_visible_summary": "private local smoke test request; metadata only",
    }



def _default_user_visible_status(blocked: bool) -> str:
    return "Private local smoke test is blocked." if blocked else "Private local smoke test metadata only."



def _default_operator_visible_summary(candidate: Mapping[str, Any], blocked: bool, entrypoint_result: Mapping[str, Any]) -> str:
    return (
        f"{_safe_str(candidate.get('smoke_test_mode'))} | "
        f"entrypoint={_safe_str(entrypoint_result.get('entrypoint_status'))} | "
        f"blocked={blocked} | "
        f"approval={_safe_bool(_as_mapping(candidate.get('owner_approval_metadata')).get('owner_approval_granted'))}"
    )



def _build_case_packet(case: Mapping[str, Any]) -> dict[str, Any]:
    packet = {
        "schema_version": _safe_str(case.get("schema_version")) or SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "case_id": _safe_str(case.get("case_id")) or "smoke-case-001",
        "request_id": _safe_str(case.get("request_id")) or "smoke-request-001",
        "project_id": _safe_str(case.get("project_id")) or "project-001",
        "owner_user_scope": _safe_str(case.get("owner_user_scope")) or "owner-user",
        "tenant_account_scope": _safe_str(case.get("tenant_account_scope")) or "tenant-a",
        "source_scope": _safe_str(case.get("source_scope")) or "project_metadata_only",
        "user_intent_class": _safe_str(case.get("user_intent_class")) or "project-chat",
        "smoke_test_mode": _safe_str(case.get("smoke_test_mode")) or SMOKE_TEST_MODE_V1,
        "owner_approval_metadata_supplied": _safe_bool(case.get("owner_approval_metadata_supplied", False)),
        "owner_approval_metadata": _as_mapping(case.get("owner_approval_metadata")),
        "public_user_facing_mode_requested": _safe_bool(case.get("public_user_facing_mode_requested", False)),
        "answer_delivery_requested": _safe_bool(case.get("answer_delivery_requested", False)),
        "provider_model_search_tool_requested": _safe_bool(case.get("provider_model_search_tool_requested", False)),
        "provider_call_requested": _safe_bool(case.get("provider_call_requested", False)),
        "model_call_requested": _safe_bool(case.get("model_call_requested", False)),
        "search_call_requested": _safe_bool(case.get("search_call_requested", False)),
        "tool_call_requested": _safe_bool(case.get("tool_call_requested", False)),
        "persistence_requested": _safe_bool(case.get("persistence_requested", False)),
        "weslr_io_requested": _safe_bool(case.get("weslr_io_requested", False)),
        "retrieval_requested": _safe_bool(case.get("retrieval_requested", False)),
        "live_retrieval_requested": _safe_bool(case.get("live_retrieval_requested", False)),
        "approval_refs": _safe_list(case.get("approval_refs")) or ["approval-001"],
        "operator_visibility_refs": _safe_list(case.get("operator_visibility_refs")) or ["operator-001"],
        "uncertainty_flags": _normalize_flags(case.get("uncertainty_flags")),
        "stale_state_flags": _normalize_flags(case.get("stale_state_flags")),
        "contradiction_flags": _normalize_flags(case.get("contradiction_flags")),
        "missing_evidence_flags": _normalize_flags(case.get("missing_evidence_flags")),
        "limitations": _normalize_flags(case.get("limitations")),
        "blocked_labels": _normalize_flags(case.get("blocked_labels")),
        "provenance_refs": _safe_list(case.get("provenance_refs")) or ["smoke-test-provenance-001"],
        "user_visible_status": _safe_str(case.get("user_visible_status")) or "private local project chat smoke test metadata only",
        "operator_visible_summary": _safe_str(case.get("operator_visible_summary")) or "private local smoke test request; metadata only",
    }
    if not packet["case_id"]:
        digest_source = {k: v for k, v in packet.items() if k != "case_id"}
        packet["case_id"] = f"private-local-smoke-case-{_stable_digest(digest_source)[:16]}"
    return packet



def build_private_local_project_chat_smoke_test_case_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    case = _base_case_metadata()
    case.update(data)
    return _build_case_packet(case)



def _validate_case(candidate: Mapping[str, Any]) -> list[str]:
    blocked_labels: list[str] = []

    for field in ("case_id", "request_id", "project_id", "owner_user_scope", "tenant_account_scope", "source_scope", "user_intent_class", "smoke_test_mode"):
        if not _safe_str(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    if candidate.get("smoke_test_mode") not in ALLOWED_SMOKE_TEST_MODES_V1:
        blocked_labels.append("unknown_smoke_test_mode")

    if candidate.get("owner_approval_metadata_supplied") is not True:
        blocked_labels.append("missing_owner_approval_metadata")

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



def _entrypoint_case(payload: Mapping[str, Any]) -> dict[str, Any]:
    return build_private_local_project_chat_entrypoint_request_v1(payload)



def _build_result(candidate: Mapping[str, Any]) -> dict[str, Any]:
    entrypoint_request = _entrypoint_case(candidate)
    entrypoint_result = run_private_local_project_chat_entrypoint_dry_run_v1(entrypoint_request)

    blocked_labels: list[str] = []
    blocked_labels.extend(_validate_case(candidate))
    blocked_labels.extend(_normalize_flags(candidate.get("blocked_labels")))
    blocked_labels.extend(_normalize_flags(entrypoint_result.get("blocked_labels")))

    blocked = bool(blocked_labels) or _safe_bool(entrypoint_result.get("blocked"))
    blocked_labels = _dedupe(blocked_labels)
    result_status = "blocked" if blocked else "private_local_smoke_test_valid_metadata_only"

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "smoke_test_case_packet": candidate,
        "case_id": candidate["case_id"],
        "request_id": candidate["request_id"],
        "project_id": candidate["project_id"],
        "owner_user_scope": candidate["owner_user_scope"],
        "tenant_account_scope": candidate["tenant_account_scope"],
        "source_scope": candidate["source_scope"],
        "smoke_test_mode": candidate["smoke_test_mode"],
        "owner_approval_metadata_supplied": candidate["owner_approval_metadata_supplied"],
        "owner_approval_metadata": candidate["owner_approval_metadata"],
        "entrypoint_request_packet": entrypoint_request,
        "entrypoint_result_packet": entrypoint_result,
        "entrypoint_status": _safe_str(entrypoint_result.get("entrypoint_status")),
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "smoke_test_status": result_status,
        "metadata_only_verified": _safe_bool(entrypoint_result.get("blocked")) is False,
        "answer_delivery_verified": not _safe_bool(entrypoint_result.get("safe_metadata", {}).get("answer_delivery_requested")),
        "public_mode_verified": not _safe_bool(entrypoint_result.get("safe_metadata", {}).get("public_user_facing_mode_requested")),
        "provider_model_search_tool_verified": not _safe_bool(entrypoint_result.get("safe_metadata", {}).get("provider_model_search_tool_requested")),
        "live_retrieval_verified": not _safe_bool(entrypoint_result.get("safe_metadata", {}).get("retrieval_requested")) and not _safe_bool(entrypoint_result.get("safe_metadata", {}).get("entrypoint_blocked")),
        "persistence_verified": not _safe_bool(entrypoint_result.get("safe_metadata", {}).get("persistence_requested")),
        "blocked_state": _as_mapping(entrypoint_result.get("blocked_state")),
        "missing_evidence_state": _as_mapping(entrypoint_result.get("missing_evidence_state")),
        "conflict_state": _as_mapping(entrypoint_result.get("conflict_state")),
        "approval_state": _as_mapping(entrypoint_result.get("approval_state")),
        "provenance_chain": _as_mapping(entrypoint_result.get("provenance_chain")),
        "runtime_boundary_validation": _as_mapping(entrypoint_result.get("runtime_boundary_validation")),
        "user_visible_status": _default_user_visible_status(blocked),
        "operator_visible_summary": _default_operator_visible_summary(candidate, blocked, entrypoint_result),
        "safe_metadata": {
            "smoke_test_mode": candidate["smoke_test_mode"],
            "owner_approval_required": True,
            "owner_approval_granted": _safe_bool(_as_mapping(candidate.get("owner_approval_metadata")).get("owner_approval_granted")),
            "owner_approval_metadata_supplied": _safe_bool(candidate.get("owner_approval_metadata_supplied")),
            "entrypoint_status": _safe_str(entrypoint_result.get("entrypoint_status")),
            "entrypoint_blocked": _safe_bool(entrypoint_result.get("blocked")),
            "runtime_boundary_decision": _safe_str(_as_mapping(entrypoint_result.get("runtime_boundary_validation")).get("boundary_decision")),
        },
    }



def validate_private_local_project_chat_smoke_test_case_v1(packet: Any) -> dict[str, Any]:
    candidate = build_private_local_project_chat_smoke_test_case_v1(packet)
    result = _build_result(candidate)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "smoke_test_case_packet": candidate,
        **result,
    }



def run_private_local_project_chat_smoke_test_v1(packet: Any) -> dict[str, Any]:
    return _build_result(build_private_local_project_chat_smoke_test_case_v1(packet))



def summarize_private_local_project_chat_smoke_test_result_v1(packet: Any) -> dict[str, Any]:
    result = run_private_local_project_chat_smoke_test_v1(packet)
    summary_text = (
        f"{_safe_str(result.get('smoke_test_status'))} | "
        f"entrypoint={_safe_str(result.get('entrypoint_status'))} | "
        f"blocked={result.get('blocked')}"
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "case_id": result.get("case_id"),
        "request_id": result.get("request_id"),
        "summary_text": summary_text,
        "smoke_test_status": result.get("smoke_test_status"),
        "blocked": result.get("blocked"),
        "blocked_labels": result.get("blocked_labels", []),
        "operator_visible_summary": result.get("operator_visible_summary"),
        "safe_metadata": result.get("safe_metadata", {}),
    }



def to_private_local_project_chat_smoke_test_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def build_initial_private_local_project_chat_smoke_test_examples_v1() -> list[dict[str, Any]]:
    approval = {
        "owner_approval_required": True,
        "owner_approval_granted": True,
        "owner_approval_ref": "approval-001",
        "operator_visible_summary": "owner approval granted for private local smoke test only",
    }
    valid = run_private_local_project_chat_smoke_test_v1({"owner_approval_metadata_supplied": True, "owner_approval_metadata": approval})
    blocked = run_private_local_project_chat_smoke_test_v1(
        {
            "owner_approval_metadata_supplied": True,
            "owner_approval_metadata": approval,
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
        to_private_local_project_chat_smoke_test_json_safe_v1(valid),
        to_private_local_project_chat_smoke_test_json_safe_v1(blocked),
    ]


__all__ = [
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "SMOKE_TEST_MODE_V1",
    "ALLOWED_SMOKE_TEST_MODES_V1",
    "allowed_private_local_project_chat_smoke_test_modes_v1",
    "build_private_local_project_chat_smoke_test_case_v1",
    "validate_private_local_project_chat_smoke_test_case_v1",
    "run_private_local_project_chat_smoke_test_v1",
    "summarize_private_local_project_chat_smoke_test_result_v1",
    "to_private_local_project_chat_smoke_test_json_safe_v1",
    "build_initial_private_local_project_chat_smoke_test_examples_v1",
]
