"""Metadata-only helpers for controlled real-answer sample-run approval readiness v1.

This module is intentionally pure, deterministic, and fail-closed.
It prepares and validates approval-readiness metadata only; it does not grant
approval, execute runs, call adapters, capture answers, or persist raw content.
"""

from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

from weslr.evaluation_matrix_case_registry_helpers import (
    ALLOWED_SOURCE_CLASSES_V1 as MATRIX_ALLOWED_SOURCE_CLASSES_V1,
    EVALUATION_FAMILIES_V1 as MATRIX_EVALUATION_FAMILIES_V1,
)

HELPER_TYPE_V1 = "weslr_run_controlled_real_answer_sample_run_approval_helpers_v1"
BOUNDARY_TYPE_V1 = "run_controlled_real_answer_sample_run_approval_boundary_v1"
PRECONDITION_TYPE_V1 = "run_controlled_real_answer_sample_approval_preconditions_v1"
APPROVAL_PACKET_TYPE_V1 = "run_controlled_real_answer_sample_approval_packet_v1"
REVIEW_PACKET_TYPE_V1 = "run_controlled_real_answer_sample_approval_review_packet_v1"
SUMMARY_TYPE_V1 = "run_controlled_real_answer_sample_approval_summary_v1"
BATCH_TYPE_V1 = "run_controlled_real_answer_sample_approval_batch_v1"

ALLOWED_SOURCE_CLASSES_V1 = {"public_open", "synthetic_weslr_created"}
APPROVAL_DECISIONS_V1 = {
    "approval_ready_for_review",
    "approval_blocked",
    "approval_requires_operator_decision",
}
REQUIRED_EVALUATION_MATRIX_FAMILIES_V1 = tuple(sorted(MATRIX_EVALUATION_FAMILIES_V1))

DENIED_AUTHORITY_FLAGS_V1 = {
    "runtime_authority",
    "final_answer_authority",
    "public_output_authority",
    "source_approval_authority",
    "scoring_certification_authority",
    "benchmark_turing_intelligence_claim_authority",
    "hidden_router_authority",
    "self_modification_authority",
    "run_execution_authority",
}

BOOLEAN_PASSTHROUGH_KEYS_V1 = {
    "registry_approved_all",
    "evaluation_matrix_coverage_acknowledged",
    "raw_answer_stored",
    "metadata_only",
    "internal_only",
    "no_run_marker",
    "operator_review_required",
    *DENIED_AUTHORITY_FLAGS_V1,
}

METADATA_PASSTHROUGH_KEYS_V1 = {
    "approval_id",
    "requested_run_id",
    "authoritative_commit",
    "implementation_review_ref",
    "operator_approval_ref",
    "approved_case_ids",
    "source_case_refs",
    "source_classes",
    "adapter_contract_ref",
    "run_plan_ref",
    "precondition_status",
    "redaction_status",
    "no_persistence_policy",
    "abort_conditions",
    "evaluation_matrix_review_ref",
    "evaluation_matrix_families_acknowledged",
    "approval_decision",
    "precondition_result",
    "validation_result",
    "blocked_labels",
    "blocked_reasons",
    "matrix_coverage_status",
    "review_status",
    "packet_status",
    "batch_status",
    "summary_type",
    "boundary_type",
    "helper_type",
    "precondition_type",
    "packet_type",
    "review_packet_type",
    "metadata_only",
    "internal_only",
    "validation_results",
    "packet_results",
    "approval_packets",
    "packets",
    "packet_count",
    "valid_packet_count",
    "blocked_packet_count",
    "approval_decision_counts",
    "status_counts",
}

SENSITIVE_KEY_HINTS_V1 = (
    "raw_answer",
    "raw_prompt",
    "raw prompt",
    "raw_response",
    "raw answer",
    "response_text",
    "raw_transcript",
    "raw transcript",
    "transcript_text",
    "raw_context",
    "raw context",
    "context_text",
    "private_memory",
    "private_data",
    "private_text",
    "live_user",
    "hidden_benchmark",
    "benchmark",
    "provider_model_output",
    "provider_output",
    "model_output",
    "answer_sample",
    "final_answer",
    "public_output",
    "runtime_authority",
    "official_claim",
    "turing",
    "intelligence",
    "certification",
    "public_readiness",
    "source_approval",
    "scoring",
    "hidden_router",
    "manipulation",
    "fake_empathy",
    "template",
    "stereotype",
    "persona",
    "roleplay",
    "production",
    "auto_learning",
    "dot_weslr",
)

FORBIDDEN_MARKERS_V1 = (
    ".weslr",
    "private memory",
    "private_memory",
    "private data",
    "private_data",
    "raw private",
    "raw prompt",
    "raw answer",
    "raw transcript",
    "raw context",
    "raw pii",
    "corporate secret",
    "corporate secrets",
    "live public traffic",
    "live traffic",
    "live user",
    "live chat",
    "hidden benchmark",
    "semi-private",
    "semi private",
    "private dataset",
    "private datasets",
    "unapproved proprietary",
    "proprietary docs",
    "provider/model",
    "provider model",
    "provider output",
    "provider_output",
    "model output",
    "model_output",
    "runtime",
    "chatresponder",
    "respond_chat",
    "generate_chat",
    "official claim",
    "public claim",
    "scoring",
    "certification",
    "turing",
    "intelligence",
    "final answer",
    "final_answer",
    "public output",
    "public_output",
    "public voice",
    "voice",
    "source approval",
    "hidden router",
    "shadow router",
    "manipulation",
    "fake empathy",
    "persona",
    "template",
    "auto-learning",
    "auto learning",
    "production promotion",
)


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


def _unique_sorted(values: Iterable[str]) -> list[str]:
    if isinstance(values, (str, bytes)):
        items = [values]
    else:
        items = list(values)
    return sorted(set(_safe_list(items)))


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _collect_strings(value: Any, *, include_keys: bool = False) -> list[str]:
    strings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if include_keys:
                strings.extend(_collect_strings(key, include_keys=include_keys))
            strings.extend(_collect_strings(item, include_keys=include_keys))
        return strings
    if isinstance(value, (list, tuple, set)):
        for item in value:
            strings.extend(_collect_strings(item, include_keys=include_keys))
        return strings
    text = _safe_str(value)
    if text:
        strings.append(text)
    return strings


def _contains_forbidden_marker(value: Any) -> bool:
    for text in _collect_strings(value, include_keys=False):
        lowered = text.lower()
        for marker in FORBIDDEN_MARKERS_V1:
            if marker in lowered:
                return True
    return False


def _contains_approved_to_run(value: Any) -> bool:
    for text in _collect_strings(value, include_keys=True):
        if "approved_to_run" in text.lower():
            return True
    return False


def _redact_key(key: str, value: Any) -> Any:
    key_text = _safe_str(key).lower()
    if key_text in BOOLEAN_PASSTHROUGH_KEYS_V1 or key_text in METADATA_PASSTHROUGH_KEYS_V1:
        return _json_safe(value)
    if any(hint in key_text for hint in SENSITIVE_KEY_HINTS_V1):
        return f"[redacted:{_safe_str(key) or 'sensitive'}]"
    return _json_safe(value)


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _redact_key(str(key), val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted((_json_safe(item) for item in value), key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return f"[redacted:{type(value).__name__}]"


def to_run_controlled_real_answer_sample_approval_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _normalize_denied_authority_flags(value: Any) -> dict[str, bool]:
    mapping = _as_mapping(value)
    out: dict[str, bool] = {flag: False for flag in sorted(DENIED_AUTHORITY_FLAGS_V1)}
    for flag in DENIED_AUTHORITY_FLAGS_V1:
        if flag in mapping:
            out[flag] = _safe_bool(mapping.get(flag))
    return out


def _iter_records(value: Any) -> list[Any]:
    if isinstance(value, Mapping):
        for key in ("packets", "approval_packets", "records", "items"):
            if key in value:
                value = value.get(key)
                break
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _matrix_family_ack_list(value: Any) -> list[str]:
    items = _unique_sorted(value)
    return items


def _approval_decision_allowed(decision: Any) -> bool:
    return _safe_str(decision) in APPROVAL_DECISIONS_V1


def _source_classes_allowed(classes: Any) -> bool:
    items = _unique_sorted(classes)
    return bool(items) and all(item in ALLOWED_SOURCE_CLASSES_V1 for item in items)


def _matrix_families_acknowledged_ok(value: Any) -> bool:
    families = set(_matrix_family_ack_list(value))
    return families == set(REQUIRED_EVALUATION_MATRIX_FAMILIES_V1)


def _base_record(**fields: Any) -> dict[str, Any]:
    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "metadata_only": True,
        "internal_only": True,
        "raw_answer_stored": False,
        "no_run_marker": True,
    }
    record.update(fields)
    record["raw_answer_stored"] = False
    record["metadata_only"] = True
    record["internal_only"] = True
    record["no_run_marker"] = True
    return to_run_controlled_real_answer_sample_approval_json_safe_v1(record)


def build_run_controlled_real_answer_sample_approval_preconditions_v1(
    *,
    authoritative_commit: str,
    implementation_review_ref: str,
    source_case_refs: Any,
    source_classes: Any,
    registry_approved_all: bool,
    adapter_contract_ref: str,
    run_plan_ref: str,
    precondition_status: str,
    denied_authority_flags: Any,
    redaction_status: str,
    raw_answer_stored: bool = False,
    no_persistence_policy: str = "",
    abort_conditions: Any = None,
    evaluation_matrix_review_ref: str = "",
    evaluation_matrix_coverage_acknowledged: bool = True,
    evaluation_matrix_families_acknowledged: Any = None,
) -> dict[str, Any]:
    families = _matrix_family_ack_list(
        evaluation_matrix_families_acknowledged if evaluation_matrix_families_acknowledged is not None else (REQUIRED_EVALUATION_MATRIX_FAMILIES_V1 if evaluation_matrix_coverage_acknowledged else [])
    )
    return _base_record(
        precondition_type=PRECONDITION_TYPE_V1,
        authoritative_commit=_safe_str(authoritative_commit),
        implementation_review_ref=_safe_str(implementation_review_ref),
        source_case_refs=_unique_sorted(source_case_refs),
        source_classes=_unique_sorted(source_classes),
        registry_approved_all=_safe_bool(registry_approved_all),
        adapter_contract_ref=_safe_str(adapter_contract_ref),
        run_plan_ref=_safe_str(run_plan_ref),
        precondition_status=_safe_str(precondition_status),
        denied_authority_flags=_normalize_denied_authority_flags(denied_authority_flags),
        redaction_status=_safe_str(redaction_status),
        raw_answer_stored=False,
        no_persistence_policy=_safe_str(no_persistence_policy),
        abort_conditions=_json_safe(abort_conditions if abort_conditions is not None else []),
        evaluation_matrix_review_ref=_safe_str(evaluation_matrix_review_ref),
        evaluation_matrix_coverage_acknowledged=_safe_bool(evaluation_matrix_coverage_acknowledged),
        evaluation_matrix_families_acknowledged=families,
    )


def validate_run_controlled_real_answer_sample_approval_preconditions_v1(value: Any) -> dict[str, Any]:
    record = to_run_controlled_real_answer_sample_approval_json_safe_v1(_as_mapping(value))
    if not isinstance(record, dict):
        record = {}

    blocked_labels: list[str] = []
    blocked_reasons: list[str] = []

    if _contains_approved_to_run(record):
        blocked_labels.append("approved_to_run_present")
        blocked_reasons.append("approved_to_run_present")
    if _contains_forbidden_marker(record):
        blocked_labels.append("forbidden_marker_detected")
        blocked_reasons.append("forbidden_marker_detected")

    if not _safe_str(record.get("authoritative_commit")):
        blocked_labels.append("missing_authoritative_commit")
        blocked_reasons.append("missing_authoritative_commit")
    if not _safe_str(record.get("implementation_review_ref")):
        blocked_labels.append("missing_implementation_review_ref")
        blocked_reasons.append("missing_implementation_review_ref")
    if not _safe_list(record.get("source_case_refs")):
        blocked_labels.append("missing_source_case_refs")
        blocked_reasons.append("missing_source_case_refs")
    if not _source_classes_allowed(record.get("source_classes")):
        blocked_labels.append("invalid_source_classes")
        blocked_reasons.append("invalid_source_classes")
    if not _safe_bool(record.get("registry_approved_all")):
        blocked_labels.append("registry_not_approved_all")
        blocked_reasons.append("registry_not_approved_all")
    if not _safe_str(record.get("adapter_contract_ref")):
        blocked_labels.append("missing_adapter_contract_ref")
        blocked_reasons.append("missing_adapter_contract_ref")
    if not _safe_str(record.get("run_plan_ref")):
        blocked_labels.append("missing_run_plan_ref")
        blocked_reasons.append("missing_run_plan_ref")
    if _safe_str(record.get("precondition_status")) != "valid":
        blocked_labels.append("invalid_precondition_status")
        blocked_reasons.append("invalid_precondition_status")
    denied = _normalize_denied_authority_flags(record.get("denied_authority_flags"))
    if any(denied.values()):
        blocked_labels.append("denied_authority_flags_true")
        blocked_reasons.append("denied_authority_flags_true")
    if _safe_str(record.get("redaction_status")).lower() not in {"redacted", "active", "enabled", "on"}:
        blocked_labels.append("redaction_inactive")
        blocked_reasons.append("redaction_inactive")
    if _safe_bool(record.get("raw_answer_stored")):
        blocked_labels.append("raw_answer_stored_true")
        blocked_reasons.append("raw_answer_stored_true")
    if not _safe_str(record.get("no_persistence_policy")):
        blocked_labels.append("missing_no_persistence_policy")
        blocked_reasons.append("missing_no_persistence_policy")
    if not _safe_list(record.get("abort_conditions")):
        blocked_labels.append("missing_abort_conditions")
        blocked_reasons.append("missing_abort_conditions")
    if not _safe_str(record.get("evaluation_matrix_review_ref")):
        blocked_labels.append("missing_evaluation_matrix_review_ref")
        blocked_reasons.append("missing_evaluation_matrix_review_ref")
    if not _safe_bool(record.get("evaluation_matrix_coverage_acknowledged")):
        blocked_labels.append("evaluation_matrix_coverage_not_acknowledged")
        blocked_reasons.append("evaluation_matrix_coverage_not_acknowledged")
    if not _matrix_families_acknowledged_ok(record.get("evaluation_matrix_families_acknowledged")):
        blocked_labels.append("missing_evaluation_matrix_families_acknowledged")
        blocked_reasons.append("missing_evaluation_matrix_families_acknowledged")

    valid = not blocked_labels
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "precondition_type": PRECONDITION_TYPE_V1,
        "valid": valid,
        "blocked": not valid,
        "precondition_status": "valid" if valid else "blocked",
        "blocked_labels": _unique_sorted(blocked_labels),
        "blocked_reasons": _unique_sorted(blocked_reasons),
        "denied_authority_flags": denied,
        "evaluation_matrix_coverage_acknowledged": _safe_bool(record.get("evaluation_matrix_coverage_acknowledged")),
        "evaluation_matrix_families_acknowledged": _matrix_family_ack_list(record.get("evaluation_matrix_families_acknowledged")),
        "metadata_only": True,
        "internal_only": True,
        "raw_answer_stored": False,
        "normalized": record,
    }


def build_run_controlled_real_answer_sample_approval_packet_v1(
    *,
    approval_id: str,
    requested_run_id: str,
    authoritative_commit: str,
    implementation_review_ref: str,
    operator_approval_ref: str,
    approved_case_ids: Any,
    source_case_refs: Any,
    source_classes: Any,
    registry_approved_all: bool,
    adapter_contract_ref: str,
    run_plan_ref: str,
    precondition_status: str,
    denied_authority_flags: Any,
    redaction_status: str,
    raw_answer_stored: bool = False,
    no_persistence_policy: str = "",
    abort_conditions: Any = None,
    evaluation_matrix_review_ref: str = "",
    evaluation_matrix_families_acknowledged: Any = None,
    approval_decision: str = "approval_requires_operator_decision",
) -> dict[str, Any]:
    families = _matrix_family_ack_list(
        evaluation_matrix_families_acknowledged if evaluation_matrix_families_acknowledged is not None else REQUIRED_EVALUATION_MATRIX_FAMILIES_V1
    )
    return _base_record(
        packet_type=APPROVAL_PACKET_TYPE_V1,
        approval_id=_safe_str(approval_id),
        requested_run_id=_safe_str(requested_run_id),
        authoritative_commit=_safe_str(authoritative_commit),
        implementation_review_ref=_safe_str(implementation_review_ref),
        operator_approval_ref=_safe_str(operator_approval_ref),
        approved_case_ids=_unique_sorted(approved_case_ids),
        source_case_refs=_unique_sorted(source_case_refs),
        source_classes=_unique_sorted(source_classes),
        registry_approved_all=_safe_bool(registry_approved_all),
        adapter_contract_ref=_safe_str(adapter_contract_ref),
        run_plan_ref=_safe_str(run_plan_ref),
        precondition_status=_safe_str(precondition_status),
        denied_authority_flags=_normalize_denied_authority_flags(denied_authority_flags),
        redaction_status=_safe_str(redaction_status),
        raw_answer_stored=False,
        no_persistence_policy=_safe_str(no_persistence_policy),
        abort_conditions=_json_safe(abort_conditions if abort_conditions is not None else []),
        evaluation_matrix_review_ref=_safe_str(evaluation_matrix_review_ref),
        evaluation_matrix_families_acknowledged=families,
        approval_decision=_safe_str(approval_decision),
    )


def validate_run_controlled_real_answer_sample_approval_packet_v1(value: Any) -> dict[str, Any]:
    record = to_run_controlled_real_answer_sample_approval_json_safe_v1(_as_mapping(value))
    if not isinstance(record, dict):
        record = {}

    blocked_labels: list[str] = []
    blocked_reasons: list[str] = []

    if _contains_approved_to_run(record):
        blocked_labels.append("approved_to_run_present")
        blocked_reasons.append("approved_to_run_present")
    if _contains_forbidden_marker(record):
        blocked_labels.append("forbidden_marker_detected")
        blocked_reasons.append("forbidden_marker_detected")

    required_string_fields = (
        "approval_id",
        "requested_run_id",
        "authoritative_commit",
        "implementation_review_ref",
        "operator_approval_ref",
        "adapter_contract_ref",
        "run_plan_ref",
        "precondition_status",
        "redaction_status",
        "no_persistence_policy",
        "evaluation_matrix_review_ref",
        "approval_decision",
    )
    for field in required_string_fields:
        if not _safe_str(record.get(field)):
            blocked_labels.append(f"missing_{field}")
            blocked_reasons.append(f"missing_{field}")

    if not _safe_list(record.get("approved_case_ids")):
        blocked_labels.append("missing_approved_case_ids")
        blocked_reasons.append("missing_approved_case_ids")
    if not _safe_list(record.get("source_case_refs")):
        blocked_labels.append("missing_source_case_refs")
        blocked_reasons.append("missing_source_case_refs")
    if not _source_classes_allowed(record.get("source_classes")):
        blocked_labels.append("invalid_source_classes")
        blocked_reasons.append("invalid_source_classes")
    if not _safe_bool(record.get("registry_approved_all")):
        blocked_labels.append("registry_not_approved_all")
        blocked_reasons.append("registry_not_approved_all")
    if _safe_str(record.get("precondition_status")) != "valid":
        blocked_labels.append("invalid_precondition_status")
        blocked_reasons.append("invalid_precondition_status")
    if _safe_bool(record.get("raw_answer_stored")):
        blocked_labels.append("raw_answer_stored_true")
        blocked_reasons.append("raw_answer_stored_true")
    if _safe_str(record.get("redaction_status")).lower() not in {"redacted", "active", "enabled", "on"}:
        blocked_labels.append("redaction_inactive")
        blocked_reasons.append("redaction_inactive")
    if not _safe_str(record.get("abort_conditions")) and not _safe_list(record.get("abort_conditions")):
        blocked_labels.append("missing_abort_conditions")
        blocked_reasons.append("missing_abort_conditions")
    if not _matrix_families_acknowledged_ok(record.get("evaluation_matrix_families_acknowledged")):
        blocked_labels.append("missing_evaluation_matrix_families_acknowledged")
        blocked_reasons.append("missing_evaluation_matrix_families_acknowledged")
    if not _approval_decision_allowed(record.get("approval_decision")):
        blocked_labels.append("invalid_approval_decision")
        blocked_reasons.append("invalid_approval_decision")

    denied = _normalize_denied_authority_flags(record.get("denied_authority_flags"))
    if any(denied.values()):
        blocked_labels.append("denied_authority_flags_true")
        blocked_reasons.append("denied_authority_flags_true")

    valid = not blocked_labels
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": APPROVAL_PACKET_TYPE_V1,
        "valid": valid,
        "blocked": not valid,
        "approval_decision": _safe_str(record.get("approval_decision")),
        "blocked_labels": _unique_sorted(blocked_labels),
        "blocked_reasons": _unique_sorted(blocked_reasons),
        "denied_authority_flags": denied,
        "evaluation_matrix_review_ref": _safe_str(record.get("evaluation_matrix_review_ref")),
        "evaluation_matrix_families_acknowledged": _matrix_family_ack_list(record.get("evaluation_matrix_families_acknowledged")),
        "metadata_only": True,
        "internal_only": True,
        "raw_answer_stored": False,
        "normalized": record,
    }


def build_run_controlled_real_answer_sample_approval_review_packet_v1(
    *,
    packet: Mapping[str, Any],
    precondition_result: Mapping[str, Any] | None = None,
    validation_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_packet = to_run_controlled_real_answer_sample_approval_json_safe_v1(_as_mapping(packet))
    if not isinstance(normalized_packet, dict):
        normalized_packet = {}
    preconditions = (
        validate_run_controlled_real_answer_sample_approval_preconditions_v1(precondition_result)
        if precondition_result is not None
        else validate_run_controlled_real_answer_sample_approval_preconditions_v1(normalized_packet)
    )
    validation = (
        to_run_controlled_real_answer_sample_approval_json_safe_v1(_as_mapping(validation_result))
        if validation_result is not None
        else validate_run_controlled_real_answer_sample_approval_packet_v1(normalized_packet)
    )
    if not isinstance(validation, dict):
        validation = validate_run_controlled_real_answer_sample_approval_packet_v1(normalized_packet)
    if not isinstance(preconditions, dict):
        preconditions = validate_run_controlled_real_answer_sample_approval_preconditions_v1(normalized_packet)

    matrix_coverage_status = {
        "evaluation_matrix_review_ref": _safe_str(normalized_packet.get("evaluation_matrix_review_ref") or preconditions.get("evaluation_matrix_review_ref")),
        "evaluation_matrix_coverage_acknowledged": set(_matrix_family_ack_list(normalized_packet.get("evaluation_matrix_families_acknowledged") or preconditions.get("evaluation_matrix_families_acknowledged"))) == set(REQUIRED_EVALUATION_MATRIX_FAMILIES_V1),
        "evaluation_matrix_families_acknowledged": _matrix_family_ack_list(
            normalized_packet.get("evaluation_matrix_families_acknowledged") or preconditions.get("evaluation_matrix_families_acknowledged")
        ),
        "coverage_complete": set(
            _matrix_family_ack_list(normalized_packet.get("evaluation_matrix_families_acknowledged") or preconditions.get("evaluation_matrix_families_acknowledged"))
        )
        == set(REQUIRED_EVALUATION_MATRIX_FAMILIES_V1),
    }

    review = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "review_packet_type": REVIEW_PACKET_TYPE_V1,
        "review_status": "valid" if _safe_bool(validation.get("valid")) and _safe_bool(preconditions.get("valid")) else "blocked",
        "validation_result": validation,
        "precondition_result": preconditions,
        "blocked_labels": _unique_sorted(
            list(_safe_list(validation.get("blocked_labels")))
            + list(_safe_list(preconditions.get("blocked_labels")))
        ),
        "blocked_reasons": _unique_sorted(
            list(_safe_list(validation.get("blocked_reasons")))
            + list(_safe_list(preconditions.get("blocked_reasons")))
        ),
        "denied_authority_flags": _normalize_denied_authority_flags(
            {
                **_as_mapping(preconditions.get("denied_authority_flags")),
                **_as_mapping(validation.get("denied_authority_flags")),
                **_as_mapping(normalized_packet.get("denied_authority_flags")),
            }
        ),
        "matrix_coverage_status": matrix_coverage_status,
        "no_run_marker": True,
        "metadata_only": True,
        "internal_only": True,
        "raw_answer_stored": False,
    }
    return to_run_controlled_real_answer_sample_approval_json_safe_v1(review)


def summarize_run_controlled_real_answer_sample_approval_packet_v1(value: Any) -> dict[str, Any]:
    records = [to_run_controlled_real_answer_sample_approval_json_safe_v1(item) for item in _iter_records(value)]
    normalized = [record if isinstance(record, dict) else {} for record in records]

    validation_results = [validate_run_controlled_real_answer_sample_approval_packet_v1(record) for record in normalized]
    decision_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    blocked_labels: list[str] = []
    for result in validation_results:
        decision = _safe_str(result.get("approval_decision")) or "approval_requires_operator_decision"
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        status = "valid" if _safe_bool(result.get("valid")) else "blocked"
        status_counts[status] = status_counts.get(status, 0) + 1
        blocked_labels.extend(_safe_list(result.get("blocked_labels")))

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "summary_type": SUMMARY_TYPE_V1,
        "packet_count": len(normalized),
        "valid_packet_count": status_counts.get("valid", 0),
        "blocked_packet_count": status_counts.get("blocked", 0),
        "approval_decision_counts": {key: decision_counts[key] for key in sorted(decision_counts)},
        "status_counts": {key: status_counts[key] for key in sorted(status_counts)},
        "blocked_label_count": len(_unique_sorted(blocked_labels)),
        "blocked_labels": _unique_sorted(blocked_labels),
        "raw_answer_stored": False,
        "metadata_only": True,
        "internal_only": True,
    }


def validate_run_controlled_real_answer_sample_approval_batch_v1(value: Any) -> dict[str, Any]:
    packets = _iter_records(value)
    validation_results = [validate_run_controlled_real_answer_sample_approval_packet_v1(packet) for packet in packets]
    blocked_labels: list[str] = []
    blocked_reasons: list[str] = []
    for result in validation_results:
        blocked_labels.extend(_safe_list(result.get("blocked_labels")))
        blocked_reasons.extend(_safe_list(result.get("blocked_reasons")))
    valid = all(_safe_bool(result.get("valid")) for result in validation_results)
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "batch_type": BATCH_TYPE_V1,
        "valid": valid,
        "blocked": not valid,
        "packet_count": len(packets),
        "blocked_labels": _unique_sorted(blocked_labels),
        "blocked_reasons": _unique_sorted(blocked_reasons),
        "validation_results": validation_results,
        "metadata_only": True,
        "internal_only": True,
        "raw_answer_stored": False,
    }


__all__ = [
    "HELPER_TYPE_V1",
    "BOUNDARY_TYPE_V1",
    "PRECONDITION_TYPE_V1",
    "APPROVAL_PACKET_TYPE_V1",
    "REVIEW_PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "BATCH_TYPE_V1",
    "ALLOWED_SOURCE_CLASSES_V1",
    "APPROVAL_DECISIONS_V1",
    "REQUIRED_EVALUATION_MATRIX_FAMILIES_V1",
    "DENIED_AUTHORITY_FLAGS_V1",
    "build_run_controlled_real_answer_sample_approval_preconditions_v1",
    "validate_run_controlled_real_answer_sample_approval_preconditions_v1",
    "build_run_controlled_real_answer_sample_approval_packet_v1",
    "validate_run_controlled_real_answer_sample_approval_packet_v1",
    "build_run_controlled_real_answer_sample_approval_review_packet_v1",
    "summarize_run_controlled_real_answer_sample_approval_packet_v1",
    "to_run_controlled_real_answer_sample_approval_json_safe_v1",
    "validate_run_controlled_real_answer_sample_approval_batch_v1",
]
