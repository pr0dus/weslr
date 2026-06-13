"""WESLR MLCF Metadata-Only Source Locator Record V1.

Deterministic, metadata-only helpers for candidate source locator records.
This module does not browse, fetch, ingest, retain raw content, or authorize
runtime/public claims/final answers.
"""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "mlcf_metadata_only_source_locator_record_v1"
HELPER_FAMILY_V1 = "mlcf_metadata_only_source_locator_record"

_ALLOWED_SOURCE_CLASSES_V1 = (
    "official_standard",
    "official_government_or_agency_data",
    "official_vendor_documentation",
    "public_research_paper",
    "public_dataset",
    "github_repository",
    "public_lab_or_university_artifact",
    "public_benchmark_or_test_suite",
    "blocked_private_or_hidden_source",
)

_ALLOWED_AUTHORITY_LEVELS_V1 = (
    "official_primary",
    "public_primary",
    "public_secondary",
    "implementation_evidence",
    "community_signal",
    "owner_context",
    "internal_context",
    "unknown_authority",
    "blocked",
)

_ALLOWED_EVIDENCE_ROLES_V1 = (
    "definition_or_standard",
    "measurement_data",
    "implementation_reference",
    "prior_art",
    "candidate_signal",
    "counterexample_source",
    "replication_target",
    "constraint_source",
    "domain_context",
    "safety_boundary_context",
    "not_authoritative_context",
)

_ALLOWED_FRESHNESS_STATUSES_V1 = ("current", "recent", "stale", "unknown")
_ALLOWED_ACCESS_LICENSE_STATUSES_V1 = ("open", "permissioned", "restricted", "blocked", "unknown")
_ALLOWED_PRIVACY_STATUSES_V1 = ("low", "medium", "high", "unknown")
_ALLOWED_NEXT_STEPS_V1 = (
    "operator_review",
    "prepare_metadata_only_source_summary",
    "reject_locator",
    "needs_repair",
    "blocked_by_safety",
)

_AUTHORITY_FALSE_FLAGS_V1 = (
    "source_ingestion_authorized",
    "raw_retention_authorized",
    "web_call_authority",
    "github_call_authority",
    "source_fetching_authorized",
    "source_summary_authorized",
    "source_access_authorized",
    "public_claim_authorized",
    "final_answer_authority",
    "discovery_claim_authorized",
    "proof_claim_authorized",
    "agi_claim_authorized",
    "benchmark_claim_authorized",
    "public_science_claim_authorized",
    "behavior_pack_promotion_authorized",
    "database_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "cross_user_leakage_authorized",
    "hidden_private_protected_authorized",
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
    "api key",
    "token",
)

_SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1 = (
    "metadata_only",
    "json_safe",
    "non_public",
    "no_raw_content",
    "no_ingestion",
    "no_claims",
    "no_web_calls",
    "no_github_calls",
    "no_source_fetching",
    "no_source_summary",
    "operator_review_required",
)

_REQUIRED_FIELD_NAMES_V1 = (
    "schema_version",
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
    "blocked_conditions",
    "authority_status",
    "safe_metadata",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
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

_REQUIRED_LIST_FIELDS_V1 = ("blocked_conditions",)


def allowed_mlcf_locator_source_classes_v1() -> tuple[str, ...]:
    return _ALLOWED_SOURCE_CLASSES_V1


def allowed_mlcf_locator_authority_levels_v1() -> tuple[str, ...]:
    return _ALLOWED_AUTHORITY_LEVELS_V1


def allowed_mlcf_locator_evidence_roles_v1() -> tuple[str, ...]:
    return _ALLOWED_EVIDENCE_ROLES_V1


def allowed_mlcf_locator_freshness_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_FRESHNESS_STATUSES_V1


def allowed_mlcf_locator_access_license_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_ACCESS_LICENSE_STATUSES_V1


def allowed_mlcf_locator_privacy_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_PRIVACY_STATUSES_V1


def allowed_mlcf_locator_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEPS_V1


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
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
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return f"<non-json-safe:{type(value).__name__}>"


def _first_non_json_safe_path(value: Any, path: str = "result") -> str | None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        return path
    if isinstance(value, tuple):
        return path
    if isinstance(value, set):
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


_SOURCE_CLASS_RULES_V1 = {
    "official_standard": {
        "authority_levels": {"official_primary"},
        "evidence_roles": {"definition_or_standard", "constraint_source"},
    },
    "official_government_or_agency_data": {
        "authority_levels": {"official_primary"},
        "evidence_roles": {"measurement_data", "domain_context"},
    },
    "official_vendor_documentation": {
        "authority_levels": {"official_primary"},
        "evidence_roles": {"implementation_reference", "constraint_source"},
    },
    "public_research_paper": {
        "authority_levels": {"public_primary"},
        "evidence_roles": {"prior_art", "replication_target"},
    },
    "public_dataset": {
        "authority_levels": {"public_primary"},
        "evidence_roles": {"measurement_data", "replication_target"},
    },
    "github_repository": {
        "authority_levels": {"implementation_evidence"},
        "evidence_roles": {"implementation_reference", "candidate_signal"},
    },
    "public_lab_or_university_artifact": {
        "authority_levels": {"public_secondary"},
        "evidence_roles": {"measurement_data", "replication_target"},
    },
    "public_benchmark_or_test_suite": {
        "authority_levels": {"public_secondary"},
        "evidence_roles": {"counterexample_source", "replication_target"},
    },
    "blocked_private_or_hidden_source": {
        "authority_levels": {"blocked"},
        "evidence_roles": {"not_authoritative_context", "safety_boundary_context"},
    },
    "blocked_private_or_hidden_source": {
        "authority_levels": {"blocked"},
        "evidence_roles": {"not_authoritative_context", "safety_boundary_context"},
    },
}


def _default_authority_status() -> dict[str, Any]:
    status = {flag: False for flag in _AUTHORITY_FALSE_FLAGS_V1}
    status.update(
        {
            "all_authority_flags_false": True,
            "status": "metadata_only_locator_record",
            "boundary_notes": "metadata-only source locator record boundary",
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
        "no_source_fetching": True,
        "no_source_summary": True,
        "operator_review_required": True,
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
        "no_sensitive_source_markers": True,
        "source_ingestion_authorized": False,
        "raw_retention_authorized": False,
        "web_call_authority": False,
        "github_call_authority": False,
        "source_fetching_authorized": False,
        "source_summary_authorized": False,
        "source_access_authorized": False,
        "public_claim_authorized": False,
        "final_answer_authority": False,
        "discovery_claim_authorized": False,
        "proof_claim_authorized": False,
        "agi_claim_authorized": False,
        "benchmark_claim_authorized": False,
        "public_science_claim_authorized": False,
    }


def _build_default_record() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "locator_id": "default_locator",
        "science_direction_id": "default_science_direction",
        "query_family": "default_query_family",
        "source_class": "official_standard",
        "candidate_title": "Default candidate locator",
        "candidate_url_or_identifier": "https://example.invalid",
        "candidate_domain": "example.invalid",
        "authority_level_guess": "official_primary",
        "evidence_role_guess": "definition_or_standard",
        "relevance_reason": "Metadata-only locator record.",
        "freshness_status": "unknown",
        "access_license_status": "unknown",
        "privacy_status": "unknown",
        "operator_review_need": "Operator review required.",
        "allowed_next_step": "operator_review",
        "blocked_conditions": [],
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
    }


def build_mlcf_metadata_only_source_locator_record_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    record = _build_default_record()
    record.update(_merge_payload(payload, **overrides))
    record["blocked_conditions"] = _normalize_text_list(record.get("blocked_conditions"))
    if isinstance(record.get("authority_status"), Mapping):
        record["authority_status"] = dict(record["authority_status"])
    if isinstance(record.get("safe_metadata"), Mapping):
        record["safe_metadata"] = dict(record["safe_metadata"])
    return record


def _blocked(labels: list[str], summary: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": False,
        "blocked": True,
        "blocked_labels": labels,
        "validation_posture": "blocked",
        "summary_text": summary,
    }


def _valid(summary: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
        "validation_posture": "valid",
        "summary_text": summary,
    }


def _validate_nonempty_text_fields(record: Mapping[str, Any], labels: list[str]) -> None:
    for field in _REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(record.get(field)):
            labels.append(f"missing_{field}")


def _validate_enum(value: Any, allowed: tuple[str, ...], label: str, labels: list[str]) -> str:
    text = _compact_text(value)
    if text not in allowed:
        labels.append(label)
    return text


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
    if _compact_text(authority_status.get("status")) != "metadata_only_locator_record":
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
    for flag in _SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1:
        if safe_metadata.get(flag) is not True:
            labels.append(f"unsafe_safe_metadata_flag:{flag}")
    # These key authority flags must remain false if present.
    false_flags = (
        "source_ingestion_authorized",
        "raw_retention_authorized",
        "web_call_authority",
        "github_call_authority",
        "source_fetching_authorized",
        "source_summary_authorized",
        "source_access_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "discovery_claim_authorized",
        "proof_claim_authorized",
        "agi_claim_authorized",
        "benchmark_claim_authorized",
        "public_science_claim_authorized",
    )
    for flag in false_flags:
        if flag in safe_metadata and safe_metadata[flag] is not False:
            labels.append(f"unsafe_safe_metadata_flag:{flag}")
    if _contains_forbidden_markers(safe_metadata, _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_safe_metadata_text")
    if _contains_forbidden_markers(safe_metadata, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("unsafe_hidden_private_protected_marker")
    return not labels, labels


def _validate_blocked_conditions(record: Mapping[str, Any]) -> list[str]:
    blocked_conditions = record.get("blocked_conditions")
    if not isinstance(blocked_conditions, list):
        return ["invalid_blocked_conditions"]
    if not blocked_conditions:
        return ["missing_blocked_conditions"]
    if any(not _compact_text(item) for item in blocked_conditions):
        return ["invalid_blocked_conditions"]
    return []


def _validate_source_class_constraints(record: Mapping[str, Any], labels: list[str]) -> None:
    source_class = _compact_text(record.get("source_class"))
    authority_level = _compact_text(record.get("authority_level_guess"))
    evidence_role = _compact_text(record.get("evidence_role_guess"))
    rule = _SOURCE_CLASS_RULES_V1.get(source_class)
    if rule is None:
        labels.append("invalid_source_class")
        return
    if authority_level not in rule["authority_levels"]:
        labels.append("invalid_authority_level")
    if evidence_role not in rule["evidence_roles"]:
        labels.append("invalid_evidence_role")
    if source_class == "github_repository" and authority_level != "implementation_evidence":
        labels.append("github_locator_claims_official_science_authority")
    if source_class == "blocked_private_or_hidden_source":
        if authority_level != "blocked":
            labels.append("blocked_private_or_hidden_source_must_be_blocked")
        if _compact_text(record.get("allowed_next_step")) != "blocked_by_safety":
            labels.append("blocked_private_or_hidden_source_bad_next_step")
        if _compact_text(record.get("access_license_status")) != "blocked":
            labels.append("blocked_private_or_hidden_source_bad_access_status")
        if _compact_text(record.get("privacy_status")) != "high":
            labels.append("blocked_private_or_hidden_source_bad_privacy_status")
        blocked_conditions = _normalize_text_list(record.get("blocked_conditions"))
        if not blocked_conditions:
            labels.append("blocked_private_or_hidden_source_missing_blocked_conditions")


def _validate_forbidden_markers(record: Mapping[str, Any], labels: list[str]) -> None:
    source_class = _compact_text(record.get("source_class"))
    if source_class == "blocked_private_or_hidden_source":
        return
    forbidden_fields = {
        key: value
        for key, value in record.items()
        if key != "blocked_conditions"
    }
    safe_context = _contains_forbidden_markers(forbidden_fields, _SAFE_NON_CLAIM_CONTEXT_MARKERS_V1)
    if _contains_forbidden_markers(forbidden_fields, (".weslr",)):
        labels.append("unsafe_weslr_io_implication")
    if _contains_forbidden_markers(forbidden_fields, ("database write", "database writes", "database")):
        labels.append("unsafe_database_write_implication")
    if _contains_forbidden_markers(forbidden_fields, ("memory mutation", "memory", "project mutation", "project")):
        labels.append("unsafe_memory_project_mutation_implication")
    if _contains_forbidden_markers(forbidden_fields, ("behavior pack", "behavior-pack", "promotion")):
        labels.append("unsafe_behavior_pack_promotion_implication")
    if _contains_forbidden_markers(forbidden_fields, _EXPLICIT_CLAIM_LANGUAGE_MARKERS_V1):
        labels.append("unsafe_claim_language")
    elif not safe_context and _contains_forbidden_markers(forbidden_fields, _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_claim_language")
    if _contains_forbidden_markers(forbidden_fields, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("unsafe_hidden_private_protected_marker")


def validate_mlcf_metadata_only_source_locator_record_v1(record: Any) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        return _blocked(["invalid_record_type"], "Invalid metadata-only source locator record.")

    labels: list[str] = []
    for field in _REQUIRED_FIELD_NAMES_V1:
        if field not in record:
            labels.append(f"missing_{field}")

    if labels:
        return _blocked(labels, "Missing required metadata-only source locator record fields.")

    _validate_nonempty_text_fields(record, labels)

    if _compact_text(record.get("schema_version")) != SCHEMA_VERSION_V1:
        labels.append("invalid_schema_version")

    _validate_enum(record.get("source_class"), _ALLOWED_SOURCE_CLASSES_V1, "invalid_source_class", labels)
    _validate_enum(record.get("authority_level_guess"), _ALLOWED_AUTHORITY_LEVELS_V1, "invalid_authority_level", labels)
    _validate_enum(record.get("evidence_role_guess"), _ALLOWED_EVIDENCE_ROLES_V1, "invalid_evidence_role", labels)
    _validate_enum(record.get("freshness_status"), _ALLOWED_FRESHNESS_STATUSES_V1, "invalid_freshness_status", labels)
    _validate_enum(record.get("access_license_status"), _ALLOWED_ACCESS_LICENSE_STATUSES_V1, "invalid_access_license_status", labels)
    _validate_enum(record.get("privacy_status"), _ALLOWED_PRIVACY_STATUSES_V1, "invalid_privacy_status", labels)
    _validate_enum(record.get("allowed_next_step"), _ALLOWED_NEXT_STEPS_V1, "invalid_allowed_next_step", labels)

    labels.extend(_validate_blocked_conditions(record))
    _validate_source_class_constraints(record, labels)

    authority_ok, authority_labels = _validate_authority_status(record.get("authority_status"))
    if not authority_ok:
        labels.extend(authority_labels)

    safe_ok, safe_labels = _validate_safe_metadata(record.get("safe_metadata"))
    if not safe_ok:
        labels.extend(safe_labels)

    if _contains_forbidden_markers(record.get("authority_status"), _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_authority_text")

    _validate_forbidden_markers(record, labels)

    if _first_non_json_safe_path(record) is not None:
        labels.append("non_json_safe_output")

    labels = list(dict.fromkeys(labels))
    if labels:
        return _blocked(labels, "Blocked metadata-only source locator record.")
    return _valid("Valid metadata-only source locator record.")


def summarize_mlcf_metadata_only_source_locator_record_v1(record: Any) -> dict[str, Any]:
    validation = validate_mlcf_metadata_only_source_locator_record_v1(record)
    packet = record if isinstance(record, Mapping) else {}
    blocked_conditions = _normalize_text_list(packet.get("blocked_conditions"))
    summary_text = _compact_text(packet.get("relevance_reason"), "Metadata-only source locator record.")
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "locator_id": _compact_text(packet.get("locator_id")),
        "science_direction_id": _compact_text(packet.get("science_direction_id")),
        "query_family": _compact_text(packet.get("query_family")),
        "source_class": _compact_text(packet.get("source_class")),
        "authority_level_guess": _compact_text(packet.get("authority_level_guess")),
        "evidence_role_guess": _compact_text(packet.get("evidence_role_guess")),
        "freshness_status": _compact_text(packet.get("freshness_status")),
        "access_license_status": _compact_text(packet.get("access_license_status")),
        "privacy_status": _compact_text(packet.get("privacy_status")),
        "blocked_conditions_count": len(blocked_conditions),
        "allowed_next_step": _compact_text(packet.get("allowed_next_step")),
        "validation_posture": validation.get("validation_posture", "blocked"),
        "summary_text": summary_text[:200],
    }


def to_mlcf_metadata_only_source_locator_record_json_safe_v1(record: Any) -> Any:
    return _json_safe(deepcopy(record))


def build_initial_mlcf_metadata_only_source_locator_record_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []

    examples.append(
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="rf_wifi_standard_locator_record",
            science_direction_id="sparse_rf_spatial_change_map_floorplan_scattering_v1",
            query_family="official_rf_wifi_standards",
            source_class="official_standard",
            candidate_title="WiFi / RF standard locator",
            candidate_url_or_identifier="https://example.invalid/standard/wifi-rf",
            candidate_domain="example.invalid",
            authority_level_guess="official_primary",
            evidence_role_guess="definition_or_standard",
            relevance_reason="Locates standards that define RF/WiFi sensing constraints and terminology.",
            freshness_status="unknown",
            access_license_status="unknown",
            privacy_status="low",
            operator_review_need="Operator review required before any source access.",
            allowed_next_step="operator_review",
            blocked_conditions=["No source access yet", "No ingestion", "No public claim"],
        )
    )

    examples.append(
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="rf_sensing_public_paper_locator_record",
            science_direction_id="sparse_rf_spatial_change_map_floorplan_scattering_v1",
            query_family="rf_sensing_public_papers",
            source_class="public_research_paper",
            candidate_title="Public RF sensing paper locator",
            candidate_url_or_identifier="https://example.invalid/paper/rf-sensing",
            candidate_domain="example.invalid",
            authority_level_guess="public_primary",
            evidence_role_guess="prior_art",
            relevance_reason="Locates prior-art papers on RF sensing, indoor propagation, and floor-plan constrained inference.",
            freshness_status="unknown",
            access_license_status="unknown",
            privacy_status="low",
            operator_review_need="Operator review required before paper access.",
            allowed_next_step="operator_review",
            blocked_conditions=["No paper fetching", "No ingestion", "No public claim"],
        )
    )

    examples.append(
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="wifi_sensing_github_repo_locator_record",
            science_direction_id="sparse_rf_spatial_change_map_floorplan_scattering_v1",
            query_family="wifi_sensing_github_implementations",
            source_class="github_repository",
            candidate_title="WiFi sensing GitHub repository locator",
            candidate_url_or_identifier="https://example.invalid/github/wifi-sensing",
            candidate_domain="example.invalid",
            authority_level_guess="implementation_evidence",
            evidence_role_guess="implementation_reference",
            relevance_reason="GitHub is useful for implementation references and candidate signals, but not official science evidence alone.",
            freshness_status="unknown",
            access_license_status="unknown",
            privacy_status="low",
            operator_review_need="Operator review required before any source access.",
            allowed_next_step="operator_review",
            blocked_conditions=["No GitHub calls", "Implementation evidence only", "Not official science evidence alone"],
        )
    )

    examples.append(
        build_mlcf_metadata_only_source_locator_record_v1(
            locator_id="blocked_private_hidden_locator_record",
            science_direction_id="sparse_rf_spatial_change_map_floorplan_scattering_v1",
            query_family="blocked_source_locator",
            source_class="blocked_private_or_hidden_source",
            candidate_title="Blocked source locator record",
            candidate_url_or_identifier="blocked://source",
            candidate_domain="blocked.local",
            authority_level_guess="blocked",
            evidence_role_guess="not_authoritative_context",
            relevance_reason="This locator is blocked by safety.",
            freshness_status="unknown",
            access_license_status="blocked",
            privacy_status="high",
            operator_review_need="Operator review required; source is blocked by safety.",
            allowed_next_step="blocked_by_safety",
            blocked_conditions=["Private source", "Hidden source", "Protected source"],
        )
    )

    return examples
