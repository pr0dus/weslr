"""WESLR Calibrated Proposed Directions V1.

Deterministic, metadata-only helpers for turning calibrated internal evidence
into proposed next-direction packets without authorizing findings, discovery,
proof, public claims, ingestion, runtime, or final-answer authority.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "calibrated_proposed_directions_v1"
HELPER_FAMILY_V1 = "calibrated_proposed_directions"

_ALLOWED_DIRECTION_STATUSES_V1 = (
    "candidate_direction",
    "needs_probe",
    "needs_pressure_test",
    "needs_calibration",
    "needs_evidence",
    "watch",
    "archive",
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
    "database_write_authority",
    "database_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "hidden_private_protected_authorized",
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
    ".weslr implication",
    ".weslr read/write implication",
    ".weslr persistence/state implication",
    "persistence/database implication",
    "memory/project mutation implication",
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
    "direction_id",
    "source_signal_summary",
    "source_scope",
    "proposed_direction_summary",
    "why_this_direction",
    "calibration_axes_used",
    "reverse_trace_reference",
    "expected_next_step",
    "direction_status",
    "supporting_evidence_summary",
    "missing_evidence",
    "disconfirming_signal",
    "risk_of_overclaim",
    "risk_of_underexploration",
    "operator_review_need",
    "promotion_blockers",
    "forbidden_interpretations",
    "authority_status",
    "safe_metadata",
)

_REQUIRED_PACKET_TEXT_FIELDS_V1 = (
    "direction_id",
    "source_signal_summary",
    "source_scope",
    "proposed_direction_summary",
    "why_this_direction",
    "reverse_trace_reference",
    "expected_next_step",
    "direction_status",
    "supporting_evidence_summary",
    "risk_of_overclaim",
    "risk_of_underexploration",
    "operator_review_need",
)

_REQUIRED_PACKET_LIST_FIELDS_V1 = (
    "calibration_axes_used",
    "missing_evidence",
    "disconfirming_signal",
    "promotion_blockers",
    "forbidden_interpretations",
)

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
    "database_write_authority": False,
    "database_write_authorized": False,
    "memory_mutation_authorized": False,
    "project_mutation_authorized": False,
    "hidden_private_protected_authorized": False,
    "public_science_claim_authorized": False,
    "proof_claim_authorized": False,
    "benchmark_claim_authorized": False,
    "agi_claim_authorized": False,
    "automatic_discovery_authorized": False,
    "all_authority_flags_false": True,
    "status": "metadata_only",
    "boundary_notes": "metadata-only calibrated proposed direction boundary",
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
    "no_public_claim_authority": True,
    "no_final_answer_authority": True,
    "no_discovery_claims": True,
    "no_proof_claims": True,
    "no_benchmark_claims": True,
    "no_score_claims": True,
    "no_agi_claims": True,
    "no_public_science_claims": True,
    "no_hidden_private_protected_markers": True,
    "direction_family": HELPER_FAMILY_V1,
    "helper_family": SCHEMA_VERSION_V1,
}

_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1 = [
    "this is proven",
    "this is discovered",
    "this is public truth",
    "this is a final answer",
    "this authorizes ingestion",
    "this authorizes runtime",
    "this authorizes provider/tool/web use",
    "this authorizes .weslr access",
]


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


def allowed_calibrated_direction_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_DIRECTION_STATUSES_V1


def _default_authority_status() -> dict[str, Any]:
    return deepcopy(_DEFAULT_AUTHORITY_STATUS_V1)


def _default_safe_metadata() -> dict[str, Any]:
    return deepcopy(_DEFAULT_SAFE_METADATA_V1)


def build_calibrated_proposed_direction_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    authority_status = data.get("authority_status")
    safe_metadata = data.get("safe_metadata")
    built = {
        "schema_version": SCHEMA_VERSION_V1,
        "direction_id": _compact_text(data.get("direction_id")),
        "source_signal_summary": _compact_text(data.get("source_signal_summary")),
        "source_scope": _compact_text(data.get("source_scope")),
        "proposed_direction_summary": _compact_text(data.get("proposed_direction_summary")),
        "why_this_direction": _compact_text(data.get("why_this_direction")),
        "calibration_axes_used": _normalize_text_list(data.get("calibration_axes_used")),
        "reverse_trace_reference": _compact_text(data.get("reverse_trace_reference")),
        "expected_next_step": _compact_text(data.get("expected_next_step")),
        "direction_status": _compact_text(data.get("direction_status")),
        "supporting_evidence_summary": _compact_text(data.get("supporting_evidence_summary")),
        "missing_evidence": _normalize_text_list(data.get("missing_evidence")),
        "disconfirming_signal": _normalize_text_list(data.get("disconfirming_signal")),
        "risk_of_overclaim": _compact_text(data.get("risk_of_overclaim")),
        "risk_of_underexploration": _compact_text(data.get("risk_of_underexploration")),
        "operator_review_need": _compact_text(data.get("operator_review_need")),
        "promotion_blockers": _normalize_text_list(data.get("promotion_blockers")),
        "forbidden_interpretations": _normalize_text_list(data.get("forbidden_interpretations")),
        "authority_status": _default_authority_status() if authority_status is None else _json_safe(authority_status),
        "safe_metadata": _default_safe_metadata() if safe_metadata is None else _json_safe(safe_metadata),
    }
    if isinstance(built["authority_status"], Mapping):
        built["authority_status"].setdefault("status", "metadata_only")
        built["authority_status"].setdefault(
            "boundary_notes", "metadata-only calibrated proposed direction boundary"
        )
        built["authority_status"].setdefault("all_authority_flags_false", True)
    if isinstance(built["safe_metadata"], Mapping):
        built["safe_metadata"].setdefault("direction_family", HELPER_FAMILY_V1)
        built["safe_metadata"].setdefault("helper_family", SCHEMA_VERSION_V1)
    return built


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
    if _compact_text(metadata.get("direction_family")) != HELPER_FAMILY_V1:
        blocked_labels.append("unsafe_safe_metadata_direction_family")
    if _compact_text(metadata.get("helper_family")) != SCHEMA_VERSION_V1:
        blocked_labels.append("unsafe_safe_metadata_helper_family")
    if _contains_text_markers(metadata, _AUTHORITY_TEXT_MARKERS_V1):
        blocked_labels.append("unsafe_safe_metadata_text")
    if _contains_text_markers(metadata, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")


def validate_calibrated_proposed_direction_v1(packet: Any) -> dict[str, Any]:
    blocked_labels: list[str] = []
    if not isinstance(packet, Mapping):
        blocked_labels.append("invalid_packet_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "validation_posture": "blocked",
            "summary_text": "Blocked calibrated proposed direction packet: invalid packet type.",
        }

    raw = packet

    for field in _REQUIRED_FIELD_NAMES_V1:
        if field not in raw:
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_PACKET_TEXT_FIELDS_V1:
        if _compact_text(raw.get(field)) == "":
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_PACKET_LIST_FIELDS_V1:
        value = raw.get(field)
        if not isinstance(value, list) or not value:
            blocked_labels.append(f"missing_{field}")
        elif any(_compact_text(item) == "" for item in value):
            blocked_labels.append(f"invalid_{field}")

    direction_status = _compact_text(raw.get("direction_status"))
    if direction_status and direction_status not in _ALLOWED_DIRECTION_STATUSES_V1:
        blocked_labels.append("invalid_direction_status")

    _validate_authority_status(raw.get("authority_status"), blocked_labels)
    _validate_safe_metadata(raw.get("safe_metadata"), blocked_labels)

    if _compact_text(raw.get("reverse_trace_reference")) == "":
        blocked_labels.append("missing_reverse_trace_reference")

    if _compact_text(raw.get("expected_next_step")) == "":
        blocked_labels.append("missing_expected_next_step")

    if _compact_text(raw.get("disconfirming_signal")) == "":
        blocked_labels.append("missing_disconfirming_signal")

    if _compact_text(raw.get("forbidden_interpretations")) == "":
        blocked_labels.append("missing_forbidden_interpretations")

    if _first_non_json_safe_path(raw) is not None:
        blocked_labels.append("non_json_safe_output")

    # Canonical fail-closed checks for explicit public-authority language.
    if _contains_text_markers(raw.get("authority_status"), _AUTHORITY_TEXT_MARKERS_V1):
        blocked_labels.append("unsafe_authority_text")
    if _contains_text_markers(raw.get("safe_metadata"), _AUTHORITY_TEXT_MARKERS_V1):
        blocked_labels.append("unsafe_safe_metadata_text")
    if _contains_text_markers(raw.get("authority_status"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")
    if _contains_text_markers(raw.get("safe_metadata"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")
    if _contains_text_markers(raw, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")

    valid = not blocked_labels
    summary = "Valid calibrated proposed direction packet." if valid else "Blocked calibrated proposed direction packet: metadata or authority checks failed."
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": blocked_labels,
        "validation_posture": "valid" if valid else "blocked",
        "summary_text": summary,
    }


def summarize_calibrated_proposed_direction_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    validation = validate_calibrated_proposed_direction_v1(raw) if isinstance(raw, Mapping) else {}
    missing_evidence = raw.get("missing_evidence") if isinstance(raw.get("missing_evidence"), list) else []
    disconfirming_signal = raw.get("disconfirming_signal") if isinstance(raw.get("disconfirming_signal"), list) else []
    promotion_blockers = raw.get("promotion_blockers") if isinstance(raw.get("promotion_blockers"), list) else []
    return {
        "direction_id": _compact_text(raw.get("direction_id"), "unknown_direction"),
        "direction_status": _compact_text(raw.get("direction_status"), "unknown_status"),
        "expected_next_step": _compact_text(raw.get("expected_next_step"), "unknown"),
        "calibration_axes_used": list(raw.get("calibration_axes_used")) if isinstance(raw.get("calibration_axes_used"), list) else [],
        "missing_evidence_visible": list(missing_evidence),
        "disconfirming_signal_visible": list(disconfirming_signal),
        "promotion_blockers_count": len(promotion_blockers),
        "authority_status": _json_safe(
            raw.get("authority_status") if isinstance(raw.get("authority_status"), Mapping) else _default_authority_status()
        ),
        "validation_posture": _compact_text(validation.get("validation_posture"), "unknown"),
        "summary_text": (
            f"Calibrated proposed direction {_compact_text(raw.get('direction_id'), 'unknown_direction')}: "
            f"status {_compact_text(raw.get('direction_status'), 'unknown_status')}, "
            f"next step {_compact_text(raw.get('expected_next_step'), 'unknown')}, "
            f"blockers {len(promotion_blockers)}."
        ),
    }


def to_calibrated_proposed_direction_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def build_initial_calibrated_proposed_direction_examples_v1() -> list[dict[str, Any]]:
    return [
        build_calibrated_proposed_direction_v1(
            {
                "direction_id": "pulsar_signal_followup_direction",
                "source_signal_summary": "A strange repeated signal is observed in the historical record and deserves a bounded follow-up.",
                "source_scope": "historical signal metadata only",
                "proposed_direction_summary": "Continue an internal probe and pressure-test style follow-up rather than claim, archive, or finalize.",
                "why_this_direction": "The signal repeats, but the evidence is still thin enough that pressure-testing is safer than promotion.",
                "calibration_axes_used": [
                    "reverse_calibration_backcasting",
                    "signal_detection_calibration",
                    "popper_falsification_calibration",
                    "bayesian_calibration",
                    "capability_suppression_boundary",
                ],
                "reverse_trace_reference": "pulsar_reverse_calibration_trace",
                "expected_next_step": "pressure_test",
                "direction_status": "needs_pressure_test",
                "supporting_evidence_summary": "The repeated signal is structured enough to justify a bounded internal follow-up.",
                "missing_evidence": [
                    "No independent confirmation yet",
                    "No disconfirming counter-test has been run yet",
                ],
                "disconfirming_signal": [
                    "A one-off artifact or noisy coincidence would weaken the follow-up direction.",
                ],
                "risk_of_overclaim": "High overclaim risk if the repeated signal is promoted to discovery, proof, or truth too early.",
                "risk_of_underexploration": "High underexploration risk if the signal is archived before a probe or pressure test has a chance to run.",
                "operator_review_need": "Operator review is needed if any safety or authority signal changes.",
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
