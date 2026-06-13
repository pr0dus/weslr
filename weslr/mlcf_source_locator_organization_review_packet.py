"""WESLR MLCF Source Locator Organization Review Packet V1.

Metadata-only helpers for organizing validated source locator records into
review buckets. This module does not browse, fetch, ingest, retain raw
content, summarize source content, or authorize runtime/public claims.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.mlcf_metadata_only_source_locator_record import (
    build_initial_mlcf_metadata_only_source_locator_record_examples_v1,
    build_mlcf_metadata_only_source_locator_record_v1,
    validate_mlcf_metadata_only_source_locator_record_v1,
)

SCHEMA_VERSION_V1 = "mlcf_source_locator_organization_review_packet_v1"
HELPER_FAMILY_V1 = "mlcf_source_locator_organization_review_packet"

_ALLOWED_BUCKET_IDS_V1 = (
    "keep_for_operator_review",
    "ready_for_authorized_metadata_only_source_summary",
    "needs_repair",
    "reject",
    "blocked",
    "duplicate_or_low_value",
)

_ALLOWED_NEXT_STEPS_V1 = (
    "operator_review",
    "prepare_authorized_metadata_only_source_summary",
    "repair_locator_records",
    "reject_locator_batch",
    "blocked_by_safety",
)

_ALLOWED_DECISION_REASONS_V1 = (
    "keep_for_operator_review",
    "ready_for_authorized_metadata_only_source_summary",
    "needs_repair_missing_or_invalid_metadata",
    "reject_locator",
    "blocked_private_hidden_or_protected_source",
    "duplicate_or_low_value",
    "unsafe_authority_or_claim_language",
)

_AUTHORITY_FALSE_FLAGS_V1 = (
    "source_ingestion_authorized",
    "raw_retention_authorized",
    "web_call_authority",
    "github_call_authority",
    "searxng_call_authority",
    "source_access_authorized",
    "source_fetching_authority",
    "source_summary_authority",
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
    "public claim",
    "source ingestion",
    "raw retention",
    "web call",
    "github call",
    "searxng call",
    "source fetching",
    "source summary",
    "behavior pack",
    "database write",
    "memory mutation",
    "project mutation",
    "cross-user leakage",
    ".weslr",
)

_SAFE_NON_CLAIM_CONTEXT_MARKERS_V1 = (
    "frontier/discovery-style fixture",
    "future frontier/discovery-style artifact routing",
    "synthetic space-discovery-style locator fixture",
    "frontier-style locator fixture",
    "discovery-style locator fixture",
    "candidate artifact routing test",
    "not a discovery claim",
    "metadata-only non-claim context",
    "frontier_space_discovery_style_locator",
)

_EXPLICIT_CLAIM_LANGUAGE_MARKERS_V1 = (
    "weslr discovered",
    "confirmed discovery",
    "discovery confirmed",
    "discovered",
    "proof claim",
    "proved",
    "benchmark-winning",
    "benchmark winning",
    "official result",
    "public science result",
    "public science",
    "community-only claim",
    "community claim confirmed",
    "agi",
    "sentience",
    "consciousness",
    "competition-winning",
    "competition winning",
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

_REQUIRED_FIELD_NAMES_V1 = (
    "schema_version",
    "review_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "source_packet_origin",
    "input_locator_count",
    "bucketed_locator_records",
    "bucket_counts",
    "source_class_distribution",
    "authority_distribution",
    "evidence_role_distribution",
    "blocked_locator_count",
    "ready_for_summary_count",
    "needs_repair_count",
    "operator_review_count",
    "duplicate_or_low_value_count",
    "organization_notes",
    "operator_review_need",
    "allowed_next_step",
    "blocked_conditions",
    "authority_status",
    "safe_metadata",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "review_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "source_packet_origin",
    "organization_notes",
    "operator_review_need",
    "allowed_next_step",
)

_REQUIRED_LIST_FIELDS_V1 = ("blocked_conditions",)

_REQUIRED_DICT_FIELDS_V1 = (
    "bucketed_locator_records",
    "bucket_counts",
    "source_class_distribution",
    "authority_distribution",
    "evidence_role_distribution",
    "authority_status",
    "safe_metadata",
)

_RECORD_REQUIRED_TEXT_FIELDS_V1 = (
    "locator_id",
    "science_direction_id",
    "query_family",
    "source_class",
    "candidate_title",
    "candidate_url_or_identifier",
    "candidate_domain",
    "authority_level_guess",
    "evidence_role_guess",
    "relevance_reason",
    "freshness_status",
    "access_license_status",
    "privacy_status",
    "operator_review_need",
    "allowed_next_step",
)

_READY_SOURCE_CLASSES_V1 = {
    "official_standard",
    "official_government_or_agency_data",
    "official_vendor_documentation",
    "public_research_paper",
    "public_dataset",
    "github_repository",
}

_NONREADY_SOURCE_CLASSES_V1 = {"public_lab_or_university_artifact", "public_benchmark_or_test_suite"}


def allowed_mlcf_locator_review_bucket_ids_v1() -> tuple[str, ...]:
    return _ALLOWED_BUCKET_IDS_V1


def allowed_mlcf_locator_review_packet_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEPS_V1


def allowed_mlcf_locator_review_decision_reasons_v1() -> tuple[str, ...]:
    return _ALLOWED_DECISION_REASONS_V1


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    elif isinstance(payload, list):
        merged["locator_records"] = payload
    elif payload is not None:
        merged["locator_records"] = payload
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
    return any(marker in lowered for marker in markers)


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
            "status": "metadata_only_locator_organization_review_packet",
            "boundary_notes": "metadata-only source locator organization review packet boundary",
        }
    )
    return status


def _default_safe_metadata() -> dict[str, Any]:
    return {
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_raw_content": True,
        "no_ingestion": True,
        "no_claims": True,
        "no_web_calls": True,
        "no_github_calls": True,
        "no_searxng_calls": True,
        "no_source_fetching": True,
        "no_source_summary": True,
        "operator_review_required": True,
        "source_ingestion_authorized": False,
        "raw_retention_authorized": False,
        "web_call_authority": False,
        "github_call_authority": False,
        "searxng_call_authority": False,
        "source_fetching_authorized": False,
        "source_summary_authorized": False,
        "source_summary_authority": False,
        "source_access_authorized": False,
        "public_claim_authorized": False,
        "final_answer_authority": False,
        "discovery_claim_authorized": False,
        "proof_claim_authorized": False,
        "agi_claim_authorized": False,
        "benchmark_claim_authorized": False,
        "public_science_claim_authorized": False,
    }


def _normalize_record(record: Any) -> dict[str, Any]:
    if isinstance(record, Mapping):
        normalized = deepcopy(dict(record))
        if isinstance(normalized.get("blocked_conditions"), (list, tuple)):
            normalized["blocked_conditions"] = _normalize_text_list(normalized.get("blocked_conditions"))
        return normalized
    return {"invalid_record": record}


def _record_signature(record: Mapping[str, Any]) -> str:
    payload = "|".join(
        [
            _compact_text(record.get("source_class")),
            _compact_text(record.get("candidate_title")),
            _compact_text(record.get("candidate_url_or_identifier")),
            _compact_text(record.get("candidate_domain")),
            _compact_text(record.get("authority_level_guess")),
            _compact_text(record.get("evidence_role_guess")),
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


def _missing_record_fields(record: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in _RECORD_REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(record.get(field)):
            missing.append(field)
    for field in ("authority_status", "safe_metadata"):
        if field not in record or not isinstance(record.get(field), Mapping):
            missing.append(field)
    if not isinstance(record.get("blocked_conditions"), list):
        missing.append("blocked_conditions")
    return missing


def _record_needs_repair_labels(validation: Mapping[str, Any]) -> list[str]:
    blocked = _normalize_text_list(validation.get("blocked_labels"))
    repairable: list[str] = []
    for label in blocked:
        if label.startswith("missing_") or label.startswith("invalid_") or label == "missing_blocked_conditions":
            repairable.append(label)
    return repairable


def _record_blocking_labels(validation: Mapping[str, Any]) -> list[str]:
    blocked = _normalize_text_list(validation.get("blocked_labels"))
    return [
        label
        for label in blocked
        if label.startswith("unsafe_")
        or label.startswith("blocked_private_or_hidden_source_")
        or label in {"github_locator_claims_official_science_authority", "non_json_safe_output"}
    ]


def _record_has_safe_summary_conditions(record: Mapping[str, Any]) -> bool:
    authority_status = record.get("authority_status")
    safe_metadata = record.get("safe_metadata")
    if not isinstance(authority_status, Mapping) or not isinstance(safe_metadata, Mapping):
        return False
    if _compact_text(record.get("access_license_status")) not in {"open", "permissioned"}:
        return False
    if _compact_text(record.get("privacy_status")) == "high":
        return False
    if _compact_text(record.get("freshness_status")) not in {"current", "recent"}:
        return False
    for key, value in authority_status.items():
        if key in {"status", "boundary_notes", "all_authority_flags_false"}:
            continue
        if value is True:
            return False
    if authority_status.get("all_authority_flags_false") is not True:
        return False
    if safe_metadata.get("source_summary_authorized") is True:
        return False
    if safe_metadata.get("source_access_authorized") is True:
        return False
    if safe_metadata.get("source_summary_authority") is True:
        return False
    return True


def classify_mlcf_locator_record_for_review_v1(record: Any, *, duplicate_signatures: set[str] | None = None) -> dict[str, Any]:
    normalized = _normalize_record(record)
    validation = validate_mlcf_metadata_only_source_locator_record_v1(normalized)
    blocked_labels = _normalize_text_list(validation.get("blocked_labels"))
    signature = _record_signature(normalized) if isinstance(normalized, Mapping) else "invalid"
    duplicate_seen = duplicate_signatures is not None and signature in duplicate_signatures
    if duplicate_signatures is not None:
        duplicate_signatures.add(signature)

    bucket = "keep_for_operator_review"
    next_step = "operator_review"
    reason = "keep_for_operator_review"

    if duplicate_seen:
        bucket = "duplicate_or_low_value"
        reason = "duplicate_or_low_value"
    elif not isinstance(record, Mapping):
        bucket = "needs_repair"
        next_step = "repair_locator_records"
        reason = "needs_repair_missing_or_invalid_metadata"
    else:
        missing = _missing_record_fields(normalized)
        blocking = _record_blocking_labels(validation)
        repairable = _record_needs_repair_labels(validation)
        source_class = _compact_text(normalized.get("source_class"))
        authority_level = _compact_text(normalized.get("authority_level_guess"))
        evidence_role = _compact_text(normalized.get("evidence_role_guess"))

        if blocking:
            bucket = "blocked"
            next_step = "blocked_by_safety"
            reason = "unsafe_authority_or_claim_language"
        elif source_class == "blocked_private_or_hidden_source" or _compact_text(normalized.get("allowed_next_step")) == "blocked_by_safety":
            bucket = "blocked"
            next_step = "blocked_by_safety"
            reason = "blocked_private_hidden_or_protected_source"
        elif missing or repairable or authority_level == "" or evidence_role == "":
            bucket = "needs_repair"
            next_step = "repair_locator_records"
            reason = "needs_repair_missing_or_invalid_metadata"
        elif source_class == "github_repository":
            if _record_has_safe_summary_conditions(normalized):
                bucket = "ready_for_authorized_metadata_only_source_summary"
                next_step = "prepare_authorized_metadata_only_source_summary"
                reason = "ready_for_authorized_metadata_only_source_summary"
            else:
                reason = "keep_for_operator_review"
        elif source_class in _READY_SOURCE_CLASSES_V1:
            if _record_has_safe_summary_conditions(normalized):
                bucket = "ready_for_authorized_metadata_only_source_summary"
                next_step = "prepare_authorized_metadata_only_source_summary"
                reason = "ready_for_authorized_metadata_only_source_summary"
            else:
                reason = "keep_for_operator_review"
        elif source_class in _NONREADY_SOURCE_CLASSES_V1:
            reason = "keep_for_operator_review"
        elif _compact_text(normalized.get("authority_level_guess")) in {"community_signal", "unknown_authority"}:
            bucket = "reject"
            next_step = "reject_locator_batch"
            reason = "reject_locator"
        else:
            reason = "keep_for_operator_review"

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "record_signature": signature,
        "review_bucket": bucket,
        "next_step": next_step,
        "decision_reason": reason,
        "locator_id": _compact_text(normalized.get("locator_id")),
        "source_class": _compact_text(normalized.get("source_class")),
        "authority_level_guess": _compact_text(normalized.get("authority_level_guess")),
        "evidence_role_guess": _compact_text(normalized.get("evidence_role_guess")),
        "blocked_labels": blocked_labels,
        "validation_posture": validation.get("validation_posture", "blocked"),
    }


def _default_packet(locator_records: list[Any] | None = None) -> dict[str, Any]:
    records = locator_records or []
    bucketed = {bucket: [] for bucket in _ALLOWED_BUCKET_IDS_V1}
    bucket_counts = {bucket: 0 for bucket in _ALLOWED_BUCKET_IDS_V1}
    signatures: set[str] = set()
    source_class_counter: Counter[str] = Counter()
    authority_counter: Counter[str] = Counter()
    evidence_counter: Counter[str] = Counter()
    blocked_conditions: list[str] = []

    for raw_record in records:
        normalized = _normalize_record(raw_record)
        classification = classify_mlcf_locator_record_for_review_v1(normalized, duplicate_signatures=signatures)
        bucket = classification["review_bucket"]
        bucket_counts[bucket] += 1
        bucket_record = deepcopy(normalized)
        bucket_record["review_bucket"] = bucket
        bucket_record["review_next_step"] = classification["next_step"]
        bucket_record["review_decision_reason"] = classification["decision_reason"]
        bucket_record["review_record_signature"] = classification["record_signature"]
        bucketed[bucket].append(bucket_record)

        source_class = _compact_text(normalized.get("source_class")) or "unknown"
        authority_level = _compact_text(normalized.get("authority_level_guess")) or "unknown"
        evidence_role = _compact_text(normalized.get("evidence_role_guess")) or "unknown"
        source_class_counter[source_class] += 1
        authority_counter[authority_level] += 1
        evidence_counter[evidence_role] += 1

        reason = classification["decision_reason"]
        if reason and reason not in blocked_conditions:
            blocked_conditions.append(reason)

    blocked_count = bucket_counts["blocked"]
    ready_count = bucket_counts["ready_for_authorized_metadata_only_source_summary"]
    needs_repair_count = bucket_counts["needs_repair"]
    operator_count = bucket_counts["keep_for_operator_review"]
    duplicate_count = bucket_counts["duplicate_or_low_value"]

    if blocked_count > 0:
        next_step = "blocked_by_safety"
    elif needs_repair_count > 0:
        next_step = "repair_locator_records"
    elif bucket_counts["reject"] > 0:
        next_step = "reject_locator_batch"
    elif ready_count > 0:
        next_step = "prepare_authorized_metadata_only_source_summary"
    else:
        next_step = "operator_review"

    notes = [
        f"Metadata-only organization review packet for {len(records)} locator records.",
        f"Buckets: keep={operator_count}, ready={ready_count}, needs_repair={needs_repair_count}, reject={bucket_counts['reject']}, blocked={blocked_count}, duplicate_or_low_value={duplicate_count}.",
    ]
    if blocked_count:
        notes.append("Blocked records stay blocked and do not advance to summary or ingestion.")
    if ready_count:
        notes.append("Ready records remain metadata-only and do not grant summary authority.")
    if duplicate_count:
        notes.append("Duplicate or low-value records remain review-only.")

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "review_packet_id": "default_review_packet",
        "science_direction_id": "default_science_direction",
        "science_direction_summary": "Metadata-only source locator organization review packet.",
        "source_packet_origin": "validated_metadata_only_source_locator_records",
        "input_locator_count": len(records),
        "bucketed_locator_records": bucketed,
        "bucket_counts": bucket_counts,
        "source_class_distribution": dict(source_class_counter),
        "authority_distribution": dict(authority_counter),
        "evidence_role_distribution": dict(evidence_counter),
        "blocked_locator_count": blocked_count,
        "ready_for_summary_count": ready_count,
        "needs_repair_count": needs_repair_count,
        "operator_review_count": operator_count,
        "duplicate_or_low_value_count": duplicate_count,
        "organization_notes": " ".join(notes),
        "operator_review_need": (
            "Operator review required; blocked records preserved."
            if blocked_count
            else "Operator review required for metadata-only organization."
        ),
        "allowed_next_step": next_step,
        "blocked_conditions": blocked_conditions,
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
    }


def build_mlcf_source_locator_organization_review_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged = _merge_payload(payload, **overrides)
    locator_records = merged.pop("locator_records", None)
    packet = _default_packet(list(locator_records) if locator_records is not None else [])
    packet.update(merged)
    if locator_records is not None:
        packet["locator_records"] = list(locator_records)
    packet["bucketed_locator_records"] = packet.get("bucketed_locator_records", {bucket: [] for bucket in _ALLOWED_BUCKET_IDS_V1})
    packet["bucket_counts"] = packet.get("bucket_counts", {bucket: 0 for bucket in _ALLOWED_BUCKET_IDS_V1})
    packet["source_class_distribution"] = dict(packet.get("source_class_distribution", {}))
    packet["authority_distribution"] = dict(packet.get("authority_distribution", {}))
    packet["evidence_role_distribution"] = dict(packet.get("evidence_role_distribution", {}))
    packet["blocked_conditions"] = _normalize_text_list(packet.get("blocked_conditions"))
    packet["authority_status"] = dict(packet.get("authority_status", _default_authority_status()))
    packet["safe_metadata"] = dict(packet.get("safe_metadata", _default_safe_metadata()))
    packet["input_locator_count"] = int(packet.get("input_locator_count", len(locator_records or [])))
    return packet


def _expected_bucket_counts(packet: Mapping[str, Any]) -> dict[str, int]:
    counts = {bucket: 0 for bucket in _ALLOWED_BUCKET_IDS_V1}
    bucketed = packet.get("bucketed_locator_records")
    if not isinstance(bucketed, Mapping):
        return counts
    for bucket in _ALLOWED_BUCKET_IDS_V1:
        value = bucketed.get(bucket, [])
        if isinstance(value, list):
            counts[bucket] = len(value)
    return counts


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
    if _compact_text(authority_status.get("status")) != "metadata_only_locator_organization_review_packet":
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
    for flag in (
        "metadata_only",
        "json_safe",
        "non_public",
        "no_raw_content",
        "no_ingestion",
        "no_claims",
        "no_web_calls",
        "no_github_calls",
        "no_searxng_calls",
        "no_source_fetching",
        "no_source_summary",
        "operator_review_required",
    ):
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


def _validate_packet_records(packet: Mapping[str, Any], labels: list[str]) -> None:
    bucketed = packet.get("bucketed_locator_records")
    if not isinstance(bucketed, Mapping):
        labels.append("invalid_bucketed_locator_records")
        return

    seen: set[str] = set()
    for bucket in _ALLOWED_BUCKET_IDS_V1:
        records = bucketed.get(bucket)
        if not isinstance(records, list):
            labels.append(f"invalid_bucket_list:{bucket}")
            continue
        for index, record in enumerate(records):
            if not isinstance(record, Mapping):
                labels.append(f"invalid_record_type:{bucket}[{index}]")
                continue
            if _first_non_json_safe_path(record, f"bucketed_locator_records.{bucket}[{index}]") is not None:
                labels.append("non_json_safe_output")
            classification = classify_mlcf_locator_record_for_review_v1(record, duplicate_signatures=seen)
            if classification["review_bucket"] != bucket:
                labels.append(f"bucket_mismatch:{_compact_text(classification['review_bucket'])}->{bucket}")
            if bucket == "blocked" and classification["decision_reason"] != "blocked_private_hidden_or_protected_source":
                labels.append("blocked_record_must_stay_blocked")
            if classification["record_signature"] in seen and bucket != "duplicate_or_low_value" and classification["review_bucket"] == "duplicate_or_low_value":
                labels.append("duplicate_record_not_bucketed")


def validate_mlcf_source_locator_organization_review_packet_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_packet_type"],
            "validation_posture": "blocked",
            "summary_text": "Invalid source locator organization review packet.",
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
            "summary_text": "Missing required source locator organization review packet fields.",
        }

    for field in _REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(packet.get(field)):
            labels.append(f"missing_{field}")
    for field in _REQUIRED_LIST_FIELDS_V1:
        if not isinstance(packet.get(field), list):
            labels.append(f"invalid_{field}")
    for field in _REQUIRED_DICT_FIELDS_V1:
        if not isinstance(packet.get(field), Mapping):
            labels.append(f"invalid_{field}")

    if _compact_text(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        labels.append("invalid_schema_version")
    if _compact_text(packet.get("allowed_next_step")) not in _ALLOWED_NEXT_STEPS_V1:
        labels.append("invalid_allowed_next_step")

    allowed_buckets = set(_ALLOWED_BUCKET_IDS_V1)
    bucketed = packet.get("bucketed_locator_records")
    if isinstance(bucketed, Mapping):
        if set(bucketed.keys()) != allowed_buckets:
            labels.append("invalid_bucket_ids")
    else:
        labels.append("invalid_bucketed_locator_records")

    if _first_non_json_safe_path(packet) is not None:
        labels.append("non_json_safe_output")

    authority_ok, authority_labels = _validate_authority_status(packet.get("authority_status"))
    if not authority_ok:
        labels.extend(authority_labels)

    safe_ok, safe_labels = _validate_safe_metadata(packet.get("safe_metadata"))
    if not safe_ok:
        labels.extend(safe_labels)

    for field_name in ("organization_notes", "science_direction_summary", "source_packet_origin"):
        field_value = packet.get(field_name)
        if _contains_forbidden_markers(field_value, (".weslr",)):
            labels.append("unsafe_weslr_io_implication")
        if _contains_forbidden_markers(field_value, ("database write", "database writes", "database")):
            labels.append("unsafe_database_write_implication")
        if _contains_forbidden_markers(field_value, ("memory mutation", "memory", "project mutation", "project")):
            labels.append("unsafe_memory_project_mutation_implication")
        if _contains_forbidden_markers(field_value, ("behavior pack", "behavior-pack", "promotion")):
            labels.append("unsafe_behavior_pack_promotion_implication")
        if _contains_forbidden_markers(field_value, _AUTHORITY_TEXT_MARKERS_V1):
            labels.append("unsafe_authority_text")
        if _contains_forbidden_markers(field_value, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            labels.append("unsafe_hidden_private_protected_marker")
    if _contains_forbidden_markers(packet.get("science_direction_summary"), _EXPLICIT_CLAIM_LANGUAGE_MARKERS_V1):
        labels.append("unsafe_claim_language")
    elif not _contains_forbidden_markers(packet.get("science_direction_summary"), _SAFE_NON_CLAIM_CONTEXT_MARKERS_V1) and _contains_forbidden_markers(packet.get("science_direction_summary"), _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_claim_language")

    _validate_packet_records(packet, labels)

    expected_counts = _expected_bucket_counts(packet)
    packet_counts = packet.get("bucket_counts")
    if isinstance(packet_counts, Mapping):
        for bucket in _ALLOWED_BUCKET_IDS_V1:
            if _compact_text(packet_counts.get(bucket, 0)) != _compact_text(expected_counts[bucket]):
                labels.append(f"bucket_count_mismatch:{bucket}")
    else:
        labels.append("invalid_bucket_counts")

    if _compact_text(packet.get("input_locator_count")) != _compact_text(
        sum(expected_counts[bucket] for bucket in _ALLOWED_BUCKET_IDS_V1)
    ):
        labels.append("input_locator_count_mismatch")

    for field in ("blocked_locator_count", "ready_for_summary_count", "needs_repair_count", "operator_review_count", "duplicate_or_low_value_count"):
        if not isinstance(packet.get(field), int):
            labels.append(f"invalid_{field}")

    if labels:
        labels = list(dict.fromkeys(labels))
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": labels,
            "validation_posture": "blocked",
            "summary_text": "Blocked source locator organization review packet.",
        }

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
        "validation_posture": "valid",
        "summary_text": "Valid source locator organization review packet.",
    }


def summarize_mlcf_source_locator_organization_review_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_mlcf_source_locator_organization_review_packet_v1(packet)
    packet = packet if isinstance(packet, Mapping) else {}
    bucket_counts = packet.get("bucket_counts") if isinstance(packet.get("bucket_counts"), Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "review_packet_id": _compact_text(packet.get("review_packet_id")),
        "science_direction_id": _compact_text(packet.get("science_direction_id")),
        "source_packet_origin": _compact_text(packet.get("source_packet_origin")),
        "blocked_locator_count": _compact_text(packet.get("blocked_locator_count", 0)),
        "ready_for_summary_count": _compact_text(packet.get("ready_for_summary_count", 0)),
        "needs_repair_count": _compact_text(packet.get("needs_repair_count", 0)),
        "operator_review_count": _compact_text(packet.get("operator_review_count", 0)),
        "duplicate_or_low_value_count": _compact_text(packet.get("duplicate_or_low_value_count", 0)),
        "allowed_next_step": _compact_text(packet.get("allowed_next_step")),
        "validation_posture": validation.get("validation_posture", "blocked"),
        "summary_text": _compact_text(packet.get("organization_notes"), "Metadata-only source locator organization review packet.")[:220],
        "bucket_counts": {
            bucket: int(bucket_counts.get(bucket, 0)) if str(bucket_counts.get(bucket, 0)).isdigit() else bucket_counts.get(bucket, 0)
            for bucket in _ALLOWED_BUCKET_IDS_V1
        },
    }


def to_mlcf_source_locator_organization_review_packet_json_safe_v1(packet: Any) -> Any:
    return _json_safe(deepcopy(packet))


def build_initial_mlcf_source_locator_organization_review_packet_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []

    rf_records = build_initial_mlcf_metadata_only_source_locator_record_examples_v1()
    examples.append(
        build_mlcf_source_locator_organization_review_packet_v1(
            review_packet_id="rf_material_floorplan_locator_review_packet",
            science_direction_id="rf_material_floorplan_sparse_change_map",
            science_direction_summary="Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.",
            source_packet_origin="validated_metadata_only_source_locator_records",
            locator_records=rf_records,
            organization_notes="RF/material/floor-plan locator review packet using official/public/GitHub/lab and blocked source metadata.",
        )
    )

    frontier_records = [
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="frontier_agency_locator_record",
            science_direction_id="frontier_space_discovery_style_locator_fixture",
            query_family="frontier_space_discovery_style_locator",
            source_class="official_government_or_agency_data",
            candidate_title="Space agency candidate object locator",
            candidate_url_or_identifier="https://example.invalid/agency/candidate-object",
            candidate_domain="example.invalid",
            authority_level_guess="official_primary",
            evidence_role_guess="domain_context",
            relevance_reason="Metadata-only agency-style locator for a future candidate artifact.",
            freshness_status="recent",
            access_license_status="open",
            privacy_status="low",
            operator_review_need="Operator review required before any source access.",
            allowed_next_step="operator_review",
            blocked_conditions=["No source access", "No ingestion"],
        ),
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="frontier_public_paper_locator_record",
            science_direction_id="frontier_space_discovery_style_locator_fixture",
            query_family="frontier_space_discovery_style_locator",
            source_class="public_research_paper",
            candidate_title="Candidate astronomical object paper locator",
            candidate_url_or_identifier="https://example.invalid/paper/candidate-astronomical-object",
            candidate_domain="example.invalid",
            authority_level_guess="public_primary",
            evidence_role_guess="prior_art",
            relevance_reason="Metadata-only paper locator for candidate astronomical object context.",
            freshness_status="recent",
            access_license_status="permissioned",
            privacy_status="low",
            operator_review_need="Operator review required before paper access.",
            allowed_next_step="operator_review",
            blocked_conditions=["No paper fetching", "No ingestion"],
        ),
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="frontier_public_dataset_locator_record",
            science_direction_id="frontier_space_discovery_style_locator_fixture",
            query_family="frontier_space_discovery_style_locator",
            source_class="public_dataset",
            candidate_title="Telescope observation archive locator",
            candidate_url_or_identifier="https://example.invalid/archive/telescope-observation",
            candidate_domain="example.invalid",
            authority_level_guess="public_primary",
            evidence_role_guess="measurement_data",
            relevance_reason="Metadata-only dataset/archive locator for candidate observation routing.",
            freshness_status="current",
            access_license_status="open",
            privacy_status="medium",
            operator_review_need="Operator review required before archive access.",
            allowed_next_step="operator_review",
            blocked_conditions=["No archive fetching", "No ingestion"],
        ),
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="frontier_lab_locator_record",
            science_direction_id="frontier_space_discovery_style_locator_fixture",
            query_family="frontier_space_discovery_style_locator",
            source_class="public_lab_or_university_artifact",
            candidate_title="University observatory follow-up locator",
            candidate_url_or_identifier="https://example.invalid/university/observatory-follow-up",
            candidate_domain="example.invalid",
            authority_level_guess="public_secondary",
            evidence_role_guess="replication_target",
            relevance_reason="Metadata-only lab locator for follow-up artifact routing.",
            freshness_status="recent",
            access_license_status="open",
            privacy_status="low",
            operator_review_need="Operator review required before lab artifact access.",
            allowed_next_step="operator_review",
            blocked_conditions=["No lab fetching", "No ingestion"],
        ),
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="frontier_blocked_locator_record",
            science_direction_id="frontier_space_discovery_style_locator_fixture",
            query_family="frontier_space_discovery_style_locator",
            source_class="blocked_private_or_hidden_source",
            candidate_title="Blocked forum locator record",
            candidate_url_or_identifier="blocked://forum/confirmed-discovery",
            candidate_domain="blocked.local",
            authority_level_guess="blocked",
            evidence_role_guess="not_authoritative_context",
            relevance_reason="This locator remains blocked by safety.",
            freshness_status="unknown",
            access_license_status="blocked",
            privacy_status="high",
            operator_review_need="Operator review required; source is blocked by safety.",
            allowed_next_step="blocked_by_safety",
            blocked_conditions=["Private source", "Hidden source", "Protected source"],
        ),
    ]
    examples.append(
        build_mlcf_source_locator_organization_review_packet_v1(
            review_packet_id="frontier_space_fixture_locator_review_packet",
            science_direction_id="frontier_space_discovery_style_locator_fixture",
            science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space, used only to test locator-to-future-candidate-artifact routing.",
            source_packet_origin="validated_metadata_only_source_locator_records",
            locator_records=frontier_records,
            organization_notes="Frontier/space fixture review packet with metadata-only routing and blocked source metadata preserved safely.",
        )
    )

    broken_records = [
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="broken_missing_fields_locator_record",
            science_direction_id="broken_locator_review_packet",
            query_family="broken_locator_review_packet",
            source_class="official_standard",
            candidate_title="",
            candidate_url_or_identifier="",
            candidate_domain="",
            authority_level_guess="official_primary",
            evidence_role_guess="definition_or_standard",
            relevance_reason="",
            freshness_status="",
            access_license_status="",
            privacy_status="",
            operator_review_need="",
            allowed_next_step="operator_review",
            blocked_conditions=[],
        ),
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="broken_unsafe_authority_locator_record",
            science_direction_id="broken_locator_review_packet",
            query_family="broken_locator_review_packet",
            source_class="public_research_paper",
            candidate_title="Broken authority attempt",
            candidate_url_or_identifier="https://example.invalid/broken/authority",
            candidate_domain="example.invalid",
            authority_level_guess="public_primary",
            evidence_role_guess="prior_art",
            relevance_reason="Attempting an unsafe authority flip for testing.",
            freshness_status="recent",
            access_license_status="open",
            privacy_status="low",
            operator_review_need="Operator review required before any source access.",
            allowed_next_step="operator_review",
            blocked_conditions=["No source access"],
        ),
    ]
    broken_records[1]["authority_status"]["source_ingestion_authorized"] = True
    examples.append(
        build_mlcf_source_locator_organization_review_packet_v1(
            review_packet_id="broken_locator_review_packet",
            science_direction_id="broken_locator_review_packet",
            science_direction_summary="Broken review packet used to verify fail-closed routing for missing metadata and unsafe authority attempts.",
            source_packet_origin="validated_metadata_only_source_locator_records",
            locator_records=broken_records,
            organization_notes="Broken packet with missing metadata and an unsafe authority attempt.",
        )
    )

    return examples
