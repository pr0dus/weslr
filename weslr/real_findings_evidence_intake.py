"""WESLR Real Findings Evidence Intake V1.

Deterministic, metadata-only helpers for representing bounded evidence signals
as safe intake packets before any proposed direction is considered.

This module does not authorize ingestion, retrieval, web/provider/tool calls,
persistence, runtime behavior, public claims, discovery, proof, or final-answer
authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "real_findings_evidence_intake_v1"
HELPER_FAMILY_V1 = "real_findings_evidence_intake"

_ALLOWED_EVIDENCE_SOURCE_KINDS_V1 = (
    "public_open_source",
    "owner_supplied_document",
    "owner_supplied_observation",
    "synthetic_example",
    "known_science_replay",
    "internal_project_artifact",
    "blocked_private_source",
    "unknown_source",
)

_ALLOWED_EVIDENCE_ACCESS_STATUSES_V1 = (
    "not_accessed",
    "metadata_only",
    "owner_supplied_summary",
    "future_access_requires_review",
    "blocked",
    "needs_repair",
)

_ALLOWED_EVIDENCE_CONFIDENCE_POSTURES_V1 = (
    "unassessed",
    "weak_signal",
    "moderate_signal",
    "strong_signal_requires_pressure_test",
    "conflicting_signal",
    "insufficient_context",
    "blocked_by_safety",
)

_ALLOWED_PROPOSED_DIRECTION_ELIGIBILITY_V1 = (
    "not_eligible",
    "eligible_for_candidate_direction",
    "eligible_after_probe",
    "eligible_after_pressure_test",
    "operator_review_required",
    "blocked_by_safety",
    "needs_repair",
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
    "hidden_private_protected_authorized",
    "cross_user_leakage_authorized",
    "public_science_claim_authorized",
    "proof_claim_authorized",
    "benchmark_claim_authorized",
    "agi_claim_authorized",
    "automatic_discovery_authorized",
)

_AUTHORITY_TEXT_MARKERS_V1 = (
    "discovery",
    "proof",
    "benchmark",
    "score",
    "agi",
    "intelligence",
    "sentience",
    "consciousness",
    "public claim authorized",
    "final answer authority",
    "runtime authorization",
    "source ingestion authorization",
    "provider/model/tool/retrieval/web implication",
    "provider/model/tool/web/retrieval",
    ".weslr implication",
    ".weslr read/write implication",
    ".weslr persistence/state implication",
    "persistence/database implication",
    "memory/project mutation implication",
    "cross-user leakage",
    "hidden/private/protected markers",
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
    "no_raw_content_retention",
    "no_weslr_io",
    "no_weslr_read",
    "no_weslr_write",
    "no_weslr_persistence",
    "no_database_writes",
    "no_memory_mutation",
    "no_project_mutation",
    "no_public_claim_authority",
    "no_final_answer_authority",
    "no_discovery_claims",
    "no_proof_claims",
    "no_benchmark_claims",
    "no_score_claims",
    "no_agi_claims",
    "no_public_science_claims",
    "no_hidden_private_protected_markers",
)

_REQUIRED_FIELD_NAMES_V1 = (
    "evidence_intake_id",
    "source_scope",
    "source_kind",
    "source_reference_summary",
    "source_access_status",
    "raw_content_retained",
    "evidence_signal_summary",
    "observed_pattern",
    "known_limitations",
    "missing_context",
    "confidence_posture",
    "calibration_axes_to_apply",
    "reverse_trace_reference",
    "proposed_direction_eligibility",
    "disconfirming_signal",
    "operator_review_need",
    "privacy_sensitivity",
    "safety_sensitivity",
    "promotion_blockers",
    "forbidden_interpretations",
    "authority_status",
    "safe_metadata",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "evidence_intake_id",
    "source_scope",
    "source_kind",
    "source_reference_summary",
    "source_access_status",
    "evidence_signal_summary",
    "observed_pattern",
    "confidence_posture",
    "reverse_trace_reference",
    "proposed_direction_eligibility",
    "operator_review_need",
    "privacy_sensitivity",
    "safety_sensitivity",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "known_limitations",
    "missing_context",
    "calibration_axes_to_apply",
    "disconfirming_signal",
    "promotion_blockers",
    "forbidden_interpretations",
)

_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1 = [
    "this is proven",
    "this is discovered",
    "this is public truth",
    "this is a final answer",
    "this authorizes ingestion",
    "this authorizes runtime",
    "this authorizes provider/tool/web use",
    "this authorizes .weslr access",
    "this authorizes persistence",
]


def allowed_evidence_source_kinds_v1() -> tuple[str, ...]:
    return _ALLOWED_EVIDENCE_SOURCE_KINDS_V1


def allowed_evidence_access_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_EVIDENCE_ACCESS_STATUSES_V1


def allowed_evidence_confidence_postures_v1() -> tuple[str, ...]:
    return _ALLOWED_EVIDENCE_CONFIDENCE_POSTURES_V1


def allowed_proposed_direction_eligibility_v1() -> tuple[str, ...]:
    return _ALLOWED_PROPOSED_DIRECTION_ELIGIBILITY_V1


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    merged.update({key: value for key, value in overrides.items() if value is not None})
    return merged


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_compact_text(item) for item in value if _compact_text(item)]
    if isinstance(value, tuple):
        return [_compact_text(item) for item in value if _compact_text(item)]
    if isinstance(value, set):
        return [_compact_text(item) for item in sorted(value, key=repr) if _compact_text(item)]
    text = _compact_text(value)
    return [text] if text else []


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
    if isinstance(value, (str, bool, int, float)) or value is None:
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


def _default_authority_status() -> dict[str, Any]:
    return {
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
        "hidden_private_protected_authorized": False,
        "cross_user_leakage_authorized": False,
        "public_science_claim_authorized": False,
        "proof_claim_authorized": False,
        "benchmark_claim_authorized": False,
        "agi_claim_authorized": False,
        "automatic_discovery_authorized": False,
        "raw_content_retention_authorized": False,
        "all_authority_flags_false": True,
        "status": "metadata_only",
        "boundary_notes": "metadata-only real findings evidence intake boundary",
    }


def _default_safe_metadata() -> dict[str, Any]:
    return {
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
        "no_raw_content_retention": True,
        "no_weslr_io": True,
        "no_weslr_read": True,
        "no_weslr_write": True,
        "no_weslr_persistence": True,
        "no_database_writes": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_public_claim_authority": True,
        "no_final_answer_authority": True,
        "no_discovery_claims": True,
        "no_proof_claims": True,
        "no_benchmark_claims": True,
        "no_score_claims": True,
        "no_agi_claims": True,
        "no_public_science_claims": True,
        "no_hidden_private_protected_markers": True,
        "evidence_family": HELPER_FAMILY_V1,
        "helper_family": SCHEMA_VERSION_V1,
    }


def _validate_authority_status(authority_status: Any, blocked_labels: list[str]) -> None:
    if not isinstance(authority_status, Mapping):
        blocked_labels.append("missing_authority_status")
        return
    status = {str(key): value for key, value in authority_status.items()}
    for flag in _AUTHORITY_FALSE_FLAGS_V1:
        if status.get(flag) is True:
            blocked_labels.append(f"unsafe_authority_flag:{flag}")
    if status.get("all_authority_flags_false") is not True:
        blocked_labels.append("unsafe_authority_flags")
    if _compact_text(status.get("status")) != "metadata_only":
        blocked_labels.append("unsafe_authority_status")
    if _compact_text(status.get("boundary_notes")) == "":
        blocked_labels.append("missing_authority_boundary_notes")
    if _contains_text_markers(status, _AUTHORITY_TEXT_MARKERS_V1):
        blocked_labels.append("unsafe_authority_text")
    if _contains_text_markers(status, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")


def _validate_safe_metadata(safe_metadata: Any, blocked_labels: list[str]) -> None:
    if not isinstance(safe_metadata, Mapping):
        blocked_labels.append("missing_safe_metadata")
        return
    metadata = {str(key): value for key, value in safe_metadata.items()}
    for flag in _SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1:
        if metadata.get(flag) is not True:
            blocked_labels.append(f"unsafe_safe_metadata_flag:{flag}")
    if _compact_text(metadata.get("evidence_family")) != HELPER_FAMILY_V1:
        blocked_labels.append("unsafe_safe_metadata_evidence_family")
    if _compact_text(metadata.get("helper_family")) != SCHEMA_VERSION_V1:
        blocked_labels.append("unsafe_safe_metadata_helper_family")
    if _contains_text_markers(metadata, _AUTHORITY_TEXT_MARKERS_V1):
        blocked_labels.append("unsafe_safe_metadata_text")
    if _contains_text_markers(metadata, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")


def build_real_findings_evidence_intake_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged = _merge_payload(payload, **overrides)
    built = {
        "evidence_intake_id": _compact_text(merged.get("evidence_intake_id")),
        "source_scope": _compact_text(merged.get("source_scope")),
        "source_kind": _compact_text(merged.get("source_kind")),
        "source_reference_summary": _compact_text(merged.get("source_reference_summary")),
        "source_access_status": _compact_text(merged.get("source_access_status")),
        "raw_content_retained": merged.get("raw_content_retained", False),
        "evidence_signal_summary": _compact_text(merged.get("evidence_signal_summary")),
        "observed_pattern": _compact_text(merged.get("observed_pattern")),
        "known_limitations": _normalize_text_list(merged.get("known_limitations")),
        "missing_context": _normalize_text_list(merged.get("missing_context")),
        "confidence_posture": _compact_text(merged.get("confidence_posture")),
        "calibration_axes_to_apply": _normalize_text_list(merged.get("calibration_axes_to_apply")),
        "reverse_trace_reference": _compact_text(merged.get("reverse_trace_reference")),
        "proposed_direction_eligibility": _compact_text(merged.get("proposed_direction_eligibility")),
        "disconfirming_signal": _normalize_text_list(merged.get("disconfirming_signal")),
        "operator_review_need": _compact_text(merged.get("operator_review_need")),
        "privacy_sensitivity": _compact_text(merged.get("privacy_sensitivity")),
        "safety_sensitivity": _compact_text(merged.get("safety_sensitivity")),
        "promotion_blockers": _normalize_text_list(merged.get("promotion_blockers")),
        "forbidden_interpretations": _normalize_text_list(merged.get("forbidden_interpretations")),
        "authority_status": deepcopy(merged.get("authority_status"))
        if isinstance(merged.get("authority_status"), Mapping)
        else _default_authority_status(),
        "safe_metadata": deepcopy(merged.get("safe_metadata"))
        if isinstance(merged.get("safe_metadata"), Mapping)
        else _default_safe_metadata(),
    }
    if isinstance(built["authority_status"], Mapping):
        built["authority_status"].setdefault("all_authority_flags_false", True)
        built["authority_status"].setdefault("status", "metadata_only")
        built["authority_status"].setdefault(
            "boundary_notes", "metadata-only real findings evidence intake boundary"
        )
    if isinstance(built["safe_metadata"], Mapping):
        built["safe_metadata"].setdefault("evidence_family", HELPER_FAMILY_V1)
        built["safe_metadata"].setdefault("helper_family", SCHEMA_VERSION_V1)
    return built


def validate_real_findings_evidence_intake_packet_v1(packet: Any) -> dict[str, Any]:
    blocked_labels: list[str] = []
    if not isinstance(packet, Mapping):
        blocked_labels.append("invalid_packet_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "validation_posture": "blocked",
            "summary_text": "Blocked real findings evidence intake packet: invalid packet type.",
        }

    raw = packet

    for field in _REQUIRED_FIELD_NAMES_V1:
        if field not in raw:
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_TEXT_FIELDS_V1:
        if _compact_text(raw.get(field)) == "":
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_LIST_FIELDS_V1:
        value = raw.get(field)
        if not isinstance(value, list) or not value:
            blocked_labels.append(f"missing_{field}")
        elif any(_compact_text(item) == "" for item in value):
            blocked_labels.append(f"invalid_{field}")

    source_kind = _compact_text(raw.get("source_kind"))
    if source_kind and source_kind not in _ALLOWED_EVIDENCE_SOURCE_KINDS_V1:
        blocked_labels.append("invalid_source_kind")

    source_access_status = _compact_text(raw.get("source_access_status"))
    if source_access_status and source_access_status not in _ALLOWED_EVIDENCE_ACCESS_STATUSES_V1:
        blocked_labels.append("invalid_source_access_status")

    confidence_posture = _compact_text(raw.get("confidence_posture"))
    if confidence_posture and confidence_posture not in _ALLOWED_EVIDENCE_CONFIDENCE_POSTURES_V1:
        blocked_labels.append("invalid_confidence_posture")

    eligibility = _compact_text(raw.get("proposed_direction_eligibility"))
    if eligibility and eligibility not in _ALLOWED_PROPOSED_DIRECTION_ELIGIBILITY_V1:
        blocked_labels.append("invalid_proposed_direction_eligibility")

    raw_content_retained = raw.get("raw_content_retained")
    if not isinstance(raw_content_retained, bool):
        blocked_labels.append("invalid_raw_content_retained")
    elif raw_content_retained is True:
        authority_status = raw.get("authority_status")
        authorized = isinstance(authority_status, Mapping) and authority_status.get(
            "raw_content_retention_authorized"
        ) is True
        if not authorized:
            blocked_labels.append("raw_content_retained_without_explicit_authorization")

    _validate_authority_status(raw.get("authority_status"), blocked_labels)
    _validate_safe_metadata(raw.get("safe_metadata"), blocked_labels)

    if _compact_text(raw.get("source_scope")) == "":
        blocked_labels.append("missing_source_scope")
    if _compact_text(raw.get("source_reference_summary")) == "":
        blocked_labels.append("missing_source_reference_summary")
    if _compact_text(raw.get("evidence_signal_summary")) == "":
        blocked_labels.append("missing_evidence_signal_summary")
    if _compact_text(raw.get("observed_pattern")) == "":
        blocked_labels.append("missing_observed_pattern")
    if _compact_text(raw.get("reverse_trace_reference")) == "":
        blocked_labels.append("missing_reverse_trace_reference")
    if _compact_text(raw.get("operator_review_need")) == "":
        blocked_labels.append("missing_operator_review_need")
    if _compact_text(raw.get("privacy_sensitivity")) == "":
        blocked_labels.append("missing_privacy_sensitivity")
    if _compact_text(raw.get("safety_sensitivity")) == "":
        blocked_labels.append("missing_safety_sensitivity")

    if _first_non_json_safe_path(raw) is not None:
        blocked_labels.append("non_json_safe_output")

    narrative_fields = (
        "source_reference_summary",
        "evidence_signal_summary",
        "observed_pattern",
        "known_limitations",
        "missing_context",
        "disconfirming_signal",
        "promotion_blockers",
        "forbidden_interpretations",
    )
    if any(_contains_text_markers(raw.get(field), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1) for field in narrative_fields):
        blocked_labels.append("forbidden_hidden_private_protected_marker")

    if _contains_text_markers(raw.get("authority_status"), _AUTHORITY_TEXT_MARKERS_V1):
        blocked_labels.append("unsafe_authority_text")
    if _contains_text_markers(raw.get("safe_metadata"), _AUTHORITY_TEXT_MARKERS_V1):
        blocked_labels.append("unsafe_safe_metadata_text")
    if _contains_text_markers(raw.get("authority_status"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")
    if _contains_text_markers(raw.get("safe_metadata"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")

    valid = not blocked_labels
    summary = (
        "Valid real findings evidence intake packet."
        if valid
        else "Blocked real findings evidence intake packet: metadata or authority checks failed."
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": blocked_labels,
        "validation_posture": "valid" if valid else "blocked",
        "summary_text": summary,
    }


def summarize_real_findings_evidence_intake_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    validation = validate_real_findings_evidence_intake_packet_v1(raw) if isinstance(raw, Mapping) else {}
    known_limitations = raw.get("known_limitations") if isinstance(raw.get("known_limitations"), list) else []
    missing_context = raw.get("missing_context") if isinstance(raw.get("missing_context"), list) else []
    disconfirming_signal = raw.get("disconfirming_signal") if isinstance(raw.get("disconfirming_signal"), list) else []
    promotion_blockers = raw.get("promotion_blockers") if isinstance(raw.get("promotion_blockers"), list) else []
    calibration_axes = raw.get("calibration_axes_to_apply") if isinstance(raw.get("calibration_axes_to_apply"), list) else []
    return {
        "evidence_intake_id": _compact_text(raw.get("evidence_intake_id"), "unknown_evidence_intake"),
        "source_kind": _compact_text(raw.get("source_kind"), "unknown_source_kind"),
        "source_access_status": _compact_text(raw.get("source_access_status"), "unknown_access_status"),
        "confidence_posture": _compact_text(raw.get("confidence_posture"), "unknown_confidence_posture"),
        "proposed_direction_eligibility": _compact_text(
            raw.get("proposed_direction_eligibility"), "unknown_proposed_direction_eligibility"
        ),
        "raw_content_retained": raw.get("raw_content_retained") if isinstance(raw.get("raw_content_retained"), bool) else False,
        "calibration_axes_count": len(calibration_axes),
        "missing_context_visible": list(missing_context),
        "disconfirming_signal_visible": list(disconfirming_signal),
        "promotion_blockers_count": len(promotion_blockers),
        "known_limitations_visible": list(known_limitations),
        "authority_status": _json_safe(
            raw.get("authority_status") if isinstance(raw.get("authority_status"), Mapping) else _default_authority_status()
        ),
        "validation_posture": _compact_text(validation.get("validation_posture"), "unknown"),
        "summary_text": (
            f"Real findings evidence intake {_compact_text(raw.get('evidence_intake_id'), 'unknown_evidence_intake')}: "
            f"kind {_compact_text(raw.get('source_kind'), 'unknown_source_kind')}, "
            f"access {_compact_text(raw.get('source_access_status'), 'unknown_access_status')}, "
            f"confidence {_compact_text(raw.get('confidence_posture'), 'unknown_confidence_posture')}, "
            f"eligibility {_compact_text(raw.get('proposed_direction_eligibility'), 'unknown_proposed_direction_eligibility')}, "
            f"calibration axes {len(calibration_axes)}, "
            f"raw retained {raw.get('raw_content_retained') if isinstance(raw.get('raw_content_retained'), bool) else False}."
        ),
    }


def to_real_findings_evidence_intake_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def build_initial_real_findings_evidence_intake_examples_v1() -> list[dict[str, Any]]:
    return [
        build_real_findings_evidence_intake_packet_v1(
            {
                "evidence_intake_id": "owner_observed_repeating_signal_intake",
                "source_scope": "owner-supplied observation metadata only",
                "source_kind": "owner_supplied_observation",
                "source_reference_summary": "Repeated owner-supplied observations show a bounded signal that deserves internal pressure testing, not promotion.",
                "source_access_status": "metadata_only",
                "raw_content_retained": False,
                "evidence_signal_summary": "A repeating signal persists across owner-supplied observations, but it remains bounded and unpromoted.",
                "observed_pattern": "The signal repeats with enough structure to justify a pressure-test style follow-up.",
                "known_limitations": [
                    "No independent confirmation yet",
                    "No falsifying test yet",
                    "No broader context archive yet",
                ],
                "missing_context": [
                    "Independent confirmation",
                    "Counterexample or falsifying test",
                    "Longer history of the observation",
                ],
                "confidence_posture": "strong_signal_requires_pressure_test",
                "calibration_axes_to_apply": [
                    "signal_detection_calibration",
                    "popper_falsification_calibration",
                    "bayesian_calibration",
                    "reverse_calibration_backcasting",
                ],
                "reverse_trace_reference": "pulsar_reverse_calibration_trace",
                "proposed_direction_eligibility": "eligible_after_pressure_test",
                "disconfirming_signal": [
                    "A noisy one-off artifact would weaken the signal.",
                    "An unrelated observation pattern would argue against promotion.",
                ],
                "operator_review_need": "Operator review is needed before any higher-authority step.",
                "privacy_sensitivity": "owner observation, not public claim",
                "safety_sensitivity": "bounded metadata-only intake",
                "promotion_blockers": [
                    "Missing independent confirmation",
                    "No falsifying test yet",
                    "No operator review for higher authority",
                ],
                "forbidden_interpretations": list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1),
                "authority_status": _default_authority_status(),
                "safe_metadata": _default_safe_metadata(),
            }
        )
    ]
