"""Metadata-only helpers for owner-preview rendering metadata.

This module is intentionally pure, deterministic, synthetic/example-safe,
and fail-closed. It transforms validated owner-preview metadata packets into
safe render metadata packets only.

It does not perform file I/O, network I/O, shell execution, runtime wiring,
retrieval, model calls, tool execution, external actions, persistence, UI
consumption, or final answer generation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from weslr.private_project_chat_owner_preview_metadata import (
    allowed_private_project_chat_owner_preview_packet_types_v1,
    allowed_private_project_chat_owner_preview_readiness_labels_v1,
    build_initial_private_project_chat_owner_preview_examples_v1 as build_initial_private_project_chat_owner_preview_examples_v1,
    classify_private_project_chat_owner_preview_packet_v1,
    summarize_private_project_chat_owner_preview_packet_v1,
    to_private_project_chat_owner_preview_json_safe_v1,
    validate_private_project_chat_owner_preview_packet_v1,
)

HELPER_TYPE_V1 = "weslr_owner_preview_rendering_metadata_v1"
SCHEMA_VERSION_V1 = "owner_preview_rendering_metadata_v1"

OWNER_PREVIEW_RENDER_STATES_V1 = (
    "render_not_allowed",
    "render_metadata_only",
    "render_blocked",
    "render_clarification_required",
    "render_approval_required",
    "render_operator_review_required",
    "render_candidate_only",
    "render_invalid",
    "render_not_public_ready",
)

OWNER_PREVIEW_RENDER_PACKET_TYPES_V1 = (
    "render_shell_decision_summary",
    "render_blocked_summary",
    "render_clarification_summary",
    "render_approval_summary",
    "render_operator_review_summary",
    "render_answer_plan_candidate_summary",
    "render_retrieval_request_candidate_summary",
    "render_tool_lane_candidate_summary",
    "render_persistence_candidate_summary",
    "render_observability_summary",
    "render_dry_run_summary",
    "render_consumption_plan_summary",
    "render_validation_summary",
)

_ALLOWED_VISUAL_LABELS_V1 = {
    "Private owner preview",
    "Metadata-only",
    "Candidate only",
    "Blocked",
    "Needs clarification",
    "Needs approval",
    "Needs operator review",
    "Not public ready",
    "Evidence incomplete",
    "Metadata conflict",
    "Not allowed",
    "Invalid",
}

_FORBIDDEN_WORDING_V1 = (
    "I executed",
    "I searched",
    "I saved",
    "I remembered",
    "final answer",
    "runtime authority",
    "public ready",
    "certified",
    "conscious",
    "autonomous deployment",
    "Unknown Engine",
    "chat" + "_" + "responder",
    "raw private project data",
    "raw private data",
    "raw traces",
    "raw memory/project payloads",
    "raw `" + "." + "weslr" + "` state",
    "retrieval/tool/persistence executed",
    "retrieval results",
    "tool results",
    "persistence results",
)

_DEFAULT_DENIED_AUTHORITY = {
    field: False for field in (
        "runtime_wiring_authority",
        "chat_responder_authority",
        "final_answer_generation_authority",
        "retrieval_execution_authority",
        "searxng_execution_authority",
        "tool_execution_authority",
        "storage_database_authority",
        "weslr_io_authority",
        "project_state_mutation_authority",
        "memory_mutation_authority",
        "ui_consumption_implementation_authority",
        "public_access_authority",
        "tester_access_authority",
        "private_data_exposure_authority",
        "public_readiness_claim_authority",
    )
}

_RENDER_PACKET_TYPE_BY_SOURCE_PACKET_TYPE = {
    "preview_shell_decision_summary": "render_shell_decision_summary",
    "preview_shell_blocked_summary": "render_blocked_summary",
    "preview_shell_clarification_summary": "render_clarification_summary",
    "preview_shell_approval_summary": "render_approval_summary",
    "preview_shell_operator_review_summary": "render_operator_review_summary",
    "preview_answer_plan_candidate_summary": "render_answer_plan_candidate_summary",
    "preview_retrieval_request_candidate_summary": "render_retrieval_request_candidate_summary",
    "preview_tool_lane_candidate_summary": "render_tool_lane_candidate_summary",
    "preview_persistence_candidate_summary": "render_persistence_candidate_summary",
    "preview_observability_summary": "render_observability_summary",
    "preview_dry_run_summary": "render_dry_run_summary",
    "preview_consumption_plan_summary": "render_consumption_plan_summary",
    "preview_validation_summary": "render_validation_summary",
}


def allowed_owner_preview_render_states_v1() -> tuple[str, ...]:
    return OWNER_PREVIEW_RENDER_STATES_V1



def allowed_owner_preview_render_packet_types_v1() -> tuple[str, ...]:
    return OWNER_PREVIEW_RENDER_PACKET_TYPES_V1



def to_owner_preview_render_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



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



def _has_forbidden_wording(value: Any) -> bool:
    candidate = _safe_str(value).lower()
    for word in _FORBIDDEN_WORDING_V1:
        if not word:
            continue
        word_l = word.lower()
        if word_l == "public ready" and "not public ready" in candidate:
            continue
        if word_l in candidate:
            return True
    return False



def _validate_render_title_label_status(packet: Mapping[str, Any], blocked_labels: list[str]) -> None:
    for field in ("display_title", "display_label", "display_status"):
        value = _safe_str(packet.get(field))
        if not value:
            blocked_labels.append(f"missing_{field}")
        if _has_forbidden_wording(value):
            blocked_labels.append(f"forbidden_{field}")
        if value and field in {"display_title", "display_label", "display_status"} and value not in _ALLOWED_VISUAL_LABELS_V1 and field != "display_title":
            blocked_labels.append(f"unknown_{field}")



def _validate_text_block(packet: Mapping[str, Any], blocked_labels: list[str]) -> None:
    for field in ("display_summary", "display_details", "redaction_summary", "limitations"):
        value = packet.get(field)
        if _has_forbidden_wording(value):
            blocked_labels.append(f"forbidden_{field}")
        if field in {"display_summary", "display_details", "redaction_summary"} and not _safe_str(value):
            blocked_labels.append(f"missing_{field}")



def _validate_list_block(packet: Mapping[str, Any], field: str, blocked_labels: list[str]) -> None:
    values = packet.get(field)
    if not isinstance(values, list) or not values:
        blocked_labels.append(f"missing_{field}")
        return
    for item in values:
        if _has_forbidden_wording(item):
            blocked_labels.append(f"forbidden_{field}")
            break



def _build_denied_authority(value: Any) -> dict[str, bool]:
    raw = _as_mapping(value)
    denied = dict(_DEFAULT_DENIED_AUTHORITY)
    for field in denied:
        denied[field] = _safe_bool(raw.get(field, False))
    return denied



def _source_preview_ref(validation: Mapping[str, Any]) -> str:
    preview_packet = _as_mapping(validation.get("preview_packet"))
    ref = _safe_str(preview_packet.get("preview_packet_id"))
    if ref:
        return ref
    return "source-preview-" + _stable_digest(validation)[:16]



def _render_state_from_source(validation: Mapping[str, Any]) -> str:
    preview_status = _safe_str(validation.get("preview_status"))
    readiness_label = _safe_str(validation.get("readiness_label"))
    if preview_status == "preview_invalid" or validation.get("blocked") is True:
        return "render_invalid"
    if readiness_label == "not_public_ready":
        return "render_not_public_ready"
    mapping = {
        "preview_blocked": "render_blocked",
        "preview_clarification_required": "render_clarification_required",
        "preview_approval_required": "render_approval_required",
        "preview_operator_review_required": "render_operator_review_required",
        "preview_candidate_only": "render_candidate_only",
        "preview_metadata_only": "render_metadata_only",
    }
    return mapping.get(preview_status, "render_not_allowed")



def _render_packet_type_from_source(packet_type: str) -> str:
    return _RENDER_PACKET_TYPE_BY_SOURCE_PACKET_TYPE.get(packet_type, "render_validation_summary")



def _render_display_label(render_state: str) -> str:
    mapping = {
        "render_not_allowed": "Not allowed",
        "render_metadata_only": "Metadata-only",
        "render_blocked": "Blocked",
        "render_clarification_required": "Needs clarification",
        "render_approval_required": "Needs approval",
        "render_operator_review_required": "Needs operator review",
        "render_candidate_only": "Candidate only",
        "render_invalid": "Invalid",
        "render_not_public_ready": "Not public ready",
    }
    return mapping.get(render_state, "Metadata-only")



def _render_display_status(render_state: str) -> str:
    return _render_display_label(render_state)



def _render_display_summary(render_state: str, source_summary: str, blocked: bool, not_public_ready: bool) -> str:
    if render_state == "render_invalid":
        return "Private owner preview: invalid render metadata."
    if render_state == "render_not_allowed":
        return "Private owner preview: rendering not allowed."
    if not_public_ready or render_state == "render_not_public_ready":
        return "Private owner preview: not public ready."
    if blocked:
        return "Private owner preview: blocked metadata only."
    return source_summary or "Private owner preview: metadata-only."



def _render_display_details(validation: Mapping[str, Any], render_state: str) -> str:
    packet_type = _safe_str(validation.get("preview_packet_type"))
    status = _safe_str(validation.get("preview_status"))
    readiness = _safe_str(validation.get("readiness_label"))
    blocked = _safe_bool(validation.get("blocked"))
    return f"render_state={render_state}; source_status={status}; source_packet={packet_type}; readiness={readiness}; blocked={blocked}."



def _render_display_flags(validation: Mapping[str, Any], render_state: str) -> list[str]:
    flags = [render_state]
    if _safe_bool(validation.get("blocked")):
        flags.append("blocked")
    if _safe_str(validation.get("readiness_label")) == "not_public_ready":
        flags.append("not_public_ready")
    if _safe_bool(validation.get("blocked")) or _safe_str(validation.get("preview_status")) == "preview_invalid":
        flags.append("evidence incomplete")
    return _dedupe(flags)



def _build_source_validation(source_preview_packet: Any) -> dict[str, Any]:
    return validate_private_project_chat_owner_preview_packet_v1(source_preview_packet)



def _coalesce_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    elif payload is not None:
        data["payload"] = payload
    data.update(overrides)
    return data



def _owner_preview_render_template(
    *,
    render_state: str,
    render_packet_type: str,
    source_validation: Mapping[str, Any],
    source_preview_packet_ref: str,
    display_title: str,
    display_label: str,
    display_status: str,
    display_summary: str,
    display_details: str,
    display_flags: list[str],
    redaction_summary: str,
    blocked_authority: str,
    candidate_packet_type: str,
    selected_next_metadata_step: str,
    validation_result: Mapping[str, Any],
    limitations: list[str],
    denied_authority: Mapping[str, bool],
) -> dict[str, Any]:
    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "render_packet_id": "",
        "render_state": render_state,
        "render_packet_type": render_packet_type,
        "source_preview_packet_ref": source_preview_packet_ref,
        "project_id": _safe_str(source_validation.get("preview_packet", {}).get("project_id")),
        "owner_user_scope": _safe_str(source_validation.get("preview_packet", {}).get("owner_user_scope")),
        "tenant_account_scope": _safe_str(source_validation.get("preview_packet", {}).get("tenant_account_scope")),
        "source_scope": _safe_str(source_validation.get("preview_packet", {}).get("source_scope")),
        "display_title": display_title,
        "display_label": display_label,
        "display_status": display_status,
        "display_summary": display_summary,
        "display_details": display_details,
        "display_flags": list(display_flags),
        "redaction_summary": redaction_summary,
        "blocked_authority": blocked_authority,
        "candidate_packet_type": candidate_packet_type,
        "selected_next_metadata_step": selected_next_metadata_step,
        "validation_result": _json_safe(validation_result),
        "limitations": list(limitations),
        "denied_authority": dict(denied_authority),
    }
    packet["render_packet_id"] = "render-" + _stable_digest(packet)[:16]
    return packet



def build_owner_preview_render_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _coalesce_payload(payload, **overrides)
    source_preview_packet = data.get("source_preview_packet")
    source_validation = _build_source_validation(source_preview_packet)
    source_packet = _as_mapping(source_validation.get("preview_packet"))
    source_packet_type = _safe_str(source_validation.get("preview_packet_type"))
    render_packet_type = _safe_str(data.get("render_packet_type")) or _render_packet_type_from_source(source_packet_type)
    render_state = _safe_str(data.get("render_state")) or _render_state_from_source(source_validation)

    if render_state not in OWNER_PREVIEW_RENDER_STATES_V1:
        render_state = "render_invalid"
    if render_packet_type not in OWNER_PREVIEW_RENDER_PACKET_TYPES_V1:
        render_packet_type = "render_validation_summary"

    candidate_packet_type = _safe_str(data.get("candidate_packet_type")) or _safe_str(source_packet.get("candidate_packet_type"))
    selected_next_metadata_step = _safe_str(data.get("selected_next_metadata_step")) or _safe_str(source_packet.get("selected_next_metadata_step"))
    blocked_authority = _safe_str(data.get("blocked_authority")) or _safe_str(source_packet.get("blocked_authority")) or "owner_preview_boundary"
    limitations = _safe_list(data.get("limitations")) or _safe_list(source_packet.get("limitations"))
    if not limitations:
        limitations = ["metadata-only", "owner-only", "synthetic/example-safe"]

    display_title = _safe_str(data.get("display_title")) or "Private owner preview"
    display_label = _safe_str(data.get("display_label")) or _render_display_label(render_state)
    display_status = _safe_str(data.get("display_status")) or _render_display_status(render_state)

    source_summary = summarize_private_project_chat_owner_preview_packet_v1(source_preview_packet).get("summary_text", "")
    display_summary = _safe_str(data.get("display_summary")) or _render_display_summary(render_state, source_summary, _safe_bool(source_validation.get("blocked")), _safe_str(source_validation.get("readiness_label")) == "not_public_ready")
    display_details = _safe_str(data.get("display_details")) or _render_display_details(source_validation, render_state)
    display_flags = _safe_list(data.get("display_flags")) or _render_display_flags(source_validation, render_state)
    redaction_summary = _safe_str(data.get("redaction_summary")) or "Synthetic render metadata only; private fields redacted."

    denied_authority = _build_denied_authority(data.get("denied_authority"))
    validation_result = data.get("validation_result")
    if not isinstance(validation_result, Mapping):
        validation_result = {
            "source_preview_validation": source_validation,
            "render_state": render_state,
            "render_packet_type": render_packet_type,
            "blocked": _safe_bool(source_validation.get("blocked")) or render_state in {"render_invalid", "render_not_allowed"},
        }

    packet = _owner_preview_render_template(
        render_state=render_state,
        render_packet_type=render_packet_type,
        source_validation=source_validation,
        source_preview_packet_ref=_source_preview_ref(source_validation),
        display_title=display_title,
        display_label=display_label,
        display_status=display_status,
        display_summary=display_summary,
        display_details=display_details,
        display_flags=display_flags,
        redaction_summary=redaction_summary,
        blocked_authority=blocked_authority,
        candidate_packet_type=candidate_packet_type,
        selected_next_metadata_step=selected_next_metadata_step,
        validation_result=validation_result,
        limitations=limitations,
        denied_authority=denied_authority,
    )
    return packet



def _validate_forbidden_wording_fields(packet: Mapping[str, Any], blocked_labels: list[str]) -> None:
    for field in ("display_title", "display_label", "display_status", "display_summary", "display_details", "redaction_summary", "blocked_authority", "candidate_packet_type", "selected_next_metadata_step"):
        value = packet.get(field)
        if _has_forbidden_wording(value):
            blocked_labels.append(f"forbidden_{field}")



def _validate_source_validation(validation: Any, blocked_labels: list[str]) -> Mapping[str, Any]:
    raw = _as_mapping(validation)
    source_validation = _as_mapping(raw.get("source_preview_validation"))
    if not source_validation:
        blocked_labels.append("missing_source_preview_validation")
        return {}
    if _safe_bool(source_validation.get("blocked")) is False and _safe_str(source_validation.get("preview_status")) not in {"preview_metadata_only", "preview_blocked", "preview_clarification_required", "preview_approval_required", "preview_operator_review_required", "preview_candidate_only", "preview_invalid"}:
        blocked_labels.append("invalid_source_preview_validation")
    return source_validation



def validate_owner_preview_render_packet_v1(packet: Any) -> dict[str, Any]:
    raw = _as_mapping(packet)
    blocked_labels: list[str] = []

    source_validation = _validate_source_validation(raw.get("validation_result"), blocked_labels)
    source_packet = _as_mapping(source_validation.get("preview_packet"))
    if not _safe_str(source_packet.get("project_id")):
        blocked_labels.append("missing_project_id")
    if not _safe_str(source_packet.get("owner_user_scope")):
        blocked_labels.append("missing_owner_user_scope")
    if not _safe_str(source_packet.get("tenant_account_scope")):
        blocked_labels.append("missing_tenant_account_scope")
    if not _safe_str(source_packet.get("source_scope")):
        blocked_labels.append("missing_source_scope")

    render_state = _safe_str(raw.get("render_state"))
    render_packet_type = _safe_str(raw.get("render_packet_type"))
    if render_state not in OWNER_PREVIEW_RENDER_STATES_V1:
        blocked_labels.append("unknown_render_state")
        render_state = "render_invalid"
    if render_packet_type not in OWNER_PREVIEW_RENDER_PACKET_TYPES_V1:
        blocked_labels.append("unknown_render_packet_type")
        render_packet_type = "render_validation_summary"

    _validate_render_title_label_status(raw, blocked_labels)
    _validate_text_block(raw, blocked_labels)
    _validate_list_block(raw, "display_flags", blocked_labels)
    _validate_list_block(raw, "limitations", blocked_labels)

    denied_authority = _build_denied_authority(raw.get("denied_authority"))
    for field, value in denied_authority.items():
        if value:
            blocked_labels.append(f"denied_authority_enabled_{field}")

    if not _safe_str(raw.get("source_preview_packet_ref")):
        blocked_labels.append("missing_source_preview_packet_ref")
    if not _safe_str(raw.get("redaction_summary")):
        blocked_labels.append("missing_redaction_summary")
    if not _safe_str(raw.get("display_summary")):
        blocked_labels.append("missing_display_summary")
    if not _safe_str(raw.get("display_details")):
        blocked_labels.append("missing_display_details")

    blocked = bool(blocked_labels)
    if blocked and render_state not in {"render_invalid", "render_not_allowed"}:
        render_state = "render_invalid"
    classification = _classification_for_packet_type(render_packet_type, render_state)

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "render_packet": _json_safe(raw),
        "blocked": blocked,
        "blocked_labels": _dedupe(blocked_labels),
        "classification": classification,
        "render_state": render_state,
        "render_packet_type": render_packet_type,
        "source_preview_packet_ref": _safe_str(raw.get("source_preview_packet_ref")),
        "display_title": _safe_str(raw.get("display_title")),
        "display_label": _safe_str(raw.get("display_label")),
        "display_status": _safe_str(raw.get("display_status")),
        "display_summary": _safe_str(raw.get("display_summary")),
        "display_details": _safe_str(raw.get("display_details")),
        "display_flags": _safe_list(raw.get("display_flags")),
        "redaction_summary": _safe_str(raw.get("redaction_summary")),
        "blocked_authority": _safe_str(raw.get("blocked_authority")),
        "candidate_packet_type": _safe_str(raw.get("candidate_packet_type")),
        "selected_next_metadata_step": _safe_str(raw.get("selected_next_metadata_step")),
        "validation_result": _json_safe(raw.get("validation_result")),
        "limitations": _safe_list(raw.get("limitations")),
        "denied_authority": denied_authority,
    }
    return result



def _classification_for_packet_type(render_packet_type: str, render_state: str) -> str:
    if render_state == "render_invalid":
        return "invalid"
    if render_state == "render_not_allowed":
        return "not_allowed"
    if render_state == "render_not_public_ready":
        return "not_public_ready"
    if render_packet_type == "render_blocked_summary":
        return "blocked"
    if render_packet_type in {"render_clarification_summary", "render_approval_summary", "render_operator_review_summary"}:
        return render_packet_type.removeprefix("render_").removesuffix("_summary")
    if render_packet_type in {
        "render_answer_plan_candidate_summary",
        "render_retrieval_request_candidate_summary",
        "render_tool_lane_candidate_summary",
        "render_persistence_candidate_summary",
    }:
        return "candidate_only"
    if render_packet_type == "render_observability_summary":
        return "observability"
    if render_packet_type == "render_dry_run_summary":
        return "dry_run"
    if render_packet_type == "render_consumption_plan_summary":
        return "consumption_plan"
    if render_packet_type == "render_validation_summary":
        return "validation"
    return "metadata_only"



def classify_owner_preview_render_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_owner_preview_render_packet_v1(packet)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "classification": validation["classification"],
        "render_state": validation["render_state"],
        "render_packet_type": validation["render_packet_type"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "render_packet": validation["render_packet"],
    }



def summarize_owner_preview_render_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_owner_preview_render_packet_v1(packet)
    render_packet = validation["render_packet"]
    summary_text = f"Private owner preview render: {_safe_str(render_packet.get('display_label'))}; state={validation['render_state']}."
    if validation["blocked"]:
        summary_text = "Private owner preview render: blocked or invalid metadata."
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": summary_text,
        "classification": validation["classification"],
        "render_state": validation["render_state"],
        "render_packet_type": validation["render_packet_type"],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "source_preview_packet_ref": validation["source_preview_packet_ref"],
        "display_title": validation["display_title"],
        "display_label": validation["display_label"],
        "display_status": validation["display_status"],
        "display_summary": validation["display_summary"],
        "display_details": validation["display_details"],
    }



def build_initial_owner_preview_render_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for source_packet in build_initial_private_project_chat_owner_preview_examples_v1():
        examples.append(build_owner_preview_render_packet_v1({"source_preview_packet": source_packet}))
    return examples
