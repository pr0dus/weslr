"""WESLR MLCF Authorized Metadata-Only Source Summary V1.

Metadata-only helpers for summarizing reviewed locator metadata.
This module does not browse, fetch, ingest, retain raw content, or authorize
runtime/public claims.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.mlcf_source_locator_organization_review_packet import (
    classify_mlcf_locator_record_for_review_v1,
)

SCHEMA_VERSION_V1 = "mlcf_authorized_metadata_only_source_summary_v1"
HELPER_FAMILY_V1 = "mlcf_authorized_metadata_only_source_summary"

_ALLOWED_STATUSES_V1 = (
    "metadata_summary_prepared",
    "excluded_needs_operator_review",
    "excluded_needs_repair",
    "excluded_rejected",
    "excluded_duplicate_or_low_value",
    "blocked_by_safety",
)

_ALLOWED_NEXT_STEPS_V1 = (
    "operator_review",
    "prepare_evidence_intake_packet",
    "repair_locator_records",
    "reject_source_summary_batch",
    "blocked_by_safety",
)

_ALLOWED_EXCLUSION_REASONS_V1 = (
    "operator_review_required_before_summary",
    "locator_record_needs_repair",
    "rejected_locator_record",
    "duplicate_or_low_value_record",
    "blocked_by_safety",
    "unsupported_summary_field",
)

_AUTHORITY_FALSE_FLAGS_V1 = (
    "source_access_authorized",
    "source_fetching_authority",
    "source_summary_authority",
    "source_summary_authorized",
    "source_content_summary_authorized",
    "source_ingestion_authorized",
    "raw_retention_authorized",
    "web_call_authority",
    "github_call_authority",
    "searxng_call_authority",
    "public_claim_authorized",
    "final_answer_authority",
    "discovery_claim_authorized",
    "proof_claim_authorized",
    "agi_claim_authorized",
    "benchmark_claim_authorized",
    "public_science_claim_authorized",
)

_AUTHORITY_TEXT_MARKERS_V1 = (
    "discovery",
    "proof",
    "benchmark",
    "agi",
    "public science",
    "final answer",
    "source ingestion",
    "raw retention",
    "web call",
    "github call",
    "searxng call",
    "source fetching",
    "behavior pack",
    "database write",
    "memory mutation",
    "project mutation",
    "cross-user leakage",
    ".weslr",
)

_HIDDEN_PRIVATE_PROTECTED_MARKERS_V1 = (
    "hidden",
    "private",
    "protected",
    "secret",
    "credential",
    "credentials",
    "cookie",
    "cookies",
    "api key",
    "apikey",
    "token",
    "bearer",
    "password",
    "session",
    "csrf",
)

_FORBIDDEN_CONTENT_FIELDS_V1 = (
    "source_content",
    "full_text",
    "raw_page_content",
    "raw_content",
    "repository_content",
    "dataset_content",
    "paper_text",
    "downloaded_content",
)

_FORBIDDEN_QUOTE_FIELDS_V1 = (
    "quote",
    "excerpt",
    "quoted_text",
)

_REQUIRED_FIELD_NAMES_V1 = (
    "schema_version",
    "summary_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "source_locator_review_packet_ref",
    "input_review_record_count",
    "metadata_only_source_summaries",
    "excluded_records",
    "blocked_records",
    "summary_record_count",
    "excluded_record_count",
    "blocked_record_count",
    "source_class_distribution",
    "authority_distribution",
    "evidence_role_distribution",
    "metadata_summary_scope",
    "operator_review_need",
    "allowed_next_step",
    "blocked_conditions",
    "authority_status",
    "safe_metadata",
    "summary_status",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "summary_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "source_locator_review_packet_ref",
    "metadata_summary_scope",
    "operator_review_need",
    "allowed_next_step",
    "summary_status",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "metadata_only_source_summaries",
    "excluded_records",
    "blocked_records",
    "blocked_conditions",
)

_REQUIRED_DICT_FIELDS_V1 = (
    "source_class_distribution",
    "authority_distribution",
    "evidence_role_distribution",
    "authority_status",
    "safe_metadata",
)

_RECORD_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "metadata_summary_id",
    "source_locator_id",
    "science_direction_id",
    "source_class",
    "authority_level_guess",
    "evidence_role_guess",
    "candidate_title",
    "candidate_url_or_identifier",
    "candidate_domain",
    "query_family",
    "freshness_status",
    "access_license_status",
    "privacy_status",
    "review_bucket",
    "review_decision_reason",
    "metadata_summary_text",
    "not_evidence_notice",
    "operator_review_need",
    "allowed_next_step",
    "summary_status",
)

_REVIEW_BUCKET_READY = "ready_for_authorized_metadata_only_source_summary"
_REVIEW_BUCKET_KEEP = "keep_for_operator_review"
_REVIEW_BUCKET_NEEDS_REPAIR = "needs_repair"
_REVIEW_BUCKET_REJECT = "reject"
_REVIEW_BUCKET_BLOCKED = "blocked"
_REVIEW_BUCKET_DUP = "duplicate_or_low_value"



def allowed_mlcf_metadata_only_source_summary_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_STATUSES_V1



def allowed_mlcf_metadata_only_source_summary_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEPS_V1



def allowed_mlcf_metadata_only_source_summary_exclusion_reasons_v1() -> tuple[str, ...]:
    return _ALLOWED_EXCLUSION_REASONS_V1



def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    elif isinstance(payload, list):
        merged["review_records"] = payload
    elif payload is not None:
        merged["review_records"] = payload
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
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
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return f"<non-json-safe:{type(value).__name__}>"



def _first_non_json_safe_path(value: Any, path: str = "packet") -> str | None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return None
    if isinstance(value, (bytes, bytearray, memoryview, tuple, set)):
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
    if callable(value):
        return path
    return path



def _contains_any_marker(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)



def _contains_forbidden_markers(value: Any, markers: tuple[str, ...]) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_forbidden_markers(item, markers) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_markers(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    return _contains_any_marker(value, markers)



def _default_authority_status() -> dict[str, Any]:
    status = {flag: False for flag in _AUTHORITY_FALSE_FLAGS_V1}
    status.update(
        {
            "all_authority_flags_false": True,
            "status": "metadata_only_source_summary_packet",
            "boundary_notes": "metadata-only packet boundary",
        }
    )
    return status



def _default_safe_metadata() -> dict[str, Any]:
    return {
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_raw_content": True,
        "no_source_content": True,
        "no_source_fetching": True,
        "no_source_summary": True,
        "no_source_content_summary": True,
        "no_ingestion": True,
        "no_claims": True,
        "no_web_calls": True,
        "no_github_calls": True,
        "no_searxng_calls": True,
        "operator_review_required": True,
        "source_access_authorized": False,
        "source_fetching_authority": False,
        "source_summary_authority": False,
        "source_summary_authorized": False,
        "source_content_summary_authorized": False,
        "source_ingestion_authorized": False,
        "raw_retention_authorized": False,
        "web_call_authority": False,
        "github_call_authority": False,
        "searxng_call_authority": False,
        "public_claim_authorized": False,
        "final_answer_authority": False,
        "discovery_claim_authorized": False,
        "proof_claim_authorized": False,
        "agi_claim_authorized": False,
        "benchmark_claim_authorized": False,
        "public_science_claim_authorized": False,
        "source_content_summary_authorized": False,
    }



def _normalize_review_record(record: Any) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return deepcopy(dict(record))
    return {"invalid_record": record}



def _record_signature(record: Mapping[str, Any]) -> str:
    payload = "|".join(
        [
            _compact_text(record.get("source_locator_id")),
            _compact_text(record.get("candidate_title")),
            _compact_text(record.get("candidate_url_or_identifier")),
            _compact_text(record.get("candidate_domain")),
            _compact_text(record.get("review_bucket")),
            _compact_text(record.get("review_decision_reason")),
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()[:16]



def _record_has_forbidden_summary_content(record: Mapping[str, Any]) -> bool:
    for field in _FORBIDDEN_CONTENT_FIELDS_V1 + _FORBIDDEN_QUOTE_FIELDS_V1:
        if field in record:
            return True
    return False



def _summary_basis_fields() -> list[str]:
    return [
        "candidate_title",
        "candidate_url_or_identifier",
        "candidate_domain",
        "source_class",
        "authority_level_guess",
        "evidence_role_guess",
        "query_family",
        "freshness_status",
        "access_license_status",
        "privacy_status",
        "review_bucket",
        "review_decision_reason",
        "relevance_reason",
        "blocked_conditions",
    ]



def build_mlcf_metadata_only_source_summary_record_v1(review_record: Any, **overrides: Any) -> dict[str, Any]:
    record = _normalize_review_record(review_record)
    classification = classify_mlcf_locator_record_for_review_v1(record)
    summary_basis = _summary_basis_fields()
    record.update(
        {
            "schema_version": SCHEMA_VERSION_V1,
            "metadata_summary_id": _compact_text(
                overrides.get(
                    "metadata_summary_id",
                    f"metadata_summary_{classification['record_signature']}",
                )
            ),
            "source_locator_id": _compact_text(record.get("locator_id")),
            "science_direction_id": _compact_text(record.get("science_direction_id")),
            "source_class": _compact_text(record.get("source_class")),
            "authority_level_guess": _compact_text(record.get("authority_level_guess")),
            "evidence_role_guess": _compact_text(record.get("evidence_role_guess")),
            "candidate_title": _compact_text(record.get("candidate_title")),
            "candidate_url_or_identifier": _compact_text(record.get("candidate_url_or_identifier")),
            "candidate_domain": _compact_text(record.get("candidate_domain")),
            "query_family": _compact_text(record.get("query_family")),
            "freshness_status": _compact_text(record.get("freshness_status")),
            "access_license_status": _compact_text(record.get("access_license_status")),
            "privacy_status": _compact_text(record.get("privacy_status")),
            "review_bucket": _compact_text(classification.get("review_bucket")),
            "review_decision_reason": _compact_text(classification.get("decision_reason")),
            "metadata_summary_text": _compact_text(
                overrides.get(
                    "metadata_summary_text",
                    "Metadata-only source summary for {} ({}, {}, {}).".format(
                        _compact_text(record.get("candidate_title"), "locator record"),
                        _compact_text(record.get("source_class"), "unknown source class"),
                        _compact_text(record.get("authority_level_guess"), "unknown authority"),
                        _compact_text(record.get("evidence_role_guess"), "unknown evidence role"),
                    ),
                )
            )[:220],
            "summary_status": _compact_text(overrides.get("summary_status", "metadata_summary_prepared")),
            "summary_basis_fields": list(overrides.get("summary_basis_fields", summary_basis)),
            "limitations": _compact_text(
                overrides.get(
                    "limitations",
                    "Metadata-only summary; no source content, no raw pages, no ingestion, no claim authority, and no truth conclusion.",
                )
            )[:240],
            "not_evidence_notice": _compact_text(
                overrides.get(
                    "not_evidence_notice",
                    "This is metadata-only locator summary, not source content, not evidence, and not a public claim.",
                )
            )[:240],
            "operator_review_need": _compact_text(
                overrides.get(
                    "operator_review_need",
                    _compact_text(record.get("operator_review_need"), "Operator review required before any source access."),
                )
            )[:220],
            "allowed_next_step": _compact_text(
                overrides.get("allowed_next_step", "prepare_evidence_intake_packet")
            ),
            "blocked_conditions": _normalize_text_list(
                overrides.get("blocked_conditions", record.get("blocked_conditions"))
            ),
            "authority_status": _default_authority_status(),
            "safe_metadata": _default_safe_metadata(),
        }
    )
    record["authority_status"] = dict(overrides.get("authority_status", record["authority_status"]))
    record["safe_metadata"] = dict(overrides.get("safe_metadata", record["safe_metadata"]))
    return record



def _summary_bucket_status(summary_count: int, blocked_count: int, needs_repair_count: int, rejected_count: int, duplicate_count: int) -> str:
    if summary_count > 0:
        return "metadata_summary_prepared"
    if blocked_count > 0:
        return "blocked_by_safety"
    if needs_repair_count > 0:
        return "excluded_needs_repair"
    if rejected_count > 0:
        return "excluded_rejected"
    if duplicate_count > 0:
        return "excluded_duplicate_or_low_value"
    return "excluded_needs_operator_review"



def _packet_next_step(summary_count: int, blocked_count: int, needs_repair_count: int, rejected_count: int, duplicate_count: int) -> str:
    if summary_count > 0:
        return "prepare_evidence_intake_packet"
    if blocked_count > 0:
        return "blocked_by_safety"
    if needs_repair_count > 0:
        return "repair_locator_records"
    if rejected_count > 0:
        return "reject_source_summary_batch"
    if duplicate_count > 0:
        return "operator_review"
    return "operator_review"



def build_mlcf_authorized_metadata_only_source_summary_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged = _merge_payload(payload, **overrides)
    review_records = merged.pop("review_records", None)
    if review_records is None:
        review_records = []
    review_records = list(review_records)

    summary_records: list[dict[str, Any]] = []
    excluded_records: list[dict[str, Any]] = []
    blocked_records: list[dict[str, Any]] = []
    source_class_counter: Counter[str] = Counter()
    authority_counter: Counter[str] = Counter()
    evidence_counter: Counter[str] = Counter()
    blocked_conditions: list[str] = []
    summary_count = 0
    excluded_needs_operator_review = 0
    excluded_needs_repair = 0
    excluded_rejected = 0
    excluded_duplicate_or_low_value = 0
    blocked_count = 0
    packet_ref = _compact_text(merged.get("source_locator_review_packet_ref"), _compact_text(merged.get("review_packet_ref"), "review_packet_ref_missing"))

    for raw_record in review_records:
        record = _normalize_review_record(raw_record)
        classification = classify_mlcf_locator_record_for_review_v1(record)
        source_class = _compact_text(record.get("source_class")) or "unknown"
        authority = _compact_text(record.get("authority_level_guess")) or "unknown"
        evidence = _compact_text(record.get("evidence_role_guess")) or "unknown"
        source_class_counter[source_class] += 1
        authority_counter[authority] += 1
        evidence_counter[evidence] += 1

        bucket = classification["review_bucket"]
        decision_reason = classification["decision_reason"]
        if bucket == _REVIEW_BUCKET_READY:
            summary_record = build_mlcf_metadata_only_source_summary_record_v1(
                record,
                metadata_summary_id=f"summary_{classification['record_signature']}",
                allowed_next_step="prepare_evidence_intake_packet",
                blocked_conditions=list(record.get("blocked_conditions", [])),
            )
            summary_records.append(summary_record)
            summary_count += 1
        elif bucket == _REVIEW_BUCKET_KEEP:
            excluded_records.append(
                {
                    **deepcopy(record),
                    "summary_status": "excluded_needs_operator_review",
                    "summary_exclusion_reason": "operator_review_required_before_summary",
                    "summary_next_step": "operator_review",
                    "review_bucket": bucket,
                    "review_decision_reason": decision_reason,
                }
            )
            excluded_needs_operator_review += 1
        elif bucket == _REVIEW_BUCKET_NEEDS_REPAIR:
            excluded_records.append(
                {
                    **deepcopy(record),
                    "summary_status": "excluded_needs_repair",
                    "summary_exclusion_reason": "locator_record_needs_repair",
                    "summary_next_step": "repair_locator_records",
                    "review_bucket": bucket,
                    "review_decision_reason": decision_reason,
                }
            )
            excluded_needs_repair += 1
        elif bucket == _REVIEW_BUCKET_REJECT:
            excluded_records.append(
                {
                    **deepcopy(record),
                    "summary_status": "excluded_rejected",
                    "summary_exclusion_reason": "rejected_locator_record",
                    "summary_next_step": "reject_source_summary_batch",
                    "review_bucket": bucket,
                    "review_decision_reason": decision_reason,
                }
            )
            excluded_rejected += 1
        elif bucket == _REVIEW_BUCKET_DUP:
            excluded_records.append(
                {
                    **deepcopy(record),
                    "summary_status": "excluded_duplicate_or_low_value",
                    "summary_exclusion_reason": "duplicate_or_low_value_record",
                    "summary_next_step": "operator_review",
                    "review_bucket": bucket,
                    "review_decision_reason": decision_reason,
                }
            )
            excluded_duplicate_or_low_value += 1
        elif bucket == _REVIEW_BUCKET_BLOCKED:
            blocked_records.append(
                {
                    **deepcopy(record),
                    "summary_status": "blocked_by_safety",
                    "summary_exclusion_reason": "blocked_by_safety",
                    "summary_next_step": "blocked_by_safety",
                    "review_bucket": bucket,
                    "review_decision_reason": decision_reason,
                }
            )
            blocked_count += 1
        else:
            excluded_records.append(
                {
                    **deepcopy(record),
                    "summary_status": "excluded_needs_operator_review",
                    "summary_exclusion_reason": "operator_review_required_before_summary",
                    "summary_next_step": "operator_review",
                    "review_bucket": bucket,
                    "review_decision_reason": decision_reason,
                }
            )
            excluded_needs_operator_review += 1

        reason = _compact_text(record.get("review_decision_reason")) or decision_reason
        if reason and reason not in blocked_conditions:
            blocked_conditions.append(reason)

    summary_status = _summary_bucket_status(
        summary_count, blocked_count, excluded_needs_repair, excluded_rejected, excluded_duplicate_or_low_value
    )
    allowed_next_step = _packet_next_step(
        summary_count, blocked_count, excluded_needs_repair, excluded_rejected, excluded_duplicate_or_low_value
    )

    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "summary_packet_id": _compact_text(merged.get("summary_packet_id"), "default_summary_packet"),
        "science_direction_id": _compact_text(merged.get("science_direction_id"), "default_science_direction"),
        "science_direction_summary": _compact_text(
            merged.get("science_direction_summary"), "Metadata-only source summary packet."
        ),
        "source_locator_review_packet_ref": packet_ref,
        "input_review_record_count": len(review_records),
        "metadata_only_source_summaries": summary_records,
        "excluded_records": excluded_records,
        "blocked_records": blocked_records,
        "summary_record_count": summary_count,
        "excluded_record_count": len(excluded_records),
        "blocked_record_count": len(blocked_records),
        "source_class_distribution": dict(source_class_counter),
        "authority_distribution": dict(authority_counter),
        "evidence_role_distribution": dict(evidence_counter),
        "metadata_summary_scope": _compact_text(
            merged.get("metadata_summary_scope"), "ready_records_only"
        ),
        "operator_review_need": _compact_text(
            merged.get("operator_review_need"),
            "Operator review required; metadata-only summary boundaries preserved.",
        ),
        "allowed_next_step": allowed_next_step,
        "blocked_conditions": blocked_conditions,
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
        "summary_status": summary_status,
        "review_records": review_records,
        "summary_status_counts": {
            "metadata_summary_prepared": summary_count,
            "excluded_needs_operator_review": excluded_needs_operator_review,
            "excluded_needs_repair": excluded_needs_repair,
            "excluded_rejected": excluded_rejected,
            "excluded_duplicate_or_low_value": excluded_duplicate_or_low_value,
            "blocked_by_safety": blocked_count,
        },
    }
    packet["authority_status"] = dict(merged.get("authority_status", packet["authority_status"]))
    packet["safe_metadata"] = dict(merged.get("safe_metadata", packet["safe_metadata"]))
    return packet



def _validate_authority_status(authority_status: Any) -> tuple[bool, list[str]]:
    if not isinstance(authority_status, Mapping):
        return False, ["invalid_authority_status"]
    labels: list[str] = []
    for flag in _AUTHORITY_FALSE_FLAGS_V1:
        if flag not in authority_status:
            labels.append(f"missing_authority_status_{flag}")
        elif authority_status[flag] is not False:
            labels.append(f"unsafe_authority_flag:{flag}")
    if authority_status.get("all_authority_flags_false") is not True:
        labels.append("unsafe_authority_flags")
    if _compact_text(authority_status.get("status")) != "metadata_only_source_summary_packet":
        labels.append("unsafe_authority_status")
    notes = _compact_text(authority_status.get("boundary_notes"))
    if not notes:
        labels.append("missing_authority_status_boundary_notes")
    elif _contains_any_marker(notes, _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_authority_text")
    return not labels, labels



def _validate_safe_metadata(safe_metadata: Any) -> tuple[bool, list[str]]:
    if not isinstance(safe_metadata, Mapping):
        return False, ["invalid_safe_metadata"]
    labels: list[str] = []
    required_true = (
        "metadata_only",
        "json_safe",
        "non_public",
        "no_raw_content",
        "no_source_content",
        "no_source_fetching",
        "no_source_summary",
        "no_source_content_summary",
        "no_ingestion",
        "no_claims",
        "no_web_calls",
        "no_github_calls",
        "no_searxng_calls",
        "operator_review_required",
    )
    for flag in required_true:
        if safe_metadata.get(flag) is not True:
            labels.append(f"unsafe_safe_metadata_flag:{flag}")
    for flag in _AUTHORITY_FALSE_FLAGS_V1:
        if flag in safe_metadata and safe_metadata[flag] is not False:
            labels.append(f"unsafe_safe_metadata_flag:{flag}")
    if _contains_forbidden_markers(safe_metadata, _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_safe_metadata_text")
    if _contains_forbidden_markers(safe_metadata, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("unsafe_hidden_private_protected_marker")
    return not labels, labels



def _validate_summary_record(record: Mapping[str, Any], labels: list[str]) -> None:
    for field in _RECORD_REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(record.get(field)):
            labels.append(f"missing_{field}")
    if _compact_text(record.get("review_bucket")) != _REVIEW_BUCKET_READY:
        labels.append("summary_record_not_ready_bucket")
    if _compact_text(record.get("allowed_next_step")) != "prepare_evidence_intake_packet":
        labels.append("summary_record_bad_next_step")
    if _compact_text(record.get("summary_status")) and _compact_text(record.get("summary_status")) != "metadata_summary_prepared":
        labels.append("summary_record_invalid_summary_status")
    if _record_has_forbidden_summary_content(record):
        labels.append("summary_record_contains_source_content")
    if _contains_forbidden_markers(record.get("metadata_summary_text"), _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_authority_text")
    if _contains_forbidden_markers(record.get("metadata_summary_text"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("unsafe_hidden_private_protected_marker")
    if _contains_forbidden_markers(record.get("metadata_summary_text"), ("WESLR discovered", "confirmed discovery", "proved", "public science result", "benchmark-winning", "agi", "sentience", "consciousness")):
        labels.append("unsafe_claim_language")
    if _contains_forbidden_markers(record.get("science_direction_summary"), ("WESLR discovered", "confirmed discovery", "proved", "public science result", "benchmark-winning", "agi", "sentience", "consciousness")):
        labels.append("unsafe_claim_language")



def _validate_excluded_record(record: Mapping[str, Any], labels: list[str]) -> None:
    status = _compact_text(record.get("summary_status"))
    if status not in {
        "excluded_needs_operator_review",
        "excluded_needs_repair",
        "excluded_rejected",
        "excluded_duplicate_or_low_value",
    }:
        labels.append("invalid_excluded_record_status")
    if _record_has_forbidden_summary_content(record):
        labels.append("excluded_record_contains_source_content")
    if _compact_text(record.get("source_class")) == "github_repository" and _compact_text(record.get("review_decision_reason")) not in {"keep_for_operator_review", "operator_review_required_before_summary"}:
        # GitHub can be excluded for operator review, but not treated as official science evidence.
        pass



def _validate_blocked_record(record: Mapping[str, Any], labels: list[str]) -> None:
    status = _compact_text(record.get("summary_status"))
    if status != "blocked_by_safety":
        labels.append("blocked_record_not_blocked")
    if _record_has_forbidden_summary_content(record):
        labels.append("blocked_record_contains_source_content")



def validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_packet_type"],
            "validation_posture": "blocked",
            "summary_text": "Invalid authorized metadata-only source summary packet.",
        }

    labels: list[str] = []
    for field in _REQUIRED_FIELD_NAMES_V1:
        if field not in packet:
            labels.append(f"missing_{field}")
    if labels:
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": labels,
            "validation_posture": "blocked",
            "summary_text": "Missing required metadata-only source summary packet fields.",
        }

    for field in _REQUIRED_TEXT_FIELDS_V1:
        text_value = _compact_text(packet.get(field))
        if not text_value:
            labels.append(f"missing_{field}")
        elif field == "summary_packet_id" and text_value == "default_summary_packet":
            labels.append("missing_summary_packet_id")
        elif field == "science_direction_id" and text_value == "default_science_direction":
            labels.append("missing_science_direction_id")
        elif field == "science_direction_summary" and text_value == "Metadata-only source summary packet.":
            labels.append("missing_science_direction_summary")
        elif field == "source_locator_review_packet_ref" and text_value == "review_packet_ref_missing":
            labels.append("missing_source_locator_review_packet_ref")
    for field in _REQUIRED_LIST_FIELDS_V1:
        if not isinstance(packet.get(field), list):
            labels.append(f"invalid_{field}")
    for field in _REQUIRED_DICT_FIELDS_V1:
        if not isinstance(packet.get(field), Mapping):
            labels.append(f"invalid_{field}")

    if _compact_text(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        labels.append("invalid_schema_version")
    if _compact_text(packet.get("summary_status")) not in _ALLOWED_STATUSES_V1:
        labels.append("unsupported_summary_status")
    if _compact_text(packet.get("allowed_next_step")) not in _ALLOWED_NEXT_STEPS_V1:
        labels.append("unsupported_next_step")
    if _compact_text(packet.get("metadata_summary_scope")) not in {"ready_records_only", "metadata_only_summary", "ready_for_authorized_metadata_only_source_summary"}:
        labels.append("unsupported_metadata_summary_scope")

    if _first_non_json_safe_path(packet) is not None:
        labels.append("non_json_safe_output")

    authority_ok, authority_labels = _validate_authority_status(packet.get("authority_status"))
    if not authority_ok:
        labels.extend(authority_labels)

    safe_ok, safe_labels = _validate_safe_metadata(packet.get("safe_metadata"))
    if not safe_ok:
        labels.extend(safe_labels)

    if _contains_forbidden_markers(packet.get("science_direction_summary"), _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_authority_text")
    if _contains_forbidden_markers(packet.get("science_direction_summary"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("unsafe_hidden_private_protected_marker")
    if _contains_forbidden_markers(packet.get("science_direction_summary"), ("WESLR discovered", "confirmed discovery", "proved", "public science result", "benchmark-winning", "agi", "sentience", "consciousness")):
        labels.append("unsafe_claim_language")

    summary_records = packet.get("metadata_only_source_summaries")
    excluded_records = packet.get("excluded_records")
    blocked_records = packet.get("blocked_records")
    if not isinstance(summary_records, list) or not isinstance(excluded_records, list) or not isinstance(blocked_records, list):
        labels.append("invalid_record_containers")
    else:
        if len(summary_records) != _compact_text(packet.get("summary_record_count"), str(len(summary_records))):
            if int(_compact_text(packet.get("summary_record_count"), "-1")) != len(summary_records):
                labels.append("summary_record_count_mismatch")
        if int(_compact_text(packet.get("excluded_record_count"), "-1")) != len(excluded_records):
            labels.append("excluded_record_count_mismatch")
        if int(_compact_text(packet.get("blocked_record_count"), "-1")) != len(blocked_records):
            labels.append("blocked_record_count_mismatch")
        for record in summary_records:
            if not isinstance(record, Mapping):
                labels.append("invalid_summary_record_type")
                continue
            _validate_summary_record(record, labels)
        for record in excluded_records:
            if not isinstance(record, Mapping):
                labels.append("invalid_excluded_record_type")
                continue
            _validate_excluded_record(record, labels)
        for record in blocked_records:
            if not isinstance(record, Mapping):
                labels.append("invalid_blocked_record_type")
                continue
            _validate_blocked_record(record, labels)

    input_count = packet.get("input_review_record_count")
    if isinstance(input_count, int):
        if input_count <= 0:
            labels.append("missing_input_review_records")
        if input_count != len(summary_records) + len(excluded_records) + len(blocked_records):
            labels.append("input_review_record_count_mismatch")
    else:
        labels.append("invalid_input_review_record_count")

    for field, container in (
        ("summary_record_count", summary_records),
        ("excluded_record_count", excluded_records),
        ("blocked_record_count", blocked_records),
    ):
        if not isinstance(packet.get(field), int):
            labels.append(f"invalid_{field}")

    # Disallow any evidence/truth/source-content implication in routed text fields.
    for field_name in ("metadata_summary_scope", "operator_review_need", "summary_status"):
        field_value = packet.get(field_name)
        if _contains_forbidden_markers(field_value, (".weslr",)):
            labels.append("unsafe_weslr_io_implication")
        if _contains_forbidden_markers(field_value, ("database write", "database writes", "database")):
            labels.append("unsafe_database_write_implication")
        if _contains_forbidden_markers(field_value, ("memory mutation", "memory", "project mutation", "project")):
            labels.append("unsafe_memory_project_mutation_implication")
        if _contains_forbidden_markers(field_value, ("behavior pack", "behavior-pack", "promotion")):
            labels.append("unsafe_behavior_pack_promotion_implication")

    labels = list(dict.fromkeys(labels))
    if labels:
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": labels,
            "validation_posture": "blocked",
            "summary_text": "Blocked authorized metadata-only source summary packet.",
        }

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
        "validation_posture": "valid",
        "summary_text": "Valid authorized metadata-only source summary packet.",
    }



def summarize_mlcf_authorized_metadata_only_source_summary_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    packet = packet if isinstance(packet, Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "summary_packet_id": _compact_text(packet.get("summary_packet_id")),
        "science_direction_id": _compact_text(packet.get("science_direction_id")),
        "source_locator_review_packet_ref": _compact_text(packet.get("source_locator_review_packet_ref")),
        "summary_status": _compact_text(packet.get("summary_status")),
        "summary_record_count": int(packet.get("summary_record_count", 0)) if str(packet.get("summary_record_count", 0)).isdigit() else packet.get("summary_record_count", 0),
        "excluded_record_count": int(packet.get("excluded_record_count", 0)) if str(packet.get("excluded_record_count", 0)).isdigit() else packet.get("excluded_record_count", 0),
        "blocked_record_count": int(packet.get("blocked_record_count", 0)) if str(packet.get("blocked_record_count", 0)).isdigit() else packet.get("blocked_record_count", 0),
        "allowed_next_step": _compact_text(packet.get("allowed_next_step")),
        "validation_posture": validation.get("validation_posture", "blocked"),
        "summary_text": _compact_text(packet.get("science_direction_summary"), "Metadata-only source summary packet.")[:220],
    }



def to_mlcf_authorized_metadata_only_source_summary_packet_json_safe_v1(packet: Any) -> Any:
    return _json_safe(deepcopy(packet))



def build_initial_mlcf_authorized_metadata_only_source_summary_examples_v1() -> list[dict[str, Any]]:
    from weslr.mlcf_source_locator_organization_review_packet import build_initial_mlcf_source_locator_organization_review_packet_examples_v1

    examples: list[dict[str, Any]] = []
    review_packets = build_initial_mlcf_source_locator_organization_review_packet_examples_v1()
    for review_packet in review_packets:
        if review_packet["review_packet_id"] == "frontier_space_fixture_locator_review_packet":
            records = review_packet["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"]
            examples.append(
                build_mlcf_authorized_metadata_only_source_summary_packet_v1(
                    summary_packet_id="frontier_space_ready_metadata_summary_packet",
                    science_direction_id=review_packet["science_direction_id"],
                    science_direction_summary="Metadata-only summary packet for ready frontier-space locators.",
                    source_locator_review_packet_ref=review_packet["review_packet_id"],
                    metadata_summary_scope="ready_records_only",
                    review_records=records,
                )
            )
        elif review_packet["review_packet_id"] == "rf_material_floorplan_locator_review_packet":
            records = review_packet["bucketed_locator_records"]["keep_for_operator_review"]
            examples.append(
                build_mlcf_authorized_metadata_only_source_summary_packet_v1(
                    summary_packet_id="rf_operator_review_only_metadata_summary_packet",
                    science_direction_id=review_packet["science_direction_id"],
                    science_direction_summary="Metadata-only summary packet for operator-review-only RF locators.",
                    source_locator_review_packet_ref=review_packet["review_packet_id"],
                    metadata_summary_scope="ready_records_only",
                    review_records=records,
                )
            )
        elif review_packet["review_packet_id"] == "broken_locator_review_packet":
            records = review_packet["bucketed_locator_records"]["blocked"]
            examples.append(
                build_mlcf_authorized_metadata_only_source_summary_packet_v1(
                    summary_packet_id="blocked_locator_metadata_summary_packet",
                    science_direction_id=review_packet["science_direction_id"],
                    science_direction_summary="Metadata-only blocked locator packet.",
                    source_locator_review_packet_ref=review_packet["review_packet_id"],
                    metadata_summary_scope="ready_records_only",
                    review_records=records,
                )
            )
    return examples
