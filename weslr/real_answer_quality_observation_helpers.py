"""Metadata-only helpers for WESLR real answer quality observation boundary v1.

This module is intentionally pure, deterministic, and fail-closed.
It converts approved synthetic/redacted observation metadata into source
lineage, observation records, review packets, validation results, and JSON-safe
summaries.

It does not perform file I/O, network I/O, subprocess execution, runtime/chat
wiring, live response routing, provider/model/search/advisor calls, dot-weslr
IO, or any official scoring work.
"""

from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

from weslr.response_fit_engine_helpers import (
    DENIED_AUTHORITY_FLAGS_V1 as RESPONSE_FIT_DENIED_AUTHORITY_FLAGS_V1,
    HUMAN_SITUATION_SIGNALS_V1 as RESPONSE_FIT_HUMAN_SITUATION_SIGNALS_V1,
    MISMATCH_FAMILIES_V1 as RESPONSE_FIT_MISMATCH_FAMILIES_V1,
    to_response_fit_json_safe_v1,
)

HELPER_TYPE_V1 = "weslr_real_answer_quality_observation_helpers_v1"
BOUNDARY_TYPE_V1 = "real_answer_quality_observation_boundary_v1"
SOURCE_LINEAGE_TYPE_V1 = "real_answer_quality_source_lineage_v1"
OBSERVATION_RECORD_TYPE_V1 = "real_answer_quality_observation_record_v1"
REVIEW_PACKET_TYPE_V1 = "real_answer_quality_review_packet_v1"
SUMMARY_TYPE_V1 = "real_answer_quality_observation_summary_v1"

ALLOWED_SOURCE_CLASSES_V1 = {
    "public_open",
    "synthetic_weslr_created",
}

RESULT_LABELS_V1 = {
    "answer_quality_fit",
    "answer_quality_partial",
    "answer_quality_mismatch",
    "answer_quality_inconclusive",
    "blocked_by_privacy_boundary",
    "blocked_by_runtime_boundary",
    "blocked_by_source_governance",
    "needs_operator_review",
}

OBSERVATION_DIMENSIONS_V1 = {
    "truth_kernel_preservation",
    "response_fit",
    "specificity_non_cannedness",
    "human_situation_fit",
    "continuity_retention",
    "correction_retention",
    "uncertainty_honesty",
    "evidence_boundary_honesty",
    "governance_boundary_respect",
    "context_pressure_resilience",
    "actionability",
    "emotional_pressure_handling",
    "human_perceived_ai_tone",
    "over_refusal_or_under_refusal",
    "answer_shape_quality",
}

HUMAN_PERCEIVED_AI_SIGNALS_V1 = {
    "generic_response",
    "template_like_structure",
    "fake_empathy",
    "missed_emotional_priority",
    "too_much_explanation",
    "wrong_expertise_level",
    "ignored_correction",
    "lost_thread",
    "overconfident_uncertainty",
    "mechanical_refusal",
    "poor_timing",
    "not_answering_the_person",
    "polished_but_situationally_wrong",
}

BLOCKED_LABELS_V1 = {
    "raw_answer_provided",
    "raw_prompt_provided",
    "raw_response_text_provided",
    "raw_transcript_provided",
    "raw_context_provided",
    "raw_private_content_requested",
    "raw_persistence_requested",
    "dot_weslr_requested",
    "private_memory_requested",
    "live_user_content_requested",
    "provider_model_output_requested",
    "hidden_material_requested",
    "benchmark_material_requested",
    "final_answer_authority_requested",
    "public_live_authority_requested",
    "public_ux_authority_requested",
    "voice_authority_requested",
    "runtime_authority_requested",
    "live_runtime_authority_requested",
    "model_call_authority_requested",
    "search_call_authority_requested",
    "advisor_call_authority_requested",
    "official_claim_requested",
    "turing_claim_requested",
    "intelligence_claim_requested",
    "certification_claim_requested",
    "unknown_source_class",
    "unknown_dimension",
    "unknown_signal_label",
    "unknown_mismatch_family",
    "unknown_fit_result_label",
    "unknown_authority_flag",
    "missing_source_lineage",
    "missing_observation_id",
    "missing_run_id",
    "missing_source_case_id",
    "missing_answer_sample_ref",
    "missing_truth_kernel_id",
    "missing_human_situation_frame_id",
    "missing_answer_shape_id",
    "missing_fit_result_label",
    "missing_quality_dimensions",
    "missing_blocked_labels",
    "missing_reviewer_notes",
    "missing_recommended_surface",
    "missing_operator_review_required",
    "raw_answer_stored_true",
    "registry_not_approved",
}

SENSITIVE_KEY_HINTS_V1 = (
    "raw_answer",
    "raw_prompt",
    "prompt",
    "raw_response",
    "response_text",
    "raw_transcript",
    "transcript_text",
    "raw_context",
    "context_text",
    "live_user",
    "private_memory",
    "private_data",
    "private_text",
    "hidden_material",
    "benchmark_material",
    "provider_model_output",
    "final_answer",
    "dot_weslr",
    "voice",
    "public_live_authority",
    "runtime_authority",
    "official_claim",
    "turing_claim",
    "intelligence_claim",
    "certification_claim",
    "manipulation",
    "fake_empathy",
    "template",
    "stereotype",
    "persona",
    "roleplay",
)

FORBIDDEN_MARKERS_V1 = (
    ".weslr",
    "private memory",
    "private_memory",
    "private data",
    "live user",
    "live_user",
    "live chat",
    "hidden",
    "semi-private",
    "semi private",
    "private",
    "unapproved",
    "provider output",
    "model output",
    "provider_model_output",
    "transcript",
    "final answer",
    "final_answer",
    "runtime",
    "public live",
    "voice",
    "official claim",
    "turing",
    "intelligence",
    "certification",
)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        values = list(value.keys())
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = _safe_str(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _unique_sorted(labels: Iterable[str]) -> list[str]:
    if isinstance(labels, (str, bytes)):
        items = [labels]
    else:
        items = list(labels)
    return sorted(set(_safe_list(items)))


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _redact_key(key: str, value: Any) -> Any:
    key_text = _safe_str(key).lower()
    if key_text == "raw_answer_stored":
        return _json_safe(value)
    if any(hint in key_text for hint in SENSITIVE_KEY_HINTS_V1):
        return f"[redacted:{_safe_str(key) or 'sensitive'}]"
    return _json_safe(value)


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _redact_key(str(key), val)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        safe_items = [_json_safe(item) for item in value]
        return sorted(safe_items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return f"[redacted:{type(value).__name__}]"


def to_real_answer_quality_observation_json_safe_v1(value: Any) -> Any:
    """Convert real-answer-quality observation structures to deterministic JSON-safe data."""

    return _json_safe(value)


def _collect_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            strings.extend(_collect_strings(key))
            strings.extend(_collect_strings(item))
        return strings
    if isinstance(value, (list, tuple, set)):
        for item in value:
            strings.extend(_collect_strings(item))
        return strings
    text = _safe_str(value)
    if text:
        strings.append(text)
    return strings


def _contains_forbidden_marker(value: Any) -> bool:
    for text in _collect_strings(value):
        lowered = text.lower()
        for marker in FORBIDDEN_MARKERS_V1:
            if marker in lowered:
                return True
    return False


def _list_unknown_labels(labels: Iterable[str], allowed: set[str]) -> list[str]:
    return [label for label in _safe_list(labels) if label not in allowed]


def build_real_answer_quality_source_lineage_v1(
    *,
    source_case_id: str,
    run_id: str,
    source_class: str,
    registry_approved: bool,
    adapter_ref: str,
    commit: str,
    redaction_status: str,
) -> dict[str, Any]:
    """Build a metadata-only source lineage record."""

    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "source_lineage_type": SOURCE_LINEAGE_TYPE_V1,
        "source_case_id": _safe_str(source_case_id),
        "run_id": _safe_str(run_id),
        "source_class": _safe_str(source_class),
        "registry_approved": _safe_bool(registry_approved),
        "adapter_ref": _safe_str(adapter_ref),
        "commit": _safe_str(commit),
        "redaction_status": _safe_str(redaction_status),
        "metadata_only": True,
        "internal_only": True,
        "raw_answer_stored": False,
    }
    return to_real_answer_quality_observation_json_safe_v1(record)


def build_real_answer_quality_observation_record_v1(
    *,
    observation_id: str,
    run_id: str,
    source_case_id: str,
    answer_sample_ref: str,
    raw_answer_stored: bool = False,
    redaction_status: str,
    truth_kernel_id: str,
    human_situation_frame_id: str,
    answer_shape_id: str,
    fit_result_label: str,
    mismatch_families: Iterable[str] | None = None,
    quality_dimensions: Iterable[str] | None = None,
    blocked_labels: Iterable[str] | None = None,
    reviewer_notes_metadata_only: str = "",
    recommended_existing_surface: str = "",
    operator_review_required: bool = True,
    source_lineage: Mapping[str, Any] | None = None,
    human_perceived_ai_signals: Iterable[str] | None = None,
    **extra_metadata: Any,
) -> dict[str, Any]:
    """Build a metadata-only real-answer-quality observation record."""

    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_record_type": OBSERVATION_RECORD_TYPE_V1,
        "observation_id": _safe_str(observation_id),
        "run_id": _safe_str(run_id),
        "source_case_id": _safe_str(source_case_id),
        "answer_sample_ref": _safe_str(answer_sample_ref),
        "raw_answer_stored": False,
        "redaction_status": _safe_str(redaction_status),
        "truth_kernel_id": _safe_str(truth_kernel_id),
        "human_situation_frame_id": _safe_str(human_situation_frame_id),
        "answer_shape_id": _safe_str(answer_shape_id),
        "fit_result_label": _safe_str(fit_result_label),
        "mismatch_families": _unique_sorted(mismatch_families or []),
        "quality_dimensions": _unique_sorted(quality_dimensions or []),
        "blocked_labels": _unique_sorted(blocked_labels or []),
        "reviewer_notes_metadata_only": _safe_str(reviewer_notes_metadata_only),
        "recommended_existing_surface": _safe_str(recommended_existing_surface),
        "operator_review_required": _safe_bool(operator_review_required),
        "source_lineage": to_real_answer_quality_observation_json_safe_v1(source_lineage or {}),
        "human_perceived_ai_signals": _unique_sorted(human_perceived_ai_signals or []),
        "metadata_only": True,
        "internal_only": True,
    }
    if extra_metadata:
        record.update(extra_metadata)
    record["raw_answer_stored"] = False
    record["metadata_only"] = True
    record["internal_only"] = True
    return to_real_answer_quality_observation_json_safe_v1(record)


def _check_result_label(label: str) -> list[str]:
    return [] if label in RESULT_LABELS_V1 else ["unknown_fit_result_label"]


def _check_quality_dimensions(dims: Iterable[str]) -> list[str]:
    unknown = _list_unknown_labels(dims, OBSERVATION_DIMENSIONS_V1)
    return ["unknown_dimension"] if unknown else []


def _check_signals(signals: Iterable[str]) -> list[str]:
    unknown = _list_unknown_labels(signals, HUMAN_PERCEIVED_AI_SIGNALS_V1)
    return ["unknown_signal_label"] if unknown else []


def _check_mismatch_families(families: Iterable[str]) -> list[str]:
    unknown = _list_unknown_labels(families, RESPONSE_FIT_MISMATCH_FAMILIES_V1)
    return ["unknown_mismatch_family"] if unknown else []


def _check_source_class(source_class: str) -> list[str]:
    if not source_class:
        return ["unknown_source_class"]
    if source_class not in ALLOWED_SOURCE_CLASSES_V1:
        return ["unknown_source_class"]
    return []


def _collect_validation_markers(record: Mapping[str, Any]) -> list[str]:
    blocked_labels: list[str] = []

    source_lineage = _as_mapping(record.get("source_lineage"))
    source_class = _safe_str(source_lineage.get("source_class"))
    registry_approved = _safe_bool(source_lineage.get("registry_approved"))

    blocked_labels.extend(_check_source_class(source_class))
    if source_lineage and not registry_approved:
        blocked_labels.append("registry_not_approved")
    if not source_lineage:
        blocked_labels.append("missing_source_lineage")

    if not _safe_str(record.get("observation_id")):
        blocked_labels.append("missing_observation_id")
    if not _safe_str(record.get("run_id")):
        blocked_labels.append("missing_run_id")
    if not _safe_str(record.get("source_case_id")):
        blocked_labels.append("missing_source_case_id")
    if not _safe_str(record.get("answer_sample_ref")):
        blocked_labels.append("missing_answer_sample_ref")
    if not _safe_str(record.get("truth_kernel_id")):
        blocked_labels.append("missing_truth_kernel_id")
    if not _safe_str(record.get("human_situation_frame_id")):
        blocked_labels.append("missing_human_situation_frame_id")
    if not _safe_str(record.get("answer_shape_id")):
        blocked_labels.append("missing_answer_shape_id")
    if not _safe_str(record.get("fit_result_label")):
        blocked_labels.append("missing_fit_result_label")
    if not _safe_list(record.get("quality_dimensions")):
        blocked_labels.append("missing_quality_dimensions")
    if _safe_str(record.get("reviewer_notes_metadata_only")) == "" and record.get("reviewer_notes_metadata_only") is None:
        blocked_labels.append("missing_reviewer_notes")
    if not _safe_str(record.get("recommended_existing_surface")):
        blocked_labels.append("missing_recommended_surface")
    if record.get("operator_review_required") is None:
        blocked_labels.append("missing_operator_review_required")
    if _safe_bool(record.get("raw_answer_stored")):
        blocked_labels.append("raw_answer_stored_true")

    blocked_labels.extend(_check_result_label(_safe_str(record.get("fit_result_label"))))
    blocked_labels.extend(_check_quality_dimensions(_safe_list(record.get("quality_dimensions"))))
    blocked_labels.extend(_check_mismatch_families(_safe_list(record.get("mismatch_families"))))

    unknown_blocked_labels = _list_unknown_labels(_safe_list(record.get("blocked_labels")), BLOCKED_LABELS_V1)
    if unknown_blocked_labels:
        blocked_labels.append("unknown_blocked_label")

    signals = _safe_list(record.get("human_perceived_ai_signals") or [])
    if signals:
        blocked_labels.extend(_check_signals(signals))

    # Raw/private/live/authority markers in any provided metadata.
    if _contains_forbidden_marker(record):
        if _contains_forbidden_marker(record.get("answer_sample_ref")) or _contains_forbidden_marker(record.get("reviewer_notes_metadata_only")) or _contains_forbidden_marker(record.get("recommended_existing_surface")):
            blocked_labels.append("raw_answer_provided")
        if _contains_forbidden_marker(source_lineage):
            if source_class and source_class not in ALLOWED_SOURCE_CLASSES_V1:
                blocked_labels.append("unknown_source_class")

    # Explicit marker fields and authority flags.
    for key in (
        "raw_private_content_requested",
        "raw_persistence_requested",
        "dot_weslr_requested",
        "private_memory_requested",
        "live_user_content_requested",
        "provider_model_output_requested",
        "hidden_material_requested",
        "benchmark_material_requested",
        "final_answer_authority_requested",
        "public_live_authority_requested",
        "public_ux_authority_requested",
        "voice_authority_requested",
        "runtime_authority_requested",
        "live_runtime_authority_requested",
        "model_call_authority_requested",
        "search_call_authority_requested",
        "advisor_call_authority_requested",
        "official_claim_requested",
        "turing_claim_requested",
        "intelligence_claim_requested",
        "certification_claim_requested",
        "unknown_authority_flag",
    ):
        if _safe_bool(record.get(key)):
            blocked_labels.append(key)

    for key in RESPONSE_FIT_DENIED_AUTHORITY_FLAGS_V1:
        if _safe_bool(record.get(key)):
            blocked_labels.append("unknown_authority_flag")
            break

    # Dedicated raw/transcript/private blocks derived from string fields.
    if _contains_forbidden_marker(record.get("answer_sample_ref")):
        blocked_labels.append("raw_answer_provided")
    if _contains_forbidden_marker(record.get("reviewer_notes_metadata_only")):
        blocked_labels.append("raw_answer_provided")
    if _contains_forbidden_marker(source_lineage):
        blocked_labels.append("source_registry_missing")

    blocked_labels.extend(
        label
        for label, present in (
            ("raw_answer_provided", _safe_str(record.get("raw_answer_text")) != ""),
            ("raw_prompt_provided", _safe_str(record.get("raw_prompt")) != ""),
            ("raw_response_text_provided", _safe_str(record.get("raw_response_text")) != ""),
            ("raw_transcript_provided", _safe_str(record.get("raw_transcript")) != ""),
            ("raw_context_provided", _safe_str(record.get("raw_context")) != ""),
            ("private_memory_requested", _safe_bool(record.get("private_memory_requested"))),
        )
        if present
    )

    return _unique_sorted(blocked_labels)


def _collect_denied_authority_flags(record: Mapping[str, Any]) -> list[str]:
    source_lineage = _as_mapping(record.get("source_lineage"))
    flags: list[str] = []
    for key in RESPONSE_FIT_DENIED_AUTHORITY_FLAGS_V1:
        if _safe_bool(record.get(key)) or _safe_bool(source_lineage.get(key)):
            flags.append(key)
    return _unique_sorted(flags)


def validate_real_answer_quality_observation_record_v1(
    observation_item: Mapping[str, Any] | None = None,
    source_lineage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an observation record and fail closed on unsupported input."""

    record = dict(_as_mapping(observation_item))
    if source_lineage is not None:
        record["source_lineage"] = _as_mapping(source_lineage)
    normalized = to_real_answer_quality_observation_json_safe_v1(record)
    if not isinstance(normalized, dict):
        normalized = {}

    blocked_labels = _collect_validation_markers(normalized)
    denied_authority_flags = _collect_denied_authority_flags(normalized)

    valid = not blocked_labels
    blocked = not valid

    fit_result_label = _safe_str(normalized.get("fit_result_label") or "")
    if blocked_labels:
        if any(label in blocked_labels for label in ("raw_answer_provided", "raw_prompt_provided", "raw_response_text_provided", "raw_transcript_provided", "raw_context_provided", "raw_private_content_requested", "private_memory_requested", "raw_answer_stored_true")):
            fit_result_label = "blocked_by_privacy_boundary"
        elif any(label in blocked_labels for label in ("raw_private_content_requested", "raw_persistence_requested", "dot_weslr_requested", "live_user_content_requested", "provider_model_output_requested", "hidden_material_requested", "benchmark_material_requested", "final_answer_authority_requested", "public_live_authority_requested", "public_ux_authority_requested", "voice_authority_requested", "runtime_authority_requested", "live_runtime_authority_requested", "model_call_authority_requested", "search_call_authority_requested", "advisor_call_authority_requested", "official_claim_requested", "turing_claim_requested", "intelligence_claim_requested", "certification_claim_requested", "unknown_authority_flag", "raw_answer_stored_true")):
            fit_result_label = "blocked_by_runtime_boundary"
        elif any(label in blocked_labels for label in ("unknown_source_class", "registry_not_approved", "source_registry_missing")):
            fit_result_label = "blocked_by_source_governance"
        else:
            fit_result_label = "needs_operator_review"
    elif not fit_result_label:
        fit_result_label = "answer_quality_fit"

    quality_dimensions = _safe_list(normalized.get("quality_dimensions"))
    mismatch_families = _safe_list(normalized.get("mismatch_families"))
    human_perceived_ai_signals = _safe_list(normalized.get("human_perceived_ai_signals"))

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "observation_record_type": OBSERVATION_RECORD_TYPE_V1,
        "valid": valid,
        "blocked": blocked,
        "record_status": "valid" if valid else "blocked",
        "observation_id": _safe_str(normalized.get("observation_id") or ""),
        "source_case_id": _safe_str(normalized.get("source_case_id") or ""),
        "source_lineage": _as_mapping(normalized.get("source_lineage")),
        "fit_result_label": fit_result_label,
        "quality_dimensions": quality_dimensions,
        "mismatch_families": mismatch_families,
        "human_perceived_ai_signals": human_perceived_ai_signals,
        "blocked_labels": blocked_labels,
        "denied_authority_flags": _unique_sorted(denied_authority_flags),
        "raw_answer_stored": False,
        "metadata_only": True,
        "internal_only": True,
        "operator_review_required": True,
        "normalized_record": normalized,
    }


def classify_real_answer_quality_observation_v1(
    observation_item: Mapping[str, Any] | None = None,
    source_lineage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify an observation using internal qualitative labels only."""

    validation = validate_real_answer_quality_observation_record_v1(observation_item, source_lineage=source_lineage)
    blocked_labels = _safe_list(validation.get("blocked_labels"))
    fit_result_label = _safe_str(validation.get("fit_result_label") or "")
    mismatch_families = _safe_list(validation.get("mismatch_families"))

    if blocked_labels:
        classification_label = fit_result_label if fit_result_label in RESULT_LABELS_V1 else "needs_operator_review"
    elif not mismatch_families:
        classification_label = "answer_quality_fit"
    elif len(mismatch_families) <= 2:
        classification_label = "answer_quality_partial"
    else:
        classification_label = "answer_quality_mismatch"

    if classification_label not in RESULT_LABELS_V1:
        classification_label = "answer_quality_inconclusive"

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "classification_label": classification_label,
        "fit_result_label": fit_result_label if fit_result_label in RESULT_LABELS_V1 else classification_label,
        "blocked_labels": blocked_labels,
        "mismatch_families": mismatch_families,
        "quality_dimensions": _safe_list(validation.get("quality_dimensions")),
        "operator_review_required": True,
        "raw_answer_stored": False,
        "metadata_only": True,
        "internal_only": True,
    }


def build_real_answer_quality_review_packet_v1(
    observation_item: Mapping[str, Any] | None = None,
    validation_result: Mapping[str, Any] | None = None,
    classification_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an operator-reviewable metadata-only packet."""

    observation = _as_mapping(observation_item)
    validation = _as_mapping(validation_result) or validate_real_answer_quality_observation_record_v1(observation)
    classification = _as_mapping(classification_result) or classify_real_answer_quality_observation_v1(observation)

    blocked_labels = _unique_sorted(
        list(validation.get("blocked_labels") or []) + list(classification.get("blocked_labels") or [])
    )
    denied_authority_flags = _unique_sorted(validation.get("denied_authority_flags") or [])
    fit_result_label = _safe_str(classification.get("classification_label") or validation.get("fit_result_label") or "needs_operator_review")
    if fit_result_label not in RESULT_LABELS_V1:
        fit_result_label = "needs_operator_review"

    packet = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "review_packet_type": REVIEW_PACKET_TYPE_V1,
        "observation_id": _safe_str(validation.get("observation_id") or observation.get("observation_id") or ""),
        "source_case_id": _safe_str(validation.get("source_case_id") or observation.get("source_case_id") or ""),
        "fit_result_label": fit_result_label,
        "classification_label": _safe_str(classification.get("classification_label") or fit_result_label),
        "source_lineage": validation.get("source_lineage") or observation.get("source_lineage") or {},
        "quality_dimensions": _safe_list(validation.get("quality_dimensions") or observation.get("quality_dimensions") or []),
        "mismatch_families": _safe_list(validation.get("mismatch_families") or observation.get("mismatch_families") or []),
        "human_perceived_ai_signals": _safe_list(validation.get("human_perceived_ai_signals") or observation.get("human_perceived_ai_signals") or []),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "reviewer_notes_metadata_only": _safe_str(observation.get("reviewer_notes_metadata_only") or ""),
        "recommended_existing_surface": _safe_str(observation.get("recommended_existing_surface") or ""),
        "operator_review_required": True,
        "raw_answer_stored": False,
        "metadata_only": True,
        "internal_only": True,
        "packet_status": "blocked" if blocked_labels else fit_result_label,
        "validation_summary": {
            "valid": _safe_bool(validation.get("valid")),
            "blocked": _safe_bool(validation.get("blocked")),
            "record_status": _safe_str(validation.get("record_status") or "blocked"),
        },
    }
    return to_real_answer_quality_observation_json_safe_v1(packet)


def summarize_real_answer_quality_observations_v1(value: Mapping[str, Any] | Iterable[Any]) -> dict[str, Any]:
    """Summarize real-answer-quality observations using counts/status only."""

    if isinstance(value, Mapping) and "records" in value:
        items = value["records"]
    else:
        items = value

    normalized: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, Mapping) and {"observation_id", "source_case_id", "fit_result_label"}.issubset(set(item.keys())):
            normalized.append(validate_real_answer_quality_observation_record_v1(item))
        elif isinstance(item, Mapping) and {"classification_label", "blocked_labels"}.issubset(set(item.keys())):
            label = _safe_str(item.get("classification_label") or item.get("fit_result_label") or "needs_operator_review")
            normalized.append(
                {
                    "blocked": label.startswith("blocked_") or label == "needs_operator_review" and bool(item.get("blocked_labels")),
                    "valid": not (label.startswith("blocked_") or label == "needs_operator_review" and bool(item.get("blocked_labels"))),
                    "fit_result_label": label,
                    "blocked_labels": item.get("blocked_labels") or [],
                    "quality_dimensions": item.get("quality_dimensions") or [],
                    "mismatch_families": item.get("mismatch_families") or [],
                    "record_status": "blocked" if (label.startswith("blocked_") or label == "needs_operator_review" and bool(item.get("blocked_labels"))) else "valid",
                    "denied_authority_flags": item.get("denied_authority_flags") or [],
                }
            )
        else:
            normalized.append(validate_real_answer_quality_observation_record_v1(item))

    blocked_labels = _unique_sorted(label for record in normalized for label in record.get("blocked_labels", []))
    denied_authority_flags = _unique_sorted(flag for record in normalized for flag in record.get("denied_authority_flags", []))
    classification_counts: dict[str, int] = {}
    record_status_counts: dict[str, int] = {}
    for record in normalized:
        classification = _safe_str(record.get("fit_result_label") or "needs_operator_review")
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        status = _safe_str(record.get("record_status") or ("valid" if _safe_bool(record.get("valid")) else "blocked"))
        record_status_counts[status] = record_status_counts.get(status, 0) + 1

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "summary_type": SUMMARY_TYPE_V1,
        "total_records": len(normalized),
        "valid_records": sum(1 for record in normalized if _safe_bool(record.get("valid"))),
        "blocked_records": sum(1 for record in normalized if _safe_bool(record.get("blocked"))),
        "blocked_label_count": len(blocked_labels),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "classification_counts": classification_counts,
        "record_status_counts": record_status_counts,
        "raw_answer_stored": False,
        "metadata_only": True,
        "internal_only": True,
    }


def validate_real_answer_quality_batch_v1(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate multiple observation records and report blocked counts/reasons."""

    validated = [validate_real_answer_quality_observation_record_v1(record) for record in records]
    blocked_labels = _unique_sorted(label for record in validated for label in record.get("blocked_labels", []))
    blocked_reason_counts: dict[str, int] = {}
    for record in validated:
        for label in record.get("blocked_labels", []):
            blocked_reason_counts[label] = blocked_reason_counts.get(label, 0) + 1

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "batch_type": "real_answer_quality_observation_batch_v1",
        "total_records": len(validated),
        "valid_records": sum(1 for record in validated if _safe_bool(record.get("valid"))),
        "blocked_records": sum(1 for record in validated if _safe_bool(record.get("blocked"))),
        "blocked_label_count": len(blocked_labels),
        "blocked_labels": blocked_labels,
        "blocked_reason_counts": blocked_reason_counts,
        "record_status_counts": {
            "valid": sum(1 for record in validated if _safe_bool(record.get("valid"))),
            "blocked": sum(1 for record in validated if _safe_bool(record.get("blocked"))),
        },
        "metadata_only": True,
        "internal_only": True,
        "raw_answer_stored": False,
        "records": validated,
    }


__all__ = [
    "HELPER_TYPE_V1",
    "BOUNDARY_TYPE_V1",
    "SOURCE_LINEAGE_TYPE_V1",
    "OBSERVATION_RECORD_TYPE_V1",
    "REVIEW_PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "ALLOWED_SOURCE_CLASSES_V1",
    "RESULT_LABELS_V1",
    "OBSERVATION_DIMENSIONS_V1",
    "HUMAN_PERCEIVED_AI_SIGNALS_V1",
    "BLOCKED_LABELS_V1",
    "build_real_answer_quality_source_lineage_v1",
    "build_real_answer_quality_observation_record_v1",
    "validate_real_answer_quality_observation_record_v1",
    "classify_real_answer_quality_observation_v1",
    "build_real_answer_quality_review_packet_v1",
    "summarize_real_answer_quality_observations_v1",
    "to_real_answer_quality_observation_json_safe_v1",
    "validate_real_answer_quality_batch_v1",
]
