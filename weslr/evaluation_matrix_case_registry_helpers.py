"""Metadata-only helpers for the WESLR adversarial/fairness/enterprise cognition matrix.

This module is intentionally pure, deterministic, and fail-closed.
It registers and validates case metadata only; it does not execute evaluations,
call runtime/provider/model systems, capture answers, persist transcripts, or
perform any run approval work.
"""

from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "weslr_evaluation_matrix_case_registry_helpers_v1"
BOUNDARY_TYPE_V1 = "evaluation_matrix_case_registry_boundary_v1"
CASE_TYPE_V1 = "evaluation_matrix_case_v1"
OPERATOR_PHRASE_CASE_TYPE_V1 = "evaluation_matrix_operator_provided_synthetic_phrase_case_v1"
FAMILY_SUMMARY_TYPE_V1 = "evaluation_matrix_family_summary_v1"
REGISTRY_PACKET_TYPE_V1 = "evaluation_matrix_registry_packet_v1"
SUMMARY_TYPE_V1 = "evaluation_matrix_registry_summary_v1"

EVALUATION_FAMILIES_V1 = {
    "bias_fairness",
    "stereotype_resistance",
    "prompt_injection",
    "jailbreak_resistance",
    "privacy_pii_corporate_leakage",
    "enterprise_idor_cross_user_leakage",
    "domain_groundedness",
    "theory_of_mind_social_reasoning",
    "information_density_compression_limits",
    "human_conversation_continuity_stress",
}

RESULT_LABELS_V1 = {
    "evaluation_case_ready",
    "evaluation_case_needs_revision",
    "evaluation_case_blocked_by_source",
    "evaluation_case_blocked_by_privacy",
    "evaluation_case_blocked_by_safety",
    "evaluation_case_inconclusive",
    "needs_operator_review",
}

ALLOWED_SOURCE_CLASSES_V1 = {
    "synthetic_weslr_created",
    "public_open",
}

DENIED_AUTHORITY_FLAGS_V1 = {
    "runtime_authority",
    "final_answer_authority",
    "public_output_authority",
    "official_claim_authority",
    "scoring_certification_authority",
    "hidden_router_authority",
    "self_modification_authority",
    "run_approval_authority",
}

SENSITIVE_KEY_HINTS_V1 = (
    "raw_answer",
    "raw_prompt",
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
    "pii",
    "corporate_secret",
    "secret",
    "hidden_benchmark",
    "benchmark",
    "provider",
    "model",
    "runtime",
    "official",
    "turing",
    "intelligence",
    "certification",
    "final_answer",
    "public_output",
    "hidden_router",
    "manipulation",
    "fake_empathy",
    "template",
    "stereotype",
    "persona",
    "roleplay",
    "proprietary",
    "dot_weslr",
)

FORBIDDEN_MARKERS_V1 = (
    ".weslr",
    "private memory",
    "private_memory",
    "private data",
    "raw private",
    "raw pii",
    "pii",
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
    "private memory",
    "unapproved proprietary",
    "proprietary docs",
    "provider/model",
    "provider model",
    "provider output",
    "model output",
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
    "public output",
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
    return sorted(set(_safe_list(values)))


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


def to_evaluation_matrix_json_safe_v1(value: Any) -> Any:
    """Convert evaluation-matrix structures to deterministic JSON-safe data."""

    return _json_safe(value)


def _normalize_denied_authority_flags(value: Any) -> dict[str, bool]:
    mapping = _as_mapping(value)
    out: dict[str, bool] = {flag: False for flag in sorted(DENIED_AUTHORITY_FLAGS_V1)}
    for flag in DENIED_AUTHORITY_FLAGS_V1:
        if flag in mapping:
            out[flag] = _safe_bool(mapping.get(flag))
    return out


def _iter_case_records(value: Any) -> list[Any]:
    if isinstance(value, Mapping) and "cases" in value:
        value = value.get("cases")
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _build_case_base(
    *,
    case_id: str,
    family: str,
    source_class: str,
    registry_approved: bool,
    synthetic_case: bool,
    operator_provided: bool,
    prompt_descriptor_ref: str,
    expected_risk_family: str,
    blocked_data_present: bool,
    raw_private_data_present: bool,
    allowed_observation_dimensions: Any,
    expected_failure_modes: Any,
    operator_review_required: bool,
    official_claim_allowed: bool,
    denied_authority_flags: Any | None = None,
) -> dict[str, Any]:
    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "case_type": CASE_TYPE_V1,
        "case_id": _safe_str(case_id),
        "family": _safe_str(family),
        "source_class": _safe_str(source_class),
        "registry_approved": _safe_bool(registry_approved),
        "synthetic_case": _safe_bool(synthetic_case),
        "operator_provided": _safe_bool(operator_provided),
        "prompt_descriptor_ref": _safe_str(prompt_descriptor_ref),
        "expected_risk_family": _safe_str(expected_risk_family),
        "blocked_data_present": _safe_bool(blocked_data_present),
        "raw_private_data_present": _safe_bool(raw_private_data_present),
        "allowed_observation_dimensions": _unique_sorted(_safe_list(allowed_observation_dimensions)),
        "expected_failure_modes": _unique_sorted(_safe_list(expected_failure_modes)),
        "operator_review_required": _safe_bool(operator_review_required),
        "official_claim_allowed": _safe_bool(official_claim_allowed),
        "denied_authority_flags": _normalize_denied_authority_flags(denied_authority_flags),
        "metadata_only": True,
        "internal_only": True,
        "raw_transcript_persistence": False,
        "raw_answer_stored": False,
    }


def build_evaluation_matrix_case_v1(
    *,
    case_id: str,
    family: str,
    source_class: str,
    registry_approved: bool,
    synthetic_case: bool,
    operator_provided: bool,
    prompt_descriptor_ref: str,
    expected_risk_family: str,
    blocked_data_present: bool = False,
    raw_private_data_present: bool = False,
    allowed_observation_dimensions: Any = None,
    expected_failure_modes: Any = None,
    operator_review_required: bool = False,
    official_claim_allowed: bool = False,
    denied_authority_flags: Any | None = None,
) -> dict[str, Any]:
    """Build a metadata-only evaluation-matrix case."""

    return _build_case_base(
        case_id=case_id,
        family=family,
        source_class=source_class,
        registry_approved=registry_approved,
        synthetic_case=synthetic_case,
        operator_provided=operator_provided,
        prompt_descriptor_ref=prompt_descriptor_ref,
        expected_risk_family=expected_risk_family,
        blocked_data_present=blocked_data_present,
        raw_private_data_present=raw_private_data_present,
        allowed_observation_dimensions=allowed_observation_dimensions,
        expected_failure_modes=expected_failure_modes,
        operator_review_required=operator_review_required,
        official_claim_allowed=official_claim_allowed,
        denied_authority_flags=denied_authority_flags,
    )


def build_operator_provided_synthetic_phrase_case_v1(
    *,
    case_id: str,
    family: str,
    source_class: str,
    prompt_descriptor_ref: str,
    operator_phrase_ref: str,
    operator_reply_ref: str,
    provenance_marker: str,
    registry_approved: bool = True,
    expected_risk_family: str | None = None,
    blocked_data_present: bool = False,
    raw_private_data_present: bool = False,
    allowed_observation_dimensions: Any = None,
    expected_failure_modes: Any = None,
    operator_review_required: bool = True,
    official_claim_allowed: bool = False,
    denied_authority_flags: Any | None = None,
) -> dict[str, Any]:
    """Build an operator-provided synthetic phrase/reply descriptor case."""

    case = _build_case_base(
        case_id=case_id,
        family=family,
        source_class=source_class,
        registry_approved=registry_approved,
        synthetic_case=True,
        operator_provided=True,
        prompt_descriptor_ref=prompt_descriptor_ref,
        expected_risk_family=expected_risk_family or family,
        blocked_data_present=blocked_data_present,
        raw_private_data_present=raw_private_data_present,
        allowed_observation_dimensions=allowed_observation_dimensions,
        expected_failure_modes=expected_failure_modes,
        operator_review_required=operator_review_required,
        official_claim_allowed=official_claim_allowed,
        denied_authority_flags=denied_authority_flags,
    )
    case.update(
        {
            "case_type": OPERATOR_PHRASE_CASE_TYPE_V1,
            "operator_phrase_ref": _safe_str(operator_phrase_ref),
            "operator_reply_ref": _safe_str(operator_reply_ref),
            "provenance_marker": _safe_str(provenance_marker),
        }
    )
    return case


def _unknown_label_labels(case: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    for key in ("label", "result_label", "status_label"):
        value = _safe_str(case.get(key))
        if value and value not in RESULT_LABELS_V1:
            labels.append(value)
    return _unique_sorted(labels)


def validate_evaluation_matrix_case_v1(case: Any) -> dict[str, Any]:
    """Validate an evaluation-matrix case metadata record, fail-closed."""

    record = _as_mapping(case)
    family = _safe_str(record.get("family"))
    source_class = _safe_str(record.get("source_class"))
    case_id = _safe_str(record.get("case_id"))
    result_label = "evaluation_case_ready"
    blocked_labels: list[str] = []
    blocked_reasons: list[str] = []

    if not case_id:
        blocked_labels.append("missing_case_id")
        blocked_reasons.append("missing_case_id")
        result_label = "evaluation_case_blocked_by_source"

    if not family:
        blocked_labels.append("missing_family")
        blocked_reasons.append("missing_family")
        result_label = "evaluation_case_blocked_by_source"
    elif family not in EVALUATION_FAMILIES_V1:
        blocked_labels.append("unknown_family")
        blocked_reasons.append("unknown_family")
        result_label = "evaluation_case_blocked_by_source"

    if not source_class:
        blocked_labels.append("missing_source_class")
        blocked_reasons.append("missing_source_class")
        result_label = "evaluation_case_blocked_by_source"
    elif source_class not in ALLOWED_SOURCE_CLASSES_V1:
        blocked_labels.append("unknown_source_class")
        blocked_reasons.append("unknown_source_class")
        result_label = "evaluation_case_blocked_by_source"

    if _unknown_label_labels(record):
        blocked_labels.append("unknown_label")
        blocked_reasons.append("unknown_label")
        result_label = "evaluation_case_blocked_by_source"

    if not _safe_bool(record.get("registry_approved")):
        blocked_labels.append("registry_not_approved")
        blocked_reasons.append("registry_not_approved")
        result_label = "evaluation_case_blocked_by_source"

    if _safe_bool(record.get("blocked_data_present")):
        blocked_labels.append("blocked_data_present_true")
        blocked_reasons.append("blocked_data_present_true")
        result_label = "evaluation_case_blocked_by_privacy"

    if _safe_bool(record.get("raw_private_data_present")):
        blocked_labels.append("raw_private_data_present_true")
        blocked_reasons.append("raw_private_data_present_true")
        result_label = "evaluation_case_blocked_by_privacy"

    forbidden_marker_payload = {
        "prompt_descriptor_ref": record.get("prompt_descriptor_ref"),
        "operator_phrase_ref": record.get("operator_phrase_ref"),
        "operator_reply_ref": record.get("operator_reply_ref"),
        "provenance_marker": record.get("provenance_marker"),
        "label": record.get("label"),
        "result_label": record.get("result_label"),
        "status_label": record.get("status_label"),
    }
    if _contains_forbidden_marker(forbidden_marker_payload):
        blocked_labels.append("forbidden_marker_detected")
        blocked_reasons.append("forbidden_marker_detected")
        if result_label == "evaluation_case_ready":
            result_label = "evaluation_case_blocked_by_safety"

    denied_authority_flags = _normalize_denied_authority_flags(record.get("denied_authority_flags"))
    denied_true = [flag for flag, enabled in denied_authority_flags.items() if enabled]
    if denied_true:
        blocked_labels.extend([f"denied_authority:{flag}" for flag in denied_true])
        blocked_reasons.append("denied_authority_flags_true")
        result_label = "evaluation_case_blocked_by_safety"

    if _safe_bool(record.get("official_claim_allowed")):
        blocked_labels.append("official_claim_allowed_true")
        blocked_reasons.append("official_claim_allowed_true")
        result_label = "evaluation_case_blocked_by_safety"

    if _safe_bool(record.get("operator_review_required")) and result_label == "evaluation_case_ready":
        result_label = "needs_operator_review"

    if not _safe_str(record.get("prompt_descriptor_ref")):
        blocked_labels.append("missing_prompt_descriptor_ref")
        blocked_reasons.append("missing_prompt_descriptor_ref")
        result_label = "evaluation_case_needs_revision"

    if not _safe_list(record.get("allowed_observation_dimensions")):
        blocked_labels.append("missing_allowed_observation_dimensions")
        blocked_reasons.append("missing_allowed_observation_dimensions")
        result_label = "evaluation_case_needs_revision"

    if not _safe_list(record.get("expected_failure_modes")):
        blocked_labels.append("missing_expected_failure_modes")
        blocked_reasons.append("missing_expected_failure_modes")
        result_label = "evaluation_case_needs_revision"

    operator_phrase_ref = _safe_str(record.get("operator_phrase_ref"))
    operator_reply_ref = _safe_str(record.get("operator_reply_ref"))
    provenance_marker = _safe_str(record.get("provenance_marker"))
    raw_transcript_persistence = _safe_bool(record.get("raw_transcript_persistence"))
    if record.get("case_type") == OPERATOR_PHRASE_CASE_TYPE_V1 or _safe_bool(record.get("operator_provided")):
        if not operator_phrase_ref or not operator_reply_ref:
            blocked_labels.append("missing_operator_phrase_or_reply_ref")
            blocked_reasons.append("missing_operator_phrase_or_reply_ref")
            result_label = "evaluation_case_needs_revision"
        if not provenance_marker:
            blocked_labels.append("missing_provenance_marker")
            blocked_reasons.append("missing_provenance_marker")
            result_label = "evaluation_case_blocked_by_safety"
        if raw_transcript_persistence:
            blocked_labels.append("raw_transcript_persistence_true")
            blocked_reasons.append("raw_transcript_persistence_true")
            result_label = "evaluation_case_blocked_by_privacy"
        if not _safe_bool(record.get("synthetic_case")):
            blocked_labels.append("operator_phrase_case_not_synthetic")
            blocked_reasons.append("operator_phrase_case_not_synthetic")
            result_label = "evaluation_case_blocked_by_safety"
        if not _safe_bool(record.get("operator_provided")):
            blocked_labels.append("operator_phrase_case_not_operator_provided")
            blocked_reasons.append("operator_phrase_case_not_operator_provided")
            result_label = "evaluation_case_blocked_by_safety"
        if not _safe_bool(record.get("raw_private_data_present")) and _contains_forbidden_marker(provenance_marker):
            blocked_labels.append("provenance_marker_forbidden")
            blocked_reasons.append("provenance_marker_forbidden")
            result_label = "evaluation_case_blocked_by_safety"

    valid = result_label in {"evaluation_case_ready", "needs_operator_review"}
    if blocked_reasons and result_label == "evaluation_case_ready":
        result_label = "evaluation_case_needs_revision"
        valid = False
    if result_label == "evaluation_case_needs_revision":
        valid = False

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "case_type": _safe_str(record.get("case_type")) or CASE_TYPE_V1,
        "case_id": case_id,
        "family": family,
        "source_class": source_class,
        "valid": valid,
        "result_label": result_label,
        "blocked_labels": _unique_sorted(blocked_labels),
        "blocked_reasons": _unique_sorted(blocked_reasons),
        "denied_authority_flags": denied_authority_flags,
        "operator_review_required": _safe_bool(record.get("operator_review_required")),
        "metadata_only": True,
        "internal_only": True,
        "raw_answer_stored": False,
    }


def build_evaluation_matrix_family_summary_v1(cases: Any) -> dict[str, Any]:
    """Build counts/status by family only."""

    records = [_as_mapping(case) for case in _iter_case_records(cases)]

    family_status_counts: dict[str, dict[str, int]] = {}
    overall_status_counts: dict[str, int] = {}
    for record in records:
        validation = validate_evaluation_matrix_case_v1(record)
        family = validation.get("family") or _safe_str(record.get("family")) or "unknown_family"
        status = _safe_str(validation.get("result_label")) or "evaluation_case_inconclusive"
        family_bucket = family_status_counts.setdefault(
            family,
            {
                "case_count": 0,
                "evaluation_case_ready": 0,
                "evaluation_case_needs_revision": 0,
                "evaluation_case_blocked_by_source": 0,
                "evaluation_case_blocked_by_privacy": 0,
                "evaluation_case_blocked_by_safety": 0,
                "evaluation_case_inconclusive": 0,
                "needs_operator_review": 0,
            },
        )
        family_bucket["case_count"] += 1
        family_bucket[status] = family_bucket.get(status, 0) + 1
        overall_status_counts[status] = overall_status_counts.get(status, 0) + 1

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "summary_type": FAMILY_SUMMARY_TYPE_V1,
        "metadata_only": True,
        "internal_only": True,
        "family_status_counts": {family: family_status_counts[family] for family in sorted(family_status_counts)},
        "overall_status_counts": {status: overall_status_counts[status] for status in sorted(overall_status_counts)},
        "family_count": len(family_status_counts),
        "case_count": sum(bucket["case_count"] for bucket in family_status_counts.values()),
    }


def build_evaluation_matrix_registry_packet_v1(
    *,
    cases: Any,
    registry_id: str | None = None,
    registry_approved: bool = True,
    expected_families: Any = None,
    denied_authority_flags: Any | None = None,
) -> dict[str, Any]:
    """Build an operator-reviewable registry packet."""

    case_list = [copy.deepcopy(case) for case in _iter_case_records(cases)]

    present_families = sorted({_safe_str(_as_mapping(case).get("family")) for case in case_list if _safe_str(_as_mapping(case).get("family"))})
    expected_family_list = _unique_sorted(expected_families or EVALUATION_FAMILIES_V1)
    missing_families = [family for family in expected_family_list if family not in present_families]
    blocked_labels: list[str] = []
    denied_union = _normalize_denied_authority_flags(denied_authority_flags)
    validation_results = [validate_evaluation_matrix_case_v1(case) for case in case_list]
    for validation in validation_results:
        blocked_labels.extend(validation.get("blocked_labels", []))
        for flag, enabled in _normalize_denied_authority_flags(validation.get("denied_authority_flags")).items():
            denied_union[flag] = denied_union[flag] or enabled

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": REGISTRY_PACKET_TYPE_V1,
        "registry_id": _safe_str(registry_id),
        "registry_approved": _safe_bool(registry_approved),
        "metadata_only": True,
        "internal_only": True,
        "no_run_marker": True,
        "case_count": len(case_list),
        "cases": case_list,
        "expected_families": expected_family_list,
        "present_families": present_families,
        "missing_families": missing_families,
        "coverage_complete": not missing_families,
        "blocked_labels": _unique_sorted(blocked_labels),
        "denied_authority_flags": denied_union,
        "operator_review_required": True,
        "validation_results": validation_results,
    }


def validate_operator_provided_synthetic_phrase_case_v1(case: Any) -> dict[str, Any]:
    """Validate an operator-provided synthetic phrase/reply case."""

    validation = validate_evaluation_matrix_case_v1(case)
    record = _as_mapping(case)
    blocked_labels = list(validation.get("blocked_labels", []))
    blocked_reasons = list(validation.get("blocked_reasons", []))
    result_label = validation.get("result_label", "evaluation_case_inconclusive")

    if not _safe_bool(record.get("operator_provided")):
        blocked_labels.append("operator_provided_false")
        blocked_reasons.append("operator_provided_false")
        result_label = "evaluation_case_blocked_by_safety"
    if not _safe_bool(record.get("synthetic_case")):
        blocked_labels.append("synthetic_case_false")
        blocked_reasons.append("synthetic_case_false")
        result_label = "evaluation_case_blocked_by_safety"
    if _safe_str(record.get("source_class")) not in ALLOWED_SOURCE_CLASSES_V1:
        blocked_labels.append("source_class_not_allowed")
        blocked_reasons.append("source_class_not_allowed")
        result_label = "evaluation_case_blocked_by_source"
    if _safe_bool(record.get("raw_private_data_present")):
        blocked_labels.append("raw_private_data_present_true")
        blocked_reasons.append("raw_private_data_present_true")
        result_label = "evaluation_case_blocked_by_privacy"
    if _safe_bool(record.get("blocked_data_present")):
        blocked_labels.append("blocked_data_present_true")
        blocked_reasons.append("blocked_data_present_true")
        result_label = "evaluation_case_blocked_by_privacy"
    if _safe_bool(record.get("official_claim_allowed")):
        blocked_labels.append("official_claim_allowed_true")
        blocked_reasons.append("official_claim_allowed_true")
        result_label = "evaluation_case_blocked_by_safety"
    if not _safe_str(record.get("provenance_marker")):
        blocked_labels.append("missing_provenance_marker")
        blocked_reasons.append("missing_provenance_marker")
        result_label = "evaluation_case_blocked_by_safety"

    valid = result_label in {"evaluation_case_ready", "needs_operator_review"} and not blocked_reasons
    if blocked_reasons:
        valid = False

    return {
        **validation,
        "valid": valid,
        "result_label": result_label,
        "blocked_labels": _unique_sorted(blocked_labels),
        "blocked_reasons": _unique_sorted(blocked_reasons),
        "provenance_marker": _safe_str(record.get("provenance_marker")),
        "raw_transcript_persistence": _safe_bool(record.get("raw_transcript_persistence")),
    }


def validate_evaluation_matrix_registry_packet_v1(packet: Any) -> dict[str, Any]:
    """Validate a registry packet, reporting missing families and blocked reasons."""

    record = _as_mapping(packet)
    case_list = _iter_case_records(record)
    validation_results = [validate_evaluation_matrix_case_v1(case) for case in case_list]
    family_status = build_evaluation_matrix_family_summary_v1(case_list)
    missing_families = [family for family in _unique_sorted(record.get("expected_families") or EVALUATION_FAMILIES_V1) if family not in family_status["family_status_counts"]]
    blocked_labels: list[str] = []
    blocked_reasons: list[str] = []
    denied_union = _normalize_denied_authority_flags(record.get("denied_authority_flags"))
    for validation in validation_results:
        blocked_labels.extend(validation.get("blocked_labels", []))
        blocked_reasons.extend(validation.get("blocked_reasons", []))
        for flag, enabled in _normalize_denied_authority_flags(validation.get("denied_authority_flags")).items():
            denied_union[flag] = denied_union[flag] or enabled

    if not _safe_bool(record.get("registry_approved")):
        blocked_labels.append("registry_not_approved")
        blocked_reasons.append("registry_not_approved")
    if _safe_bool(record.get("no_run_marker")) is False:
        blocked_labels.append("no_run_marker_missing")
        blocked_reasons.append("no_run_marker_missing")
    if missing_families:
        for family in missing_families:
            blocked_labels.append(f"missing_family:{family}")
            blocked_reasons.append(f"missing_family:{family}")

    invalid_cases = [validation for validation in validation_results if not validation.get("valid")]
    result_label = "evaluation_case_ready"
    if missing_families or invalid_cases:
        result_label = "evaluation_case_needs_revision"
    if any(validation.get("result_label") == "evaluation_case_blocked_by_privacy" for validation in validation_results):
        result_label = "evaluation_case_blocked_by_privacy"
    elif any(validation.get("result_label") == "evaluation_case_blocked_by_source" for validation in validation_results):
        result_label = "evaluation_case_blocked_by_source"
    elif any(validation.get("result_label") == "evaluation_case_blocked_by_safety" for validation in validation_results):
        result_label = "evaluation_case_blocked_by_safety"
    elif any(validation.get("result_label") == "needs_operator_review" for validation in validation_results):
        result_label = "needs_operator_review"

    valid = not missing_families and not invalid_cases and _safe_bool(record.get("registry_approved")) and _safe_bool(record.get("no_run_marker"))

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": REGISTRY_PACKET_TYPE_V1,
        "valid": valid,
        "result_label": result_label,
        "case_count": len(case_list),
        "expected_families": _unique_sorted(record.get("expected_families") or EVALUATION_FAMILIES_V1),
        "present_families": sorted(family_status["family_status_counts"].keys()),
        "missing_families": _unique_sorted(missing_families),
        "blocked_labels": _unique_sorted(blocked_labels),
        "blocked_reasons": _unique_sorted(blocked_reasons),
        "denied_authority_flags": denied_union,
        "coverage_complete": not missing_families,
        "metadata_only": True,
        "internal_only": True,
        "no_run_marker": _safe_bool(record.get("no_run_marker")),
        "validation_results": validation_results,
        "family_status": family_status,
    }


def summarize_evaluation_matrix_registry_v1(value: Any) -> dict[str, Any]:
    """Summarize registry counts/status/coverage only."""

    record = _as_mapping(value)
    case_list = [_as_mapping(case) for case in _iter_case_records(record if "cases" in record else value)]
    family_summary = build_evaluation_matrix_family_summary_v1(case_list)
    validation_results = [validate_evaluation_matrix_case_v1(case) for case in case_list]
    status_counts: dict[str, int] = {}
    for validation in validation_results:
        status = _safe_str(validation.get("result_label")) or "evaluation_case_inconclusive"
        status_counts[status] = status_counts.get(status, 0) + 1
    expected_families = _unique_sorted(record.get("expected_families") or EVALUATION_FAMILIES_V1)
    present_families = sorted(family_summary["family_status_counts"].keys())
    missing_families = [family for family in expected_families if family not in present_families]
    coverage_count = len(present_families)
    coverage_total = len(expected_families)
    coverage_ratio = (coverage_count / coverage_total) if coverage_total else 0.0

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "summary_type": SUMMARY_TYPE_V1,
        "metadata_only": True,
        "internal_only": True,
        "case_count": len(case_list),
        "family_count": coverage_count,
        "expected_family_count": coverage_total,
        "coverage_ratio": coverage_ratio,
        "present_families": present_families,
        "missing_families": missing_families,
        "status_counts": {status: status_counts[status] for status in sorted(status_counts)},
        "family_status_counts": family_summary["family_status_counts"],
        "coverage_complete": not missing_families,
    }


__all__ = [
    "ALLOWED_SOURCE_CLASSES_V1",
    "BOUNDARY_TYPE_V1",
    "CASE_TYPE_V1",
    "DENIED_AUTHORITY_FLAGS_V1",
    "EVALUATION_FAMILIES_V1",
    "FAMILY_SUMMARY_TYPE_V1",
    "HELPER_TYPE_V1",
    "OPERATOR_PHRASE_CASE_TYPE_V1",
    "REGISTRY_PACKET_TYPE_V1",
    "RESULT_LABELS_V1",
    "SUMMARY_TYPE_V1",
    "build_evaluation_matrix_case_v1",
    "build_evaluation_matrix_family_summary_v1",
    "build_evaluation_matrix_registry_packet_v1",
    "build_operator_provided_synthetic_phrase_case_v1",
    "summarize_evaluation_matrix_registry_v1",
    "to_evaluation_matrix_json_safe_v1",
    "validate_evaluation_matrix_case_v1",
    "validate_evaluation_matrix_registry_packet_v1",
    "validate_operator_provided_synthetic_phrase_case_v1",
]
