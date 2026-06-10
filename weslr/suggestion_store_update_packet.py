"""WESLR Suggestion Store Update Packet V1 metadata helpers.

Deterministic, metadata-only update-intent scaffolding for proposed internal
suggestion-store changes only. This module does not persist, mutate memory or
projects, promote behavior packs, make public claims, wire runtime behavior, or
authorize execution.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from weslr.cognitive_research_protocol import (
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    summarize_cognitive_research_run_v1,
    to_cognitive_research_json_safe_v1,
    validate_cognitive_research_run_v1,
)

HELPER_TYPE_V1 = "weslr_suggestion_store_update_packet_v1"
SCHEMA_VERSION_V1 = "suggestion_store_update_packet_v1"
ENGINE_NAME_V1 = "suggestion_store_update_packet"
ENGINE_FAMILY_V1 = "candidate_store_update"

_ALLOWED_RESEARCH_MODES_V1 = (
    "internal_exploration",
    "synthetic_test",
    "calibration_replay",
    "frontier_mapping",
)
_ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = (
    "not_public_claim",
    "internal_candidate_only",
    "public_export_blocked",
)
_ALLOWED_CANDIDATE_STATUSES_V1 = (
    "new",
    "watch",
    "probe",
    "pressure_test",
    "calibrate",
    "archive",
    "blocked",
    "promote_to_next_internal_step",
    "unknown",
)
_ALLOWED_ACTION_TYPES_V1 = (
    "add_candidate",
    "update_status",
    "link_probe",
    "link_pressure_test",
    "link_calibration_record",
    "link_perspicuity_scorecard",
    "archive_candidate",
    "block_candidate",
    "recommend_next_internal_step",
    "no_op",
    "unknown",
)
_STATUS_UPDATING_ACTION_TYPES_V1 = {
    "add_candidate",
    "update_status",
    "archive_candidate",
    "block_candidate",
    "recommend_next_internal_step",
}
_LINK_ACTION_REQUIREMENTS_V1 = {
    "link_probe": "linked_probe_ref",
    "link_pressure_test": "linked_pressure_test_ref",
    "link_calibration_record": "linked_calibration_record_ref",
    "link_perspicuity_scorecard": "linked_perspicuity_scorecard_ref",
}

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw private text",
    "raw private data",
    "raw private project data",
    "private content",
    "hidden prompt",
    "hidden system prompt",
    "system prompt",
    "developer prompt",
    "secret",
    "password",
    "token=",
    "credential",
    "final answer",
    "final-answer",
    "answer draft",
    "reply output",
    "provider output",
    "model output",
    "tool execution",
    "tool authority",
    "provider authority",
    "runtime authority",
    "llm authority",
    "public discovery",
    "proof",
    "truth",
    "breakthrough",
    "official intelligence",
    "agi",
    "sentience",
    "consciousness",
    "runtime",
    "provider",
    "tool",
    "persistence",
    "write to store",
    "commit to store",
    "storage write",
    "database write",
    "memory mutation",
    "project mutation",
    "behavior change",
    "behavior-pack promotion",
    "behavior pack",
    "promotion",
    ".weslr",
    "live ingestion",
    "network",
    "github rss",
    "lab notebook",
    "executable code-as-action",
)

_FORBIDDEN_KEY_FRAGMENTS_V1 = (
    "raw_private",
    "raw_response",
    "raw_artifact",
    "private_content",
    "hidden_prompt",
    "hidden_system_prompt",
    "system_prompt",
    "developer_prompt",
    "secret",
    "password",
    "token",
    "provider_output",
    "model_output",
    "search_output",
    ".weslr",
    "answer_draft",
    "final_answer",
)

_ALLOWED_RAW_KEY_NAMES_V1 = {
    "raw_content_included",
    "raw_content_ref_only",
    "raw_generated_content_included",
    "raw_generated_content_ref_only",
}


def _compact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.replace("\r", " ").replace("\n", " ").split())
    return _compact_text(str(value))


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    if overrides:
        data.update(overrides)
    return data


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(list(value), key=_compact_text)
    if isinstance(value, Mapping):
        return list(value.values())
    return [value]


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"1", "true", "yes", "y", "on"}:
            return True
        if raw in {"0", "false", "no", "n", "off"}:
            return False
    return bool(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda item: str(item)):
            key_text = str(key)
            key_lc = key_text.lower()
            if (
                not key_lc.endswith("_authority")
                and (any(fragment in key_lc for fragment in _FORBIDDEN_KEY_FRAGMENTS_V1) or (key_lc.startswith("raw_") and key_lc not in _ALLOWED_RAW_KEY_NAMES_V1))
            ):
                continue
            out[key_text] = _json_safe(value[key])
        return out
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_compact_text)]
    if isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in _FORBIDDEN_TEXT_MARKERS_V1):
            return "[redacted]"
        return value
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _compact_text(value)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_choice(value: Any, allowed: tuple[str, ...], default: str) -> str:
    raw = _compact_text(value).lower()
    if not raw:
        return default
    return raw if raw in allowed else default


def _normalize_candidate_status(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_CANDIDATE_STATUSES_V1, "unknown")


def _normalize_action_type(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_ACTION_TYPES_V1, "unknown")


def _contains_forbidden_text(*values: Any) -> bool:
    text = "\n".join(_compact_text(value).lower() for value in values)
    return any(marker in text for marker in _FORBIDDEN_TEXT_MARKERS_V1)


def _default_boundary_status() -> dict[str, Any]:
    denied = build_default_cognitive_research_denied_authority_v1()
    boundary = {
        "status": "metadata_only",
        **deepcopy(denied),
        "boundary_notes": "metadata-only suggestion-store update intent; no runtime, persistence, or public-export authority",
    }
    return boundary


def _default_safe_metadata() -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_provider_calls": True,
        "no_tool_execution": True,
        "no_persistence": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_behavior_pack_promotion": True,
        "no_public_claims": True,
        "no_final_answer": True,
        "no_weslr_io": True,
        "no_network": True,
        "no_subprocess": True,
        "no_autonomous_self_modification": True,
        "suggestion_store_is_not_storage": True,
        "operator_review_required": True,
    }


def build_suggestion_store_candidate_ref_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    candidate_summary = _compact_text(data.get("candidate_summary") or data.get("summary") or "Suggestion-store candidate reference.")
    source_engine_name = _compact_text(data.get("source_engine_name") or "unknown_engine").lower() or "unknown_engine"
    source_run_id = _compact_text(data.get("source_run_id")) or f"source-run-{_stable_digest({'engine': source_engine_name, 'summary': candidate_summary})[:12]}"
    candidate_id = _compact_text(data.get("candidate_id")) or f"candidate-{_stable_digest({'engine': source_engine_name, 'run': source_run_id, 'summary': candidate_summary})[:12]}"
    return _json_safe(
        {
            "candidate_id": candidate_id,
            "source_engine_name": source_engine_name,
            "source_run_id": source_run_id,
            "candidate_type": _compact_text(data.get("candidate_type") or "unknown") or "unknown",
            "candidate_summary": candidate_summary,
            "candidate_status": _normalize_candidate_status(data.get("candidate_status") or "new"),
            "candidate_scope": _compact_text(data.get("candidate_scope") or "metadata-only scope") or "metadata-only scope",
            "public_claim_status": _normalize_choice(data.get("public_claim_status") or "internal_candidate_only", _ALLOWED_PUBLIC_CLAIM_STATUSES_V1, "internal_candidate_only"),
            "uncertainty_factors": _ensure_list(data.get("uncertainty_factors")) or ["candidate remains provisional"],
            "invalidation_signals": _ensure_list(data.get("invalidation_signals")) or ["not yet invalidated"],
        }
    )


def build_suggestion_store_update_action_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    action_type = _normalize_action_type(data.get("action_type") or "recommend_next_internal_step")
    candidate_id = _compact_text(data.get("candidate_id")) or f"candidate-{_stable_digest({'action_type': action_type, 'reason': data.get('action_reason')})[:12]}"
    action_reason = _compact_text(data.get("action_reason") or "Suggestion-store update proposal for internal review.")
    previous_status = _normalize_candidate_status(data.get("previous_status") or "unknown")
    next_status = _normalize_candidate_status(data.get("next_status") or "unknown")
    if action_type == "add_candidate" and next_status == "unknown":
        next_status = "new"
    if action_type == "archive_candidate":
        next_status = "archive"
    if action_type == "block_candidate":
        next_status = "blocked"
    if action_type == "recommend_next_internal_step":
        next_status = "promote_to_next_internal_step"
    operator_review_required = _safe_bool(data.get("operator_review_required", action_type != "no_op"), action_type != "no_op")
    return _json_safe(
        {
            "update_action_id": _compact_text(data.get("update_action_id"))
            or f"update-{_stable_digest({'candidate_id': candidate_id, 'action_type': action_type, 'reason': action_reason})[:12]}",
            "candidate_id": candidate_id,
            "action_type": action_type,
            "action_reason": action_reason,
            "previous_status": previous_status,
            "next_status": next_status,
            "linked_probe_ref": _compact_text(data.get("linked_probe_ref")),
            "linked_pressure_test_ref": _compact_text(data.get("linked_pressure_test_ref")),
            "linked_calibration_record_ref": _compact_text(data.get("linked_calibration_record_ref")),
            "linked_perspicuity_scorecard_ref": _compact_text(data.get("linked_perspicuity_scorecard_ref")),
            "operator_review_required": operator_review_required,
            "storage_write_authorized": _safe_bool(data.get("storage_write_authorized", False)),
            "behavior_change_authorized": _safe_bool(data.get("behavior_change_authorized", False)),
            "public_claim_authorized": _safe_bool(data.get("public_claim_authorized", False)),
        }
    )


def _default_candidate_ref_from_data(data: Mapping[str, Any]) -> dict[str, Any]:
    return build_suggestion_store_candidate_ref_v1(
        {
            "candidate_id": data.get("candidate_id") or data.get("primary_candidate_id") or data.get("linked_candidate_id"),
            "source_engine_name": data.get("source_engine_name") or "unknown_engine",
            "source_run_id": data.get("source_run_id") or data.get("run_id") or "source-run-unknown",
            "candidate_type": data.get("candidate_type") or "unknown",
            "candidate_summary": data.get("candidate_summary") or data.get("input_summary") or "Suggestion-store candidate reference.",
            "candidate_status": data.get("candidate_status") or "new",
            "candidate_scope": data.get("candidate_scope") or "metadata-only scope",
            "public_claim_status": data.get("public_claim_status") or "internal_candidate_only",
            "uncertainty_factors": data.get("uncertainty_factors") or ["candidate remains provisional"],
            "invalidation_signals": data.get("invalidation_signals") or ["not yet invalidated"],
        }
    )


def _default_update_action_from_candidate(candidate: Mapping[str, Any], data: Mapping[str, Any]) -> dict[str, Any]:
    candidate_id = _compact_text(candidate.get("candidate_id")) or _compact_text(data.get("candidate_id")) or "candidate-unknown"
    candidate_status = _normalize_candidate_status(candidate.get("candidate_status"))
    action_type = _normalize_action_type(data.get("action_type") or data.get("recommended_action") or "recommend_next_internal_step")
    if action_type == "unknown":
        action_type = "recommend_next_internal_step"
    if action_type == "add_candidate":
        previous_status = "unknown"
        next_status = "new"
    elif action_type == "archive_candidate":
        previous_status = candidate_status
        next_status = "archive"
    elif action_type == "block_candidate":
        previous_status = candidate_status
        next_status = "blocked"
    elif action_type == "recommend_next_internal_step":
        previous_status = candidate_status
        next_status = "promote_to_next_internal_step"
    else:
        previous_status = candidate_status
        next_status = candidate_status if candidate_status != "unknown" else "watch"
    linked_fields = {
        "link_probe": "linked_probe_ref",
        "link_pressure_test": "linked_pressure_test_ref",
        "link_calibration_record": "linked_calibration_record_ref",
        "link_perspicuity_scorecard": "linked_perspicuity_scorecard_ref",
    }
    linked_ref_key = linked_fields.get(action_type)
    linked_refs = {key: "" for key in linked_fields.values()}
    if linked_ref_key:
        linked_refs[linked_ref_key] = _compact_text(data.get(linked_ref_key) or data.get("linked_ref") or data.get("scorecard_ref") or data.get("calibration_record_ref") or data.get("probe_ref"))
    return build_suggestion_store_update_action_v1(
        {
            "candidate_id": candidate_id,
            "action_type": action_type,
            "action_reason": data.get("action_reason") or f"Propose internal update for {candidate_id}.",
            "previous_status": previous_status,
            "next_status": next_status,
            "linked_probe_ref": linked_refs["linked_probe_ref"],
            "linked_pressure_test_ref": linked_refs["linked_pressure_test_ref"],
            "linked_calibration_record_ref": linked_refs["linked_calibration_record_ref"],
            "linked_perspicuity_scorecard_ref": linked_refs["linked_perspicuity_scorecard_ref"],
            "operator_review_required": data.get("operator_review_required", action_type != "no_op"),
            "storage_write_authorized": False,
            "behavior_change_authorized": False,
            "public_claim_authorized": False,
        }
    )


def build_suggestion_store_update_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    candidate_payloads = _ensure_list(data.get("candidate_refs"))
    if not candidate_payloads:
        candidate_payloads = [_default_candidate_ref_from_data(data)]
    candidate_refs = [build_suggestion_store_candidate_ref_v1(candidate) for candidate in candidate_payloads]
    primary_candidate = candidate_refs[0]

    action_payloads = _ensure_list(data.get("update_actions"))
    if not action_payloads:
        action_payloads = [_default_update_action_from_candidate(primary_candidate, data)]
    update_actions = [build_suggestion_store_update_action_v1(action) for action in action_payloads]

    suggestion_store_updates = _ensure_list(data.get("suggestion_store_updates")) or deepcopy(update_actions)
    research_mode = _normalize_choice(data.get("research_mode") or "internal_exploration", _ALLOWED_RESEARCH_MODES_V1, "internal_exploration")
    packet_id = _compact_text(data.get("packet_id")) or f"packet-{_stable_digest({'candidate_ids': [candidate['candidate_id'] for candidate in candidate_refs], 'action_ids': [action['update_action_id'] for action in update_actions]})[:12]}"
    source_run_id = _compact_text(data.get("source_run_id")) or _compact_text(primary_candidate.get("source_run_id")) or f"source-run-{_stable_digest({'packet_id': packet_id})[:12]}"
    source_artifact_ref = _compact_text(data.get("input_artifact_ref") or f"artifact:suggestion-store-update:{packet_id}")
    input_summary = _compact_text(data.get("input_summary") or f"Suggestion-store update packet for {len(candidate_refs)} candidate(s).")
    operator_review_required = _safe_bool(data.get("operator_review_required", any(action.get("operator_review_required", False) for action in update_actions)), any(action.get("operator_review_required", False) for action in update_actions))
    storage_write_authorized = _safe_bool(data.get("storage_write_authorized", False))
    memory_mutation_authorized = _safe_bool(data.get("memory_mutation_authorized", False))
    project_mutation_authorized = _safe_bool(data.get("project_mutation_authorized", False))
    behavior_change_authorized = _safe_bool(data.get("behavior_change_authorized", False))
    behavior_promotion_authorized = _safe_bool(data.get("behavior_promotion_authorized", False))
    public_claim_authorized = _safe_bool(data.get("public_claim_authorized", False))
    public_claim_status = _normalize_choice(data.get("public_claim_status") or "internal_candidate_only", _ALLOWED_PUBLIC_CLAIM_STATUSES_V1, "internal_candidate_only")
    public_gap_card_status = _normalize_choice(data.get("public_gap_card_status") or "public_export_blocked", _ALLOWED_PUBLIC_CLAIM_STATUSES_V1, "public_export_blocked")
    denied_authority = data.get("denied_authority") if isinstance(data.get("denied_authority"), Mapping) else build_default_cognitive_research_denied_authority_v1()
    safe_metadata = data.get("safe_metadata") if isinstance(data.get("safe_metadata"), Mapping) else _default_safe_metadata()

    packet = build_cognitive_research_run_v1(
        {
            "schema_version": SCHEMA_VERSION_V1,
            "run_id": packet_id,
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": research_mode,
            "source_scope": "metadata_only",
            "input_artifact_ref": source_artifact_ref,
            "input_artifact_type": _compact_text(data.get("input_artifact_type") or "suggestion-store-update"),
            "input_summary": input_summary,
            "source_signal": {
                "signal_origin": "metadata_only",
                "source_ref": source_run_id,
                "summary": input_summary,
                "signal_type": "suggestion_store_update_intent",
                "trust_level": "bounded",
                "poison_risk": "low",
                "injection_risk": "low",
                "raw_content_included": False,
                "raw_content_ref_only": True,
                "normalization_required": True,
            },
            "hypotheses": _ensure_list(data.get("hypotheses")) or [f"Update intent for {len(candidate_refs)} candidate(s)."],
            "predictions": _ensure_list(data.get("predictions")) or ["Suggestion-store entries may be updated internally after review."],
            "verification_steps": _ensure_list(data.get("verification_steps")) or ["check candidate refs", "check update actions", "check review flags"],
            "human_verification_steps": _ensure_list(data.get("human_verification_steps")) or ["operator review"],
            "machine_verification_steps": _ensure_list(data.get("machine_verification_steps")) or ["py_compile", "pytest", "release_gate", "release_check"],
            "falsification_probes": _ensure_list(data.get("falsification_probes")) or ["missing reference", "unsafe flag"],
            "probes": _ensure_list(data.get("probes")) or ["candidate status check"],
            "generated_source_signals": _ensure_list(data.get("generated_source_signals")),
            "rule_pressure_tests": _ensure_list(data.get("rule_pressure_tests")),
            "suggestion_store_updates": suggestion_store_updates,
            "calibration_record": data.get("calibration_record") if isinstance(data.get("calibration_record"), Mapping) else {},
            "compressed_lesson": _compact_text(data.get("compressed_lesson") or "Suggestion-store updates remain proposals, not persistence."),
            "next_experiments": _ensure_list(data.get("next_experiments")) or ["operator review"],
            "public_claim_status": public_claim_status,
            "public_gap_card_status": public_gap_card_status,
            "boundary_status": data.get("boundary_status") if isinstance(data.get("boundary_status"), Mapping) else _default_boundary_status(),
            "denied_authority": denied_authority,
            "safe_metadata": safe_metadata,
            "llm_helper_role": _compact_text(data.get("llm_helper_role") or "candidate_generator_only") or "candidate_generator_only",
            "domain": _compact_text(data.get("domain") or "suggestion-store update") or "suggestion-store update",
            "domain_subtype": _compact_text(data.get("domain_subtype") or "candidate store update") or "candidate store update",
            "system_level": _compact_text(data.get("system_level") or "component") or "component",
            "artifact_scale": _compact_text(data.get("artifact_scale") or "bounded artifact") or "bounded artifact",
        }
    )

    packet.update(
        {
            "packet_id": packet_id,
            "source_run_id": source_run_id,
            "candidate_refs": candidate_refs,
            "update_actions": update_actions,
            "suggestion_store_updates": deepcopy(update_actions) if suggestion_store_updates == update_actions else suggestion_store_updates,
            "operator_review_required": operator_review_required,
            "storage_write_authorized": storage_write_authorized,
            "memory_mutation_authorized": memory_mutation_authorized,
            "project_mutation_authorized": project_mutation_authorized,
            "behavior_change_authorized": behavior_change_authorized,
            "behavior_promotion_authorized": behavior_promotion_authorized,
            "public_claim_authorized": public_claim_authorized,
            "boundary_status": _json_safe(data.get("boundary_status") if isinstance(data.get("boundary_status"), Mapping) else _default_boundary_status()),
            "denied_authority": _json_safe(denied_authority),
        }
    )
    if isinstance(packet.get("source_signal"), Mapping):
        packet["source_signal"] = {
            **packet["source_signal"],
            "raw_content_included": False,
            "raw_content_ref_only": True,
        }
    return _json_safe(packet)


def _validate_candidate_ref(candidate: Any) -> list[str]:
    blocked: list[str] = []
    item = candidate if isinstance(candidate, Mapping) else {}
    candidate_id = _compact_text(item.get("candidate_id"))
    source_run_id = _compact_text(item.get("source_run_id"))
    candidate_summary = _compact_text(item.get("candidate_summary"))
    candidate_status_raw = _compact_text(item.get("candidate_status")).lower()
    public_claim_status_raw = _compact_text(item.get("public_claim_status")).lower()
    if not candidate_id:
        blocked.append("missing_candidate_id")
    if not source_run_id:
        blocked.append("missing_source_run_id")
    if not candidate_summary:
        blocked.append("missing_candidate_summary")
    if not candidate_status_raw:
        blocked.append("missing_candidate_status")
    elif candidate_status_raw not in _ALLOWED_CANDIDATE_STATUSES_V1:
        blocked.append("invalid_candidate_status")
    if not _ensure_list(item.get("uncertainty_factors")):
        blocked.append("missing_uncertainty_factors")
    if not _ensure_list(item.get("invalidation_signals")):
        blocked.append("missing_invalidation_signals")
    if not public_claim_status_raw or public_claim_status_raw not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        blocked.append("candidate_marked_public_or_export_safe")
    if _contains_forbidden_text(item.get("candidate_summary"), item.get("candidate_scope"), item.get("candidate_type")):
        blocked.append("forbidden_candidate_text")
    return blocked


def _validate_update_action(action: Any) -> list[str]:
    blocked: list[str] = []
    item = action if isinstance(action, Mapping) else {}
    update_action_id = _compact_text(item.get("update_action_id"))
    candidate_id = _compact_text(item.get("candidate_id"))
    action_type_raw = _compact_text(item.get("action_type")).lower()
    action_reason = _compact_text(item.get("action_reason"))
    previous_status_raw = _compact_text(item.get("previous_status")).lower()
    next_status_raw = _compact_text(item.get("next_status")).lower()
    if not update_action_id:
        blocked.append("missing_update_action_id")
    if not candidate_id:
        blocked.append("missing_candidate_id")
    if not action_type_raw:
        blocked.append("invalid_action_type")
    elif action_type_raw not in _ALLOWED_ACTION_TYPES_V1:
        blocked.append("invalid_action_type")
    if not action_reason:
        blocked.append("missing_action_reason")
    if action_type_raw in _STATUS_UPDATING_ACTION_TYPES_V1:
        if not previous_status_raw or not next_status_raw:
            blocked.append("status_update_without_previous_or_next_status")
        if next_status_raw not in _ALLOWED_CANDIDATE_STATUSES_V1:
            blocked.append("invalid_next_status")
    if action_type_raw in _LINK_ACTION_REQUIREMENTS_V1:
        linked_field = _LINK_ACTION_REQUIREMENTS_V1[action_type_raw]
        if not _compact_text(item.get(linked_field)):
            blocked.append(f"missing_{linked_field}")
    if not isinstance(item.get("operator_review_required"), bool):
        blocked.append("invalid_operator_review_required")
    if _safe_bool(item.get("storage_write_authorized", False)):
        blocked.append("storage_write_authorized")
    if _safe_bool(item.get("behavior_change_authorized", False)):
        blocked.append("behavior_change_authorized")
    if _safe_bool(item.get("public_claim_authorized", False)):
        blocked.append("public_claim_authorized")
    if _contains_forbidden_text(item.get("action_reason"), item.get("linked_probe_ref"), item.get("linked_pressure_test_ref"), item.get("linked_calibration_record_ref"), item.get("linked_perspicuity_scorecard_ref")):
        blocked.append("forbidden_update_action_text")
    if any(fragment in action_reason.lower() for fragment in ("persist", "persistence", "commit", "write to store", "database", "save", "mutate store", "storage write")):
        blocked.append("update_packet_treated_as_persistence_or_write")
    return blocked


def validate_suggestion_store_update_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    protocol_validation = validate_cognitive_research_run_v1(packet)
    blocked_labels = list(protocol_validation["blocked_labels"])

    if not _compact_text(raw.get("packet_id")):
        blocked_labels.append("missing_packet_id")
    if _compact_text(raw.get("engine_name")) != ENGINE_NAME_V1:
        blocked_labels.append("invalid_engine_name")
    if _compact_text(raw.get("engine_family")) != ENGINE_FAMILY_V1:
        blocked_labels.append("invalid_engine_family")
    if _compact_text(raw.get("source_run_id")) == "":
        blocked_labels.append("missing_source_run_id")
    if _compact_text(raw.get("research_mode")).lower() not in _ALLOWED_RESEARCH_MODES_V1:
        blocked_labels.append("invalid_research_mode")
    public_claim_status_raw = _compact_text(raw.get("public_claim_status")).lower()
    public_gap_card_status_raw = _compact_text(raw.get("public_gap_card_status")).lower()
    if not public_claim_status_raw or public_claim_status_raw not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        blocked_labels.append("invalid_public_claim_status")
    if not public_gap_card_status_raw or public_gap_card_status_raw not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        blocked_labels.append("invalid_public_gap_card_status")

    candidate_refs = _ensure_list(raw.get("candidate_refs"))
    update_actions = _ensure_list(raw.get("update_actions"))
    suggestion_updates = _ensure_list(raw.get("suggestion_store_updates"))
    if not candidate_refs:
        blocked_labels.append("missing_candidate_id")
    if not update_actions:
        blocked_labels.append("invalid_action_type")
    if not suggestion_updates:
        blocked_labels.append("missing_update_action_id")

    for candidate in candidate_refs:
        blocked_labels.extend(_validate_candidate_ref(candidate))
    for action in update_actions:
        blocked_labels.extend(_validate_update_action(action))
    for update in suggestion_updates:
        if isinstance(update, Mapping):
            if _contains_forbidden_text(update):
                blocked_labels.append("forbidden_update_packet_text")
        else:
            blocked_labels.append("invalid_update_projection")

    if not isinstance(raw.get("operator_review_required"), bool):
        blocked_labels.append("invalid_operator_review_required")
    if _safe_bool(raw.get("storage_write_authorized", False)):
        blocked_labels.append("storage_write_authorized")
    if _safe_bool(raw.get("memory_mutation_authorized", False)):
        blocked_labels.append("memory_mutation_authorized")
    if _safe_bool(raw.get("project_mutation_authorized", False)):
        blocked_labels.append("project_mutation_authorized")
    if _safe_bool(raw.get("behavior_change_authorized", False)):
        blocked_labels.append("behavior_change_authorized")
    if _safe_bool(raw.get("behavior_promotion_authorized", False)):
        blocked_labels.append("behavior_promotion_authorized")
    if _safe_bool(raw.get("public_claim_authorized", False)):
        blocked_labels.append("public_claim_authorized")
    if _contains_forbidden_text(raw.get("compressed_lesson"), raw.get("input_summary"), raw.get("action_reason")):
        blocked_labels.append("forbidden_update_packet_text")
    if any(fragment in _compact_text(raw.get("compressed_lesson") or raw.get("input_summary") or "").lower() for fragment in ("public discovery", "proof", "breakthrough", "agi", "sentience", "consciousness", "final answer", "llm authority", "runtime authority", "safety gate replacement", "replace safety gate", ".weslr", "live ingestion", "network", "memory mutation", "project mutation", "behavior pack", "promotion")):
        blocked_labels.append("forbidden_update_packet_text")

    denied = raw.get("denied_authority")
    if not isinstance(denied, Mapping):
        blocked_labels.append("missing_denied_authority")
    elif any(_safe_bool(denied.get(key, False)) for key in denied):
        blocked_labels.append("denied_authority_granted")

    safe_metadata = raw.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        blocked_labels.append("unsafe_safe_metadata")
    elif not _safe_bool(safe_metadata.get("safe", False)):
        blocked_labels.append("unsafe_safe_metadata")
    else:
        for key in ("metadata_only", "json_safe", "non_public", "no_runtime_wiring", "no_provider_calls", "no_tool_execution", "no_persistence", "no_memory_mutation", "no_project_mutation", "no_behavior_pack_promotion", "no_public_claims", "no_final_answer"):
            if key in safe_metadata and not _safe_bool(safe_metadata.get(key, False)):
                blocked_labels.append("unsafe_safe_metadata")
                break

    if any(fragment in _compact_text(raw.get("compressed_lesson") or raw.get("input_summary") or "").lower() for fragment in ("persist", "persistence", "commit", "database", "write to store", "storage write", "memory mutation", "project mutation", "behavior change", "behavior pack", "public export")):
        blocked_labels.append("update_packet_treated_as_persistence_or_write")

    blocked = bool(blocked_labels)
    summary_text = _suggestion_store_update_summary_text(raw, blocked, blocked_labels)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "classification": ENGINE_NAME_V1 if not blocked else "invalid",
        "engine_name": ENGINE_NAME_V1,
        "engine_family": ENGINE_FAMILY_V1,
        "research_mode": _compact_text(raw.get("research_mode")) or "internal_exploration",
        "public_claim_status": _normalize_choice(raw.get("public_claim_status") or "internal_candidate_only", _ALLOWED_PUBLIC_CLAIM_STATUSES_V1, "internal_candidate_only"),
        "public_gap_card_status": _normalize_choice(raw.get("public_gap_card_status") or "public_export_blocked", _ALLOWED_PUBLIC_CLAIM_STATUSES_V1, "public_export_blocked"),
        "llm_helper_role": protocol_validation["llm_helper_role"],
        "boundary_status": protocol_validation["boundary_status"],
        "summary_text": summary_text[:320],
        "packet": to_suggestion_store_update_json_safe_v1(packet),
    }


def _suggestion_store_update_summary_text(packet: Mapping[str, Any], blocked: bool, blocked_labels: list[str]) -> str:
    engine_name = _compact_text(packet.get("engine_name")) or ENGINE_NAME_V1
    engine_family = _compact_text(packet.get("engine_family")) or ENGINE_FAMILY_V1
    packet_id = _compact_text(packet.get("packet_id")) or "packet-unknown"
    candidates = _ensure_list(packet.get("candidate_refs"))
    actions = _ensure_list(packet.get("update_actions"))
    review_required = _safe_bool(packet.get("operator_review_required", False))
    summary = (
        f"Suggestion store update packet: engine={engine_name}; family={engine_family}; packet_id={packet_id}; "
        f"candidates={len(candidates)}; actions={len(actions)}; review_required={str(review_required).lower()}."
    )
    if blocked:
        preview = ", ".join(blocked_labels[:4])
        return f"Blocked suggestion store update packet: {preview or 'validation failed'}. {summary}"
    return summary


def summarize_suggestion_store_update_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_suggestion_store_update_packet_v1(packet)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": _suggestion_store_update_summary_text(validation["packet"], validation["blocked"], validation["blocked_labels"])[:320],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "classification": validation["classification"],
        "engine_name": validation["engine_name"],
        "engine_family": validation["engine_family"],
        "research_mode": validation["research_mode"],
        "public_claim_status": validation["public_claim_status"],
        "public_gap_card_status": validation["public_gap_card_status"],
        "llm_helper_role": validation["llm_helper_role"],
        "boundary_status": validation["boundary_status"],
        "packet": validation["packet"],
    }


def to_suggestion_store_update_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def build_initial_suggestion_store_update_examples_v1() -> list[dict[str, Any]]:
    examples = [
        build_suggestion_store_update_packet_v1(
            {
                "source_run_id": "source-run-perspicuity-001",
                "research_mode": "frontier_mapping",
                "input_artifact_ref": "artifact:suggestion-perspicuity-001",
                "input_artifact_type": "suggestion-store-update",
                "input_summary": "Perspicuity-ranked candidate ready for internal update proposal.",
                "candidate_refs": [
                    build_suggestion_store_candidate_ref_v1(
                        {
                            "candidate_id": "candidate-perspicuity-001",
                            "source_engine_name": "perspicuity_scorer",
                            "source_run_id": "source-run-perspicuity-001",
                            "candidate_type": "perspicuity_ranked_candidate",
                            "candidate_summary": "Perspicuity-ranked candidate for internal review.",
                            "candidate_status": "watch",
                            "candidate_scope": "internal candidate store",
                            "public_claim_status": "internal_candidate_only",
                            "uncertainty_factors": ["score remains provisional"],
                            "invalidation_signals": ["not yet invalidated"],
                        }
                    )
                ],
                "update_actions": [
                    build_suggestion_store_update_action_v1(
                        {
                            "candidate_id": "candidate-perspicuity-001",
                            "action_type": "link_perspicuity_scorecard",
                            "action_reason": "Link the scorecard as internal update metadata.",
                            "previous_status": "watch",
                            "next_status": "watch",
                            "linked_perspicuity_scorecard_ref": "scorecard:perspicuity-001",
                            "operator_review_required": True,
                        }
                    )
                ],
            }
        ),
        build_suggestion_store_update_packet_v1(
            {
                "source_run_id": "source-run-rule-pressure-001",
                "research_mode": "synthetic_test",
                "input_artifact_ref": "artifact:suggestion-rule-pressure-001",
                "input_artifact_type": "suggestion-store-update",
                "input_summary": "Rule Pressure candidate update proposal.",
                "candidate_refs": [
                    build_suggestion_store_candidate_ref_v1(
                        {
                            "candidate_id": "candidate-rule-pressure-001",
                            "source_engine_name": "rule_pressure_engine",
                            "source_run_id": "source-run-rule-pressure-001",
                            "candidate_type": "pressure_result",
                            "candidate_summary": "Rule Pressure candidate for internal review.",
                            "candidate_status": "pressure_test",
                            "candidate_scope": "bounded pressure scope",
                            "public_claim_status": "internal_candidate_only",
                            "uncertainty_factors": ["pressure result still provisional"],
                            "invalidation_signals": ["not yet invalidated"],
                        }
                    )
                ],
                "update_actions": [
                    build_suggestion_store_update_action_v1(
                        {
                            "candidate_id": "candidate-rule-pressure-001",
                            "action_type": "link_pressure_test",
                            "action_reason": "Link the pressure test as internal update metadata.",
                            "previous_status": "pressure_test",
                            "next_status": "pressure_test",
                            "linked_pressure_test_ref": "pressure:rule-pressure-001",
                            "operator_review_required": True,
                        }
                    )
                ],
            }
        ),
        build_suggestion_store_update_packet_v1(
            {
                "source_run_id": "source-run-dialectic-001",
                "research_mode": "calibration_replay",
                "input_artifact_ref": "artifact:suggestion-dialectic-001",
                "input_artifact_type": "suggestion-store-update",
                "input_summary": "Dialectic-generated candidate update proposal.",
                "candidate_refs": [
                    build_suggestion_store_candidate_ref_v1(
                        {
                            "candidate_id": "candidate-dialectic-001",
                            "source_engine_name": "dialectic_generator_loop",
                            "source_run_id": "source-run-dialectic-001",
                            "candidate_type": "generated_source_signal",
                            "candidate_summary": "Dialectic generated candidate for internal review.",
                            "candidate_status": "probe",
                            "candidate_scope": "internal candidate store",
                            "public_claim_status": "internal_candidate_only",
                            "uncertainty_factors": ["generated candidate remains provisional"],
                            "invalidation_signals": ["not yet invalidated"],
                        }
                    )
                ],
                "update_actions": [
                    build_suggestion_store_update_action_v1(
                        {
                            "candidate_id": "candidate-dialectic-001",
                            "action_type": "add_candidate",
                            "action_reason": "Add the generated candidate to the internal proposal list.",
                            "previous_status": "unknown",
                            "next_status": "new",
                            "operator_review_required": True,
                        }
                    )
                ],
            }
        ),
        build_suggestion_store_update_packet_v1(
            {
                "source_run_id": "source-run-calibration-001",
                "research_mode": "calibration_replay",
                "input_artifact_ref": "artifact:suggestion-calibration-001",
                "input_artifact_type": "suggestion-store-update",
                "input_summary": "Calibration-linked candidate update proposal.",
                "candidate_refs": [
                    build_suggestion_store_candidate_ref_v1(
                        {
                            "candidate_id": "candidate-calibration-001",
                            "source_engine_name": "forecast_calibration_bridge",
                            "source_run_id": "source-run-calibration-001",
                            "candidate_type": "calibration_record",
                            "candidate_summary": "Calibration-linked candidate for internal review.",
                            "candidate_status": "calibrate",
                            "candidate_scope": "calibration review scope",
                            "public_claim_status": "internal_candidate_only",
                            "uncertainty_factors": ["calibration link remains provisional"],
                            "invalidation_signals": ["not yet invalidated"],
                        }
                    )
                ],
                "update_actions": [
                    build_suggestion_store_update_action_v1(
                        {
                            "candidate_id": "candidate-calibration-001",
                            "action_type": "link_calibration_record",
                            "action_reason": "Link the calibration record as internal update metadata.",
                            "previous_status": "calibrate",
                            "next_status": "calibrate",
                            "linked_calibration_record_ref": "calibration:forecast-001",
                            "operator_review_required": True,
                        }
                    )
                ],
            }
        ),
    ]
    return examples
