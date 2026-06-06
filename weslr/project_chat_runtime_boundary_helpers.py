"""Metadata-only helpers for the WESLR project-chat runtime boundary V1.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed.
It consumes project-chat runtime shell dry-run consumer metadata only and
produces runtime-boundary metadata only.

It does not perform file I/O, network I/O, shell execution, runtime wiring,
retrieval execution, model/provider/search/tool calls, external actions,
persistence, UI/Nova behavior, live chat output, answer delivery, or final
answer generation.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from weslr.project_chat_runtime_shell_dry_run_consumer import (
    CONSUMER_DECISIONS_V1 as SHELL_CONSUMER_DECISIONS_V1,
    CONSUMER_MODES_V1 as SHELL_CONSUMER_MODES_V1,
    CONSUMER_STATUSES_V1 as SHELL_CONSUMER_STATUSES_V1,
    RUNTIME_SHELL_READINESS_LABELS_V1 as SHELL_READINESS_LABELS_V1,
    build_project_chat_runtime_shell_dry_run_consumer_packet_v1,
    validate_project_chat_runtime_shell_dry_run_consumer_packet_v1,
)

HELPER_TYPE_V1 = "weslr_project_chat_runtime_boundary_helpers_v1"
SCHEMA_VERSION_V1 = "project_chat_runtime_boundary_v1"

BOUNDARY_MODES_V1 = (
    "metadata_only_runtime_boundary",
    "blocked_runtime_boundary",
)

BOUNDARY_STATUSES_V1 = (
    "boundary_valid_metadata_only",
    "owner_approval_required",
    "operator_review_required",
    "blocked",
    "invalid",
)

BOUNDARY_DECISIONS_V1 = (
    "preserve_metadata_only",
    "block_before_runtime",
    "require_owner_approval_before_runtime_wiring",
    "require_operator_review_before_runtime_wiring",
    "refuse_runtime_wiring",
)

BOUNDARY_READINESS_LABELS_V1 = (
    "consumer_packet_preserved",
    "runtime_shell_readiness_labels_preserved",
    "blocked_state_preserved",
    "missing_evidence_state_preserved",
    "conflict_state_preserved",
    "approval_state_preserved",
    "provenance_chain_preserved",
    "boundary_metadata_only",
    "future_owner_approval_required",
    "runtime_wiring_blocked",
    "live_chat_output_blocked",
    "answer_delivery_blocked",
    "retrieval_execution_blocked",
    "model_provider_search_tool_calls_blocked",
    "persistence_blocked",
    "weslr_io_blocked",
    "ui_nova_behavior_blocked",
    "public_user_facing_behavior_blocked",
    "private_leak_blocked",
    "public_ready_claim_blocked",
    "cognitive_engine_authority_blocked",
)

BOUNDARY_POLICY_MAY_CONSUME_V1 = (
    "dry_run_consumer_packet_metadata",
    "runtime_shell_readiness_labels",
    "blocked_state",
    "missing_evidence_state",
    "conflict_state",
    "approval_state",
    "provenance_chain",
)

BOUNDARY_POLICY_MAY_PASS_FORWARD_V1 = (
    "dry_run_consumer_packet_metadata",
    "runtime_shell_readiness_labels",
    "blocked_state",
    "missing_evidence_state",
    "conflict_state",
    "approval_state",
    "provenance_chain",
    "user_visible_status",
    "operator_visible_summary",
)

BOUNDARY_POLICY_MUST_BLOCK_V1 = (
    "live_chat_output",
    "answer_delivery",
    "retrieval_execution",
    "provider_calls",
    "model_calls",
    "search_calls",
    "tool_calls",
    "persistence",
    "weslr_io",
    "ui_nova_behavior",
    "public_user_facing_behavior",
    "private_raw_secret_hidden_system_leakage",
    "public_ready_claims",
    "cognitive_engine_runtime_authority",
)

BOUNDARY_POLICY_MUST_REFUSE_V1 = (
    "runtime_wiring",
    "live_chat_output",
    "answer_delivery",
    "retrieval_execution",
    "provider_model_search_tool_calls",
    "persistence",
    "weslr_io",
    "ui_nova_behavior",
    "public_user_facing_behavior",
    "private_raw_secret_hidden_system_leakage",
    "public_ready_claims",
    "cognitive_engine_runtime_authority",
)

DENIED_AUTHORITY_FIELDS_V1 = (
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
    "chat_responder",
    "chat_ui",
    "dialogue",
    "main.py",
    ".weslr",
    "internal scoring",
    "SearXNG proves",
    "the web confirms",
    "truth authority",
    "mutation authority",
    "memory authority",
    "tool execution authority",
    "storage authority",
    "autonomous self-improvement",
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


def allowed_project_chat_runtime_boundary_modes_v1() -> tuple[str, ...]:
    return BOUNDARY_MODES_V1



def allowed_project_chat_runtime_boundary_statuses_v1() -> tuple[str, ...]:
    return BOUNDARY_STATUSES_V1



def allowed_project_chat_runtime_boundary_decisions_v1() -> tuple[str, ...]:
    return BOUNDARY_DECISIONS_V1



def allowed_project_chat_runtime_boundary_readiness_labels_v1() -> tuple[str, ...]:
    return BOUNDARY_READINESS_LABELS_V1



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



def _readiness_label_set_v1() -> set[str]:
    return set((*SHELL_READINESS_LABELS_V1, *BOUNDARY_READINESS_LABELS_V1))



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



def _find_forbidden_hits_v1(*values: Any) -> list[str]:
    hits: list[str] = []
    for value in values:
        text = _safe_str(value).lower()
        for phrase in FORBIDDEN_VISIBLE_PHRASES_V1:
            phrase_lower = _safe_str(phrase).lower()
            if phrase_lower in text:
                hits.append(phrase_lower)
    return _dedupe(hits)



def _base_assembly_metadata() -> dict[str, Any]:
    return {
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



def _base_consumer_packet() -> dict[str, Any]:
    return build_project_chat_runtime_shell_dry_run_consumer_packet_v1({"assembly_packet_metadata": _base_assembly_metadata()})



def _boundary_policy() -> dict[str, Any]:
    return {
        "may_consume": list(BOUNDARY_POLICY_MAY_CONSUME_V1),
        "may_pass_forward": list(BOUNDARY_POLICY_MAY_PASS_FORWARD_V1),
        "must_block": list(BOUNDARY_POLICY_MUST_BLOCK_V1),
        "must_refuse": list(BOUNDARY_POLICY_MUST_REFUSE_V1),
    }



def _boundary_requirements() -> dict[str, Any]:
    return {
        "future_owner_approval_required": True,
        "runtime_wiring_blocked": True,
        "live_chat_output_blocked": True,
        "answer_delivery_blocked": True,
        "retrieval_execution_blocked": True,
        "model_provider_search_tool_calls_blocked": True,
        "persistence_blocked": True,
        "weslr_io_blocked": True,
        "ui_nova_behavior_blocked": True,
        "public_user_facing_behavior_blocked": True,
        "private_leak_blocked": True,
        "public_ready_claim_blocked": True,
        "cognitive_engine_authority_blocked": True,
    }



def _boundary_blocked_state() -> dict[str, Any]:
    return {
        "blocked": True,
        "blocked_labels": [
            "live_chat_output_blocked",
            "answer_delivery_blocked",
            "retrieval_execution_blocked",
            "provider_model_search_tool_authority_blocked",
            "model_provider_search_tool_calls_blocked",
            "persistence_blocked",
            "weslr_io_blocked",
            "ui_nova_behavior_blocked",
            "public_user_facing_behavior_blocked",
            "private_leak_blocked",
            "private_raw_secret_hidden_system_leakage_blocked",
            "public_ready_claim_blocked",
            "cognitive_engine_authority_blocked",
        ],
        "blocked_reasons": [
            "live chat output blocked",
            "answer delivery blocked",
            "retrieval execution blocked",
            "model/provider/search/tool calls blocked",
            "persistence blocked",
            "weslr io blocked",
            "ui/nova behavior blocked",
            "public user-facing behavior blocked",
            "private/raw/secret/hidden-system leakage blocked",
            "public-ready claims blocked",
            "cognitive engine authority blocked",
        ],
        "blocked_authority": "runtime_boundary_metadata_only",
        "live_chat_output_blocked": True,
        "answer_delivery_blocked": True,
        "retrieval_execution_blocked": True,
        "provider_model_search_tool_authority_blocked": True,
        "model_provider_search_tool_calls_blocked": True,
        "persistence_blocked": True,
        "weslr_io_blocked": True,
        "ui_nova_behavior_blocked": True,
        "public_user_facing_behavior_blocked": True,
        "private_leak_blocked": True,
        "private_raw_secret_hidden_system_leakage_blocked": True,
        "public_ready_claim_blocked": True,
        "cognitive_engine_authority_blocked": True,
    }



def _boundary_missing_evidence_state(consumer_validation: Mapping[str, Any]) -> dict[str, Any]:
    state = _json_safe(consumer_validation.get("missing_evidence_state") or {})
    if isinstance(state, Mapping):
        state = dict(state)
    else:
        state = {}
    state.setdefault("boundary_missing_evidence_state", True)
    return state



def _boundary_conflict_state(consumer_validation: Mapping[str, Any]) -> dict[str, Any]:
    state = _json_safe(consumer_validation.get("conflict_state") or {})
    if isinstance(state, Mapping):
        state = dict(state)
    else:
        state = {}
    state.setdefault("boundary_conflict_state", True)
    return state



def _boundary_approval_state(consumer_validation: Mapping[str, Any]) -> dict[str, Any]:
    state = _json_safe(consumer_validation.get("approval_state") or {})
    if isinstance(state, Mapping):
        state = dict(state)
    else:
        state = {}
    state.setdefault("future_owner_approval_required", True)
    return state



def _boundary_provenance_chain(consumer_validation: Mapping[str, Any]) -> dict[str, Any]:
    chain = _json_safe(consumer_validation.get("provenance_chain") or {})
    if isinstance(chain, Mapping):
        chain = dict(chain)
    else:
        chain = {}
    chain.setdefault("boundary_provenance_state", "metadata_only")
    return chain



def _boundary_user_visible_status(boundary_status: str) -> str:
    if boundary_status == "blocked":
        return "This runtime boundary is blocked."
    if boundary_status == "operator_review_required":
        return "This runtime boundary needs operator review before any future wiring."
    return "Runtime boundary metadata only; owner approval required."



def _boundary_operator_visible_summary(boundary_status: str, boundary_decision: str, consumer_mode: str) -> str:
    return f"{boundary_decision} | {boundary_status} | consumer={consumer_mode} | metadata only"



def _default_boundary_mode(consumer_blocked: bool, boundary_status: str) -> str:
    if consumer_blocked or boundary_status == "blocked":
        return "blocked_runtime_boundary"
    return "metadata_only_runtime_boundary"



def _default_boundary_status(consumer_validation: Mapping[str, Any], requested_status: str = "") -> str:
    if requested_status in BOUNDARY_STATUSES_V1:
        return requested_status
    if consumer_validation.get("blocked"):
        return "blocked"
    approval_state = _as_mapping(consumer_validation.get("approval_state"))
    if _safe_bool(approval_state.get("operator_review_required")):
        return "operator_review_required"
    return "owner_approval_required"



def _default_boundary_decision(boundary_status: str, requested_decision: str = "") -> str:
    if requested_decision in BOUNDARY_DECISIONS_V1:
        return requested_decision
    if boundary_status == "blocked":
        return "block_before_runtime"
    if boundary_status == "operator_review_required":
        return "require_operator_review_before_runtime_wiring"
    if boundary_status == "boundary_valid_metadata_only":
        return "preserve_metadata_only"
    return "require_owner_approval_before_runtime_wiring"



def _boundary_readiness_labels(consumer_validation: Mapping[str, Any]) -> list[str]:
    consumer_labels = _normalize_refs(consumer_validation.get("runtime_shell_readiness_labels"))
    boundary_labels = list(BOUNDARY_READINESS_LABELS_V1)
    return _dedupe([*consumer_labels, *boundary_labels])



def build_project_chat_runtime_boundary_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    source = (
        data.get("dry_run_consumer_packet_metadata")
        or data.get("runtime_shell_dry_run_consumer_packet_metadata")
        or data.get("consumer_packet_metadata")
        or data.get("consumer_packet")
        or data.get("dry_run_consumer_packet")
        or data.get("runtime_shell_dry_run_consumer_packet")
        or data.get("consumer")
    )

    if source is None:
        consumer_packet = _base_consumer_packet()
    else:
        consumer_packet = validate_project_chat_runtime_shell_dry_run_consumer_packet_v1(source)["consumer_packet"]

    consumer_validation = validate_project_chat_runtime_shell_dry_run_consumer_packet_v1(consumer_packet)
    consumer_blocked = _safe_bool(consumer_validation.get("blocked"))

    boundary_status = _default_boundary_status(consumer_validation, _safe_str(data.get("boundary_status")))
    boundary_decision = _default_boundary_decision(boundary_status, _safe_str(data.get("boundary_decision")))
    boundary_mode = _safe_str(data.get("boundary_mode")) or _default_boundary_mode(consumer_blocked, boundary_status)

    runtime_shell_readiness_labels = _normalize_refs(
        data.get("runtime_shell_readiness_labels") or consumer_validation.get("runtime_shell_readiness_labels")
    )
    runtime_boundary_readiness_labels = _normalize_refs(
        data.get("runtime_boundary_readiness_labels") or _boundary_readiness_labels(consumer_validation)
    )

    blocked_state = _boundary_blocked_state()
    missing_evidence_state = _boundary_missing_evidence_state(consumer_validation)
    conflict_state = _boundary_conflict_state(consumer_validation)
    approval_state = _boundary_approval_state(consumer_validation)
    provenance_chain = _boundary_provenance_chain(consumer_validation)

    denied_authority = _normalize_denied_authority(data.get("denied_authority") or consumer_validation.get("denied_authority") or {})

    user_visible_status = _safe_str(data.get("user_visible_status")) or _boundary_user_visible_status(boundary_status)
    operator_visible_summary = _safe_str(data.get("operator_visible_summary")) or _boundary_operator_visible_summary(
        boundary_status,
        boundary_decision,
        _safe_str(consumer_validation.get("consumer_mode")),
    )

    safe_metadata = {
        "boundary_summary": _boundary_operator_visible_summary(
            boundary_status,
            boundary_decision,
            _safe_str(consumer_validation.get("consumer_mode")),
        ),
        "boundary_mode": boundary_mode,
        "boundary_status": boundary_status,
        "boundary_decision": boundary_decision,
        "consumer_mode": _safe_str(consumer_validation.get("consumer_mode")),
        "consumer_status": _safe_str(consumer_validation.get("consumer_status")),
        "future_owner_approval_required": True,
        "runtime_wiring_blocked": True,
        "live_chat_output_blocked": True,
        "answer_delivery_blocked": True,
        "retrieval_execution_blocked": True,
        "model_provider_search_tool_calls_blocked": True,
        "persistence_blocked": True,
        "weslr_io_blocked": True,
        "ui_nova_behavior_blocked": True,
        "public_user_facing_behavior_blocked": True,
        "private_leak_blocked": True,
        "public_ready_claim_blocked": True,
        "cognitive_engine_authority_blocked": True,
    }

    boundary_packet = {
        "schema_version": _safe_str(data.get("schema_version")) or SCHEMA_VERSION_V1,
        "boundary_id": _safe_str(data.get("boundary_id")),
        "boundary_mode": boundary_mode,
        "boundary_status": boundary_status,
        "boundary_decision": boundary_decision,
        "dry_run_consumer_packet_metadata": consumer_packet,
        "consumer_validation": consumer_validation,
        "runtime_shell_readiness_labels": runtime_shell_readiness_labels,
        "runtime_boundary_readiness_labels": runtime_boundary_readiness_labels,
        "boundary_policy": _json_safe(data.get("boundary_policy")) if isinstance(data.get("boundary_policy"), Mapping) else _boundary_policy(),
        "boundary_requirements": _boundary_requirements(),
        "blocked_state": blocked_state,
        "missing_evidence_state": missing_evidence_state,
        "conflict_state": conflict_state,
        "approval_state": approval_state,
        "provenance_chain": provenance_chain,
        "denied_authority": denied_authority,
        "user_visible_status": user_visible_status,
        "operator_visible_summary": operator_visible_summary,
        "safe_metadata": safe_metadata,
        "helper_type": HELPER_TYPE_V1,
    }

    if not boundary_packet["boundary_id"]:
        digest_source = {k: v for k, v in boundary_packet.items() if k not in {"boundary_id", "consumer_validation"}}
        boundary_packet["boundary_id"] = f"project-chat-runtime-boundary-{_stable_digest(digest_source)[:16]}"

    return boundary_packet



def validate_project_chat_runtime_boundary_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_runtime_boundary_packet_v1(packet)
    blocked_labels: list[str] = []

    if candidate.get("schema_version") != SCHEMA_VERSION_V1:
        blocked_labels.append("unknown_schema_version")
    if _safe_str(candidate.get("boundary_id")) == "":
        blocked_labels.append("missing_boundary_id")
    if candidate.get("boundary_mode") not in BOUNDARY_MODES_V1:
        blocked_labels.append("unknown_boundary_mode")
    if candidate.get("boundary_status") not in BOUNDARY_STATUSES_V1:
        blocked_labels.append("unknown_boundary_status")
    if candidate.get("boundary_decision") not in BOUNDARY_DECISIONS_V1:
        blocked_labels.append("unknown_boundary_decision")

    for field in (
        "dry_run_consumer_packet_metadata",
        "consumer_validation",
        "boundary_policy",
        "boundary_requirements",
        "blocked_state",
        "missing_evidence_state",
        "conflict_state",
        "approval_state",
        "provenance_chain",
        "denied_authority",
        "safe_metadata",
    ):
        if not isinstance(candidate.get(field), Mapping):
            blocked_labels.append(f"missing_{field}")

    if not isinstance(candidate.get("runtime_shell_readiness_labels"), list) or not candidate["runtime_shell_readiness_labels"]:
        blocked_labels.append("missing_runtime_shell_readiness_labels")
    if not isinstance(candidate.get("runtime_boundary_readiness_labels"), list) or not candidate["runtime_boundary_readiness_labels"]:
        blocked_labels.append("missing_runtime_boundary_readiness_labels")

    consumer_validation = _as_mapping(candidate.get("consumer_validation"))
    consumer_packet = _as_mapping(candidate.get("dry_run_consumer_packet_metadata"))
    if not consumer_packet:
        blocked_labels.append("missing_dry_run_consumer_packet_metadata")
    if not consumer_validation:
        blocked_labels.append("missing_consumer_validation")

    boundary_policy = _as_mapping(candidate.get("boundary_policy"))
    for key, required_values in (
        ("may_consume", BOUNDARY_POLICY_MAY_CONSUME_V1),
        ("may_pass_forward", BOUNDARY_POLICY_MAY_PASS_FORWARD_V1),
        ("must_block", BOUNDARY_POLICY_MUST_BLOCK_V1),
        ("must_refuse", BOUNDARY_POLICY_MUST_REFUSE_V1),
    ):
        items = _normalize_refs(boundary_policy.get(key))
        if not items:
            blocked_labels.append(f"missing_boundary_policy_{key}")
            continue
        for required in required_values:
            if required not in items:
                blocked_labels.append(f"boundary_policy_{key}_missing_{_slugify_v1(required)}")

    boundary_requirements = _as_mapping(candidate.get("boundary_requirements"))
    for key in (
        "future_owner_approval_required",
        "runtime_wiring_blocked",
        "live_chat_output_blocked",
        "answer_delivery_blocked",
        "retrieval_execution_blocked",
        "model_provider_search_tool_calls_blocked",
        "persistence_blocked",
        "weslr_io_blocked",
        "ui_nova_behavior_blocked",
        "public_user_facing_behavior_blocked",
        "private_leak_blocked",
        "public_ready_claim_blocked",
        "cognitive_engine_authority_blocked",
    ):
        if boundary_requirements.get(key) is not True:
            blocked_labels.append(f"missing_boundary_requirement_{key}")

    blocked_state = _as_mapping(candidate.get("blocked_state"))
    for key in (
        "blocked",
        "live_chat_output_blocked",
        "answer_delivery_blocked",
        "retrieval_execution_blocked",
        "provider_model_search_tool_authority_blocked",
        "model_provider_search_tool_calls_blocked",
        "persistence_blocked",
        "weslr_io_blocked",
        "ui_nova_behavior_blocked",
        "public_user_facing_behavior_blocked",
        "private_leak_blocked",
        "private_raw_secret_hidden_system_leakage_blocked",
        "public_ready_claim_blocked",
        "cognitive_engine_authority_blocked",
    ):
        if blocked_state.get(key) is not True:
            blocked_labels.append(f"missing_{key}")

    if _safe_bool(boundary_requirements.get("future_owner_approval_required")) is not True:
        blocked_labels.append("future_owner_approval_required_must_be_true")

    if _safe_bool(_as_mapping(candidate.get("approval_state")).get("future_owner_approval_required")) is not True:
        blocked_labels.append("approval_state_missing_future_owner_approval_required")

    if not _safe_str(candidate.get("user_visible_status")):
        blocked_labels.append("missing_user_visible_status")
    if not _safe_str(candidate.get("operator_visible_summary")):
        blocked_labels.append("missing_operator_visible_summary")

    for phrase in _find_forbidden_hits_v1(
        candidate.get("user_visible_status"),
        candidate.get("operator_visible_summary"),
        _as_mapping(candidate.get("safe_metadata")).get("boundary_summary"),
    ):
        blocked_labels.append(f"forbidden_phrase_{_slugify_v1(phrase)}")

    for field, value in candidate.get("denied_authority", {}).items():
        if field not in DENIED_AUTHORITY_FIELDS_V1:
            blocked_labels.append(f"unknown_denied_authority_field_{_slugify_v1(field)}")
        elif _safe_bool(value):
            blocked_labels.append(f"denied_authority_must_remain_false_{field}")

    allowed_readiness_labels = _readiness_label_set_v1()
    for label in _normalize_refs(candidate.get("runtime_shell_readiness_labels")):
        if label not in allowed_readiness_labels:
            blocked_labels.append(f"unknown_runtime_shell_readiness_label_{_slugify_v1(label)}")
    for label in _normalize_refs(candidate.get("runtime_boundary_readiness_labels")):
        if label not in allowed_readiness_labels:
            blocked_labels.append(f"unknown_runtime_boundary_readiness_label_{_slugify_v1(label)}")

    classification = _classify_boundary_validation(candidate, blocked_labels)
    blocked = bool(blocked_labels)

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "boundary_packet": candidate,
        "future_owner_approval_required": True,
        "runtime_wiring_blocked": True,
        "boundary_id": candidate["boundary_id"],
        "boundary_mode": candidate["boundary_mode"],
        "boundary_status": "blocked" if blocked else candidate["boundary_status"],
        "boundary_decision": candidate["boundary_decision"],
        "classification": classification,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "dry_run_consumer_packet_metadata": candidate["dry_run_consumer_packet_metadata"],
        "consumer_validation": consumer_validation,
        "runtime_shell_readiness_labels": candidate["runtime_shell_readiness_labels"],
        "runtime_boundary_readiness_labels": candidate["runtime_boundary_readiness_labels"],
        "boundary_policy": candidate["boundary_policy"],
        "boundary_requirements": candidate["boundary_requirements"],
        "blocked_state": candidate["blocked_state"],
        "missing_evidence_state": candidate["missing_evidence_state"],
        "conflict_state": candidate["conflict_state"],
        "approval_state": candidate["approval_state"],
        "provenance_chain": candidate["provenance_chain"],
        "denied_authority": candidate["denied_authority"],
        "user_visible_status": candidate["user_visible_status"],
        "operator_visible_summary": candidate["operator_visible_summary"],
        "safe_metadata": candidate["safe_metadata"],
    }



def _classify_boundary_validation(candidate: Mapping[str, Any], blocked_labels: list[str]) -> str:
    if blocked_labels:
        return "blocked"
    if candidate.get("boundary_status") == "blocked":
        return "blocked"
    if candidate.get("boundary_status") == "operator_review_required":
        return "operator_review_required"
    if candidate.get("boundary_status") == "boundary_valid_metadata_only":
        return "boundary_valid_metadata_only"
    return "owner_approval_required"



def classify_project_chat_runtime_boundary_decision_v1(packet: Any) -> dict[str, Any]:
    validation = validate_project_chat_runtime_boundary_packet_v1(packet)
    candidate = validation["boundary_packet"]
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "classification": validation["classification"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "boundary_id": candidate["boundary_id"],
        "boundary_mode": candidate["boundary_mode"],
        "boundary_status": validation["boundary_status"],
        "boundary_decision": candidate["boundary_decision"],
        "future_owner_approval_required": True,
        "runtime_wiring_blocked": True,
        "user_visible_status": validation["user_visible_status"],
        "operator_visible_summary": validation["operator_visible_summary"],
    }



def summarize_project_chat_runtime_boundary_packet_v1(packet: Any) -> dict[str, Any]:
    candidate = build_project_chat_runtime_boundary_packet_v1(packet)
    validation = validate_project_chat_runtime_boundary_packet_v1(candidate)
    summary_text = (
        f"boundary={_safe_str(candidate.get('boundary_decision'))} | "
        f"status={_safe_str(validation.get('boundary_status'))} | "
        f"consumer={_safe_str(_as_mapping(candidate.get('dry_run_consumer_packet_metadata')).get('consumer_mode'))} | "
        f"blocked={validation['blocked']}"
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "boundary_id": validation["boundary_id"],
        "summary_text": summary_text,
        "boundary_mode": validation["boundary_mode"],
        "boundary_status": validation["boundary_status"],
        "boundary_decision": validation["boundary_decision"],
        "classification": validation["classification"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "future_owner_approval_required": True,
        "runtime_wiring_blocked": True,
        "runtime_shell_readiness_labels": validation["runtime_shell_readiness_labels"],
        "runtime_boundary_readiness_labels": validation["runtime_boundary_readiness_labels"],
        "safe_metadata": validation["safe_metadata"],
    }



def to_project_chat_runtime_boundary_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def _lighten_example_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    example = _json_safe(packet)
    if isinstance(example, Mapping):
        example = dict(example)
        example.pop("consumer_validation", None)
    return example



def build_initial_project_chat_runtime_boundary_examples_v1() -> list[dict[str, Any]]:
    valid_example = build_project_chat_runtime_boundary_packet_v1({})
    blocked_example = build_project_chat_runtime_boundary_packet_v1(
        {
            "boundary_status": "blocked",
            "boundary_decision": "block_before_runtime",
            "user_visible_status": "This runtime boundary is blocked.",
            "operator_visible_summary": "Blocked boundary metadata only.",
        }
    )
    return [
        _lighten_example_packet(valid_example),
        _lighten_example_packet(blocked_example),
    ]


__all__ = [
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "BOUNDARY_MODES_V1",
    "BOUNDARY_STATUSES_V1",
    "BOUNDARY_DECISIONS_V1",
    "BOUNDARY_READINESS_LABELS_V1",
    "DENIED_AUTHORITY_FIELDS_V1",
    "allowed_project_chat_runtime_boundary_modes_v1",
    "allowed_project_chat_runtime_boundary_statuses_v1",
    "allowed_project_chat_runtime_boundary_decisions_v1",
    "allowed_project_chat_runtime_boundary_readiness_labels_v1",
    "build_project_chat_runtime_boundary_packet_v1",
    "validate_project_chat_runtime_boundary_packet_v1",
    "classify_project_chat_runtime_boundary_decision_v1",
    "summarize_project_chat_runtime_boundary_packet_v1",
    "to_project_chat_runtime_boundary_json_safe_v1",
    "build_initial_project_chat_runtime_boundary_examples_v1",
]
