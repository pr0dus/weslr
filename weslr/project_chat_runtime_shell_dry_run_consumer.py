"""Metadata-only helpers for the WESLR project-chat runtime shell dry-run consumer V1.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It consumes project-chat assembly/orchestration metadata and prepares a
runtime-shell dry-run consumer packet only.

It does not perform file I/O, network I/O, shell execution, runtime wiring,
retrieval execution, model calls, tool execution, external actions,
persistence, UI consumption, live chat output, answer delivery, or final
answer generation.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from weslr.controlled_project_chat_runtime_shell_metadata import (
    build_controlled_project_chat_shell_packet_v1,
    validate_controlled_project_chat_shell_packet_v1,
)
from weslr.project_chat_assembly_orchestration_packet import (
    DENIED_AUTHORITY_FIELDS_V1 as ASSEMBLY_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_assembly_packet_v1,
    validate_project_chat_assembly_packet_v1,
)
from weslr.project_chat_runtime_dry_run_consumption_plan import (
    build_project_chat_dry_run_consumption_plan_v1,
    validate_project_chat_dry_run_consumption_plan_v1,
)
from weslr.project_chat_final_answer_generation import (
    DENIED_AUTHORITY_FIELDS_V1 as FINAL_ANSWER_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_final_answer_packet_v1,
    validate_project_chat_final_answer_packet_v1,
)
from weslr.project_chat_runtime_dry_run_metadata import (
    build_project_chat_runtime_dry_run_v1,
    validate_project_chat_runtime_dry_run_v1,
)

HELPER_TYPE_V1 = "weslr_project_chat_runtime_shell_dry_run_consumer_v1"
SCHEMA_VERSION_V1 = "project_chat_runtime_shell_dry_run_consumer_v1"

CONSUMER_MODES_V1 = (
    "blocked_dry_run_consumer",
    "metadata_only_dry_run_consumer",
)

CONSUMER_STATUSES_V1 = (
    "consumer_valid_metadata_only",
    "blocked",
    "invalid",
)

CONSUMER_DECISIONS_V1 = (
    "block_before_runtime",
    "preserve_metadata_only",
)

RUNTIME_SHELL_READINESS_LABELS_V1 = (
    "assembly_packet_preserved",
    "shell_packet_preserved",
    "dry_run_metadata_preserved",
    "consumption_plan_metadata_preserved",
    "final_answer_packet_preserved",
    "blocked_state_preserved",
    "missing_evidence_state_preserved",
    "conflict_state_preserved",
    "approval_state_preserved",
    "provenance_chain_preserved",
    "shell_metadata_dry_run_only",
    "not_ready_for_live_runtime",
    "answer_delivery_blocked",
    "retrieval_execution_blocked",
    "provider_model_search_tool_authority_blocked",
    "persistence_blocked",
    "private_leak_blocked",
    "public_ready_claim_blocked",
    "cognitive_engine_authority_blocked",
)

DENIED_AUTHORITY_FIELDS_V1 = tuple(dict.fromkeys((*ASSEMBLY_DENIED_AUTHORITY_FIELDS_V1, *FINAL_ANSWER_DENIED_AUTHORITY_FIELDS_V1)))

FORBIDDEN_LEAKAGE_PHRASES_V1 = (
    "unknown engine",
    "raw transcript",
    "raw prompt",
    "raw message",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "private content",
    "secret",
    "confidential",
    "live chat",
    "live chat output",
    "chat responder",
    "respond_chat",
    "generate_chat",
    "provider output",
    "model output",
    "search output",
    "tool output",
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

_DEFAULT_FALSE_DENIED_AUTHORITY = {field: False for field in DENIED_AUTHORITY_FIELDS_V1}


def allowed_project_chat_runtime_shell_dry_run_consumer_modes_v1() -> tuple[str, ...]:
    return CONSUMER_MODES_V1



def allowed_project_chat_runtime_shell_dry_run_consumer_statuses_v1() -> tuple[str, ...]:
    return CONSUMER_STATUSES_V1



def allowed_project_chat_runtime_shell_dry_run_consumer_decisions_v1() -> tuple[str, ...]:
    return CONSUMER_DECISIONS_V1



def allowed_project_chat_runtime_shell_dry_run_consumer_readiness_labels_v1() -> tuple[str, ...]:
    return RUNTIME_SHELL_READINESS_LABELS_V1



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



def _normalize_denied_authority(value: Any) -> dict[str, bool]:
    payload = dict(_DEFAULT_FALSE_DENIED_AUTHORITY)
    raw = _as_mapping(value)
    for field in DENIED_AUTHORITY_FIELDS_V1:
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
    text = _safe_str(value).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "value"



def _find_forbidden_hits_v1(values: Any) -> list[str]:
    hits: list[str] = []
    stack = [values]
    while stack:
        current = stack.pop()
        if isinstance(current, Mapping):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, tuple):
            stack.extend(list(current))
        elif isinstance(current, set):
            stack.extend(list(current))
        else:
            text = _safe_str(current).lower()
            for phrase in FORBIDDEN_LEAKAGE_PHRASES_V1:
                if phrase and phrase in text:
                    hits.append(phrase)
    return _dedupe(hits)



def _nested_validation_or_empty(value: Any, validator, label: str) -> dict[str, Any]:
    candidate = _as_mapping(value)
    if not candidate:
        return {"present": False, "blocked": False, "blocked_labels": [], "classification": "absent"}
    validation = validator(candidate)
    if validation.get("blocked"):
        validation = dict(validation)
        validation.setdefault("blocked_labels", [])
        validation["blocked_labels"] = list(validation["blocked_labels"])
        validation["blocked"] = True
        validation["nested_label"] = label
    return validation



def _default_readiness_labels() -> list[str]:
    return [
        "assembly_packet_preserved",
        "shell_packet_preserved",
        "dry_run_metadata_preserved",
        "consumption_plan_metadata_preserved",
        "final_answer_packet_preserved",
        "blocked_state_preserved",
        "missing_evidence_state_preserved",
        "conflict_state_preserved",
        "approval_state_preserved",
        "provenance_chain_preserved",
        "shell_metadata_dry_run_only",
        "not_ready_for_live_runtime",
        "answer_delivery_blocked",
        "retrieval_execution_blocked",
        "provider_model_search_tool_authority_blocked",
        "persistence_blocked",
        "private_leak_blocked",
        "public_ready_claim_blocked",
        "cognitive_engine_authority_blocked",
    ]



def _normalize_state_copy(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in value.items()}
    return {}



def _consumer_mode_for_blocked(blocked: bool) -> str:
    return "blocked_dry_run_consumer" if blocked else "metadata_only_dry_run_consumer"



def _consumer_decision_for_blocked(blocked: bool) -> str:
    return "block_before_runtime" if blocked else "preserve_metadata_only"



def _consumer_status_for_blocked(blocked: bool) -> str:
    return "blocked" if blocked else "consumer_valid_metadata_only"



def _build_default_message_metadata(assembly_packet: Mapping[str, Any]) -> dict[str, Any]:
    user_request = _as_mapping(assembly_packet.get("user_request_metadata"))
    return {
        "project_id": _safe_str(user_request.get("project_id")) or _safe_str(assembly_packet.get("project_id")),
        "owner_user_scope": _safe_str(user_request.get("owner_user_scope")) or _safe_str(assembly_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(user_request.get("tenant_account_scope")) or _safe_str(assembly_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(user_request.get("source_scope")) or _safe_str(assembly_packet.get("source_scope")),
        "message_intent_class": _safe_str(user_request.get("user_intent_class")) or "project-chat",
        "message_status": "metadata only",
        "user_visible_status": _safe_str(user_request.get("user_visible_status")) or "metadata only",
        "operator_visible_summary": _safe_str(user_request.get("operator_visible_summary")) or "message metadata only",
    }



def _build_default_shell_payload(assembly_packet: Mapping[str, Any], shell_state: str, shell_decision: str, shell_packet_type: str) -> dict[str, Any]:
    user_request = _as_mapping(assembly_packet.get("user_request_metadata"))
    project_context = _as_mapping(assembly_packet.get("project_context_metadata"))
    answer_plan = _as_mapping(assembly_packet.get("answer_plan_metadata"))
    retrieval_need = _as_mapping(assembly_packet.get("retrieval_need_metadata"))
    evidence_packets = assembly_packet.get("evidence_packet_metadata") if isinstance(assembly_packet.get("evidence_packet_metadata"), list) else []
    return {
        "project_id": _safe_str(user_request.get("project_id")) or _safe_str(assembly_packet.get("project_id")),
        "owner_user_scope": _safe_str(user_request.get("owner_user_scope")) or _safe_str(assembly_packet.get("owner_user_scope")),
        "tenant_account_scope": _safe_str(user_request.get("tenant_account_scope")) or _safe_str(assembly_packet.get("tenant_account_scope")),
        "source_scope": _safe_str(user_request.get("source_scope")) or _safe_str(assembly_packet.get("source_scope")),
        "shell_state": shell_state,
        "shell_decision": shell_decision,
        "shell_packet_type": shell_packet_type,
        "message_metadata": _build_default_message_metadata(assembly_packet),
        "project_state_metadata": {
            "project_state_refs": _normalize_refs(project_context.get("project_state_refs")),
            "user_visible_status": _safe_str(project_context.get("user_visible_status")) or "metadata only",
            "operator_visible_summary": _safe_str(project_context.get("operator_visible_summary")) or "project context metadata only",
        },
        "memory_state_metadata": {
            "memory_state_refs": _normalize_refs(project_context.get("memory_state_refs")),
        },
        "continuity_metadata": {
            "continuity_state_refs": _normalize_refs(project_context.get("continuity_state_refs")),
        },
        "evidence_retrieval_metadata": {
            "retrieval_need_class": _safe_str(retrieval_need.get("retrieval_need_class")) or "project_metadata_retrieval_needed",
            "retrieval_status": _safe_str(retrieval_need.get("retrieval_status")) or "metadata only",
            "evidence_packet_refs": _normalize_refs(
                [
                    item.get("evidence_packet_id") if isinstance(item, Mapping) else item
                    for item in evidence_packets
                ]
            ),
        },
        "answer_plan_metadata": answer_plan,
        "blocked_authority": "runtime_shell_dry_run_consumer_boundary",
        "user_visible_status": _safe_str(user_request.get("user_visible_status")) or "metadata only",
        "operator_visible_summary": _safe_str(user_request.get("operator_visible_summary")) or "metadata only",
        "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
    }



def _build_default_runtime_shell_readiness_labels(assembly_packet: Mapping[str, Any], shell_packet: Mapping[str, Any]) -> list[str]:
    labels = _default_readiness_labels()
    assembly_mode = _safe_str(assembly_packet.get("assembly_mode"))
    assembly_status = _safe_str(assembly_packet.get("assembly_status"))
    shell_state = _safe_str(shell_packet.get("shell_state"))
    if assembly_mode == "blocked_orchestration" or assembly_status == "blocked" or shell_state == "shell_blocked":
        labels = [label for label in labels if label != "shell_metadata_dry_run_only"]
        if "shell_not_ready_for_live_runtime" not in labels:
            labels.append("shell_not_ready_for_live_runtime")
    return _dedupe(labels)



def build_project_chat_runtime_shell_dry_run_consumer_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)

    assembly_source = (
        data.get("assembly_packet_metadata")
        or data.get("assembly_packet")
        or data.get("assembly_orchestration_packet")
        or data
    )
    assembly_packet = build_project_chat_assembly_packet_v1(assembly_source)
    assembly_validation = validate_project_chat_assembly_packet_v1(assembly_packet)

    shell_state = _safe_str(data.get("shell_state")) or ("shell_blocked" if assembly_validation["blocked"] else "shell_metadata_dry_run_only")
    shell_decision = _safe_str(data.get("shell_decision")) or ("block_before_runtime" if assembly_validation["blocked"] else "build_consumption_plan_metadata")
    shell_packet_type = _safe_str(data.get("shell_packet_type")) or ("shell_blocked_packet" if assembly_validation["blocked"] else "shell_observability_packet")

    shell_packet = build_controlled_project_chat_shell_packet_v1(
        _build_default_shell_payload(assembly_packet, shell_state, shell_decision, shell_packet_type)
    )
    shell_validation = validate_controlled_project_chat_shell_packet_v1(shell_packet)

    dry_run_metadata = _as_mapping(shell_packet.get("dry_run_metadata"))
    dry_run_validation = validate_project_chat_runtime_dry_run_v1(dry_run_metadata)
    consumption_plan_metadata = _as_mapping(shell_packet.get("consumption_plan_metadata"))
    consumption_plan_validation = validate_project_chat_dry_run_consumption_plan_v1(consumption_plan_metadata)
    final_answer_packet_metadata = _as_mapping(assembly_packet.get("final_answer_packet_metadata"))
    final_answer_validation = validate_project_chat_final_answer_packet_v1(final_answer_packet_metadata)

    runtime_shell_readiness_labels = _normalize_refs(data.get("runtime_shell_readiness_labels")) or _build_default_runtime_shell_readiness_labels(assembly_packet, shell_packet)

    blocked_state = _normalize_state_copy(assembly_packet.get("blocked_state"))
    for field in (
        "live_chat_output_blocked",
        "answer_delivery_blocked",
        "retrieval_execution_blocked",
        "persistence_blocked",
        "provider_model_search_tool_authority_blocked",
        "private_leak_blocked",
        "public_ready_claim_blocked",
        "cognitive_engine_authority_blocked",
    ):
        blocked_state[field] = True
    blocked_state.setdefault("blocked", bool(assembly_validation["blocked"] or shell_validation["blocked"] or dry_run_validation["blocked"] or consumption_plan_validation["blocked"] or final_answer_validation["blocked"]))
    blocked_state.setdefault("blocked_labels", [])
    blocked_state.setdefault("blocked_reasons", list(blocked_state.get("blocked_labels") or []))

    missing_evidence_state = _normalize_state_copy(assembly_packet.get("missing_evidence_state"))
    conflict_state = _normalize_state_copy(assembly_packet.get("conflict_state"))
    approval_state = _normalize_state_copy(assembly_packet.get("approval_state"))
    provenance_chain = _normalize_state_copy(assembly_packet.get("provenance_chain"))

    forbidden_texts = [
        _as_mapping(assembly_packet.get("user_request_metadata")).get("user_visible_status"),
        _as_mapping(assembly_packet.get("final_answer_packet_metadata")).get("controlled_answer_text_proposal"),
        shell_packet.get("user_visible_status"),
        _as_mapping(dry_run_metadata).get("user_visible_status"),
        _as_mapping(consumption_plan_metadata).get("user_visible_status"),
        _as_mapping(data.get("safe_metadata")).get("consumer_summary"),
    ]
    blocked = bool(assembly_validation["blocked"] or shell_validation["blocked"] or dry_run_validation["blocked"] or consumption_plan_validation["blocked"] or final_answer_validation["blocked"] or _find_forbidden_hits_v1(forbidden_texts))
    consumer_mode = _safe_str(data.get("consumer_mode")) or _consumer_mode_for_blocked(blocked)
    consumer_decision = _safe_str(data.get("consumer_decision")) or _consumer_decision_for_blocked(blocked)
    consumer_status = _safe_str(data.get("consumer_status")) or _consumer_status_for_blocked(blocked)

    consumer_packet = {
        "schema_version": _safe_str(data.get("schema_version")) or SCHEMA_VERSION_V1,
        "consumer_id": _safe_str(data.get("consumer_id")),
        "consumer_mode": consumer_mode,
        "consumer_decision": consumer_decision,
        "consumer_status": consumer_status,
        "assembly_packet_metadata": assembly_packet,
        "shell_packet_metadata": shell_packet,
        "dry_run_metadata": dry_run_metadata,
        "consumption_plan_metadata": consumption_plan_metadata,
        "final_answer_packet_metadata": final_answer_packet_metadata,
        "runtime_shell_readiness_labels": runtime_shell_readiness_labels,
        "blocked_state": blocked_state,
        "missing_evidence_state": missing_evidence_state,
        "conflict_state": conflict_state,
        "approval_state": approval_state,
        "provenance_chain": provenance_chain,
        "denied_authority": _normalize_denied_authority(data.get("denied_authority") or {}),
        "assembly_validation": assembly_validation,
        "shell_validation": shell_validation,
        "dry_run_validation": dry_run_validation,
        "consumption_plan_validation": consumption_plan_validation,
        "final_answer_validation": final_answer_validation,
        "safe_metadata": {
            "consumer_summary": "metadata only runtime shell dry-run consumer packet",
            "consumer_mode": consumer_mode,
            "consumer_status": consumer_status,
            "consumer_decision": consumer_decision,
            "assembly_mode": _safe_str(assembly_packet.get("assembly_mode")),
            "assembly_status": _safe_str(assembly_packet.get("assembly_status")),
            "shell_state": _safe_str(shell_packet.get("shell_state")),
            "shell_decision": _safe_str(shell_packet.get("shell_decision")),
            "shell_packet_type": _safe_str(shell_packet.get("shell_packet_type")),
            "final_answer_status": _safe_str(final_answer_packet_metadata.get("final_answer_status")),
            "readiness_labels": runtime_shell_readiness_labels,
            "live_chat_output_blocked": True,
            "answer_delivery_blocked": True,
            "retrieval_execution_blocked": True,
            "persistence_blocked": True,
            "provider_model_search_tool_authority_blocked": True,
            "private_leak_blocked": True,
            "public_ready_claim_blocked": True,
            "cognitive_engine_authority_blocked": True,
        },
        "helper_type": HELPER_TYPE_V1,
    }

    if not consumer_packet["consumer_id"]:
        digest_source = {key: value for key, value in consumer_packet.items() if key not in {"consumer_id", "safe_metadata", "assembly_validation", "shell_validation", "dry_run_validation", "consumption_plan_validation", "final_answer_validation"}}
        consumer_packet["consumer_id"] = f"project-chat-runtime-shell-dry-run-consumer-{_stable_digest(digest_source)[:16]}"

    return consumer_packet



def validate_project_chat_runtime_shell_dry_run_consumer_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_runtime_shell_dry_run_consumer_packet_v1(packet)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")

    required_fields = (
        "consumer_id",
        "consumer_mode",
        "consumer_decision",
        "consumer_status",
        "assembly_packet_metadata",
        "shell_packet_metadata",
        "dry_run_metadata",
        "consumption_plan_metadata",
        "final_answer_packet_metadata",
        "runtime_shell_readiness_labels",
        "blocked_state",
        "missing_evidence_state",
        "conflict_state",
        "approval_state",
        "provenance_chain",
        "denied_authority",
        "safe_metadata",
    )
    for field in required_fields:
        value = candidate.get(field)
        if field in {"assembly_packet_metadata", "shell_packet_metadata", "dry_run_metadata", "consumption_plan_metadata", "final_answer_packet_metadata", "blocked_state", "missing_evidence_state", "conflict_state", "approval_state", "provenance_chain", "denied_authority", "safe_metadata"}:
            if not isinstance(value, Mapping):
                blocked_labels.append(f"missing_{field}")
        elif field == "runtime_shell_readiness_labels":
            if not isinstance(value, list) or not value:
                blocked_labels.append("missing_runtime_shell_readiness_labels")
        elif not _safe_str(value):
            blocked_labels.append(f"missing_{field}")

    if candidate.get("consumer_mode") not in CONSUMER_MODES_V1:
        blocked_labels.append("unknown_consumer_mode")
    if candidate.get("consumer_status") not in CONSUMER_STATUSES_V1:
        blocked_labels.append("unknown_consumer_status")
    if candidate.get("consumer_decision") not in CONSUMER_DECISIONS_V1:
        blocked_labels.append("unknown_consumer_decision")

    for label in _normalize_refs(candidate.get("runtime_shell_readiness_labels")):
        if label not in RUNTIME_SHELL_READINESS_LABELS_V1:
            blocked_labels.append(f"unknown_runtime_shell_readiness_label_{_slugify_v1(label)}")

    assembly_validation = candidate.get("assembly_validation") if isinstance(candidate.get("assembly_validation"), Mapping) else validate_project_chat_assembly_packet_v1(candidate.get("assembly_packet_metadata", {}))
    shell_validation = candidate.get("shell_validation") if isinstance(candidate.get("shell_validation"), Mapping) else validate_controlled_project_chat_shell_packet_v1(candidate.get("shell_packet_metadata", {}))
    dry_run_validation = candidate.get("dry_run_validation") if isinstance(candidate.get("dry_run_validation"), Mapping) else validate_project_chat_runtime_dry_run_v1(candidate.get("dry_run_metadata", {}))
    consumption_plan_validation = candidate.get("consumption_plan_validation") if isinstance(candidate.get("consumption_plan_validation"), Mapping) else validate_project_chat_dry_run_consumption_plan_v1(candidate.get("consumption_plan_metadata", {}))
    final_answer_validation = candidate.get("final_answer_validation") if isinstance(candidate.get("final_answer_validation"), Mapping) else validate_project_chat_final_answer_packet_v1(candidate.get("final_answer_packet_metadata", {}))

    if not isinstance(candidate.get("assembly_packet_metadata"), Mapping):
        blocked_labels.append("invalid_assembly_packet_metadata")
    elif assembly_validation.get("blocked"):
        blocked_labels.append("invalid_assembly_packet_metadata")

    if not isinstance(candidate.get("shell_packet_metadata"), Mapping):
        blocked_labels.append("invalid_shell_packet_metadata")
    elif shell_validation.get("blocked"):
        blocked_labels.append("invalid_shell_packet_metadata")

    if not isinstance(candidate.get("dry_run_metadata"), Mapping):
        blocked_labels.append("invalid_dry_run_metadata")
    elif dry_run_validation.get("blocked"):
        blocked_labels.append("invalid_dry_run_metadata")

    if not isinstance(candidate.get("consumption_plan_metadata"), Mapping):
        blocked_labels.append("invalid_consumption_plan_metadata")
    elif consumption_plan_validation.get("blocked"):
        blocked_labels.append("invalid_consumption_plan_metadata")

    if not isinstance(candidate.get("final_answer_packet_metadata"), Mapping):
        blocked_labels.append("invalid_final_answer_packet_metadata")
    elif final_answer_validation.get("blocked"):
        blocked_labels.append("invalid_final_answer_packet_metadata")

    blocked_state = _as_mapping(candidate.get("blocked_state"))
    for field in (
        "live_chat_output_blocked",
        "answer_delivery_blocked",
        "retrieval_execution_blocked",
        "persistence_blocked",
        "provider_model_search_tool_authority_blocked",
        "private_leak_blocked",
        "public_ready_claim_blocked",
        "cognitive_engine_authority_blocked",
    ):
        if blocked_state.get(field) is not True:
            blocked_labels.append(f"missing_{field}")

    if _safe_bool(blocked_state.get("blocked")) and not _normalize_refs(blocked_state.get("blocked_labels")):
        blocked_labels.append("blocked_state_missing_labels")

    for field, value in candidate.get("denied_authority", {}).items():
        if field not in DENIED_AUTHORITY_FIELDS_V1:
            blocked_labels.append(f"unknown_denied_authority_field_{field}")
        elif _safe_bool(value):
            blocked_labels.append(f"denied_authority_must_remain_false_{field}")

    if len(_normalize_refs(candidate.get("runtime_shell_readiness_labels"))) < 5:
        blocked_labels.append("runtime_shell_readiness_labels_incomplete")

    if len(_normalize_refs(_as_mapping(candidate.get("provenance_chain")).get("steps"))) == 0:
        blocked_labels.append("missing_provenance_chain")

    forbidden_texts = [
        _as_mapping(candidate.get("assembly_packet_metadata")).get("user_request_metadata", {}).get("user_visible_status"),
        _as_mapping(candidate.get("assembly_packet_metadata")).get("final_answer_packet_metadata", {}).get("controlled_answer_text_proposal"),
        _as_mapping(candidate.get("shell_packet_metadata")).get("user_visible_status"),
        _as_mapping(candidate.get("dry_run_metadata")).get("user_visible_status"),
        _as_mapping(candidate.get("consumption_plan_metadata")).get("user_visible_status"),
        _as_mapping(candidate.get("safe_metadata")).get("consumer_summary"),
    ]
    for phrase in _find_forbidden_hits_v1(forbidden_texts):
        blocked_labels.append(f"forbidden_phrase_{_slugify_v1(phrase)}")

    blocked = bool(blocked_labels)
    status = "blocked" if blocked else "consumer_valid_metadata_only"
    if blocked and status == "consumer_valid_metadata_only":
        status = "blocked"

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "consumer_packet": candidate,
        "consumer_id": candidate["consumer_id"],
        "consumer_mode": candidate["consumer_mode"],
        "consumer_decision": candidate["consumer_decision"],
        "consumer_status": status,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "assembly_validation": assembly_validation,
        "shell_validation": shell_validation,
        "dry_run_validation": dry_run_validation,
        "consumption_plan_validation": consumption_plan_validation,
        "final_answer_validation": final_answer_validation,
        "assembly_packet_metadata": candidate["assembly_packet_metadata"],
        "shell_packet_metadata": candidate["shell_packet_metadata"],
        "dry_run_metadata": candidate["dry_run_metadata"],
        "consumption_plan_metadata": candidate["consumption_plan_metadata"],
        "final_answer_packet_metadata": candidate["final_answer_packet_metadata"],
        "runtime_shell_readiness_labels": candidate["runtime_shell_readiness_labels"],
        "blocked_state": candidate["blocked_state"],
        "missing_evidence_state": candidate["missing_evidence_state"],
        "conflict_state": candidate["conflict_state"],
        "approval_state": candidate["approval_state"],
        "provenance_chain": candidate["provenance_chain"],
        "denied_authority": candidate["denied_authority"],
        "safe_metadata": candidate["safe_metadata"],
    }



def summarize_project_chat_runtime_shell_dry_run_consumer_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_runtime_shell_dry_run_consumer_packet_v1(packet)
    validation = validate_project_chat_runtime_shell_dry_run_consumer_packet_v1(candidate)
    summary_text = (
        f"consumer={_safe_str(candidate.get('consumer_mode'))} | "
        f"status={_safe_str(validation.get('consumer_status'))} | "
        f"blocked={validation['blocked']} | "
        f"shell={_safe_str(validation.get('shell_validation', {}).get('shell_state'))} | "
        f"assembly={_safe_str(validation.get('assembly_validation', {}).get('assembly_mode'))} | "
        f"final={_safe_str(validation.get('final_answer_validation', {}).get('final_answer_status'))}"
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "consumer_id": validation["consumer_id"],
        "summary_text": summary_text,
        "consumer_mode": validation["consumer_mode"],
        "consumer_decision": validation["consumer_decision"],
        "consumer_status": validation["consumer_status"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "runtime_shell_readiness_labels": validation["runtime_shell_readiness_labels"],
        "assembly_validation": validation["assembly_validation"],
        "shell_validation": validation["shell_validation"],
        "dry_run_validation": validation["dry_run_validation"],
        "consumption_plan_validation": validation["consumption_plan_validation"],
        "final_answer_validation": validation["final_answer_validation"],
        "safe_metadata": validation["safe_metadata"],
    }



def to_project_chat_runtime_shell_dry_run_consumer_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def _lighten_example_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    example = _json_safe(packet)
    for field in (
        "assembly_validation",
        "shell_validation",
        "dry_run_validation",
        "consumption_plan_validation",
        "final_answer_validation",
    ):
        example.pop(field, None)
    return example



def build_initial_project_chat_runtime_shell_dry_run_consumer_examples_v1() -> list[dict[str, Any]]:
    base_assembly = build_project_chat_assembly_packet_v1(
        {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "user_request_metadata": {
                "request_id": "request-001",
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
                "approval_refs": ["approval-001"],
                "user_visible_status": "evidence grounded answer",
                "operator_visible_summary": "evidence grounded; metadata only",
            },
            "retrieval_need_metadata": {
                "retrieval_need_class": "project_metadata_retrieval_needed",
                "retrieval_status": "metadata only",
            },
            "evidence_packet_metadata": [
                {
                    "project_id": "project-001",
                    "owner_user_scope": "owner-user",
                    "tenant_account_scope": "tenant-a",
                    "source_scope": "project_metadata_only",
                    "retrieval_request_id": "request-001",
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
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
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
    )
    blocked_assembly = build_project_chat_assembly_packet_v1(
        {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "user_request_metadata": {
                "request_id": "request-002",
                "message_ref": "message-002",
                "message_status": "metadata only",
                "user_visible_status": "raw prompt should never be shown",
                "operator_visible_summary": "blocked message intake metadata only",
            },
            "project_context_metadata": {
                "project_state_refs": ["project-state-002"],
                "memory_state_refs": ["memory-state-002"],
                "continuity_state_refs": ["continuity-state-002"],
                "gap_analysis_refs": ["gap-002"],
                "approval_refs": ["approval-002"],
                "user_visible_status": "evidence grounded answer",
                "operator_visible_summary": "evidence grounded; metadata only",
            },
            "retrieval_need_metadata": {
                "retrieval_need_class": "project_metadata_retrieval_needed",
                "retrieval_status": "metadata only",
            },
            "evidence_packet_metadata": [
                {
                    "project_id": "project-001",
                    "owner_user_scope": "owner-user",
                    "tenant_account_scope": "tenant-a",
                    "source_scope": "project_metadata_only",
                    "retrieval_request_id": "request-002",
                    "retrieval_need_class": "project_metadata_retrieval_needed",
                    "retrieval_adapter": "ProjectStateMetadataAdapter",
                    "source_type": "project_metadata",
                    "source_ref": "project-metadata-002",
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
                "project_id": "project-001",
                "owner_user_scope": "owner-user",
                "tenant_account_scope": "tenant-a",
                "source_scope": "project_metadata_only",
                "user_intent_class": "project-chat",
                "answer_mode": "evidence_grounded_answer",
                "allowed_answer_scope": "approved_evidence_packet",
                "answer_status": "plan_valid_metadata_only",
                "evidence_packet_refs": ["evidence-001"],
                "user_visible_status": "evidence grounded answer",
                "operator_visible_summary": "evidence grounded; metadata only",
            },
            "blocked_state": {
                "blocked": True,
                "blocked_labels": ["runtime_wiring_boundary"],
                "blocked_reasons": ["runtime_wiring_boundary"],
                "live_chat_output_blocked": True,
                "answer_delivery_blocked": True,
                "retrieval_execution_blocked": True,
                "persistence_blocked": True,
                "provider_model_search_tool_authority_blocked": True,
                "private_leak_blocked": True,
                "public_ready_claim_blocked": True,
                "cognitive_engine_authority_blocked": True,
            },
            "final_answer_packet_metadata": {
                "controlled_answer_text_proposal": "Boundary-only metadata response.",
            },
        }
    )
    return [
        _lighten_example_packet(build_project_chat_runtime_shell_dry_run_consumer_packet_v1({"assembly_packet_metadata": base_assembly})),
        _lighten_example_packet(build_project_chat_runtime_shell_dry_run_consumer_packet_v1({"assembly_packet_metadata": blocked_assembly})),
    ]
