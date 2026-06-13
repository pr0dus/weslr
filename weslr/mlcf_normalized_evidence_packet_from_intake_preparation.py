"""WESLR MLCF Normalized Evidence Packet From Intake Preparation V1.

Metadata-only helpers for preparing normalized-evidence packets from intake
preparation records only. This module does not ingest source content, does not
create trusted evidence, and does not authorize claims or runtime actions.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.mlcf_evidence_intake_packet_from_metadata_summary import (
    build_initial_mlcf_evidence_intake_packet_from_metadata_summary_examples_v1,
)

SCHEMA_VERSION_V1 = "mlcf_normalized_evidence_packet_from_intake_preparation_v1"
HELPER_FAMILY_V1 = "mlcf_normalized_evidence_packet_from_intake_preparation"

_ALLOWED_STATUSES_V1 = (
    "normalized_evidence_preparation_packet_prepared",
    "excluded_needs_operator_review",
    "excluded_needs_repair",
    "excluded_blocked_by_safety",
    "blocked_by_safety",
)

_ALLOWED_NEXT_STEPS_V1 = (
    "operator_review",
    "prepare_provisional_candidate_evidence_packet",
    "repair_intake_preparation_records",
    "reject_normalized_evidence_packet",
    "blocked_by_safety",
)

_ALLOWED_PREPARATION_TYPES_V1 = (
    "definition_or_standard_normalization_preparation",
    "measurement_data_normalization_preparation",
    "prior_art_normalization_preparation",
    "implementation_reference_normalization_preparation",
    "replication_target_normalization_preparation",
    "domain_context_normalization_preparation",
    "constraint_source_normalization_preparation",
    "not_authoritative_context_normalization_preparation",
)

_ALLOWED_CONFIDENCE_POSTURES_V1 = (
    "metadata_only_unverified",
    "requires_source_content",
    "requires_operator_review",
    "blocked_by_safety",
)

_AUTHORITY_FALSE_FLAGS_V1 = (
    "source_access_authorized",
    "source_fetching_authority",
    "source_summary_authority",
    "source_summary_authorized",
    "source_content_summary_authorized",
    "source_ingestion_authorized",
    "source_content_ingestion_authorized",
    "evidence_claim_authorized",
    "normalized_evidence_authorized",
    "normalized_evidence_created",
    "trusted_evidence_authorized",
    "accepted_evidence_authorized",
    "candidate_graph_membership_authorized",
    "proposal_payload_authorized",
    "proposal_submission_authorized",
    "proposal_application_authorized",
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
    "public claim",
    "source ingestion",
    "raw retention",
    "web call",
    "github call",
    "searxng call",
    "source fetching",
    "source summary",
    "source content",
    "normalized evidence",
    "trusted evidence",
    "accepted evidence",
    "candidate graph",
    "proposal payload",
    "proposal submission",
    "proposal application",
    "evidence claim",
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
    "evidence_content",
    "evidence_claim",
    "normalized_evidence",
    "trusted_evidence",
    "accepted_evidence",
    "accepted_candidate",
    "proposal_payload",
)

_FORBIDDEN_QUOTE_FIELDS_V1 = (
    "quote",
    "excerpt",
    "quoted_text",
)

_REQUIRED_FIELD_NAMES_V1 = (
    "schema_version",
    "normalized_evidence_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "evidence_intake_packet_ref",
    "input_intake_record_count",
    "normalized_evidence_preparation_records",
    "excluded_intake_records",
    "blocked_records",
    "preparation_record_count",
    "excluded_record_count",
    "blocked_record_count",
    "source_kind_distribution",
    "preparation_role_distribution",
    "authority_distribution",
    "evidence_role_distribution",
    "normalization_scope",
    "operator_review_need",
    "allowed_next_step",
    "blocked_conditions",
    "authority_status",
    "safe_metadata",
    "normalized_evidence_preparation_status",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "normalized_evidence_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "evidence_intake_packet_ref",
    "normalization_scope",
    "operator_review_need",
    "allowed_next_step",
    "normalized_evidence_preparation_status",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "normalized_evidence_preparation_records",
    "excluded_intake_records",
    "blocked_records",
    "blocked_conditions",
)

_REQUIRED_DICT_FIELDS_V1 = (
    "source_kind_distribution",
    "preparation_role_distribution",
    "authority_distribution",
    "evidence_role_distribution",
    "authority_status",
    "safe_metadata",
)

_RECORD_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "normalized_evidence_preparation_id",
    "evidence_intake_record_id",
    "metadata_summary_id",
    "source_locator_id",
    "science_direction_id",
    "source_kind_hint",
    "evidence_preparation_role",
    "candidate_title",
    "candidate_url_or_identifier",
    "candidate_domain",
    "metadata_summary_text",
    "normalized_evidence_preparation_type",
    "expected_normalized_fields",
    "metadata_only_claim_shape",
    "source_content_required_notice",
    "normalization_limitations",
    "confidence_posture",
    "not_normalized_evidence_notice",
    "not_trusted_evidence_notice",
    "not_accepted_evidence_notice",
    "operator_review_need",
    "allowed_next_step",
)

_SOURCE_CLASS_TO_KIND_V1 = {
    "official_standard": "official_standard_metadata",
    "official_government_or_agency_data": "official_government_or_agency_metadata",
    "official_vendor_documentation": "official_vendor_documentation_metadata",
    "public_research_paper": "public_research_paper_metadata",
    "public_dataset": "public_dataset_metadata",
    "github_repository": "github_repository_metadata",
    "public_lab_or_university_artifact": "public_lab_or_university_artifact_metadata",
    "public_benchmark_or_test_suite": "public_benchmark_or_test_suite_metadata",
    "blocked_private_or_hidden_source": "blocked_source_metadata",
}

_SOURCE_KIND_TO_PREP_TYPE_V1 = {
    "official_standard_metadata": "definition_or_standard_normalization_preparation",
    "official_government_or_agency_metadata": "domain_context_normalization_preparation",
    "official_vendor_documentation_metadata": "constraint_source_normalization_preparation",
    "public_research_paper_metadata": "prior_art_normalization_preparation",
    "public_dataset_metadata": "measurement_data_normalization_preparation",
    "github_repository_metadata": "implementation_reference_normalization_preparation",
    "public_lab_or_university_artifact_metadata": "replication_target_normalization_preparation",
    "public_benchmark_or_test_suite_metadata": "counterexample_source_normalization_preparation",
    "blocked_source_metadata": "not_authoritative_context_normalization_preparation",
    "unknown_source_metadata": "not_authoritative_context_normalization_preparation",
}

_ROLE_TO_PREP_TYPE_V1 = {
    "definition_or_standard_preparation": "definition_or_standard_normalization_preparation",
    "measurement_data_preparation": "measurement_data_normalization_preparation",
    "prior_art_preparation": "prior_art_normalization_preparation",
    "implementation_reference_preparation": "implementation_reference_normalization_preparation",
    "replication_target_preparation": "replication_target_normalization_preparation",
    "counterexample_source_preparation": "counterexample_source_normalization_preparation",
    "domain_context_preparation": "domain_context_normalization_preparation",
    "constraint_source_preparation": "constraint_source_normalization_preparation",
    "not_authoritative_context_preparation": "not_authoritative_context_normalization_preparation",
}

_ALLOWED_PREPARATION_ROLES_V1 = tuple(_ROLE_TO_PREP_TYPE_V1.keys())


def allowed_mlcf_normalized_evidence_packet_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_STATUSES_V1



def allowed_mlcf_normalized_evidence_packet_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEPS_V1



def allowed_mlcf_normalized_evidence_preparation_types_v1() -> tuple[str, ...]:
    return _ALLOWED_PREPARATION_TYPES_V1



def allowed_mlcf_normalized_evidence_confidence_postures_v1() -> tuple[str, ...]:
    return _ALLOWED_CONFIDENCE_POSTURES_V1



def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    elif payload is not None:
        merged["intake_preparation_packet"] = payload
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
            "status": "metadata_only_normalized_evidence_preparation_packet",
            "boundary_notes": "metadata-only preparation packet boundary",
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
        "no_source_ingestion": True,
        "no_evidence_claims": True,
        "no_normalized_evidence": True,
        "no_trusted_evidence": True,
        "no_accepted_evidence": True,
        "no_candidate_graph_membership": True,
        "no_proposal_payload": True,
        "no_proposal_submission": True,
        "no_proposal_application": True,
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
        "source_content_ingestion_authorized": False,
        "evidence_claim_authorized": False,
        "normalized_evidence_authorized": False,
        "normalized_evidence_created": False,
        "trusted_evidence_authorized": False,
        "accepted_evidence_authorized": False,
        "candidate_graph_membership_authorized": False,
        "proposal_payload_authorized": False,
        "proposal_submission_authorized": False,
        "proposal_application_authorized": False,
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
    }



def _source_kind_hint(source_class: str) -> str:
    return _SOURCE_CLASS_TO_KIND_V1.get(source_class, "unknown_source_metadata")



def _prep_type_for(source_kind_hint: str, role: str) -> str:
    if role in _ROLE_TO_PREP_TYPE_V1:
        return _ROLE_TO_PREP_TYPE_V1[role]
    return _SOURCE_KIND_TO_PREP_TYPE_V1.get(source_kind_hint, "not_authoritative_context_normalization_preparation")



def _signature(record: Mapping[str, Any]) -> str:
    payload = "|".join(
        [
            _compact_text(record.get("evidence_intake_record_id")),
            _compact_text(record.get("metadata_summary_id")),
            _compact_text(record.get("source_locator_id")),
            _compact_text(record.get("candidate_title")),
            _compact_text(record.get("candidate_url_or_identifier")),
            _compact_text(record.get("candidate_domain")),
            _compact_text(record.get("source_kind_hint")),
            _compact_text(record.get("evidence_preparation_role")),
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()[:16]



def _record_has_forbidden_content(record: Mapping[str, Any]) -> bool:
    for field in _FORBIDDEN_CONTENT_FIELDS_V1 + _FORBIDDEN_QUOTE_FIELDS_V1:
        if field in record:
            return True
    return False



def _record_has_unsafe_language(record: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    ignored_fields = {
        "normalized_evidence_preparation_id",
        "evidence_intake_record_id",
        "metadata_summary_id",
        "source_locator_id",
        "science_direction_id",
        "source_kind_hint",
        "evidence_preparation_role",
        "normalized_evidence_preparation_type",
        "confidence_posture",
        "expected_normalized_fields",
        "metadata_only_claim_shape",
        "source_content_required_notice",
        "normalization_limitations",
        "not_normalized_evidence_notice",
        "not_trusted_evidence_notice",
        "not_accepted_evidence_notice",
        "operator_review_need",
        "allowed_next_step",
        "blocked_conditions",
        "authority_status",
        "safe_metadata",
    }
    for field, value in record.items():
        if field in ignored_fields:
            continue
        if _contains_forbidden_markers(value, _AUTHORITY_TEXT_MARKERS_V1):
            labels.append("unsafe_authority_text")
        if _contains_forbidden_markers(value, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            labels.append("unsafe_hidden_private_protected_marker")
        if _contains_forbidden_markers(
            value,
            (
                "WESLR discovered",
                "confirmed discovery",
                "proved",
                "public science result",
                "benchmark-winning",
                "agi",
                "sentience",
                "consciousness",
                "trusted evidence",
                "normalized evidence",
                "accepted evidence",
                "accepted candidate",
                "proposal payload",
                "proposal application",
                "proposal submission",
                "final answer",
                "public claim",
            ),
        ):
            labels.append("unsafe_claim_language")
    return labels



def _eligible_intake_record(record: Mapping[str, Any]) -> bool:
    if _compact_text(record.get("summary_status")) != "metadata_summary_prepared":
        return False
    if _compact_text(record.get("source_summary_status")) not in {"metadata_summary_prepared"}:
        return False
    if not _compact_text(record.get("not_evidence_notice")):
        return False
    if _record_has_forbidden_content(record):
        return False
    if _record_has_unsafe_language(record):
        return False
    return True



def _build_preparation_record_core(record: Mapping[str, Any], **overrides: Any) -> dict[str, Any]:
    source_kind_hint = _compact_text(overrides.get("source_kind_hint", _compact_text(record.get("source_kind_hint"), _source_kind_hint(_compact_text(record.get("source_class"))))))
    role = _compact_text(overrides.get("evidence_preparation_role", _compact_text(record.get("evidence_preparation_role"), "not_authoritative_context_preparation")))
    prep_type = _compact_text(overrides.get("normalized_evidence_preparation_type", _prep_type_for(source_kind_hint, role)))
    summary_text = _compact_text(
        overrides.get(
            "metadata_summary_text",
            _compact_text(record.get("metadata_summary_text"), "Metadata-only intake preparation record."),
        )
    )[:220]
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "normalized_evidence_preparation_id": _compact_text(
            overrides.get("normalized_evidence_preparation_id", f"normprep_{_signature(record)}")
        ),
        "evidence_intake_record_id": _compact_text(record.get("evidence_intake_record_id")),
        "metadata_summary_id": _compact_text(record.get("metadata_summary_id")),
        "source_locator_id": _compact_text(record.get("source_locator_id")),
        "science_direction_id": _compact_text(record.get("science_direction_id")),
        "source_kind_hint": source_kind_hint,
        "evidence_preparation_role": role,
        "candidate_title": _compact_text(record.get("candidate_title")),
        "candidate_url_or_identifier": _compact_text(record.get("candidate_url_or_identifier")),
        "candidate_domain": _compact_text(record.get("candidate_domain")),
        "metadata_summary_text": summary_text,
        "normalized_evidence_preparation_type": prep_type,
        "expected_normalized_fields": _compact_text(
            overrides.get(
                "expected_normalized_fields",
                f"metadata-only normalized-evidence preparation scaffold for {source_kind_hint} / {prep_type}",
            )
        )[:240],
        "metadata_only_claim_shape": _compact_text(
            overrides.get(
                "metadata_only_claim_shape",
                "metadata-only preparation shape; no claim or evidence output.",
            )
        )[:220],
        "source_content_required_notice": _compact_text(
            overrides.get(
                "source_content_required_notice",
                "Later content access would be required for full normalization; not available here.",
            )
        )[:240],
        "normalization_limitations": _compact_text(
            overrides.get(
                "normalization_limitations",
                "Metadata-only preparation; no source-content normalization, no trusted evidence, and no accepted evidence.",
            )
        )[:240],
        "confidence_posture": _compact_text(
            overrides.get("confidence_posture", "metadata_only_unverified")
        ),
        "not_normalized_evidence_notice": _compact_text(
            overrides.get(
                "not_normalized_evidence_notice",
                "Preparation only; no normalized evidence created.",
            )
        )[:220],
        "not_trusted_evidence_notice": _compact_text(
            overrides.get(
                "not_trusted_evidence_notice",
                "Preparation only; no trusted evidence created.",
            )
        )[:220],
        "not_accepted_evidence_notice": _compact_text(
            overrides.get(
                "not_accepted_evidence_notice",
                "Preparation only; no accepted evidence created.",
            )
        )[:220],
        "operator_review_need": _compact_text(
            overrides.get(
                "operator_review_need",
                _compact_text(record.get("operator_review_need"), "Operator review required before any normalized-evidence action."),
            )
        )[:220],
        "allowed_next_step": _compact_text(
            overrides.get("allowed_next_step", "prepare_provisional_candidate_evidence_packet")
        ),
        "blocked_conditions": _normalize_text_list(
            overrides.get("blocked_conditions", record.get("blocked_conditions"))
        ),
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
    }



def build_mlcf_normalized_evidence_preparation_record_v1(intake_preparation_record: Any, **overrides: Any) -> dict[str, Any]:
    record = deepcopy(dict(intake_preparation_record)) if isinstance(intake_preparation_record, Mapping) else {"invalid_record": intake_preparation_record}
    return _build_preparation_record_core(record, **overrides)



def _bucket_status(prepared_count: int, excluded_operator_count: int, excluded_repair_count: int, excluded_blocked_count: int, blocked_count: int) -> str:
    if prepared_count > 0:
        return "normalized_evidence_preparation_packet_prepared"
    if blocked_count > 0:
        return "blocked_by_safety"
    if excluded_repair_count > 0:
        return "excluded_needs_repair"
    if excluded_operator_count > 0:
        return "excluded_needs_operator_review"
    if excluded_blocked_count > 0:
        return "excluded_blocked_by_safety"
    return "blocked_by_safety"



def _packet_next_step(prepared_count: int, excluded_operator_count: int, excluded_repair_count: int, excluded_blocked_count: int, blocked_count: int) -> str:
    if prepared_count > 0:
        return "prepare_provisional_candidate_evidence_packet"
    if blocked_count > 0:
        return "blocked_by_safety"
    if excluded_repair_count > 0:
        return "repair_intake_preparation_records"
    if excluded_operator_count > 0:
        return "operator_review"
    if excluded_blocked_count > 0:
        return "blocked_by_safety"
    return "blocked_by_safety"



def build_mlcf_normalized_evidence_packet_from_intake_preparation_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged = _merge_payload(payload, **overrides)
    intake_packet = merged.pop("intake_preparation_packet", None)
    if intake_packet is None and isinstance(payload, Mapping):
        intake_packet = payload
    if not isinstance(intake_packet, Mapping):
        intake_packet = {}

    intake_records = list(intake_packet.get("evidence_intake_preparation_records", []))
    excluded_intake_records = list(intake_packet.get("excluded_intake_records", intake_packet.get("excluded_summary_records", [])))
    blocked_records = list(intake_packet.get("blocked_records", []))

    preparation_records: list[dict[str, Any]] = []
    excluded_out_records: list[dict[str, Any]] = []
    blocked_out_records: list[dict[str, Any]] = []
    source_kind_counter: Counter[str] = Counter()
    prep_role_counter: Counter[str] = Counter()
    authority_counter: Counter[str] = Counter()
    evidence_role_counter: Counter[str] = Counter()
    blocked_conditions: list[str] = []
    prepared_count = 0
    excluded_operator_count = 0
    excluded_repair_count = 0
    excluded_blocked_count = 0
    blocked_count = 0

    def tally(record: Mapping[str, Any]) -> None:
        source_kind_counter[_compact_text(record.get("source_kind_hint")) or "unknown_source_metadata"] += 1
        prep_role_counter[_compact_text(record.get("evidence_preparation_role")) or "not_authoritative_context_preparation"] += 1
        authority_counter[_compact_text(record.get("authority_level_guess")) or "unknown"] += 1
        evidence_role_counter[_compact_text(record.get("evidence_role_guess")) or "unknown"] += 1

    for record in intake_records:
        intake_record = deepcopy(dict(record)) if isinstance(record, Mapping) else {"invalid_record": record}
        tally(intake_record)
        status = _compact_text(intake_record.get("summary_status"))
        if not _eligible_intake_record(intake_record):
            if status in {"blocked_by_safety"}:
                blocked_out_records.append({
                    **intake_record,
                    "normalized_evidence_packet_status": "blocked_by_safety",
                    "normalized_evidence_exclusion_reason": "blocked_by_safety",
                    "allowed_next_step": "blocked_by_safety",
                })
                blocked_count += 1
            elif status == "excluded_needs_repair":
                excluded_out_records.append({
                    **intake_record,
                    "normalized_evidence_packet_status": "excluded_needs_repair",
                    "normalized_evidence_exclusion_reason": "intake_preparation_needs_repair",
                    "allowed_next_step": "repair_intake_preparation_records",
                })
                excluded_repair_count += 1
            elif status in {"excluded_rejected", "excluded_duplicate_or_low_value"}:
                excluded_out_records.append({
                    **intake_record,
                    "normalized_evidence_packet_status": status,
                    "normalized_evidence_exclusion_reason": "excluded_by_intake_policy",
                    "allowed_next_step": "operator_review",
                })
                excluded_blocked_count += 1
            else:
                excluded_out_records.append({
                    **intake_record,
                    "normalized_evidence_packet_status": "excluded_needs_operator_review",
                    "normalized_evidence_exclusion_reason": "operator_review_required_before_normalization",
                    "allowed_next_step": "operator_review",
                })
                excluded_operator_count += 1
            if _compact_text(intake_record.get("summary_exclusion_reason")):
                blocked_conditions.append(_compact_text(intake_record.get("summary_exclusion_reason")))
            continue

        preparation_records.append(
            _build_preparation_record_core(
                intake_record,
                normalized_evidence_preparation_id=f"normprep_{_signature(intake_record)}",
                confidence_posture="metadata_only_unverified",
                blocked_conditions=list(intake_record.get("blocked_conditions", [])),
            )
        )
        prepared_count += 1

    for record in excluded_intake_records:
        excluded = deepcopy(dict(record)) if isinstance(record, Mapping) else {"invalid_record": record}
        tally(excluded)
        status = _compact_text(excluded.get("summary_status"))
        if status == "excluded_needs_repair":
            excluded_out_records.append({
                **excluded,
                "normalized_evidence_packet_status": "excluded_needs_repair",
                "normalized_evidence_exclusion_reason": "intake_preparation_needs_repair",
                "allowed_next_step": "repair_intake_preparation_records",
            })
            excluded_repair_count += 1
        elif status in {"excluded_rejected", "excluded_duplicate_or_low_value"}:
            excluded_out_records.append({
                **excluded,
                "normalized_evidence_packet_status": status,
                "normalized_evidence_exclusion_reason": "excluded_by_intake_policy",
                "allowed_next_step": "operator_review",
            })
            excluded_blocked_count += 1
        else:
            excluded_out_records.append({
                **excluded,
                "normalized_evidence_packet_status": "excluded_needs_operator_review",
                "normalized_evidence_exclusion_reason": "operator_review_required_before_normalization",
                "allowed_next_step": "operator_review",
            })
            excluded_operator_count += 1
        reason = _compact_text(excluded.get("summary_exclusion_reason")) or _compact_text(excluded.get("normalized_evidence_exclusion_reason"))
        if reason:
            blocked_conditions.append(reason)

    for record in blocked_records:
        blocked = deepcopy(dict(record)) if isinstance(record, Mapping) else {"invalid_record": record}
        tally(blocked)
        blocked_out_records.append({
            **blocked,
            "normalized_evidence_packet_status": "blocked_by_safety",
            "normalized_evidence_exclusion_reason": "blocked_by_safety",
            "allowed_next_step": "blocked_by_safety",
        })
        blocked_count += 1
        reason = _compact_text(blocked.get("summary_exclusion_reason")) or _compact_text(blocked.get("review_decision_reason"))
        if reason:
            blocked_conditions.append(reason)

    input_count = len(intake_records) + len(excluded_intake_records) + len(blocked_records)
    status = _bucket_status(prepared_count, excluded_operator_count, excluded_repair_count, excluded_blocked_count, blocked_count)
    allowed_next_step = _packet_next_step(prepared_count, excluded_operator_count, excluded_repair_count, excluded_blocked_count, blocked_count)

    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "normalized_evidence_packet_id": _compact_text(merged.get("normalized_evidence_packet_id"), f"normalized_{_signature(intake_packet if isinstance(intake_packet, Mapping) else {})}"),
        "science_direction_id": _compact_text(merged.get("science_direction_id"), _compact_text(intake_packet.get("science_direction_id"), "default_science_direction")),
        "science_direction_summary": _compact_text(merged.get("science_direction_summary"), _compact_text(intake_packet.get("science_direction_summary"), "Metadata-only normalized evidence preparation packet.")),
        "evidence_intake_packet_ref": _compact_text(merged.get("evidence_intake_packet_ref"), _compact_text(intake_packet.get("evidence_intake_packet_id"), _compact_text(intake_packet.get("evidence_intake_packet_ref"), "evidence_intake_packet_ref_missing"))),
        "input_intake_record_count": input_count,
        "normalized_evidence_preparation_records": preparation_records,
        "excluded_intake_records": excluded_out_records,
        "blocked_records": blocked_out_records,
        "preparation_record_count": prepared_count,
        "excluded_record_count": len(excluded_out_records),
        "blocked_record_count": len(blocked_out_records),
        "source_kind_distribution": dict(source_kind_counter),
        "preparation_role_distribution": dict(prep_role_counter),
        "authority_distribution": dict(authority_counter),
        "evidence_role_distribution": dict(evidence_role_counter),
        "normalization_scope": _compact_text(merged.get("normalization_scope"), "intake_preparation_records_only"),
        "operator_review_need": _compact_text(merged.get("operator_review_need"), "Operator review required; metadata-only normalized-evidence preparation boundaries preserved."),
        "allowed_next_step": allowed_next_step,
        "blocked_conditions": blocked_conditions,
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
        "normalized_evidence_preparation_status": status,
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
    if _compact_text(authority_status.get("status")) != "metadata_only_normalized_evidence_preparation_packet":
        labels.append("unsafe_authority_status")
    notes = _compact_text(authority_status.get("boundary_notes"))
    if not notes:
        labels.append("missing_authority_status_boundary_notes")
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
        "no_source_ingestion",
        "no_evidence_claims",
        "no_normalized_evidence",
        "no_trusted_evidence",
        "no_accepted_evidence",
        "no_candidate_graph_membership",
        "no_proposal_payload",
        "no_proposal_submission",
        "no_proposal_application",
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
    return not labels, labels



def _validate_preparation_record(record: Mapping[str, Any], labels: list[str]) -> None:
    for field in _RECORD_REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(record.get(field)):
            labels.append(f"missing_{field}")
    summary_status = _compact_text(record.get("summary_status"))
    if summary_status in {"blocked_by_safety"}:
        labels.append("blocked_record_not_blocked")
    if summary_status and summary_status not in {"metadata_summary_prepared", "metadata_only_unverified"}:
        labels.append("preparation_record_bad_summary_status")
    if _compact_text(record.get("normalized_evidence_packet_status")) == "blocked_by_safety":
        labels.append("blocked_record_not_blocked")
    if _compact_text(record.get("source_kind_hint")) not in set(_SOURCE_CLASS_TO_KIND_V1.values()) | {"unknown_source_metadata"}:
        labels.append("unsupported_source_kind_hint")
    if _compact_text(record.get("evidence_preparation_role")) not in _ALLOWED_PREPARATION_ROLES_V1:
        labels.append("unsupported_preparation_role")
    if _compact_text(record.get("normalized_evidence_preparation_type")) not in _ALLOWED_PREPARATION_TYPES_V1:
        labels.append("unsupported_preparation_type")
    if _compact_text(record.get("confidence_posture")) not in _ALLOWED_CONFIDENCE_POSTURES_V1:
        labels.append("unsupported_confidence_posture")
    if _compact_text(record.get("allowed_next_step")) != "prepare_provisional_candidate_evidence_packet":
        labels.append("preparation_record_bad_next_step")
    if _compact_text(record.get("metadata_only_claim_shape")) and _contains_forbidden_markers(record.get("metadata_only_claim_shape"), _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_claim_language")
    if _record_has_forbidden_content(record):
        labels.append("preparation_record_contains_source_content")
    labels.extend(_record_has_unsafe_language(record))



def _validate_excluded_record(record: Mapping[str, Any], labels: list[str]) -> None:
    status = _compact_text(record.get("normalized_evidence_packet_status")) or _compact_text(record.get("summary_status"))
    if status not in {"excluded_needs_operator_review", "excluded_needs_repair", "excluded_rejected", "excluded_duplicate_or_low_value", "blocked_by_safety"}:
        labels.append("invalid_excluded_record_status")
    if _record_has_forbidden_content(record):
        labels.append("excluded_record_contains_source_content")
    labels.extend(_record_has_unsafe_language(record))



def _validate_blocked_record(record: Mapping[str, Any], labels: list[str]) -> None:
    status = _compact_text(record.get("normalized_evidence_packet_status")) or _compact_text(record.get("summary_status"))
    if status != "blocked_by_safety":
        labels.append("blocked_record_not_blocked")
    if _record_has_forbidden_content(record):
        labels.append("blocked_record_contains_source_content")
    labels.extend(_record_has_unsafe_language(record))



def validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_packet_type"],
            "validation_posture": "blocked",
            "summary_text": "Invalid metadata-only normalized evidence preparation packet.",
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
            "summary_text": "Missing required metadata-only normalized evidence preparation packet fields.",
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
    if _compact_text(packet.get("normalized_evidence_preparation_status")) not in _ALLOWED_STATUSES_V1:
        labels.append("unsupported_packet_status")
    if _compact_text(packet.get("allowed_next_step")) not in _ALLOWED_NEXT_STEPS_V1:
        labels.append("unsupported_next_step")
    if _compact_text(packet.get("input_intake_record_count"), "x").isdigit() is False:
        labels.append("invalid_input_intake_record_count")
    if _compact_text(packet.get("normalization_scope")) not in {"intake_preparation_records_only", "metadata_only_intake_preparation", "ready_prepared_records_only"}:
        labels.append("unsupported_normalization_scope")

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
    if _contains_forbidden_markers(packet.get("science_direction_summary"), (
        "WESLR discovered",
        "confirmed discovery",
        "proved",
        "public science result",
        "benchmark-winning",
        "agi",
        "sentience",
        "consciousness",
        "trusted evidence",
        "normalized evidence",
        "accepted evidence",
        "accepted candidate",
        "proposal payload",
        "proposal application",
        "proposal submission",
        "final answer",
        "public claim",
    )):
        labels.append("unsafe_claim_language")

    prep_records = packet.get("normalized_evidence_preparation_records")
    excl_records = packet.get("excluded_intake_records")
    blk_records = packet.get("blocked_records")
    if not isinstance(prep_records, list) or not isinstance(excl_records, list) or not isinstance(blk_records, list):
        labels.append("invalid_record_containers")
    else:
        if int(_compact_text(packet.get("preparation_record_count"), "-1")) != len(prep_records):
            labels.append("preparation_record_count_mismatch")
        if int(_compact_text(packet.get("excluded_record_count"), "-1")) != len(excl_records):
            labels.append("excluded_record_count_mismatch")
        if int(_compact_text(packet.get("blocked_record_count"), "-1")) != len(blk_records):
            labels.append("blocked_record_count_mismatch")
        for record in prep_records:
            if not isinstance(record, Mapping):
                labels.append("invalid_preparation_record_type")
                continue
            _validate_preparation_record(record, labels)
        for record in excl_records:
            if not isinstance(record, Mapping):
                labels.append("invalid_excluded_record_type")
                continue
            _validate_excluded_record(record, labels)
        for record in blk_records:
            if not isinstance(record, Mapping):
                labels.append("invalid_blocked_record_type")
                continue
            _validate_blocked_record(record, labels)

    input_count = packet.get("input_intake_record_count")
    if isinstance(input_count, int):
        if input_count <= 0:
            labels.append("missing_input_intake_records")
        if input_count != len(prep_records) + len(excl_records) + len(blk_records):
            labels.append("input_intake_record_count_mismatch")
    else:
        labels.append("invalid_input_intake_record_count")

    for field_name in ("normalization_scope", "operator_review_need", "normalized_evidence_preparation_status"):
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
            "summary_text": "Blocked metadata-only normalized evidence preparation packet.",
        }
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
        "validation_posture": "valid",
        "summary_text": "Valid metadata-only normalized evidence preparation packet.",
    }



def summarize_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet: Any) -> dict[str, Any]:
    validation = validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    packet = packet if isinstance(packet, Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "normalized_evidence_packet_id": _compact_text(packet.get("normalized_evidence_packet_id")),
        "science_direction_id": _compact_text(packet.get("science_direction_id")),
        "evidence_intake_packet_ref": _compact_text(packet.get("evidence_intake_packet_ref")),
        "normalized_evidence_preparation_status": _compact_text(packet.get("normalized_evidence_preparation_status")),
        "preparation_record_count": int(packet.get("preparation_record_count", 0)) if str(packet.get("preparation_record_count", 0)).isdigit() else packet.get("preparation_record_count", 0),
        "excluded_record_count": int(packet.get("excluded_record_count", 0)) if str(packet.get("excluded_record_count", 0)).isdigit() else packet.get("excluded_record_count", 0),
        "blocked_record_count": int(packet.get("blocked_record_count", 0)) if str(packet.get("blocked_record_count", 0)).isdigit() else packet.get("blocked_record_count", 0),
        "allowed_next_step": _compact_text(packet.get("allowed_next_step")),
        "validation_posture": validation.get("validation_posture", "blocked"),
        "summary_text": _compact_text(packet.get("science_direction_summary"), "Metadata-only normalized evidence preparation packet.")[:220],
    }



def to_mlcf_normalized_evidence_packet_from_intake_preparation_json_safe_v1(packet: Any) -> Any:
    return _json_safe(deepcopy(packet))



def build_initial_mlcf_normalized_evidence_packet_from_intake_preparation_examples_v1() -> list[dict[str, Any]]:
    intake_examples = build_initial_mlcf_evidence_intake_packet_from_metadata_summary_examples_v1()
    frontier_intake = next(item for item in intake_examples if item["evidence_intake_packet_id"] == "frontier_space_metadata_summary_to_evidence_intake_packet")
    rf_intake = next(item for item in intake_examples if item["evidence_intake_packet_id"] == "rf_metadata_summary_operator_review_excluded_packet")
    blocked_intake = next(item for item in intake_examples if item["evidence_intake_packet_id"] == "blocked_metadata_summary_to_evidence_intake_packet")
    return [
        build_mlcf_normalized_evidence_packet_from_intake_preparation_v1(
            normalized_evidence_packet_id="frontier_space_intake_to_normalized_evidence_preparation_packet",
            science_direction_id="frontier_space_discovery_style_locator_fixture",
            science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space, used only to test locator-to-future-candidate-artifact routing.",
            evidence_intake_packet_ref=frontier_intake["evidence_intake_packet_id"],
            intake_preparation_packet=frontier_intake,
        ),
        build_mlcf_normalized_evidence_packet_from_intake_preparation_v1(
            normalized_evidence_packet_id="rf_excluded_intake_to_normalized_evidence_preparation_packet",
            science_direction_id="rf_material_floorplan_sparse_change_map",
            science_direction_summary="Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.",
            evidence_intake_packet_ref=rf_intake["evidence_intake_packet_id"],
            intake_preparation_packet=rf_intake,
        ),
        build_mlcf_normalized_evidence_packet_from_intake_preparation_v1(
            normalized_evidence_packet_id="blocked_intake_to_normalized_evidence_preparation_packet",
            science_direction_id="frontier_space_discovery_style_locator_fixture",
            science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space, used only to test locator-to-future-candidate-artifact routing.",
            evidence_intake_packet_ref=blocked_intake["evidence_intake_packet_id"],
            intake_preparation_packet=blocked_intake,
        ),
    ]
