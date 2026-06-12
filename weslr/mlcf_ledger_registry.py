"""WESLR MLCF Ledger Registry V1.

Deterministic, metadata-only helpers for defining the canonical Multi-Ledger
Cognitive Fabric ledgers without runtime wiring, persistence, memory mutation,
public claims, or authority escalation.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "mlcf_ledger_registry_v1"
HELPER_FAMILY_V1 = "mlcf_ledger_registry"

_ALLOWED_MLCF_LEDGER_IDS_V1 = (
    "user_preference_ledger",
    "user_identity_context_ledger",
    "project_state_ledger",
    "idea_candidate_ledger",
    "decision_ledger",
    "evidence_ledger",
    "failed_idea_ledger",
    "calibration_outcome_ledger",
    "relationship_context_ledger",
    "behavior_candidate_ledger",
    "architecture_direction_ledger",
)

_AUTHORITY_FALSE_FLAGS_V1 = (
    "runtime_authorized",
    "source_ingestion_authorized",
    "public_claim_authorized",
    "final_answer_authority",
    "provider_model_call_authority",
    "provider_authority",
    "model_authority",
    "tool_execution_authority",
    "retrieval_tool_authority",
    "web_authority",
    "weslr_io_authorized",
    "weslr_read_authorized",
    "weslr_write_authorized",
    "weslr_persistence_authorized",
    "database_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "behavior_pack_promotion_authorized",
    "public_science_claim_authorized",
    "proof_claim_authorized",
    "benchmark_claim_authorized",
    "agi_claim_authorized",
    "automatic_discovery_authorized",
    "cross_user_leakage_authorized",
    "hidden_private_protected_authorized",
)

_AUTHORITY_TEXT_MARKERS_V1 = (
    "discovery",
    "proof",
    "benchmark",
    "agi",
    "final answer",
    "public claim",
    "runtime authorization",
    "source ingestion authorization",
    "provider/model/tool/retrieval/web",
    ".weslr",
    "memory mutation",
    "project mutation",
    "behavior pack promotion",
    "cross-user leakage",
    "hidden/private/protected",
)

_HIDDEN_PRIVATE_PROTECTED_MARKERS_V1 = (
    "hidden prompt",
    "system prompt",
    "private text",
    "secret",
    "api key",
    "protected file",
    "protected",
    "private",
)

_SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1 = (
    "safe",
    "metadata_only",
    "json_safe",
    "non_public",
    "no_runtime_wiring",
    "no_model_provider_calls",
    "no_tool_execution",
    "no_retrieval",
    "no_web_calls",
    "no_source_ingestion",
    "no_weslr_io",
    "no_weslr_read",
    "no_weslr_write",
    "no_weslr_persistence",
    "no_database_writes",
    "no_memory_mutation",
    "no_project_mutation",
    "no_behavior_pack_promotion",
    "no_public_claim_authority",
    "no_final_answer_authority",
    "no_discovery_claims",
    "no_proof_claims",
    "no_benchmark_claims",
    "no_agi_claims",
    "no_public_science_claims",
    "no_hidden_private_protected_markers",
)

_REQUIRED_LEDGER_FIELD_NAMES_V1 = (
    "schema_version",
    "ledger_id",
    "ledger_name",
    "ledger_purpose",
    "ledger_scope",
    "authority_requirement",
    "allowed_source_kinds",
    "allowed_record_kinds",
    "read_model_targets",
    "forbidden_operations",
    "privacy_boundary",
    "tombstone_policy",
    "rollback_policy",
    "cross_ledger_reference_policy",
    "retention_review_policy",
    "authority_status",
    "safe_metadata",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "allowed_source_kinds",
    "allowed_record_kinds",
    "read_model_targets",
    "forbidden_operations",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "ledger_id",
    "ledger_name",
    "ledger_purpose",
    "ledger_scope",
    "authority_requirement",
    "privacy_boundary",
    "tombstone_policy",
    "rollback_policy",
    "cross_ledger_reference_policy",
    "retention_review_policy",
)

_DEFAULT_FORBIDDEN_OPERATIONS_V1 = [
    "runtime wiring",
    "source ingestion",
    "public claims",
    "final-answer authority",
    "provider/model/tool/web/retrieval authority",
    ".weslr read/write/persistence",
    "database writes",
    "memory mutation",
    "project mutation",
    "behavior-pack promotion",
    "public discovery/proof/AGI/benchmark claims",
    "cross-user leakage",
    "hidden/private/protected markers",
]

_DEFAULT_AUTHORITY_STATUS_V1 = {
    "runtime_authorized": False,
    "source_ingestion_authorized": False,
    "public_claim_authorized": False,
    "final_answer_authority": False,
    "provider_model_call_authority": False,
    "provider_authority": False,
    "model_authority": False,
    "tool_execution_authority": False,
    "retrieval_tool_authority": False,
    "web_authority": False,
    "weslr_io_authorized": False,
    "weslr_read_authorized": False,
    "weslr_write_authorized": False,
    "weslr_persistence_authorized": False,
    "database_write_authorized": False,
    "memory_mutation_authorized": False,
    "project_mutation_authorized": False,
    "behavior_pack_promotion_authorized": False,
    "public_science_claim_authorized": False,
    "proof_claim_authorized": False,
    "benchmark_claim_authorized": False,
    "agi_claim_authorized": False,
    "automatic_discovery_authorized": False,
    "cross_user_leakage_authorized": False,
    "hidden_private_protected_authorized": False,
    "all_authority_flags_false": True,
    "status": "metadata_only",
    "boundary_notes": "metadata-only ledger registry boundary",
}

_DEFAULT_SAFE_METADATA_V1 = {
    "safe": True,
    "metadata_only": True,
    "json_safe": True,
    "non_public": True,
    "no_runtime_wiring": True,
    "no_model_provider_calls": True,
    "no_tool_execution": True,
    "no_retrieval": True,
    "no_web_calls": True,
    "no_source_ingestion": True,
    "no_weslr_io": True,
    "no_weslr_read": True,
    "no_weslr_write": True,
    "no_weslr_persistence": True,
    "no_database_writes": True,
    "no_memory_mutation": True,
    "no_project_mutation": True,
    "no_behavior_pack_promotion": True,
    "no_public_claim_authority": True,
    "no_final_answer_authority": True,
    "no_discovery_claims": True,
    "no_proof_claims": True,
    "no_benchmark_claims": True,
    "no_agi_claims": True,
    "no_public_science_claims": True,
    "no_hidden_private_protected_markers": True,
    "registry_family": HELPER_FAMILY_V1,
    "helper_family": SCHEMA_VERSION_V1,
}

_CANONICAL_LEDGER_SPECS_V1: dict[str, dict[str, Any]] = {
    "user_preference_ledger": {
        "ledger_name": "User Preference Ledger",
        "ledger_purpose": "Store user preference signals with explicit scope and contradiction history.",
        "ledger_scope": "user_scoped_no_cross_user_leakage",
        "authority_requirement": "explicit_user_signal",
        "allowed_source_kinds": [
            "explicit_user_statement",
            "confirmed_user_correction",
            "verified_session_interaction",
            "operator_confirmed_preference",
        ],
        "allowed_record_kinds": [
            "preference_record",
            "preference_correction_record",
            "preference_confirmation_record",
            "preference_tombstone_record",
        ],
        "read_model_targets": [
            "user_preference_summary_read_model",
            "preference_contradiction_read_model",
        ],
        "privacy_boundary": "user_scoped_no_cross_user_leakage",
        "tombstone_policy": "use tombstones for retired preferences instead of silent deletion.",
        "rollback_policy": "record reversal events and rebuild preference read models.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review on contradiction, staleness, or explicit user correction.",
    },
    "user_identity_context_ledger": {
        "ledger_name": "User Identity Context Ledger",
        "ledger_purpose": "Store verified identity and context signals without inferring from unrelated memory.",
        "ledger_scope": "user_scoped_verified_context_only",
        "authority_requirement": "verified_context_or_operator_review",
        "allowed_source_kinds": [
            "verified_session_context",
            "channel_verified_identity",
            "device_verified_identity",
            "operator_confirmed_identity",
        ],
        "allowed_record_kinds": [
            "identity_context_record",
            "verification_record",
            "context_revocation_record",
            "identity_tombstone_record",
        ],
        "read_model_targets": [
            "identity_context_read_model",
            "verification_history_read_model",
        ],
        "privacy_boundary": "user_scoped_verified_context_only",
        "tombstone_policy": "use tombstones when verification is revoked or expires.",
        "rollback_policy": "record revocation events and rebuild identity context views.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review when verification weakens or context changes.",
    },
    "project_state_ledger": {
        "ledger_name": "Project State Ledger",
        "ledger_purpose": "Store project facts, continuity markers, and approved project state.",
        "ledger_scope": "project_scoped_no_cross_user_leakage",
        "authority_requirement": "project_scope_authority",
        "allowed_source_kinds": [
            "internal_project_artifact",
            "operator_note",
            "approved_decision",
            "continuity_snapshot",
        ],
        "allowed_record_kinds": [
            "project_state_record",
            "project_update_record",
            "continuity_record",
            "project_tombstone_record",
        ],
        "read_model_targets": [
            "project_state_read_model",
            "project_continuity_read_model",
        ],
        "privacy_boundary": "project_scoped_no_cross_user_leakage",
        "tombstone_policy": "use tombstones for superseded or retired project facts.",
        "rollback_policy": "record reversal events and rebuild project state read models.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review on project scope change, contradiction, or operator override.",
    },
    "idea_candidate_ledger": {
        "ledger_name": "Idea Candidate Ledger",
        "ledger_purpose": "Store candidate ideas, hypotheses, and evolving next-step options.",
        "ledger_scope": "workspace_or_project_candidate_scope",
        "authority_requirement": "owner_or_operator_review",
        "allowed_source_kinds": [
            "owner_prompt",
            "internal_candidate",
            "calibrated_proposed_direction",
            "synthetic_example",
        ],
        "allowed_record_kinds": [
            "idea_candidate_record",
            "hypothesis_record",
            "candidate_direction_record",
            "idea_tombstone_record",
        ],
        "read_model_targets": [
            "idea_candidate_read_model",
            "candidate_direction_read_model",
        ],
        "privacy_boundary": "workspace_or_project_candidate_scope",
        "tombstone_policy": "use tombstones for rejected or retired ideas instead of erasing history.",
        "rollback_policy": "record rejection or reversal events and rebuild candidate views.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review after pressure tests, contradiction, or operator decision.",
    },
    "decision_ledger": {
        "ledger_name": "Decision Ledger",
        "ledger_purpose": "Store operator decisions, approvals, rejections, and reversals.",
        "ledger_scope": "operator_or_project_scoped",
        "authority_requirement": "operator_authority",
        "allowed_source_kinds": [
            "operator_approval",
            "governance_outcome",
            "review_result",
            "rollback_event",
        ],
        "allowed_record_kinds": [
            "decision_record",
            "approval_record",
            "rejection_record",
            "decision_reversal_record",
        ],
        "read_model_targets": [
            "decision_history_read_model",
            "approval_queue_read_model",
        ],
        "privacy_boundary": "operator_or_project_scoped",
        "tombstone_policy": "use tombstones for superseded decision views; preserve decision history.",
        "rollback_policy": "record formal reversal events and rebuild decision views.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review only when governance policy changes or a decision is explicitly reversed.",
    },
    "evidence_ledger": {
        "ledger_name": "Evidence Ledger",
        "ledger_purpose": "Store bounded evidence packets and source-linked confidence posture.",
        "ledger_scope": "project_or_operator_scoped_evidence",
        "authority_requirement": "evidence_intake_boundary_authority",
        "allowed_source_kinds": [
            "owner_supplied_observation",
            "owner_supplied_document_metadata",
            "internal_project_artifact",
            "known_science_replay",
            "synthetic_example",
        ],
        "allowed_record_kinds": [
            "evidence_record",
            "evidence_intake_record",
            "source_limitation_record",
            "evidence_tombstone_record",
        ],
        "read_model_targets": [
            "evidence_summary_read_model",
            "evidence_contradiction_read_model",
        ],
        "privacy_boundary": "source_posture_scoped_no_raw_retention",
        "tombstone_policy": "use tombstones when evidence is invalidated or retracted.",
        "rollback_policy": "record invalidation events and rebuild evidence views.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review when source freshness changes or contradiction appears.",
    },
    "failed_idea_ledger": {
        "ledger_name": "Failed Idea Ledger",
        "ledger_purpose": "Store rejected or disproved ideas as durable negative signals.",
        "ledger_scope": "project_scoped_negative_signal_only",
        "authority_requirement": "operator_review_or_replay_authority",
        "allowed_source_kinds": [
            "rejected_candidate",
            "disproved_hypothesis",
            "negative_signal",
            "operator_rejected_candidate",
        ],
        "allowed_record_kinds": [
            "failed_idea_record",
            "rejection_record",
            "counterexample_record",
            "failed_idea_tombstone_record",
        ],
        "read_model_targets": [
            "failed_idea_read_model",
            "counterexample_read_model",
        ],
        "privacy_boundary": "project_scoped_negative_signal_only",
        "tombstone_policy": "use tombstones for retired failure signals while preserving the failure trace.",
        "rollback_policy": "record reversal or repair events and rebuild failed idea views.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review when revisiting the same theme or after new contradictory evidence.",
    },
    "calibration_outcome_ledger": {
        "ledger_name": "Calibration Outcome Ledger",
        "ledger_purpose": "Store calibration results, forecast error history, and update deltas.",
        "ledger_scope": "system_or_project_internal_only",
        "authority_requirement": "calibration_review_authority",
        "allowed_source_kinds": [
            "calibration_result",
            "forecast_error",
            "reverse_trace",
            "signal_detection_result",
        ],
        "allowed_record_kinds": [
            "calibration_outcome_record",
            "forecast_error_record",
            "update_delta_record",
            "calibration_tombstone_record",
        ],
        "read_model_targets": [
            "calibration_outcome_read_model",
            "forecast_error_read_model",
        ],
        "privacy_boundary": "system_or_project_internal_only",
        "tombstone_policy": "use tombstones for superseded calibration summaries while preserving history.",
        "rollback_policy": "record correction events and rebuild calibration views.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review on calibration drift, model change, or replay mismatch.",
    },
    "relationship_context_ledger": {
        "ledger_name": "Relationship Context Ledger",
        "ledger_purpose": "Store relationship and continuity signals that may shape tone and initiative.",
        "ledger_scope": "user_entity_project_scoped_verified_only",
        "authority_requirement": "verified_interaction_authority",
        "allowed_source_kinds": [
            "verified_session_interaction",
            "shared_work_completed",
            "user_preference_saved",
            "successful_followup",
            "correction_resolved",
        ],
        "allowed_record_kinds": [
            "relationship_context_record",
            "interaction_signal_record",
            "continuity_signal_record",
            "relationship_tombstone_record",
        ],
        "read_model_targets": [
            "relationship_tone_read_model",
            "continuity_signal_read_model",
        ],
        "privacy_boundary": "user_entity_project_scoped_verified_only",
        "tombstone_policy": "use tombstones for retired relationship signals while preserving history.",
        "rollback_policy": "record correction events and rebuild relationship views.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review on inactivity, correction, or verification change.",
    },
    "behavior_candidate_ledger": {
        "ledger_name": "Behavior Candidate Ledger",
        "ledger_purpose": "Store candidate behavior packs and promotion-relevant metadata without promotion authority.",
        "ledger_scope": "system_wide_candidate_only",
        "authority_requirement": "promotion_review_authority",
        "allowed_source_kinds": [
            "behavior_pack_candidate",
            "replay_result",
            "promotion_policy_result",
            "operator_review_candidate",
        ],
        "allowed_record_kinds": [
            "behavior_candidate_record",
            "promotion_candidate_record",
            "promotion_review_record",
            "behavior_tombstone_record",
        ],
        "read_model_targets": [
            "behavior_candidate_read_model",
            "promotion_candidate_read_model",
        ],
        "privacy_boundary": "system_wide_candidate_only",
        "tombstone_policy": "use tombstones for rejected or retired candidates instead of silent disappearance.",
        "rollback_policy": "record rejection or reversal events and rebuild candidate views.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review after replay, promotion review, or policy change.",
    },
    "architecture_direction_ledger": {
        "ledger_name": "Architecture Direction Ledger",
        "ledger_purpose": "Store architecture direction packets, review outcomes, and candidate structure metadata.",
        "ledger_scope": "system_wide_design_only",
        "authority_requirement": "design_review_authority",
        "allowed_source_kinds": [
            "design_doc",
            "architecture_review",
            "calibration_theorem_review",
            "implementation_atlas_reference",
        ],
        "allowed_record_kinds": [
            "architecture_direction_record",
            "architecture_review_record",
            "design_candidate_record",
            "architecture_tombstone_record",
        ],
        "read_model_targets": [
            "architecture_direction_read_model",
            "architecture_review_read_model",
        ],
        "privacy_boundary": "system_wide_design_only",
        "tombstone_policy": "use tombstones for superseded design candidates while preserving the review trail.",
        "rollback_policy": "record design reversals and rebuild direction views.",
        "cross_ledger_reference_policy": "typed references only; no implicit joins; no cross-user joins.",
        "retention_review_policy": "review when architecture direction changes or a new lane supersedes the candidate.",
    },
}


def allowed_mlcf_ledger_ids_v1() -> tuple[str, ...]:
    return _ALLOWED_MLCF_LEDGER_IDS_V1


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    elif isinstance(value, set):
        items = sorted(value, key=repr)
    else:
        text = _compact_text(value)
        return [text] if text else []
    normalized: list[str] = []
    for item in items:
        text = _compact_text(item)
        if text:
            normalized.append(text)
    return normalized


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"[redacted:{type(value).__name__}]"
    if callable(value):
        return f"[redacted:{type(value).__name__}]"
    if isinstance(value, (bool, int, float)) or value is None or isinstance(value, str):
        return value
    return f"[redacted:{type(value).__name__}]"


def _first_non_json_safe_path(value: Any, path: str = "result") -> str | None:
    if value is None or isinstance(value, (bool, int, float, str)):
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        return path
    if isinstance(value, (tuple, set, frozenset)):
        return path
    if callable(value):
        return path
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                return f"{path}.[non-string-key:{type(key).__name__}]"
            issue = _first_non_json_safe_path(item, f"{path}.{key}")
            if issue is not None:
                return issue
        return None
    if isinstance(value, list):
        for index, item in enumerate(value):
            issue = _first_non_json_safe_path(item, f"{path}[{index}]")
            if issue is not None:
                return issue
        return None
    return path


def _contains_text_markers(value: Any, markers: tuple[str, ...]) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_text_markers(item, markers) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_markers(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in markers)


def _build_default_authority_status() -> dict[str, Any]:
    return deepcopy(_DEFAULT_AUTHORITY_STATUS_V1)


def _build_default_safe_metadata() -> dict[str, Any]:
    return deepcopy(_DEFAULT_SAFE_METADATA_V1)


def _build_default_ledger_definition(ledger_id: str) -> dict[str, Any]:
    spec = deepcopy(_CANONICAL_LEDGER_SPECS_V1.get(ledger_id, {}))
    definition: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_V1,
        "ledger_id": ledger_id,
        "ledger_name": spec.get("ledger_name", ledger_id),
        "ledger_purpose": spec.get("ledger_purpose", "metadata-only ledger candidate"),
        "ledger_scope": spec.get("ledger_scope", "system_scoped_metadata_only"),
        "authority_requirement": spec.get("authority_requirement", "metadata_only"),
        "allowed_source_kinds": list(spec.get("allowed_source_kinds", ["synthetic_example"])),
        "allowed_record_kinds": list(spec.get("allowed_record_kinds", ["ledger_record"])),
        "read_model_targets": list(spec.get("read_model_targets", ["ledger_read_model"])),
        "forbidden_operations": list(spec.get("forbidden_operations", _DEFAULT_FORBIDDEN_OPERATIONS_V1)),
        "privacy_boundary": spec.get("privacy_boundary", "system_scoped_no_cross_user_leakage"),
        "tombstone_policy": spec.get("tombstone_policy", "use tombstones rather than silent deletion."),
        "rollback_policy": spec.get("rollback_policy", "record reversal events and rebuild read models."),
        "cross_ledger_reference_policy": spec.get(
            "cross_ledger_reference_policy",
            "typed references only; no implicit joins; no cross-user joins.",
        ),
        "retention_review_policy": spec.get(
            "retention_review_policy",
            "review on contradiction, staleness, or scope change.",
        ),
        "authority_status": _build_default_authority_status(),
        "safe_metadata": _build_default_safe_metadata(),
    }
    return definition


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
    return merged


def build_mlcf_ledger_definition_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    ledger_id = _compact_text(data.get("ledger_id"))
    built = _build_default_ledger_definition(ledger_id)
    for key in (
        "schema_version",
        "ledger_id",
        "ledger_name",
        "ledger_purpose",
        "ledger_scope",
        "authority_requirement",
        "privacy_boundary",
        "tombstone_policy",
        "rollback_policy",
        "cross_ledger_reference_policy",
        "retention_review_policy",
    ):
        if key in data:
            built[key] = _compact_text(data.get(key), built[key])
    for key in ("allowed_source_kinds", "allowed_record_kinds", "read_model_targets", "forbidden_operations"):
        if key in data:
            built[key] = _normalize_text_list(data.get(key))
    if "authority_status" in data:
        built["authority_status"] = deepcopy(data.get("authority_status"))
    if "safe_metadata" in data:
        built["safe_metadata"] = deepcopy(data.get("safe_metadata"))
    return built


def _authority_status_is_fail_closed(authority_status: Any) -> tuple[bool, list[str]]:
    if not isinstance(authority_status, Mapping):
        return False, ["missing_authority_status"]
    labels: list[str] = []
    for flag in _AUTHORITY_FALSE_FLAGS_V1:
        if flag not in authority_status:
            labels.append(f"missing_authority_status_{flag}")
        elif authority_status[flag] is not False:
            labels.append(f"unsafe_authority_flag:{flag}")
    if authority_status.get("all_authority_flags_false") is not True:
        labels.append("unsafe_authority_flags")
    if _compact_text(authority_status.get("status")) != "metadata_only":
        labels.append("unsafe_authority_status")
    if not _compact_text(authority_status.get("boundary_notes")):
        labels.append("missing_authority_boundary_notes")
    if _contains_text_markers(authority_status.get("boundary_notes"), _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_authority_text")
    if _contains_text_markers(authority_status.get("boundary_notes"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("forbidden_hidden_private_protected_marker")
    return not labels, labels


def _safe_metadata_is_fail_closed(safe_metadata: Any) -> tuple[bool, list[str]]:
    if not isinstance(safe_metadata, Mapping):
        return False, ["missing_safe_metadata"]
    labels: list[str] = []
    for flag in _SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1:
        if safe_metadata.get(flag) is not True:
            labels.append(f"unsafe_safe_metadata_flag:{flag}")
    if _contains_text_markers(safe_metadata.get("boundary_notes"), _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_safe_metadata_text")
    if _contains_text_markers(safe_metadata.get("boundary_notes"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("forbidden_hidden_private_protected_marker")
    return not labels, labels


def validate_mlcf_ledger_definition_v1(definition: Any) -> dict[str, Any]:
    if not isinstance(definition, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_definition_type"],
            "validation_posture": "blocked",
            "summary_text": "Blocked MLCF ledger definition: invalid definition type.",
        }

    blocked_labels: list[str] = []
    for field in _REQUIRED_LEDGER_FIELD_NAMES_V1:
        if field not in definition:
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(definition.get(field)):
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_LIST_FIELDS_V1:
        value = definition.get(field)
        if not isinstance(value, list):
            blocked_labels.append(f"invalid_{field}")
        elif not value:
            blocked_labels.append(f"missing_{field}")
        elif any(_compact_text(item) == "" for item in value):
            blocked_labels.append(f"invalid_{field}")

    ledger_id = _compact_text(definition.get("ledger_id"))
    if ledger_id not in _ALLOWED_MLCF_LEDGER_IDS_V1:
        blocked_labels.append("invalid_ledger_id")

    if _compact_text(definition.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")

    if _compact_text(definition.get("privacy_boundary")) == "":
        blocked_labels.append("missing_privacy_boundary")
    if _compact_text(definition.get("authority_requirement")) == "":
        blocked_labels.append("missing_authority_requirement")
    if _compact_text(definition.get("tombstone_policy")) == "":
        blocked_labels.append("missing_tombstone_policy")
    if _compact_text(definition.get("rollback_policy")) == "":
        blocked_labels.append("missing_rollback_policy")
    if _compact_text(definition.get("cross_ledger_reference_policy")) == "":
        blocked_labels.append("missing_cross_ledger_reference_policy")
    if _compact_text(definition.get("retention_review_policy")) == "":
        blocked_labels.append("missing_retention_review_policy")

    _, authority_labels = _authority_status_is_fail_closed(definition.get("authority_status"))
    blocked_labels.extend(authority_labels)

    _, safe_labels = _safe_metadata_is_fail_closed(definition.get("safe_metadata"))
    blocked_labels.extend(safe_labels)

    if _compact_text(definition.get("ledger_scope")) == "":
        blocked_labels.append("missing_ledger_scope")
    for field_name in (
        "ledger_name",
        "ledger_purpose",
        "ledger_scope",
        "authority_requirement",
        "privacy_boundary",
        "tombstone_policy",
        "rollback_policy",
        "cross_ledger_reference_policy",
        "retention_review_policy",
    ):
        if _contains_text_markers(definition.get(field_name), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            blocked_labels.append("forbidden_hidden_private_protected_marker")
        if _contains_text_markers(definition.get(field_name), _AUTHORITY_TEXT_MARKERS_V1):
            blocked_labels.append("unsafe_authority_text")
    if _first_non_json_safe_path(definition) is not None:
        blocked_labels.append("non_json_safe_output")

    valid = not blocked_labels
    summary_text = (
        "Valid MLCF ledger definition."
        if valid
        else "Blocked MLCF ledger definition: metadata, authority, or safety checks failed."
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": blocked_labels,
        "validation_posture": "valid" if valid else "blocked",
        "summary_text": summary_text,
    }


def build_initial_mlcf_ledger_registry_v1() -> dict[str, Any]:
    ledger_definitions = [
        build_mlcf_ledger_definition_v1({"ledger_id": ledger_id})
        for ledger_id in _ALLOWED_MLCF_LEDGER_IDS_V1
    ]
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "registry_id": SCHEMA_VERSION_V1,
        "registry_name": "MLCF Ledger Registry",
        "registry_purpose": "Canonical metadata-only registry for WESLR Multi-Ledger Cognitive Fabric ledgers.",
        "ledger_definitions": ledger_definitions,
        "ledger_count": len(ledger_definitions),
        "canonical_ledger_ids": list(_ALLOWED_MLCF_LEDGER_IDS_V1),
        "authority_status": _build_default_authority_status(),
        "safe_metadata": _build_default_safe_metadata(),
    }


def validate_mlcf_ledger_registry_v1(registry: Any) -> dict[str, Any]:
    if not isinstance(registry, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_registry_type"],
            "validation_posture": "blocked",
            "summary_text": "Blocked MLCF ledger registry: invalid registry type.",
        }

    blocked_labels: list[str] = []
    required_fields = (
        "schema_version",
        "registry_id",
        "registry_name",
        "registry_purpose",
        "ledger_definitions",
        "ledger_count",
        "canonical_ledger_ids",
        "authority_status",
        "safe_metadata",
    )
    for field in required_fields:
        if field not in registry:
            blocked_labels.append(f"missing_{field}")

    if _compact_text(registry.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")
    if _compact_text(registry.get("registry_id")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_registry_id")
    if not _compact_text(registry.get("registry_name")):
        blocked_labels.append("missing_registry_name")
    if not _compact_text(registry.get("registry_purpose")):
        blocked_labels.append("missing_registry_purpose")

    ledger_definitions = registry.get("ledger_definitions")
    if not isinstance(ledger_definitions, list):
        blocked_labels.append("invalid_ledger_definitions")
        ledger_definitions = []
    elif not ledger_definitions:
        blocked_labels.append("missing_ledger_definitions")

    if not isinstance(registry.get("ledger_count"), int):
        blocked_labels.append("invalid_ledger_count")
    elif isinstance(ledger_definitions, list) and registry.get("ledger_count") != len(ledger_definitions):
        blocked_labels.append("ledger_count_mismatch")

    canonical_ledger_ids = registry.get("canonical_ledger_ids")
    if not isinstance(canonical_ledger_ids, list):
        blocked_labels.append("invalid_canonical_ledger_ids")
        canonical_ledger_ids = []
    elif canonical_ledger_ids != list(_ALLOWED_MLCF_LEDGER_IDS_V1):
        blocked_labels.append("invalid_canonical_ledger_ids")

    seen: set[str] = set()
    validated_ids: list[str] = []
    for index, ledger_definition in enumerate(ledger_definitions):
        if not isinstance(ledger_definition, Mapping):
            blocked_labels.append(f"invalid_ledger_definition_{index}")
            continue
        definition_validation = validate_mlcf_ledger_definition_v1(ledger_definition)
        if definition_validation.get("blocked"):
            for label in definition_validation.get("blocked_labels", []):
                blocked_labels.append(f"ledger_{index}:{label}")
        ledger_id = _compact_text(ledger_definition.get("ledger_id"))
        if ledger_id:
            validated_ids.append(ledger_id)
            if ledger_id in seen:
                blocked_labels.append(f"duplicate_ledger_id:{ledger_id}")
            seen.add(ledger_id)

    if validated_ids and validated_ids != list(_ALLOWED_MLCF_LEDGER_IDS_V1):
        blocked_labels.append("invalid_ledger_id_order")

    _, authority_labels = _authority_status_is_fail_closed(registry.get("authority_status"))
    blocked_labels.extend(authority_labels)

    _, safe_labels = _safe_metadata_is_fail_closed(registry.get("safe_metadata"))
    blocked_labels.extend(safe_labels)

    for field_name in ("registry_name", "registry_purpose"):
        if _contains_text_markers(registry.get(field_name), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            blocked_labels.append("forbidden_hidden_private_protected_marker")
        if _contains_text_markers(registry.get(field_name), _AUTHORITY_TEXT_MARKERS_V1):
            blocked_labels.append("unsafe_authority_text")
    if _first_non_json_safe_path(registry) is not None:
        blocked_labels.append("non_json_safe_output")

    valid = not blocked_labels
    summary_text = (
        "Valid MLCF ledger registry."
        if valid
        else "Blocked MLCF ledger registry: metadata, authority, or safety checks failed."
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": blocked_labels,
        "validation_posture": "valid" if valid else "blocked",
        "summary_text": summary_text,
    }


def summarize_mlcf_ledger_registry_v1(registry: Any) -> dict[str, Any]:
    raw = registry if isinstance(registry, Mapping) else {}
    validation = validate_mlcf_ledger_registry_v1(raw) if isinstance(raw, Mapping) else {}
    ledger_definitions = raw.get("ledger_definitions") if isinstance(raw.get("ledger_definitions"), list) else []
    ledger_ids = [
        _compact_text(item.get("ledger_id"), "unknown_ledger")
        for item in ledger_definitions
        if isinstance(item, Mapping)
    ]
    return {
        "registry_id": _compact_text(raw.get("registry_id"), SCHEMA_VERSION_V1),
        "registry_name": _compact_text(raw.get("registry_name"), "unknown_registry"),
        "ledger_count": len(ledger_ids),
        "ledger_ids": ledger_ids,
        "canonical_ledger_ids": list(_ALLOWED_MLCF_LEDGER_IDS_V1),
        "validation_posture": _compact_text(validation.get("validation_posture"), "unknown"),
        "summary_text": (
            f"MLCF ledger registry {_compact_text(raw.get('registry_id'), SCHEMA_VERSION_V1)}: "
            f"{len(ledger_ids)} ledgers, canonical ids stable."
        ),
        "authority_status": _json_safe(
            raw.get("authority_status") if isinstance(raw.get("authority_status"), Mapping) else _build_default_authority_status()
        ),
    }


def to_mlcf_ledger_registry_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)
