"""WESLR MLCF Evidence Intake Packet From Metadata Summary V1.

Metadata-only helpers for preparing evidence-intake packets from reviewed
source-summary metadata. This module does not ingest source content, does not
create trusted evidence, and does not authorize claims or runtime actions.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.mlcf_authorized_metadata_only_source_summary import (
    build_initial_mlcf_authorized_metadata_only_source_summary_examples_v1,
    build_mlcf_authorized_metadata_only_source_summary_packet_v1,
)
from weslr.mlcf_source_locator_organization_review_packet import (
    build_initial_mlcf_source_locator_organization_review_packet_examples_v1,
)

SCHEMA_VERSION_V1 = "mlcf_evidence_intake_packet_from_metadata_summary_v1"
HELPER_FAMILY_V1 = "mlcf_evidence_intake_packet_from_metadata_summary"

_ALLOWED_STATUSES_V1 = (
    "evidence_intake_packet_prepared",
    "excluded_needs_operator_review",
    "excluded_needs_repair",
    "excluded_blocked_by_safety",
    "blocked_by_safety",
)

_ALLOWED_NEXT_STEPS_V1 = (
    "operator_review",
    "prepare_normalized_evidence_packet",
    "repair_metadata_summary_records",
    "reject_evidence_intake_packet",
    "blocked_by_safety",
)

_ALLOWED_SOURCE_KIND_HINTS_V1 = (
    "official_standard_metadata",
    "official_government_or_agency_metadata",
    "official_vendor_documentation_metadata",
    "public_research_paper_metadata",
    "public_dataset_metadata",
    "github_repository_metadata",
    "public_lab_or_university_artifact_metadata",
    "public_benchmark_or_test_suite_metadata",
    "blocked_source_metadata",
    "unknown_source_metadata",
)

_ALLOWED_PREPARATION_ROLES_V1 = (
    "definition_or_standard_preparation",
    "measurement_data_preparation",
    "prior_art_preparation",
    "implementation_reference_preparation",
    "replication_target_preparation",
    "counterexample_source_preparation",
    "domain_context_preparation",
    "constraint_source_preparation",
    "not_authoritative_context_preparation",
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
    "trusted_evidence_authorized",
    "candidate_graph_membership_authorized",
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
    "candidate graph",
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
    "evidence_intake_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "source_summary_packet_ref",
    "input_metadata_summary_count",
    "evidence_intake_preparation_records",
    "excluded_summary_records",
    "blocked_records",
    "preparation_record_count",
    "excluded_record_count",
    "blocked_record_count",
    "source_class_distribution",
    "authority_distribution",
    "evidence_role_distribution",
    "intake_scope",
    "operator_review_need",
    "allowed_next_step",
    "blocked_conditions",
    "authority_status",
    "safe_metadata",
    "intake_status",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "evidence_intake_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "source_summary_packet_ref",
    "intake_scope",
    "operator_review_need",
    "allowed_next_step",
    "intake_status",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "evidence_intake_preparation_records",
    "excluded_summary_records",
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
    "evidence_intake_record_id",
    "metadata_summary_id",
    "source_locator_id",
    "science_direction_id",
    "source_class",
    "authority_level_guess",
    "evidence_role_guess",
    "candidate_title",
    "candidate_url_or_identifier",
    "candidate_domain",
    "metadata_summary_text",
    "source_kind_hint",
    "evidence_preparation_role",
    "expected_evidence_shape",
    "provenance_stub",
    "normalization_plan",
    "candidate_mapping_plan",
    "limitations",
    "not_evidence_notice",
    "operator_review_need",
    "allowed_next_step",
    "summary_status",
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

_EVIDENCE_ROLE_TO_PREPARATION_ROLE_V1 = {
    "definition_or_standard": "definition_or_standard_preparation",
    "measurement_data": "measurement_data_preparation",
    "implementation_reference": "implementation_reference_preparation",
    "prior_art": "prior_art_preparation",
    "candidate_signal": "domain_context_preparation",
    "counterexample_source": "counterexample_source_preparation",
    "replication_target": "replication_target_preparation",
    "constraint_source": "constraint_source_preparation",
    "domain_context": "domain_context_preparation",
    "safety_boundary_context": "not_authoritative_context_preparation",
    "not_authoritative_context": "not_authoritative_context_preparation",
}


def allowed_mlcf_evidence_intake_packet_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_STATUSES_V1



def allowed_mlcf_evidence_intake_packet_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEPS_V1



def allowed_mlcf_evidence_intake_source_kinds_v1() -> tuple[str, ...]:
    return _ALLOWED_SOURCE_KIND_HINTS_V1



def allowed_mlcf_evidence_intake_preparation_roles_v1() -> tuple[str, ...]:
    return _ALLOWED_PREPARATION_ROLES_V1



def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    elif payload is not None:
        merged["metadata_summary_packet"] = payload
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
            "status": "metadata_only_evidence_intake_preparation_packet",
            "boundary_notes": "metadata-only evidence intake preparation packet boundary",
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
        "no_candidate_graph_membership": True,
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
        "trusted_evidence_authorized": False,
        "candidate_graph_membership_authorized": False,
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



def _prepare_source_kind_hint(source_class: str) -> str:
    return _SOURCE_CLASS_TO_KIND_V1.get(source_class, "unknown_source_metadata")



def _prepare_role(source_class: str, evidence_role_guess: str) -> str:
    if source_class == "official_government_or_agency_data":
        if evidence_role_guess == "measurement_data":
            return "measurement_data_preparation"
        return "domain_context_preparation"
    if source_class == "official_vendor_documentation":
        return "constraint_source_preparation"
    if source_class == "public_dataset":
        return "measurement_data_preparation"
    if source_class == "github_repository":
        return "implementation_reference_preparation"
    if source_class == "public_lab_or_university_artifact":
        return "replication_target_preparation"
    if source_class == "public_benchmark_or_test_suite":
        return "counterexample_source_preparation"
    if source_class == "blocked_private_or_hidden_source":
        return "not_authoritative_context_preparation"
    return _EVIDENCE_ROLE_TO_PREPARATION_ROLE_V1.get(evidence_role_guess, "not_authoritative_context_preparation")



def _expected_evidence_shape(role: str, source_kind_hint: str) -> str:
    return f"metadata-only evidence intake scaffold for {source_kind_hint} / {role}"



def _normalize_summary_record(record: Any) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return deepcopy(dict(record))
    return {"invalid_record": record}



def _record_signature(record: Mapping[str, Any]) -> str:
    payload = "|".join(
        [
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
        "evidence_intake_record_id",
        "metadata_summary_id",
        "source_locator_id",
        "science_direction_id",
        "source_class",
        "authority_level_guess",
        "evidence_role_guess",
        "candidate_url_or_identifier",
        "candidate_domain",
        "source_kind_hint",
        "evidence_preparation_role",
        "source_summary_status",
        "summary_status",
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
                "accepted candidate",
                "proposal application",
                "proposal submission",
                "final answer",
                "public claim",
            ),
        ):
            labels.append("unsafe_claim_language")
    return labels



def _build_excluded_summary_record_v1(summary_record: Any, *, status: str, reason: str, next_step: str) -> dict[str, Any]:
    record = _normalize_summary_record(summary_record)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_summary_id": _compact_text(record.get("metadata_summary_id"), f"excluded_{_record_signature(record)}"),
        "source_locator_id": _compact_text(record.get("source_locator_id") or record.get("locator_id")),
        "science_direction_id": _compact_text(record.get("science_direction_id"), "metadata_only_direction"),
        "source_class": _compact_text(record.get("source_class"), "unknown_source"),
        "authority_level_guess": _compact_text(record.get("authority_level_guess"), "unknown_authority"),
        "evidence_role_guess": _compact_text(record.get("evidence_role_guess"), "not_authoritative_context"),
        "candidate_title": _compact_text(record.get("candidate_title"), "locator record"),
        "candidate_url_or_identifier": _compact_text(record.get("candidate_url_or_identifier"), "metadata-only-reference"),
        "candidate_domain": _compact_text(record.get("candidate_domain"), "metadata.invalid"),
        "metadata_summary_text": _compact_text(
            record.get("metadata_summary_text"),
            f"Metadata-only intake exclusion for {_compact_text(record.get('candidate_title'), 'locator record')}.",
        )[:220],
        "source_kind_hint": _prepare_source_kind_hint(_compact_text(record.get("source_class"))),
        "evidence_preparation_role": _prepare_role(
            _compact_text(record.get("source_class")),
            _compact_text(record.get("evidence_role_guess")),
        ),
        "expected_evidence_shape": "metadata-only excluded intake routing record",
        "provenance_stub": f"metadata-summary:{_compact_text(record.get('metadata_summary_id'), 'missing')}",
        "normalization_plan": "No normalization plan generated; record remains excluded pending review.",
        "candidate_mapping_plan": "No candidate mapping prepared while record is excluded.",
        "limitations": "Metadata-only excluded intake record; not evidence and not a proposal.",
        "not_evidence_notice": "Metadata-only excluded intake record; not evidence.",
        "operator_review_need": _compact_text(
            record.get("operator_review_need"),
            "Operator review required before any evidence-intake action.",
        )[:220],
        "allowed_next_step": next_step,
        "summary_status": status,
        "summary_exclusion_reason": reason,
        "blocked_conditions": _normalize_text_list(record.get("blocked_conditions")),
        "source_summary_status": _compact_text(record.get("summary_status"), status),
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
    }


def _build_blocked_record_v1(summary_record: Any) -> dict[str, Any]:
    record = _normalize_summary_record(summary_record)
    blocked_conditions = _normalize_text_list(record.get("blocked_conditions")) or ["blocked_by_safety"]
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_summary_id": _compact_text(record.get("metadata_summary_id"), f"blocked_{_record_signature(record)}"),
        "source_locator_id": _compact_text(record.get("source_locator_id") or record.get("locator_id"), "blocked_locator"),
        "science_direction_id": "metadata_only_blocked_direction",
        "source_class": "blocked_source_metadata",
        "authority_level_guess": "blocked",
        "evidence_role_guess": "not_authoritative_context",
        "candidate_title": _compact_text(record.get("candidate_title"), "blocked locator record"),
        "candidate_url_or_identifier": "blocked-reference",
        "candidate_domain": "blocked.invalid",
        "metadata_summary_text": "Metadata-only blocked intake record retained for safety routing only.",
        "source_kind_hint": "blocked_source_metadata",
        "evidence_preparation_role": "not_authoritative_context_preparation",
        "expected_evidence_shape": "no evidence preparation; blocked by safety",
        "provenance_stub": f"metadata-summary:{_compact_text(record.get('metadata_summary_id'), 'missing')}",
        "normalization_plan": "No normalization plan generated because the record is blocked by safety.",
        "candidate_mapping_plan": "No candidate mapping prepared because the record is blocked by safety.",
        "limitations": "Metadata-only blocked intake record; not evidence and not a proposal.",
        "not_evidence_notice": "Metadata-only blocked intake record; not evidence.",
        "operator_review_need": "Operator review required; blocked by safety.",
        "allowed_next_step": "blocked_by_safety",
        "summary_status": "blocked_by_safety",
        "summary_exclusion_reason": "blocked_by_safety",
        "blocked_conditions": blocked_conditions,
        "source_summary_status": _compact_text(record.get("summary_status"), "blocked_by_safety"),
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
    }


def build_mlcf_evidence_intake_preparation_record_v1(source_summary_record: Any, **overrides: Any) -> dict[str, Any]:
    record = _normalize_summary_record(source_summary_record)
    source_class = _compact_text(record.get("source_class"))
    evidence_role_guess = _compact_text(record.get("evidence_role_guess"))
    source_kind_hint = _prepare_source_kind_hint(source_class)
    preparation_role = _prepare_role(source_class, evidence_role_guess)
    metadata_summary_id = _compact_text(record.get("metadata_summary_id"))
    intake_record = {
        "schema_version": SCHEMA_VERSION_V1,
        "evidence_intake_record_id": _compact_text(
            overrides.get("evidence_intake_record_id", f"intake_{_record_signature(record)}")
        ),
        "metadata_summary_id": metadata_summary_id,
        "source_locator_id": _compact_text(record.get("source_locator_id")),
        "science_direction_id": _compact_text(record.get("science_direction_id")),
        "source_class": source_class,
        "authority_level_guess": _compact_text(record.get("authority_level_guess")),
        "evidence_role_guess": evidence_role_guess,
        "candidate_title": _compact_text(record.get("candidate_title")),
        "candidate_url_or_identifier": _compact_text(record.get("candidate_url_or_identifier")),
        "candidate_domain": _compact_text(record.get("candidate_domain")),
        "metadata_summary_text": _compact_text(
            overrides.get(
                "metadata_summary_text",
                "Metadata-only locator synopsis for {} ({}, {}, {}).".format(
                    _compact_text(record.get("candidate_title"), "locator record"),
                    _compact_text(record.get("source_class"), "unknown source class"),
                    _compact_text(record.get("authority_level_guess"), "unknown authority"),
                    _compact_text(record.get("evidence_role_guess"), "unknown evidence role"),
                ),
            )
        )[:220],
        "source_kind_hint": _compact_text(overrides.get("source_kind_hint", source_kind_hint)),
        "evidence_preparation_role": _compact_text(
            overrides.get("evidence_preparation_role", preparation_role)
        ),
        "expected_evidence_shape": _compact_text(
            overrides.get(
                "expected_evidence_shape",
                _expected_evidence_shape(preparation_role, source_kind_hint),
            )
        )[:220],
        "provenance_stub": _compact_text(
            overrides.get(
                "provenance_stub",
                f"metadata-summary:{metadata_summary_id or 'missing'}",
            )
        )[:240],
        "normalization_plan": _compact_text(
            overrides.get(
                "normalization_plan",
                "Metadata-only normalization plan; no raw capture, no retention, no truth claims.",
            )
        )[:240],
        "candidate_mapping_plan": _compact_text(
            overrides.get(
                "candidate_mapping_plan",
                "Prepare future candidate mapping from metadata-only summary fields only.",
            )
        )[:240],
        "limitations": _compact_text(
            overrides.get(
                "limitations",
                "Metadata-only preparation record; not evidence and not a proposal.",
            )
        )[:240],
        "not_evidence_notice": _compact_text(
            overrides.get(
                "not_evidence_notice",
                "Metadata-only evidence-intake preparation record; not evidence.",
            )
        )[:240],
        "operator_review_need": _compact_text(
            overrides.get(
                "operator_review_need",
                _compact_text(record.get("operator_review_need"), "Operator review required before any evidence-intake action."),
            )
        )[:220],
        "allowed_next_step": _compact_text(
            overrides.get("allowed_next_step", "prepare_normalized_evidence_packet")
        ),
        "summary_status": _compact_text(overrides.get("summary_status", "metadata_summary_prepared")),
        "blocked_conditions": _normalize_text_list(
            overrides.get("blocked_conditions", record.get("blocked_conditions"))
        ),
        "source_summary_status": _compact_text(
            overrides.get("source_summary_status", record.get("summary_status", "metadata_summary_prepared"))
        ),
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
    }
    intake_record["authority_status"] = dict(overrides.get("authority_status", intake_record["authority_status"]))
    intake_record["safe_metadata"] = dict(overrides.get("safe_metadata", intake_record["safe_metadata"]))
    return intake_record



def _summary_bucket_status(prepared_count: int, excluded_operator_count: int, excluded_repair_count: int, excluded_blocked_count: int, blocked_count: int) -> str:
    if prepared_count > 0:
        return "evidence_intake_packet_prepared"
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
        return "prepare_normalized_evidence_packet"
    if blocked_count > 0:
        return "blocked_by_safety"
    if excluded_repair_count > 0:
        return "repair_metadata_summary_records"
    if excluded_operator_count > 0:
        return "operator_review"
    if excluded_blocked_count > 0:
        return "blocked_by_safety"
    return "blocked_by_safety"



def build_mlcf_evidence_intake_packet_from_metadata_summary_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged = _merge_payload(payload, **overrides)
    metadata_summary_packet = merged.pop("metadata_summary_packet", None)
    if metadata_summary_packet is None and isinstance(payload, Mapping):
        metadata_summary_packet = payload
    if not isinstance(metadata_summary_packet, Mapping):
        metadata_summary_packet = {}

    summary_records = list(metadata_summary_packet.get("metadata_only_source_summaries", []))
    excluded_summary_records = list(metadata_summary_packet.get("excluded_records", []))
    blocked_records = list(metadata_summary_packet.get("blocked_records", []))

    preparation_records: list[dict[str, Any]] = []
    excluded_intake_records: list[dict[str, Any]] = []
    blocked_intake_records: list[dict[str, Any]] = []
    source_class_counter: Counter[str] = Counter()
    authority_counter: Counter[str] = Counter()
    evidence_role_counter: Counter[str] = Counter()
    blocked_conditions: list[str] = []
    prepared_count = 0
    excluded_operator_count = 0
    excluded_repair_count = 0
    excluded_blocked_count = 0
    blocked_count = 0

    for record in summary_records:
        summary_record = _normalize_summary_record(record)
        source_class = _compact_text(summary_record.get("source_class")) or "unknown"
        authority = _compact_text(summary_record.get("authority_level_guess")) or "unknown"
        evidence_role = _compact_text(summary_record.get("evidence_role_guess")) or "unknown"
        source_class_counter[source_class] += 1
        authority_counter[authority] += 1
        evidence_role_counter[evidence_role] += 1

        if _compact_text(summary_record.get("summary_status")) != "metadata_summary_prepared":
            excluded_intake_records.append(
                _build_excluded_summary_record_v1(
                    summary_record,
                    status="excluded_needs_operator_review",
                    reason="operator_review_required_before_intake",
                    next_step="operator_review",
                )
            )
            excluded_operator_count += 1
            continue

        preparation_records.append(
            build_mlcf_evidence_intake_preparation_record_v1(
                summary_record,
                evidence_intake_record_id=f"intake_{_record_signature(summary_record)}",
                blocked_conditions=list(summary_record.get("blocked_conditions", [])),
                source_summary_status="metadata_summary_prepared",
            )
        )
        prepared_count += 1

    for record in excluded_summary_records:
        summary_record = _normalize_summary_record(record)
        source_class = _compact_text(summary_record.get("source_class")) or "unknown"
        authority = _compact_text(summary_record.get("authority_level_guess")) or "unknown"
        evidence_role = _compact_text(summary_record.get("evidence_role_guess")) or "unknown"
        source_class_counter[source_class] += 1
        authority_counter[authority] += 1
        evidence_role_counter[evidence_role] += 1

        status = _compact_text(summary_record.get("summary_status"))
        if status == "excluded_needs_operator_review":
            excluded_intake_records.append(
                _build_excluded_summary_record_v1(
                    summary_record,
                    status="excluded_needs_operator_review",
                    reason="operator_review_required_before_intake",
                    next_step="operator_review",
                )
            )
            excluded_operator_count += 1
        elif status == "excluded_needs_repair":
            excluded_intake_records.append(
                _build_excluded_summary_record_v1(
                    summary_record,
                    status="excluded_needs_repair",
                    reason="metadata_summary_needs_repair",
                    next_step="repair_metadata_summary_records",
                )
            )
            excluded_repair_count += 1
        elif status in {"excluded_rejected", "excluded_duplicate_or_low_value"}:
            excluded_intake_records.append(
                _build_excluded_summary_record_v1(
                    summary_record,
                    status=status,
                    reason="excluded_by_intake_policy",
                    next_step="operator_review",
                )
            )
            excluded_blocked_count += 1
        else:
            excluded_intake_records.append(
                _build_excluded_summary_record_v1(
                    summary_record,
                    status="excluded_needs_operator_review",
                    reason="operator_review_required_before_intake",
                    next_step="operator_review",
                )
            )
            excluded_operator_count += 1

    for record in blocked_records:
        blocked_record = _normalize_summary_record(record)
        source_class = _compact_text(blocked_record.get("source_class")) or "unknown"
        authority = _compact_text(blocked_record.get("authority_level_guess")) or "unknown"
        evidence_role = _compact_text(blocked_record.get("evidence_role_guess")) or "unknown"
        source_class_counter[source_class] += 1
        authority_counter[authority] += 1
        evidence_role_counter[evidence_role] += 1

        blocked_intake_records.append(_build_blocked_record_v1(blocked_record))
        blocked_count += 1

        reason = _compact_text(blocked_record.get("summary_exclusion_reason")) or _compact_text(blocked_record.get("review_decision_reason"))
        if reason and reason not in blocked_conditions:
            blocked_conditions.append(reason)

    input_count = len(summary_records) + len(excluded_summary_records) + len(blocked_records)
    intake_status = _summary_bucket_status(prepared_count, excluded_operator_count, excluded_repair_count, excluded_blocked_count, blocked_count)
    allowed_next_step = _packet_next_step(prepared_count, excluded_operator_count, excluded_repair_count, excluded_blocked_count, blocked_count)

    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "evidence_intake_packet_id": _compact_text(merged.get("evidence_intake_packet_id"), "default_evidence_intake_packet"),
        "science_direction_id": _compact_text(merged.get("science_direction_id"), _compact_text(metadata_summary_packet.get("science_direction_id"), "default_science_direction")),
        "science_direction_summary": _compact_text(merged.get("science_direction_summary"), _compact_text(metadata_summary_packet.get("science_direction_summary"), "Metadata-only evidence intake preparation packet.")),
        "source_summary_packet_ref": _compact_text(merged.get("source_summary_packet_ref"), _compact_text(metadata_summary_packet.get("summary_packet_id"), _compact_text(metadata_summary_packet.get("source_locator_review_packet_ref"), "source_summary_packet_ref_missing"))),
        "input_metadata_summary_count": input_count,
        "evidence_intake_preparation_records": preparation_records,
        "excluded_summary_records": excluded_intake_records,
        "blocked_records": blocked_intake_records,
        "preparation_record_count": prepared_count,
        "excluded_record_count": len(excluded_intake_records),
        "blocked_record_count": len(blocked_intake_records),
        "source_class_distribution": dict(source_class_counter),
        "authority_distribution": dict(authority_counter),
        "evidence_role_distribution": dict(evidence_role_counter),
        "intake_scope": _compact_text(merged.get("intake_scope"), "metadata_summary_records_only"),
        "operator_review_need": _compact_text(
            merged.get("operator_review_need"),
            "Operator review required; metadata-only evidence intake preparation boundaries preserved.",
        ),
        "allowed_next_step": allowed_next_step,
        "blocked_conditions": blocked_conditions,
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
        "intake_status": intake_status,
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
    if _compact_text(authority_status.get("status")) != "metadata_only_evidence_intake_preparation_packet":
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
        "no_source_ingestion",
        "no_evidence_claims",
        "no_normalized_evidence",
        "no_trusted_evidence",
        "no_candidate_graph_membership",
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
    if _contains_forbidden_markers(safe_metadata, _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_safe_metadata_text")
    if _contains_forbidden_markers(safe_metadata, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("unsafe_hidden_private_protected_marker")
    return not labels, labels



def _validate_preparation_record(record: Mapping[str, Any], labels: list[str]) -> None:
    for field in _RECORD_REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(record.get(field)):
            labels.append(f"missing_{field}")
    if _compact_text(record.get("summary_status")) and _compact_text(record.get("summary_status")) != "metadata_summary_prepared":
        labels.append("preparation_record_bad_summary_status")
    if _compact_text(record.get("source_summary_status")) not in {"metadata_summary_prepared"}:
        labels.append("preparation_record_not_from_ready_summary")
    if _compact_text(record.get("source_kind_hint")) not in _ALLOWED_SOURCE_KIND_HINTS_V1:
        labels.append("unsupported_source_kind_hint")
    if _compact_text(record.get("evidence_preparation_role")) not in _ALLOWED_PREPARATION_ROLES_V1:
        labels.append("unsupported_preparation_role")
    if _compact_text(record.get("allowed_next_step")) != "prepare_normalized_evidence_packet":
        labels.append("preparation_record_bad_next_step")
    if _record_has_forbidden_content(record):
        labels.append("preparation_record_contains_source_content")
    labels.extend(_record_has_unsafe_language(record))



def _validate_excluded_record(record: Mapping[str, Any], labels: list[str]) -> None:
    status = _compact_text(record.get("summary_status"))
    if status not in {
        "excluded_needs_operator_review",
        "excluded_needs_repair",
        "excluded_rejected",
        "excluded_duplicate_or_low_value",
        "blocked_by_safety",
    }:
        labels.append("invalid_excluded_record_status")
    if _compact_text(record.get("source_summary_status")) == "metadata_summary_prepared":
        labels.append("excluded_record_converted_from_ready_record")
    if _record_has_forbidden_content(record):
        labels.append("excluded_record_contains_source_content")
    labels.extend(_record_has_unsafe_language(record))



def _validate_blocked_record(record: Mapping[str, Any], labels: list[str]) -> None:
    status = _compact_text(record.get("summary_status"))
    if status != "blocked_by_safety":
        labels.append("blocked_record_not_blocked")
    if _record_has_forbidden_content(record):
        labels.append("blocked_record_contains_source_content")
    labels.extend(_record_has_unsafe_language(record))



def validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_packet_type"],
            "validation_posture": "blocked",
            "summary_text": "Invalid metadata-only evidence intake preparation packet.",
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
            "summary_text": "Missing required metadata-only evidence intake preparation packet fields.",
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
    if _compact_text(packet.get("intake_status")) not in _ALLOWED_STATUSES_V1:
        labels.append("unsupported_packet_status")
    if _compact_text(packet.get("allowed_next_step")) not in _ALLOWED_NEXT_STEPS_V1:
        labels.append("unsupported_next_step")
    if _compact_text(packet.get("input_metadata_summary_count"), "x").isdigit() is False:
        labels.append("invalid_input_metadata_summary_count")
    if _compact_text(packet.get("intake_scope")) not in {"metadata_summary_records_only", "metadata_only_summary", "ready_records_only"}:
        labels.append("unsupported_intake_scope")

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
        "normalized evidence",
        "trusted evidence",
        "accepted candidate",
        "proposal application",
        "proposal submission",
        "final answer",
        "public claim",
    )):
        labels.append("unsafe_claim_language")

    preparation_records = packet.get("evidence_intake_preparation_records")
    excluded_records = packet.get("excluded_summary_records")
    blocked_records = packet.get("blocked_records")
    if not isinstance(preparation_records, list) or not isinstance(excluded_records, list) or not isinstance(blocked_records, list):
        labels.append("invalid_record_containers")
    else:
        if int(_compact_text(packet.get("preparation_record_count"), "-1")) != len(preparation_records):
            labels.append("preparation_record_count_mismatch")
        if int(_compact_text(packet.get("excluded_record_count"), "-1")) != len(excluded_records):
            labels.append("excluded_record_count_mismatch")
        if int(_compact_text(packet.get("blocked_record_count"), "-1")) != len(blocked_records):
            labels.append("blocked_record_count_mismatch")
        for record in preparation_records:
            if not isinstance(record, Mapping):
                labels.append("invalid_preparation_record_type")
                continue
            _validate_preparation_record(record, labels)
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

    input_count = packet.get("input_metadata_summary_count")
    if isinstance(input_count, int):
        if input_count <= 0:
            labels.append("missing_input_metadata_summary_records")
        if input_count != len(preparation_records) + len(excluded_records) + len(blocked_records):
            labels.append("input_metadata_summary_count_mismatch")
    else:
        labels.append("invalid_input_metadata_summary_count")

    for field in ("preparation_record_count", "excluded_record_count", "blocked_record_count"):
        if not isinstance(packet.get(field), int):
            labels.append(f"invalid_{field}")

    for field_name in ("intake_scope", "operator_review_need", "intake_status"):
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
            "summary_text": "Blocked metadata-only evidence intake preparation packet.",
        }

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
        "validation_posture": "valid",
        "summary_text": "Valid metadata-only evidence intake preparation packet.",
    }



def summarize_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet: Any) -> dict[str, Any]:
    validation = validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
    packet = packet if isinstance(packet, Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "evidence_intake_packet_id": _compact_text(packet.get("evidence_intake_packet_id")),
        "science_direction_id": _compact_text(packet.get("science_direction_id")),
        "source_summary_packet_ref": _compact_text(packet.get("source_summary_packet_ref")),
        "intake_status": _compact_text(packet.get("intake_status")),
        "preparation_record_count": int(packet.get("preparation_record_count", 0)) if str(packet.get("preparation_record_count", 0)).isdigit() else packet.get("preparation_record_count", 0),
        "excluded_record_count": int(packet.get("excluded_record_count", 0)) if str(packet.get("excluded_record_count", 0)).isdigit() else packet.get("excluded_record_count", 0),
        "blocked_record_count": int(packet.get("blocked_record_count", 0)) if str(packet.get("blocked_record_count", 0)).isdigit() else packet.get("blocked_record_count", 0),
        "allowed_next_step": _compact_text(packet.get("allowed_next_step")),
        "validation_posture": validation.get("validation_posture", "blocked"),
        "summary_text": _compact_text(packet.get("science_direction_summary"), "Metadata-only evidence intake preparation packet.")[:220],
    }



def to_mlcf_evidence_intake_packet_from_metadata_summary_json_safe_v1(packet: Any) -> Any:
    return _json_safe(deepcopy(packet))



def build_initial_mlcf_evidence_intake_packet_from_metadata_summary_examples_v1() -> list[dict[str, Any]]:
    source_examples = build_initial_mlcf_authorized_metadata_only_source_summary_examples_v1()
    review_examples = build_initial_mlcf_source_locator_organization_review_packet_examples_v1()
    frontier_review = next(item for item in review_examples if item["review_packet_id"] == "frontier_space_fixture_locator_review_packet")
    rf_review = next(item for item in review_examples if item["review_packet_id"] == "rf_material_floorplan_locator_review_packet")
    examples: list[dict[str, Any]] = []

    frontier_source = next(item for item in source_examples if item["summary_packet_id"] == "frontier_space_ready_metadata_summary_packet")
    examples.append(
        build_mlcf_evidence_intake_packet_from_metadata_summary_v1(
            evidence_intake_packet_id="frontier_space_metadata_summary_to_evidence_intake_packet",
            science_direction_id=frontier_source["science_direction_id"],
            science_direction_summary="Metadata-only evidence intake packet for ready frontier-space locator summaries.",
            source_summary_packet_ref=frontier_source["summary_packet_id"],
            intake_scope="metadata_summary_records_only",
            metadata_summary_packet=frontier_source,
        )
    )

    rf_source_packet = build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="rf_operator_review_only_metadata_summary_packet",
        science_direction_id=rf_review["science_direction_id"],
        science_direction_summary=rf_review["science_direction_summary"],
        source_locator_review_packet_ref=rf_review["review_packet_id"],
        review_records=rf_review["bucketed_locator_records"]["keep_for_operator_review"],
        metadata_summary_scope="ready_records_only",
    )
    examples.append(
        build_mlcf_evidence_intake_packet_from_metadata_summary_v1(
            evidence_intake_packet_id="rf_metadata_summary_operator_review_excluded_packet",
            science_direction_id=rf_source_packet["science_direction_id"],
            science_direction_summary="Metadata-only evidence intake packet for RF operator-review-only summaries.",
            source_summary_packet_ref=rf_source_packet["summary_packet_id"],
            intake_scope="metadata_summary_records_only",
            metadata_summary_packet=rf_source_packet,
        )
    )

    blocked_source_packet = build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="blocked_locator_metadata_summary_packet",
        science_direction_id=frontier_review["science_direction_id"],
        science_direction_summary="Metadata-only blocked locator packet.",
        source_locator_review_packet_ref=frontier_review["review_packet_id"],
        review_records=frontier_review["bucketed_locator_records"]["blocked"],
        metadata_summary_scope="ready_records_only",
    )
    examples.append(
        build_mlcf_evidence_intake_packet_from_metadata_summary_v1(
            evidence_intake_packet_id="blocked_metadata_summary_to_evidence_intake_packet",
            science_direction_id=blocked_source_packet["science_direction_id"],
            science_direction_summary="Metadata-only evidence intake packet for blocked metadata summaries.",
            source_summary_packet_ref=blocked_source_packet["summary_packet_id"],
            intake_scope="metadata_summary_records_only",
            metadata_summary_packet=blocked_source_packet,
        )
    )
    return examples
