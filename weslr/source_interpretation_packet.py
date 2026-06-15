"""WESLR source interpretation packet V1.

Helper-only, metadata-first, deterministic interpretation helpers for authorized
sources. These helpers do not fetch sources, read PDFs, ingest datasets,
browse the web, call providers/models, write .weslr data, auto-apply ontology,
or create accepted evidence, accepted candidates, final answers, or public
claims.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

SCHEMA_NAME_V1 = "source_interpretation_packet"
SCHEMA_VERSION_V1 = "v1"

_ALLOWED_SOURCE_CLASSES_V1 = (
    "official_standard",
    "official_government_or_agency_data",
    "official_vendor_documentation",
    "public_research_paper",
    "public_dataset",
    "github_repository",
    "public_lab_or_university_artifact",
    "public_benchmark_or_test_suite",
    "public_news_or_report",
    "forum_or_social_discussion",
    "owner_uploaded_file",
    "owner_pasted_text",
    "private_owner_authorized_source",
    "unknown_source_class",
    "blocked_source_class",
)
_ALLOWED_ACCESS_LEVELS_V1 = (
    "public_open",
    "public_unknown_license",
    "owner_uploaded",
    "owner_pasted",
    "private_owner_authorized",
    "restricted_or_paid",
    "blocked_access",
    "unknown_access",
)
_ALLOWED_LICENSE_POSTURES_V1 = (
    "open_access_confirmed",
    "public_metadata_only",
    "license_unknown",
    "restricted_or_paid",
    "owner_authorized_private",
    "blocked_license_or_access",
)
_ALLOWED_PRIVACY_POSTURES_V1 = (
    "public_non_private",
    "owner_provided_non_private",
    "owner_authorized_private",
    "private_requires_authorization",
    "contains_sensitive_data",
    "blocked_private_or_secret",
    "unknown_privacy",
)
_ALLOWED_RETENTION_MODES_V1 = (
    "metadata_only_no_content_retention",
    "derived_summary_only",
    "bounded_excerpt_with_citation",
    "full_text_transient_no_retention",
    "full_text_retention_owner_authorized",
    "blocked_retention",
)
_ALLOWED_CONFIDENCE_POSTURES_V1 = (
    "interpretation_low",
    "interpretation_medium",
    "interpretation_high",
    "interpretation_conflicted",
    "interpretation_unknown",
)
_ALLOWED_CONFLICT_STATUSES_V1 = (
    "no_known_conflict",
    "internal_source_conflict",
    "conflict_with_other_source",
    "conflict_with_known_science_replay",
    "conflict_requiring_expert_review",
    "conflict_requiring_more_evidence",
    "conflict_requiring_stop_or_block",
)
_ALLOWED_CANDIDATE_PREP_V1 = (
    "candidate_preparation_excluded",
    "candidate_preparation_premature",
    "candidate_preparation_possible_after_review",
    "candidate_preparation_possible_after_evidence_normalization",
    "candidate_preparation_blocked",
)
_ALLOWED_OER_HINTS_V1 = (
    "ontology_seems_sufficient",
    "ontology_seems_insufficient",
    "route_to_oer_noop",
    "route_to_ontology_expansion_request",
    "route_to_operator_review",
    "no_ontology_action",
)
_ALLOWED_EVIDENCE_ROLE_TARGETS_V1 = (
    "primary_evidence_candidate",
    "supporting_evidence_candidate",
    "counterevidence_candidate",
    "disconfirmation_source_candidate",
    "method_limit_source",
    "implementation_reference",
    "historical_context",
    "known_science_replay_reference",
    "source_selection_reference",
    "weak_signal_only",
    "not_evidence",
    "blocked_evidence",
)
_ALLOWED_ARTIFACT_ROUTES_V1 = (
    "unexplained_signal_artifact",
    "false_assumption_or_overclaim_artifact",
    "unfinished_work_artifact",
    "experiment_plan_artifact",
    "source_selection_evidence_plan",
    "normalized_evidence_packet",
    "artifact_forward_work_plan",
    "product_or_workflow_artifact",
    "operator_review",
    "expert_review",
    "blocked_state",
)
_DENIED_AUTHORITY_FLAGS_V1 = (
    "accepted_evidence_authority",
    "accepted_candidate_authority",
    "final_answer_authority",
    "public_claim_authority",
    "proof_claim_authority",
    "discovery_truth_claim_authority",
    "product_readiness_claim_authority",
    "runtime_wiring_authority",
    "provider_model_call_authority",
    "source_fetch_authority",
    "source_ingestion_authority",
    "raw_retention_authority",
    "memory_mutation_authority",
    "database_write_authority",
    "weslr_io_authority",
    "ontology_auto_application_authority",
    "self_modification_authority",
)
_FORBIDDEN_WORDING_V1 = (
    ".weslr",
    "hidden prompt",
    "private memory",
    "credential",
    "credentials",
    "secret",
    "secrets",
    "token",
    "tokens",
    "accepted evidence",
    "accepted candidate",
    "accepted discovery",
    "final answer",
    "proof",
    "discovery",
    "public science",
    "product ready",
    "runtime enabled",
    "provider call",
    "source fetch",
    "source ingestion",
    "ontology applied automatically",
    "self-modification",
    "same mechanism",
    "same-mechanism",
)
_REQUIRED_FIELDS_V1 = (
    "schema_name",
    "schema_version",
    "interpretation_packet_id",
    "ingestion_request_id",
    "authorization_packet_ref",
    "source_ref",
    "source_class",
    "source_access_level",
    "license_access_posture",
    "privacy_posture",
    "retention_mode",
    "source_metadata",
    "interpreted_under_authorization",
    "bounded_content_policy",
    "extracted_claims",
    "extracted_assumptions",
    "method_limits",
    "evidence_role_candidates",
    "counterevidence_or_disconfirmation",
    "source_conflicts",
    "missing_evidence",
    "pattern_attribution_candidates",
    "artifact_route_candidates",
    "mlcf_normalization_hints",
    "oer_or_noop_hints",
    "candidate_preparation_eligibility",
    "review_requirements",
    "blocked_claims",
    "denied_authority_flags",
    "abort_conditions",
    "blocked_labels",
    "safe_metadata_summary",
    "next_safe_step",
    "final_judgment",
)


def _t(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _l(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(value)
    return [deepcopy(value)]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, set):
        return [_json_safe(v) for v in sorted(value, key=str)]
    return deepcopy(value)


def _lower_text(value: Any) -> str:
    return _t(value).lower()


def _contains_forbidden_text(value: Any) -> bool:
    text = _lower_text(value)
    return any(marker in text for marker in _FORBIDDEN_WORDING_V1)


def _flatten_texts(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _flatten_texts(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _flatten_texts(item)
    else:
        yield _t(value)


def _claim_is_same_mechanism(claim: Mapping[str, Any]) -> bool:
    texts = (
        claim.get("claim_text_or_safe_paraphrase"),
        claim.get("statement"),
        claim.get("description"),
        claim.get("possible_mechanism_overlap_posture"),
    )
    return any("same mechanism" in _lower_text(text) or "same-mechanism" in _lower_text(text) for text in texts)


def _normalize_list_items(value: Any, item_key: str | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _l(value):
        if isinstance(raw, Mapping):
            item = dict(raw)
        else:
            item = {item_key or "value": raw}
        items.append(item)
    return items


def _normalize_source_metadata(value: Any) -> dict[str, Any]:
    metadata = {
        "title": "",
        "authors_or_organization": "",
        "publication_or_source_date": "",
        "source_host_or_domain": "",
        "source_class": "",
        "source_access_level": "",
        "license_access_posture": "",
        "privacy_posture": "",
        "citation_or_provenance_ref": "",
        "locator_record_ref": "",
        "safe_content_hash": "",
        "retrieval_timestamp": "",
    }
    if isinstance(value, Mapping):
        for key in metadata:
            if key in value:
                metadata[key] = value[key]
        for key, raw in value.items():
            if key not in metadata:
                metadata[str(key)] = _json_safe(raw)
    return metadata


def _normalize_bounded_content_policy(value: Any, retention_mode: str) -> dict[str, Any]:
    policy = {
        "raw_content_allowed": False,
        "safe_paraphrase_allowed": True,
        "bounded_excerpt_allowed": False,
        "max_excerpt_chars": 0,
        "max_excerpt_count": 0,
        "citation_required": True,
        "source_location_ref_required": True,
        "raw_retention_allowed": False,
        "owner_authorization_required_for_raw_retention": False,
    }
    if isinstance(value, Mapping):
        for key in policy:
            if key in value:
                policy[key] = value[key]
    if retention_mode == "bounded_excerpt_with_citation":
        policy["bounded_excerpt_allowed"] = True
        policy["citation_required"] = True
        policy["source_location_ref_required"] = True
    elif retention_mode == "metadata_only_no_content_retention":
        policy["bounded_excerpt_allowed"] = False
        policy["raw_content_allowed"] = False
        policy["raw_retention_allowed"] = False
    elif retention_mode == "derived_summary_only":
        policy["bounded_excerpt_allowed"] = False
        policy["raw_content_allowed"] = False
        policy["raw_retention_allowed"] = False
    elif retention_mode == "full_text_transient_no_retention":
        policy["raw_content_allowed"] = False
        policy["raw_retention_allowed"] = False
        policy["safe_paraphrase_allowed"] = True
    elif retention_mode == "full_text_retention_owner_authorized":
        policy["raw_content_allowed"] = True
        policy["raw_retention_allowed"] = True
        policy["owner_authorization_required_for_raw_retention"] = True
        policy["bounded_excerpt_allowed"] = True
        policy["citation_required"] = True
        policy["source_location_ref_required"] = True
    return policy


def _normalize_review_requirements(value: Any) -> dict[str, Any]:
    requirements = {
        "owner_authorization_required": False,
        "owner_authorization_present": False,
        "operator_review_required": True,
        "expert_review_required": False,
        "required_review_labels": ["operator_review"],
    }
    if isinstance(value, Mapping):
        for key in requirements:
            if key in value:
                requirements[key] = value[key]
    if requirements["owner_authorization_required"]:
        if "owner_authorization" not in requirements["required_review_labels"]:
            requirements["required_review_labels"].append("owner_authorization")
    if requirements["expert_review_required"] and "expert_review" not in requirements["required_review_labels"]:
        requirements["required_review_labels"].append("expert_review")
    return requirements


def _normalize_denied_flags(value: Any) -> dict[str, bool]:
    flags = {flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1}
    if isinstance(value, Mapping):
        for flag in flags:
            if flag in value:
                flags[flag] = bool(value[flag])
    return flags


def _normalize_extracted_claims(value: Any) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for raw in _l(value):
        if isinstance(raw, Mapping):
            claim = dict(raw)
        else:
            claim = {"claim_text_or_safe_paraphrase": raw}
        claim.setdefault("claim_id", "")
        claim.setdefault("claim_text_or_safe_paraphrase", "")
        claim.setdefault("claim_type", "")
        claim.setdefault("source_location_ref", "")
        claim.setdefault("evidence_role_candidate", "not_evidence")
        claim.setdefault("confidence_posture", "interpretation_unknown")
        claim.setdefault("required_review", "operator_review")
        claim.setdefault("blocked_claims", [])
        claim.setdefault("disconfirmation_need", "")
        claims.append(claim)
    return claims


def _normalize_assumptions_or_limits(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _l(value):
        if isinstance(raw, Mapping):
            item = dict(raw)
        else:
            item = {"statement": raw}
        item.setdefault("id", "")
        item.setdefault("statement", "")
        item.setdefault("category", "")
        item.setdefault("why_it_matters", "")
        item.setdefault("what_would_break_it", "")
        item.setdefault("review_required", "operator_review")
        item.setdefault("related_claim_ids", [])
        items.append(item)
    return items


def _normalize_evidence_roles(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _l(value):
        if isinstance(raw, Mapping):
            item = dict(raw)
        else:
            item = {"evidence_role_candidate": raw}
        item.setdefault("evidence_role_candidate", item.get("role", "not_evidence"))
        item.setdefault("role", item.get("evidence_role_candidate", "not_evidence"))
        item.setdefault("claim_ids", [])
        item.setdefault("confidence_posture", "interpretation_unknown")
        item.setdefault("required_review", "operator_review")
        item.setdefault("blocked_claims", [])
        item.setdefault("disconfirmation_need", "")
        items.append(item)
    return items


def _normalize_conflicts(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _l(value):
        if isinstance(raw, Mapping):
            item = dict(raw)
        else:
            item = {"conflict_status": raw}
        item.setdefault("conflict_status", "no_known_conflict")
        item.setdefault("conflict_ref", "")
        item.setdefault("summary", "")
        item.setdefault("required_review", "operator_review")
        items.append(item)
    return items


def _normalize_pattern_candidates(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _l(value):
        if isinstance(raw, Mapping):
            item = dict(raw)
        else:
            item = {"source_pattern_id": raw}
        item.setdefault("source_pattern_id", "")
        item.setdefault("target_domain_or_experiment", "")
        item.setdefault("shared_structure", "")
        item.setdefault("key_differences", "")
        item.setdefault("possible_mechanism_overlap_posture", "")
        item.setdefault("disconfirmation_tests", [])
        item.setdefault("analogy_strength", "interpretation_unknown")
        item.setdefault("blocked_claims", [])
        item.setdefault("next_safe_step", "")
        items.append(item)
    return items


def _normalize_routes(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _l(value):
        if isinstance(raw, Mapping):
            item = dict(raw)
        else:
            item = {"route": raw}
        item.setdefault("route", item.get("artifact_route", "blocked_state"))
        item.setdefault("artifact_route", item.get("route", "blocked_state"))
        item.setdefault("summary", "")
        item.setdefault("required_review", "operator_review")
        items.append(item)
    return items


def _normalize_hints(value: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _l(value):
        if isinstance(raw, Mapping):
            item = dict(raw)
        else:
            item = {"hint": raw}
        items.append(item)
    return items


def _default_blocked_claims() -> list[str]:
    return [
        "no evidence promotion",
        "no candidate promotion",
        "no claim finalization",
        "no public posting",
    ]


def _default_abort_conditions() -> list[str]:
    return [
        "authorization reference required",
        "provenance minimum required",
        "review gate required",
    ]


def _default_safe_summary() -> str:
    return "review-bound interpretation packet; metadata-only by default; no truth or public-claim authority"


def _default_review_requirements() -> dict[str, Any]:
    return {
        "owner_authorization_required": False,
        "owner_authorization_present": False,
        "operator_review_required": True,
        "expert_review_required": False,
        "required_review_labels": ["operator_review"],
    }


def build_source_interpretation_packet_v1(**packet: Any) -> dict[str, Any]:
    source_class = _t(packet.get("source_class", "unknown_source_class"))
    retention_mode = _t(packet.get("retention_mode", "metadata_only_no_content_retention"))
    review_requirements = _normalize_review_requirements(packet.get("review_requirements", _default_review_requirements()))
    if packet.get("owner_authorization_required") is not None:
        review_requirements["owner_authorization_required"] = bool(packet.get("owner_authorization_required"))
    if packet.get("owner_authorization_present") is not None:
        review_requirements["owner_authorization_present"] = bool(packet.get("owner_authorization_present"))
    if packet.get("operator_review_required") is not None:
        review_requirements["operator_review_required"] = bool(packet.get("operator_review_required"))
    if packet.get("expert_review_required") is not None:
        review_requirements["expert_review_required"] = bool(packet.get("expert_review_required"))
    if review_requirements["operator_review_required"] and "operator_review" not in review_requirements["required_review_labels"]:
        review_requirements["required_review_labels"].append("operator_review")
    if review_requirements["expert_review_required"] and "expert_review" not in review_requirements["required_review_labels"]:
        review_requirements["required_review_labels"].append("expert_review")
    if review_requirements["owner_authorization_required"] and "owner_authorization" not in review_requirements["required_review_labels"]:
        review_requirements["required_review_labels"].append("owner_authorization")

    bounded_content_policy = _normalize_bounded_content_policy(
        packet.get("bounded_content_policy"),
        retention_mode,
    )
    if packet.get("raw_retention_allowed") is not None:
        bounded_content_policy["raw_retention_allowed"] = bool(packet.get("raw_retention_allowed"))
    if packet.get("quoted_excerpt_allowed") is not None:
        bounded_content_policy["bounded_excerpt_allowed"] = bool(packet.get("quoted_excerpt_allowed"))
    if packet.get("safe_paraphrase_allowed") is not None:
        bounded_content_policy["safe_paraphrase_allowed"] = bool(packet.get("safe_paraphrase_allowed"))
    if packet.get("owner_authorization_required_for_raw_retention") is not None:
        bounded_content_policy["owner_authorization_required_for_raw_retention"] = bool(packet.get("owner_authorization_required_for_raw_retention"))

    source_metadata = _normalize_source_metadata(packet.get("source_metadata"))
    if "source_class" not in source_metadata or not source_metadata["source_class"]:
        source_metadata["source_class"] = source_class
    if "source_access_level" not in source_metadata or not source_metadata["source_access_level"]:
        source_metadata["source_access_level"] = _t(packet.get("source_access_level", "unknown_access"))
    if "license_access_posture" not in source_metadata or not source_metadata["license_access_posture"]:
        source_metadata["license_access_posture"] = _t(packet.get("license_access_posture", "license_unknown"))
    if "privacy_posture" not in source_metadata or not source_metadata["privacy_posture"]:
        source_metadata["privacy_posture"] = _t(packet.get("privacy_posture", "unknown_privacy"))

    source_ref = _t(packet.get("source_ref", ""))
    claim_list = _normalize_extracted_claims(packet.get("extracted_claims", []))
    assumption_list = _normalize_assumptions_or_limits(packet.get("extracted_assumptions", []))
    method_limit_list = _normalize_assumptions_or_limits(packet.get("method_limits", []))
    evidence_roles = _normalize_evidence_roles(packet.get("evidence_role_candidates", []))
    disconfirmation = _normalize_hints(packet.get("counterevidence_or_disconfirmation", []))
    conflicts = _normalize_conflicts(packet.get("source_conflicts", []))
    missing_evidence = _normalize_hints(packet.get("missing_evidence", []))
    pattern_candidates = _normalize_pattern_candidates(packet.get("pattern_attribution_candidates", []))
    artifact_routes = _normalize_routes(packet.get("artifact_route_candidates", []))
    mlcf_hints = _normalize_hints(packet.get("mlcf_normalization_hints", []))
    oer_hints = _normalize_hints(packet.get("oer_or_noop_hints", []))
    blocked_claims = _l(packet.get("blocked_claims", _default_blocked_claims()))
    abort_conditions = _l(packet.get("abort_conditions", _default_abort_conditions()))
    denied_flags = _normalize_denied_flags(packet.get("denied_authority_flags", {}))
    blocked_labels = _l(packet.get("blocked_labels", []))

    if _t(packet.get("interpretation_packet_id")):
        interpretation_packet_id = _t(packet.get("interpretation_packet_id"))
    else:
        interpretation_packet_id = f"interpretation_packet_{_t(packet.get('ingestion_request_id', 'v1'))}"

    if not _t(packet.get("authorization_packet_ref")):
        authorization_packet_ref = f"authorization_packet_ref:{_t(packet.get('ingestion_request_id', 'v1'))}"
    else:
        authorization_packet_ref = _t(packet.get("authorization_packet_ref"))

    packet_out = {
        "schema_name": SCHEMA_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "interpretation_packet_id": interpretation_packet_id,
        "ingestion_request_id": _t(packet.get("ingestion_request_id", "ingestion_request_v1")),
        "authorization_packet_ref": authorization_packet_ref,
        "source_ref": source_ref,
        "source_class": source_class,
        "source_access_level": _t(packet.get("source_access_level", source_metadata["source_access_level"])),
        "license_access_posture": _t(packet.get("license_access_posture", source_metadata["license_access_posture"])),
        "privacy_posture": _t(packet.get("privacy_posture", source_metadata["privacy_posture"])),
        "retention_mode": retention_mode,
        "source_metadata": source_metadata,
        "interpreted_under_authorization": bool(packet.get("interpreted_under_authorization", True)),
        "bounded_content_policy": bounded_content_policy,
        "extracted_claims": claim_list,
        "extracted_assumptions": assumption_list,
        "method_limits": method_limit_list,
        "evidence_role_candidates": evidence_roles,
        "counterevidence_or_disconfirmation": disconfirmation,
        "source_conflicts": conflicts,
        "missing_evidence": missing_evidence,
        "pattern_attribution_candidates": pattern_candidates,
        "artifact_route_candidates": artifact_routes,
        "mlcf_normalization_hints": mlcf_hints,
        "oer_or_noop_hints": oer_hints,
        "candidate_preparation_eligibility": _t(packet.get("candidate_preparation_eligibility", "candidate_preparation_premature")),
        "review_requirements": review_requirements,
        "blocked_claims": blocked_claims,
        "denied_authority_flags": denied_flags,
        "abort_conditions": abort_conditions,
        "blocked_labels": blocked_labels,
        "safe_metadata_summary": _t(packet.get("safe_metadata_summary", _default_safe_summary())),
        "next_safe_step": _t(packet.get("next_safe_step", "owner_review")),
        "final_judgment": _t(packet.get("final_judgment", "interpretation_packet_pending_review")),
    }

    if "source_location_ref" not in packet_out:
        packet_out["source_location_ref"] = _t(packet.get("source_location_ref", ""))
    if "confidence_posture" not in packet_out:
        packet_out["confidence_posture"] = _t(packet.get("confidence_posture", "interpretation_unknown"))

    if source_class == "blocked_source_class":
        packet_out["blocked_labels"].append("blocked_source_class_rejected")
    if retention_mode == "blocked_retention":
        packet_out["blocked_labels"].append("blocked_retention_not_allowed")

    return packet_out


def _packet_contains_raw_content(packet: Mapping[str, Any]) -> bool:
    for text in _flatten_texts(packet):
        lowered = text.lower()
        if any(marker in lowered for marker in ("raw text", "full text", "source dump", "raw dump")):
            return True
    for key in ("raw_content", "raw_text", "full_text", "source_dump", "content_dump"):
        if key in packet:
            return True
    return False


def _extract_conflict_statuses(packet: Mapping[str, Any]) -> list[str]:
    statuses: list[str] = []
    for item in _l(packet.get("source_conflicts")):
        if isinstance(item, Mapping):
            status = _t(item.get("conflict_status", item.get("status", "")))
            if status:
                statuses.append(status)
        else:
            status = _t(item)
            if status:
                statuses.append(status)
    return statuses


def _has_provenance_minimum(packet: Mapping[str, Any]) -> bool:
    source_ref = _t(packet.get("source_ref"))
    source_metadata = packet.get("source_metadata") if isinstance(packet.get("source_metadata"), Mapping) else {}
    provenance_ref = _t(source_metadata.get("citation_or_provenance_ref"))
    source_location_ref = _t(source_metadata.get("source_location_ref"))
    locator_ref = _t(source_metadata.get("locator_record_ref"))
    if not source_ref:
        return False
    return bool(provenance_ref or source_location_ref or locator_ref)


def _safe_provenance_present(packet: Mapping[str, Any]) -> bool:
    source_metadata = packet.get("source_metadata") if isinstance(packet.get("source_metadata"), Mapping) else {}
    return bool(
        _t(packet.get("source_ref"))
        or _t(source_metadata.get("citation_or_provenance_ref"))
        or _t(source_metadata.get("source_location_ref"))
        or _t(source_metadata.get("locator_record_ref"))
    )


def _claim_texts(packet: Mapping[str, Any]) -> Iterable[str]:
    for claim in _l(packet.get("extracted_claims")):
        if isinstance(claim, Mapping):
            yield _t(claim.get("claim_text_or_safe_paraphrase"))
            yield _t(claim.get("claim_type"))
            yield _t(claim.get("required_review"))
            yield _t(claim.get("evidence_role_candidate"))
            yield _t(claim.get("disconfirmation_need"))
            for blocked in _l(claim.get("blocked_claims")):
                yield _t(blocked)
        else:
            yield _t(claim)


def _hint_texts(packet: Mapping[str, Any]) -> Iterable[str]:
    for group in (
        packet.get("source_metadata"),
        packet.get("bounded_content_policy"),
        packet.get("review_requirements"),
        packet.get("safe_metadata_summary"),
        packet.get("next_safe_step"),
        packet.get("final_judgment"),
        packet.get("blocked_claims"),
        packet.get("abort_conditions"),
    ):
        yield from _flatten_texts(group)


def validate_source_interpretation_packet_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    blocked_labels: list[str] = []

    def block(label: str) -> None:
        if label not in blocked_labels:
            blocked_labels.append(label)

    if not isinstance(packet, Mapping):
        return {"valid": False, "blocked": True, "blocked_labels": ["invalid_packet_type"]}

    missing = [field for field in _REQUIRED_FIELDS_V1 if field not in packet]
    for field in missing:
        block(f"missing_field:{field}")

    if _t(packet.get("schema_name")) != SCHEMA_NAME_V1:
        block("invalid_schema_name")
    if _t(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        block("invalid_schema_version")

    source_class = _t(packet.get("source_class"))
    retention_mode = _t(packet.get("retention_mode"))
    if source_class not in _ALLOWED_SOURCE_CLASSES_V1:
        block("invalid_source_class")
    if source_class == "blocked_source_class":
        block("blocked_source_class_rejected")
    if retention_mode not in _ALLOWED_RETENTION_MODES_V1:
        block("invalid_retention_mode")
    if retention_mode == "blocked_retention":
        block("blocked_retention_not_allowed")

    if not _t(packet.get("source_ref")):
        block("missing_source_ref")

    if not _has_provenance_minimum(packet):
        block("provenance_citation_minimum_missing")

    if not _safe_provenance_present(packet):
        block("provenance_reference_missing")

    if not _t(packet.get("authorization_packet_ref")):
        block("missing_authorization_reference")

    if not _t(packet.get("ingestion_request_id")):
        block("missing_ingestion_request_id")

    review_requirements = packet.get("review_requirements") if isinstance(packet.get("review_requirements"), Mapping) else {}
    if not review_requirements:
        block("missing_review_requirements")
    else:
        if not any(bool(review_requirements.get(key)) for key in ("owner_authorization_required", "operator_review_required", "expert_review_required")):
            block("review_requirements_missing")

    if not _l(packet.get("blocked_claims")):
        block("blocked_claims_empty")
    if not _l(packet.get("abort_conditions")):
        block("abort_conditions_empty")
    if not _t(packet.get("next_safe_step")):
        block("missing_next_safe_step")

    denied = packet.get("denied_authority_flags")
    if not isinstance(denied, Mapping):
        block("denied_authority_flags_invalid")
    else:
        for flag in _DENIED_AUTHORITY_FLAGS_V1:
            if denied.get(flag) is True:
                block(f"denied_authority_true:{flag}")

    if _contains_forbidden_text(packet.get("source_ref")):
        block("forbidden_source_reference_wording")

    source_metadata = packet.get("source_metadata") if isinstance(packet.get("source_metadata"), Mapping) else {}
    for key, value in source_metadata.items():
        if key in {"raw_content", "raw_text", "full_text", "source_dump", "content_dump"}:
            block("raw_content_present")
        if _contains_forbidden_text(value):
            block(f"forbidden_source_metadata_wording:{key}")

    if _packet_contains_raw_content(packet):
        block("raw_content_present")

    for text in _hint_texts(packet):
        if any(marker in text.lower() for marker in ("hidden prompt", "private memory", "credential", "credentials", "secret", "secrets", "token", "tokens")):
            block("sensitive_content_wording_present")
        if any(marker in text.lower() for marker in ("accepted evidence", "accepted candidate", "accepted discovery", "final answer", "proof", "discovery", "public science", "product ready", "runtime enabled", "provider call", "source fetch", "source ingestion", "ontology applied automatically", "self-modification")):
            block("forbidden_claim_wording_present")
        if "same mechanism" in text.lower() or "same-mechanism" in text.lower():
            block("same_mechanism_claim_blocked")

    retention_policy = packet.get("bounded_content_policy") if isinstance(packet.get("bounded_content_policy"), Mapping) else {}
    if not retention_policy:
        block("missing_bounded_content_policy")
    else:
        if retention_mode == "metadata_only_no_content_retention":
            if retention_policy.get("bounded_excerpt_allowed"):
                block("metadata_only_excerpts_not_allowed")
            if retention_policy.get("raw_content_allowed") or retention_policy.get("raw_retention_allowed"):
                block("metadata_only_raw_content_not_allowed")
        if retention_mode == "derived_summary_only":
            if retention_policy.get("raw_content_allowed") or retention_policy.get("raw_retention_allowed"):
                block("derived_summary_raw_content_not_allowed")
        if retention_mode == "bounded_excerpt_with_citation":
            if not retention_policy.get("bounded_excerpt_allowed"):
                block("bounded_excerpt_policy_missing")
            if not retention_policy.get("citation_required"):
                block("bounded_excerpt_citation_required")
            if not retention_policy.get("source_location_ref_required"):
                block("bounded_excerpt_source_location_required")
            if int(retention_policy.get("max_excerpt_chars", 0) or 0) <= 0:
                block("bounded_excerpt_max_chars_missing")
            if int(retention_policy.get("max_excerpt_count", 0) or 0) <= 0:
                block("bounded_excerpt_max_count_missing")
        if retention_mode == "full_text_transient_no_retention":
            if retention_policy.get("raw_content_allowed") or retention_policy.get("raw_retention_allowed"):
                block("transient_full_text_raw_retention_not_allowed")
        if retention_mode == "full_text_retention_owner_authorized":
            if not bool(review_requirements.get("owner_authorization_required")):
                block("owner_authorization_required_missing_for_raw_retention")
            if not bool(review_requirements.get("owner_authorization_present")):
                block("owner_authorization_present_missing_for_raw_retention")
            if not retention_policy.get("raw_content_allowed") or not retention_policy.get("raw_retention_allowed"):
                block("raw_retention_policy_missing")
            if not retention_policy.get("owner_authorization_required_for_raw_retention"):
                block("raw_retention_owner_auth_policy_missing")

    candidate_prep = _t(packet.get("candidate_preparation_eligibility"))
    if candidate_prep not in _ALLOWED_CANDIDATE_PREP_V1:
        block("invalid_candidate_preparation_eligibility")

    conflict_labels: list[str] = []
    for conflict in _l(packet.get("source_conflicts")):
        if isinstance(conflict, Mapping):
            status = _t(conflict.get("conflict_status", conflict.get("status", "")))
            if status:
                conflict_labels.append(status)
        else:
            status = _t(conflict)
            if status:
                conflict_labels.append(status)
    for status in conflict_labels:
        if status not in _ALLOWED_CONFLICT_STATUSES_V1:
            block(f"invalid_conflict_status:{status}")
    if "conflict_requiring_expert_review" in conflict_labels and not bool(review_requirements.get("expert_review_required")):
        block("expert_review_required_for_conflict")
    if "conflict_requiring_stop_or_block" in conflict_labels:
        block("conflict_requires_block")
    if any(status in {"conflict_requiring_expert_review", "conflict_requiring_stop_or_block"} for status in conflict_labels) and not bool(review_requirements.get("expert_review_required")):
        block("expert_review_required_for_conflict_escalation")

    evidence_roles: list[str] = []
    for role in _l(packet.get("evidence_role_candidates")):
        if isinstance(role, Mapping):
            role_value = _t(role.get("evidence_role_candidate", role.get("role", "")))
        else:
            role_value = _t(role)
        if role_value:
            evidence_roles.append(role_value)
            if role_value not in _ALLOWED_EVIDENCE_ROLE_TARGETS_V1:
                block(f"invalid_evidence_role_candidate:{role_value}")
    if candidate_prep == "candidate_preparation_possible_after_evidence_normalization":
        if not bool(review_requirements.get("operator_review_required")):
            block("operator_review_required_for_candidate_prep")
        if not any(role in {"primary_evidence_candidate", "supporting_evidence_candidate", "counterevidence_candidate", "disconfirmation_source_candidate", "method_limit_source", "implementation_reference", "historical_context", "known_science_replay_reference", "source_selection_reference", "weak_signal_only"} for role in evidence_roles):
            block("candidate_prep_requires_evidence_role_candidate")
    if candidate_prep in {"candidate_preparation_possible_after_review", "candidate_preparation_possible_after_evidence_normalization"}:
        if not bool(review_requirements.get("operator_review_required")):
            block("candidate_prep_requires_operator_review")
    if candidate_prep == "candidate_preparation_blocked":
        block("candidate_prep_blocked")

    for item in _l(packet.get("artifact_route_candidates")):
        route = _t(item.get("route", item.get("artifact_route", item))) if isinstance(item, Mapping) else _t(item)
        if route and route not in _ALLOWED_ARTIFACT_ROUTES_V1:
            block(f"invalid_artifact_route_candidate:{route}")
        if route == "normalized_evidence_packet":
            if not bool(review_requirements.get("operator_review_required")):
                block("normalized_evidence_requires_operator_review")
            if not any(_t(packet.get(key)) for key in ("source_ref",)) or not _has_provenance_minimum(packet):
                block("normalized_evidence_requires_provenance")
            if not any(role in {"primary_evidence_candidate", "supporting_evidence_candidate", "counterevidence_candidate", "disconfirmation_source_candidate", "method_limit_source", "implementation_reference", "historical_context", "known_science_replay_reference", "source_selection_reference", "weak_signal_only"} for role in evidence_roles):
                block("normalized_evidence_requires_candidate_role")
            if not _l(packet.get("blocked_claims")):
                block("normalized_evidence_requires_blocked_claims")

    for item in _l(packet.get("oer_or_noop_hints")):
        hint = _t(item.get("hint", item.get("route", item))) if isinstance(item, Mapping) else _t(item)
        if hint and hint not in _ALLOWED_OER_HINTS_V1:
            block(f"invalid_oer_hint:{hint}")

    if not _l(packet.get("extracted_claims")):
        block("extracted_claims_empty")
    else:
        for claim in _l(packet.get("extracted_claims")):
            if not isinstance(claim, Mapping):
                block("claim_not_mapping")
                continue
            claim_text = _t(claim.get("claim_text_or_safe_paraphrase"))
            if not claim_text:
                block("claim_text_missing")
            if _contains_forbidden_text(claim_text):
                block("forbidden_claim_wording_present")
            if claim.get("accepted_evidence") is True or claim.get("accepted_candidate") is True or claim.get("true") is True:
                block("claim_marked_as_truth_or_acceptance")
            if _claim_is_same_mechanism(claim):
                if not bool(review_requirements.get("expert_review_required")):
                    block("same_mechanism_claim_blocked")
            evidence_role = _t(claim.get("evidence_role_candidate"))
            if evidence_role and evidence_role not in _ALLOWED_EVIDENCE_ROLE_TARGETS_V1:
                block(f"invalid_claim_evidence_role_candidate:{evidence_role}")
            if not _t(claim.get("source_location_ref")):
                block("claim_source_location_ref_missing")
            if not _t(claim.get("required_review")):
                block("claim_required_review_missing")
            if not _l(claim.get("blocked_claims")):
                block("claim_blocked_claims_missing")
            if not _t(claim.get("disconfirmation_need")):
                block("claim_disconfirmation_need_missing")
            if _t(claim.get("confidence_posture")) not in _ALLOWED_CONFIDENCE_POSTURES_V1:
                block("invalid_claim_confidence_posture")

    for assumption in _l(packet.get("extracted_assumptions")):
        if not isinstance(assumption, Mapping):
            block("assumption_not_mapping")
            continue
        if not _t(assumption.get("id")):
            block("assumption_id_missing")
        if not _t(assumption.get("statement")):
            block("assumption_statement_missing")
        if not _t(assumption.get("category")):
            block("assumption_category_missing")
        if not _t(assumption.get("why_it_matters")):
            block("assumption_why_it_matters_missing")
        if not _t(assumption.get("what_would_break_it")):
            block("assumption_what_would_break_it_missing")
        if not _t(assumption.get("review_required")):
            block("assumption_review_required_missing")
        if not _l(assumption.get("related_claim_ids")):
            block("assumption_related_claim_ids_missing")

    for method_limit in _l(packet.get("method_limits")):
        if not isinstance(method_limit, Mapping):
            block("method_limit_not_mapping")
            continue
        if not _t(method_limit.get("id")):
            block("method_limit_id_missing")
        if not _t(method_limit.get("statement")):
            block("method_limit_statement_missing")
        if not _t(method_limit.get("category")):
            block("method_limit_category_missing")
        if not _t(method_limit.get("why_it_matters")):
            block("method_limit_why_it_matters_missing")
        if not _t(method_limit.get("what_would_break_it")):
            block("method_limit_what_would_break_it_missing")
        if not _t(method_limit.get("review_required")):
            block("method_limit_review_required_missing")
        if not _l(method_limit.get("related_claim_ids")):
            block("method_limit_related_claim_ids_missing")

    if not any(_t(packet.get(key)) for key in ("safe_metadata_summary",)):
        block("safe_metadata_summary_missing")
    if not _t(packet.get("final_judgment")):
        block("final_judgment_missing")

    if retention_mode == "metadata_only_no_content_retention":
        for claim in _l(packet.get("extracted_claims")):
            if isinstance(claim, Mapping) and (not _t(claim.get("claim_text_or_safe_paraphrase")) or "quote" in _lower_text(claim.get("claim_text_or_safe_paraphrase"))):
                continue
        if _packet_contains_raw_content(packet):
            block("metadata_only_raw_content_not_allowed")
        for claim in _l(packet.get("extracted_claims")):
            if isinstance(claim, Mapping):
                text = _t(claim.get("claim_text_or_safe_paraphrase"))
                if text.startswith('"') or text.startswith("'"):
                    block("metadata_only_quote_not_allowed")
    if retention_mode == "bounded_excerpt_with_citation":
        if not bool(retention_policy.get("bounded_excerpt_allowed")):
            block("bounded_excerpt_policy_missing")
        if not bool(retention_policy.get("citation_required")) or not bool(retention_policy.get("source_location_ref_required")):
            block("bounded_excerpt_policy_incomplete")
        if int(retention_policy.get("max_excerpt_chars", 0) or 0) <= 0:
            block("bounded_excerpt_max_chars_missing")
        if int(retention_policy.get("max_excerpt_count", 0) or 0) <= 0:
            block("bounded_excerpt_max_count_missing")
        if not _safe_provenance_present(packet):
            block("bounded_excerpt_requires_provenance")
    if retention_mode == "full_text_transient_no_retention":
        if bool(retention_policy.get("raw_content_allowed")) or bool(retention_policy.get("raw_retention_allowed")):
            block("transient_full_text_raw_retention_not_allowed")
    if retention_mode == "full_text_retention_owner_authorized":
        if not bool(review_requirements.get("owner_authorization_required")):
            block("owner_authorization_required_missing_for_raw_retention")
        if not bool(review_requirements.get("owner_authorization_present")):
            block("owner_authorization_present_missing_for_raw_retention")
        if not bool(retention_policy.get("raw_content_allowed")) or not bool(retention_policy.get("raw_retention_allowed")):
            block("raw_retention_policy_missing")
        if not bool(retention_policy.get("owner_authorization_required_for_raw_retention")):
            block("raw_retention_owner_auth_policy_missing")

    for text in _flatten_texts(packet):
        if any(marker in text.lower() for marker in ("hidden prompt", "private memory", "credential", "credentials", "secret", "secrets", "token", "tokens")):
            block("sensitive_content_wording_present")
        if any(marker in text.lower() for marker in ("accepted evidence", "accepted candidate", "accepted discovery", "final answer", "proof", "discovery", "public science", "product ready", "runtime enabled", "provider call", "source fetch", "source ingestion", "ontology applied automatically", "self-modification")):
            block("forbidden_claim_wording_present")
        if "same mechanism" in text.lower() or "same-mechanism" in text.lower():
            block("same_mechanism_claim_blocked")
        if text.strip() == ".weslr":
            block("weslr_reference_blocked")

    if not _l(packet.get("artifact_route_candidates")):
        block("artifact_route_candidates_empty")

    return {"valid": not blocked_labels, "blocked": bool(blocked_labels), "blocked_labels": blocked_labels}


def summarize_source_interpretation_packet_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_source_interpretation_packet_v1(packet)
    conflict_status = "no_known_conflict"
    conflicts = _extract_conflict_statuses(packet)
    if conflicts:
        conflict_status = conflicts[0]
    return {
        "interpretation_packet_id": _t(packet.get("interpretation_packet_id")),
        "ingestion_request_id": _t(packet.get("ingestion_request_id")),
        "authorization_packet_ref": _t(packet.get("authorization_packet_ref")),
        "source_class": _t(packet.get("source_class")),
        "retention_mode": _t(packet.get("retention_mode")),
        "evidence_role_candidates": [
            _t(item.get("evidence_role_candidate", item.get("role", item))) if isinstance(item, Mapping) else _t(item)
            for item in _l(packet.get("evidence_role_candidates"))
        ],
        "conflict_status": conflict_status,
        "candidate_preparation_eligibility": _t(packet.get("candidate_preparation_eligibility")),
        "next_safe_step": _t(packet.get("next_safe_step")),
        "blocked": validation["blocked"],
        "final_judgment": _t(packet.get("final_judgment")),
    }


def _render_items(items: Iterable[Any], key: str | None = None) -> str:
    lines: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            if key and key in item:
                value = item.get(key)
            else:
                value = item.get("summary", item.get("statement", item.get("route", item.get("artifact_route", item))))
            lines.append(f"- {_t(value)}")
        else:
            lines.append(f"- {_t(item)}")
    return "\n".join(lines) if lines else "- none"


def render_source_interpretation_packet_markdown_v1(packet: Mapping[str, Any]) -> str:
    summary = summarize_source_interpretation_packet_v1(packet)
    blocked_claims = _render_items(_l(packet.get("blocked_claims")))
    abort_conditions = _render_items(_l(packet.get("abort_conditions")))
    denied = packet.get("denied_authority_flags") if isinstance(packet.get("denied_authority_flags"), Mapping) else {}
    denied_lines = "\n".join(f"- {key}: {bool(denied.get(key))}" for key in _DENIED_AUTHORITY_FLAGS_V1)
    claims = _render_items(_l(packet.get("extracted_claims")), key="claim_text_or_safe_paraphrase")
    assumptions = _render_items(_l(packet.get("extracted_assumptions")), key="statement")
    method_limits = _render_items(_l(packet.get("method_limits")), key="statement")
    disconfirmation = _render_items(_l(packet.get("counterevidence_or_disconfirmation")))
    conflicts = _render_items(_l(packet.get("source_conflicts")), key="summary")
    pattern_candidates = _render_items(_l(packet.get("pattern_attribution_candidates")), key="source_pattern_id")
    artifact_routes = _render_items(_l(packet.get("artifact_route_candidates")), key="route")
    review = packet.get("review_requirements") if isinstance(packet.get("review_requirements"), Mapping) else {}
    review_lines = "\n".join(
        [
            f"- owner authorization required: {bool(review.get('owner_authorization_required'))}",
            f"- owner authorization present: {bool(review.get('owner_authorization_present'))}",
            f"- operator review required: {bool(review.get('operator_review_required'))}",
            f"- expert review required: {bool(review.get('expert_review_required'))}",
        ]
    )
    return (
        f"# Source interpretation packet\n\n"
        f"- Interpretation packet ID: {summary['interpretation_packet_id']}\n"
        f"- Ingestion request ID: {summary['ingestion_request_id']}\n"
        f"- Authorization packet ref: {_t(packet.get('authorization_packet_ref'))}\n"
        f"- Source class: {summary['source_class']}\n"
        f"- Retention mode: {summary['retention_mode']}\n"
        f"- Candidate-prep eligibility: {summary['candidate_preparation_eligibility']}\n"
        f"- Conflict status: {summary['conflict_status']}\n"
        f"- Next safe step: {summary['next_safe_step']}\n"
        f"- Final judgment: {summary['final_judgment']}\n\n"
        f"## Authorization posture\n"
        f"{_t(packet.get('safe_metadata_summary'))}\n\n"
        f"## Source metadata\n"
        f"- title: {_t(packet.get('source_metadata', {}).get('title') if isinstance(packet.get('source_metadata'), Mapping) else '')}\n"
        f"- authors or organization: {_t(packet.get('source_metadata', {}).get('authors_or_organization') if isinstance(packet.get('source_metadata'), Mapping) else '')}\n"
        f"- publication or source date: {_t(packet.get('source_metadata', {}).get('publication_or_source_date') if isinstance(packet.get('source_metadata'), Mapping) else '')}\n"
        f"- source host or domain: {_t(packet.get('source_metadata', {}).get('source_host_or_domain') if isinstance(packet.get('source_metadata'), Mapping) else '')}\n"
        f"- citation or provenance ref: {_t(packet.get('source_metadata', {}).get('citation_or_provenance_ref') if isinstance(packet.get('source_metadata'), Mapping) else '')}\n"
        f"- locator record ref: {_t(packet.get('source_metadata', {}).get('locator_record_ref') if isinstance(packet.get('source_metadata'), Mapping) else '')}\n"
        f"- safe content hash: {_t(packet.get('source_metadata', {}).get('safe_content_hash') if isinstance(packet.get('source_metadata'), Mapping) else '')}\n\n"
        f"## Bounded content policy\n"
        f"- raw content allowed: {bool(packet.get('bounded_content_policy', {}).get('raw_content_allowed') if isinstance(packet.get('bounded_content_policy'), Mapping) else False)}\n"
        f"- safe paraphrase allowed: {bool(packet.get('bounded_content_policy', {}).get('safe_paraphrase_allowed') if isinstance(packet.get('bounded_content_policy'), Mapping) else False)}\n"
        f"- bounded excerpt allowed: {bool(packet.get('bounded_content_policy', {}).get('bounded_excerpt_allowed') if isinstance(packet.get('bounded_content_policy'), Mapping) else False)}\n"
        f"- max excerpt chars: {_t(packet.get('bounded_content_policy', {}).get('max_excerpt_chars') if isinstance(packet.get('bounded_content_policy'), Mapping) else '')}\n"
        f"- max excerpt count: {_t(packet.get('bounded_content_policy', {}).get('max_excerpt_count') if isinstance(packet.get('bounded_content_policy'), Mapping) else '')}\n"
        f"- citation required: {bool(packet.get('bounded_content_policy', {}).get('citation_required') if isinstance(packet.get('bounded_content_policy'), Mapping) else False)}\n"
        f"- source location ref required: {bool(packet.get('bounded_content_policy', {}).get('source_location_ref_required') if isinstance(packet.get('bounded_content_policy'), Mapping) else False)}\n"
        f"- raw retention allowed: {bool(packet.get('bounded_content_policy', {}).get('raw_retention_allowed') if isinstance(packet.get('bounded_content_policy'), Mapping) else False)}\n"
        f"- owner authorization required for raw retention: {bool(packet.get('bounded_content_policy', {}).get('owner_authorization_required_for_raw_retention') if isinstance(packet.get('bounded_content_policy'), Mapping) else False)}\n\n"
        f"## Extracted claim candidates\n{claims}\n\n"
        f"## Assumptions\n{assumptions}\n\n"
        f"## Method limits\n{method_limits}\n\n"
        f"## Evidence role candidates\n{_render_items(_l(packet.get('evidence_role_candidates')), key='evidence_role_candidate')}\n\n"
        f"## Disconfirmation / counterevidence\n{disconfirmation}\n\n"
        f"## Conflicts\n{conflicts}\n\n"
        f"## Pattern attribution candidates\n{pattern_candidates}\n\n"
        f"## Artifact route candidates\n{artifact_routes}\n\n"
        f"## Review requirements\n{review_lines}\n\n"
        f"## Blocked claims\n{blocked_claims}\n\n"
        f"## Abort conditions\n{abort_conditions}\n\n"
        f"## Denied authority summary\n{denied_lines}\n"
    )


def to_source_interpretation_packet_json_safe_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    return _json_safe(packet)


def build_initial_source_interpretation_examples_v1() -> tuple[dict[str, Any], ...]:
    public_research = build_source_interpretation_packet_v1(
        interpretation_packet_id="public_research_paper_interpretation_candidate",
        ingestion_request_id="public_research_paper_metadata_only",
        authorization_packet_ref="authorization_packet_v1:public_research_paper_metadata_only",
        source_ref="https://example.org/paper.pdf",
        source_class="public_research_paper",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        retention_mode="metadata_only_no_content_retention",
        source_metadata={
            "title": "Example research paper",
            "authors_or_organization": "Example Lab",
            "publication_or_source_date": "2026-01-01",
            "source_host_or_domain": "example.org",
            "source_class": "public_research_paper",
            "source_access_level": "public_open",
            "license_access_posture": "open_access_confirmed",
            "privacy_posture": "public_non_private",
            "citation_or_provenance_ref": "Example Lab 2026",
        },
        interpreted_under_authorization=True,
        bounded_content_policy={
            "raw_content_allowed": False,
            "safe_paraphrase_allowed": True,
            "bounded_excerpt_allowed": False,
            "max_excerpt_chars": 0,
            "max_excerpt_count": 0,
            "citation_required": True,
            "source_location_ref_required": True,
            "raw_retention_allowed": False,
            "owner_authorization_required_for_raw_retention": False,
        },
        extracted_claims=[
            {
                "claim_id": "c1",
                "claim_text_or_safe_paraphrase": "Paper reports a bounded result suitable for review-bound evidence candidate consideration.",
                "claim_type": "result",
                "source_location_ref": "section 2",
                "evidence_role_candidate": "primary_evidence_candidate",
                "confidence_posture": "interpretation_medium",
                "required_review": "operator_review",
                "blocked_claims": ["no evidence promotion", "no claim finalization"],
                "disconfirmation_need": "independent replication or stronger counterevidence.",
            }
        ],
        extracted_assumptions=[
            {
                "id": "a1",
                "statement": "The reported result is only a review-bound candidate until reviewed.",
                "category": "boundary",
                "why_it_matters": "prevents accepted-evidence overclaim",
                "what_would_break_it": "A separate accepted-evidence lane would be required.",
                "review_required": "operator_review",
                "related_claim_ids": ["c1"],
            }
        ],
        method_limits=[
            {
                "id": "m1",
                "statement": "Metadata-only interpretation does not prove the result.",
                "category": "retention",
                "why_it_matters": "limits truth claims",
                "what_would_break_it": "A later evidence-normalization lane.",
                "review_required": "operator_review",
                "related_claim_ids": ["c1"],
            }
        ],
        evidence_role_candidates=[{"evidence_role_candidate": "primary_evidence_candidate"}],
        counterevidence_or_disconfirmation=[
            {"hint": "A contradictory paper or failed replication would reduce confidence."}
        ],
        source_conflicts=[{"conflict_status": "no_known_conflict", "summary": "No known conflict."}],
        missing_evidence=[{"hint": "Need replication or stronger corroboration."}],
        pattern_attribution_candidates=[
            {
                "source_pattern_id": "research_bounded_result_pattern",
                "target_domain_or_experiment": "experimental review",
                "shared_structure": "bounded result with cited provenance",
                "key_differences": "No claim of acceptance.",
                "possible_mechanism_overlap_posture": "possible overlap only",
                "disconfirmation_tests": ["replication failure", "better counterexample"],
                "analogy_strength": "interpretation_medium",
                "blocked_claims": ["mechanistic overclaim"],
                "next_safe_step": "operator review",
            }
        ],
        artifact_route_candidates=[{"route": "normalized_evidence_packet", "summary": "Possible later route after review."}],
        mlcf_normalization_hints=[{"hint": "source class", "value": "public_research_paper"}],
        oer_or_noop_hints=[{"hint": "route_to_operator_review"}],
        candidate_preparation_eligibility="candidate_preparation_possible_after_evidence_normalization",
        review_requirements={
            "owner_authorization_required": False,
            "owner_authorization_present": False,
            "operator_review_required": True,
            "expert_review_required": False,
            "required_review_labels": ["operator_review"],
        },
        blocked_claims=["no evidence promotion", "no claim finalization"],
        denied_authority_flags={flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=["evidence promotion blocked", "claim finalization blocked"],
        blocked_labels=["review_bound"],
        safe_metadata_summary="public research paper interpreted as review-bound evidence candidate metadata only",
        next_safe_step="operator_review",
        final_judgment="interpretation_packet_pending_review",
    )

    official_standard = build_source_interpretation_packet_v1(
        interpretation_packet_id="official_standard_context_interpretation",
        ingestion_request_id="official_standard_metadata_only",
        authorization_packet_ref="authorization_packet_v1:official_standard_metadata_only",
        source_ref="https://example.org/standard",
        source_class="official_standard",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        retention_mode="bounded_excerpt_with_citation",
        source_metadata={
            "title": "Example standard",
            "authors_or_organization": "Standards Org",
            "publication_or_source_date": "2025-12-01",
            "source_host_or_domain": "example.org",
            "citation_or_provenance_ref": "Standards Org 2025",
            "locator_record_ref": "std-locator-1",
        },
        bounded_content_policy={
            "raw_content_allowed": False,
            "safe_paraphrase_allowed": True,
            "bounded_excerpt_allowed": True,
            "max_excerpt_chars": 280,
            "max_excerpt_count": 2,
            "citation_required": True,
            "source_location_ref_required": True,
            "raw_retention_allowed": False,
            "owner_authorization_required_for_raw_retention": False,
        },
        extracted_claims=[
            {
                "claim_id": "s1",
                "claim_text_or_safe_paraphrase": "The standard defines a bounded context note relevant to interpretation.",
                "claim_type": "context",
                "source_location_ref": "clause 3.2",
                "evidence_role_candidate": "historical_context",
                "confidence_posture": "interpretation_high",
                "required_review": "operator_review",
                "blocked_claims": ["no claim finalization"],
                "disconfirmation_need": "A superseding standard or erratum.",
            }
        ],
        method_limits=[
            {
                "id": "m2",
                "statement": "Bounded excerpts are citation-bound and do not imply acceptance.",
                "category": "retention",
                "why_it_matters": "preserves quote/paraphrase boundary",
                "what_would_break_it": "raw excerpt without citation",
                "review_required": "operator_review",
                "related_claim_ids": ["s1"],
            }
        ],
        evidence_role_candidates=[{"evidence_role_candidate": "historical_context"}],
        counterevidence_or_disconfirmation=[{"hint": "An updated erratum would supersede the clause."}],
        source_conflicts=[{"conflict_status": "no_known_conflict", "summary": "No known conflict."}],
        missing_evidence=[{"hint": "Need broader implementation context before any conclusion."}],
        pattern_attribution_candidates=[
            {
                "source_pattern_id": "standard_context_pattern",
                "target_domain_or_experiment": "policy/standard interpretation",
                "shared_structure": "explicit clause and citation",
                "key_differences": "No acceptance implied.",
                "possible_mechanism_overlap_posture": "not claimed",
                "disconfirmation_tests": ["erratum", "new standard"],
                "analogy_strength": "interpretation_low",
                "blocked_claims": ["mechanistic overclaim"],
                "next_safe_step": "operator review",
            }
        ],
        artifact_route_candidates=[{"route": "artifact_forward_work_plan", "summary": "Context may feed later work plan."}],
        mlcf_normalization_hints=[{"hint": "provenance posture", "value": "citation required"}],
        oer_or_noop_hints=[{"hint": "route_to_oer_noop"}],
        candidate_preparation_eligibility="candidate_preparation_possible_after_review",
        review_requirements={
            "owner_authorization_required": False,
            "owner_authorization_present": False,
            "operator_review_required": True,
            "expert_review_required": False,
            "required_review_labels": ["operator_review"],
        },
        blocked_claims=["no claim finalization"],
        denied_authority_flags={flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=["claim finalization blocked"],
        blocked_labels=["review_bound"],
        safe_metadata_summary="official standard interpreted as context source with bounded citation policy",
        next_safe_step="operator_review",
        final_judgment="interpretation_packet_pending_review",
    )

    github_reference = build_source_interpretation_packet_v1(
        interpretation_packet_id="github_repo_implementation_reference_interpretation",
        ingestion_request_id="github_repo_implementation_reference",
        authorization_packet_ref="authorization_packet_v1:github_repo_implementation_reference",
        source_ref="https://github.com/example/repo",
        source_class="github_repository",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        retention_mode="derived_summary_only",
        source_metadata={
            "title": "Example repository",
            "authors_or_organization": "Example Org",
            "source_host_or_domain": "github.com",
            "citation_or_provenance_ref": "GitHub repo reference",
            "locator_record_ref": "gh-locator-1",
        },
        bounded_content_policy={
            "raw_content_allowed": False,
            "safe_paraphrase_allowed": True,
            "bounded_excerpt_allowed": False,
            "max_excerpt_chars": 0,
            "max_excerpt_count": 0,
            "citation_required": True,
            "source_location_ref_required": True,
            "raw_retention_allowed": False,
            "owner_authorization_required_for_raw_retention": False,
        },
        extracted_claims=[
            {
                "claim_id": "g1",
                "claim_text_or_safe_paraphrase": "Repository serves as implementation reference only.",
                "claim_type": "implementation_reference",
                "source_location_ref": "README",
                "evidence_role_candidate": "implementation_reference",
                "confidence_posture": "interpretation_high",
                "required_review": "operator_review",
                "blocked_claims": ["no candidate promotion"],
                "disconfirmation_need": "Source code divergence or an authoritative maintenance note.",
            }
        ],
        evidence_role_candidates=[{"evidence_role_candidate": "implementation_reference"}],
        counterevidence_or_disconfirmation=[{"hint": "If the repo is archival only, it becomes less useful."}],
        source_conflicts=[{"conflict_status": "no_known_conflict", "summary": "No known conflict."}],
        missing_evidence=[{"hint": "Need operational confirmation or issue tracking context."}],
        pattern_attribution_candidates=[
            {
                "source_pattern_id": "repo_reference_pattern",
                "target_domain_or_experiment": "implementation reference",
                "shared_structure": "code or repo context",
                "key_differences": "Not primary evidence.",
                "possible_mechanism_overlap_posture": "not claimed",
                "disconfirmation_tests": ["repo archival status"],
                "analogy_strength": "interpretation_medium",
                "blocked_claims": ["mechanistic overclaim"],
                "next_safe_step": "operator review",
            }
        ],
        artifact_route_candidates=[{"route": "source_selection_evidence_plan", "summary": "May inform later evidence planning."}],
        mlcf_normalization_hints=[{"hint": "evidence role candidate", "value": "implementation_reference"}],
        oer_or_noop_hints=[{"hint": "route_to_operator_review"}],
        candidate_preparation_eligibility="candidate_preparation_premature",
        review_requirements={
            "owner_authorization_required": False,
            "owner_authorization_present": False,
            "operator_review_required": True,
            "expert_review_required": False,
            "required_review_labels": ["operator_review"],
        },
        blocked_claims=["no candidate promotion"],
        denied_authority_flags={flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=["candidate promotion blocked"],
        blocked_labels=["review_bound"],
        safe_metadata_summary="github repository interpreted only as implementation reference metadata",
        next_safe_step="operator_review",
        final_judgment="interpretation_packet_pending_review",
    )

    false_assumption = build_source_interpretation_packet_v1(
        interpretation_packet_id="false_assumption_disconfirmation_mapping",
        ingestion_request_id="false_assumption_disconfirmation_mapping",
        authorization_packet_ref="authorization_packet_v1:false_assumption_disconfirmation_mapping",
        source_ref="https://example.org/article",
        source_class="public_news_or_report",
        source_access_level="public_open",
        license_access_posture="public_metadata_only",
        privacy_posture="public_non_private",
        retention_mode="metadata_only_no_content_retention",
        source_metadata={
            "title": "Example report",
            "source_host_or_domain": "example.org",
            "citation_or_provenance_ref": "Example report 2026",
        },
        extracted_claims=[
            {
                "claim_id": "f1",
                "claim_text_or_safe_paraphrase": "This report is used for disconfirmation mapping, not acceptance.",
                "claim_type": "disconfirmation",
                "source_location_ref": "paragraph 4",
                "evidence_role_candidate": "counterevidence_candidate",
                "confidence_posture": "interpretation_medium",
                "required_review": "operator_review",
                "blocked_claims": ["no overclaim escalation", "no certainty escalation"],
                "disconfirmation_need": "A directly conflicting source or stronger empirical evidence.",
            }
        ],
        extracted_assumptions=[
            {
                "id": "f-a1",
                "statement": "The report can disconfirm a false assumption without becoming a later promoted item.",
                "category": "disconfirmation",
                "why_it_matters": "prevents overclaim",
                "what_would_break_it": "A later authoritative source overturns the mapping.",
                "review_required": "operator_review",
                "related_claim_ids": ["f1"],
            }
        ],
        method_limits=[
            {
                "id": "f-m1",
                "statement": "Disconfirmation mapping does not confirm acceptance or certainty.",
                "category": "boundary",
                "why_it_matters": "blocks overclaim",
                "what_would_break_it": "No later lane in this helper.",
                "review_required": "operator_review",
                "related_claim_ids": ["f1"],
            }
        ],
        evidence_role_candidates=[{"evidence_role_candidate": "counterevidence_candidate"}],
        counterevidence_or_disconfirmation=[{"hint": "A conflict with known science would matter more."}],
        source_conflicts=[{"conflict_status": "conflict_requiring_more_evidence", "summary": "More evidence needed."}],
        missing_evidence=[{"hint": "Need corroborating or contradicting sources."}],
        pattern_attribution_candidates=[
            {
                "source_pattern_id": "disconfirmation_mapping_pattern",
                "target_domain_or_experiment": "false assumption mapping",
                "shared_structure": "contrast against prior assumption",
                "key_differences": "No promotion claim.",
                "possible_mechanism_overlap_posture": "overlap not claimed",
                "disconfirmation_tests": ["contradictory evidence"],
                "analogy_strength": "interpretation_low",
                "blocked_claims": ["overclaim escalation", "certainty escalation"],
                "next_safe_step": "operator review",
            }
        ],
        artifact_route_candidates=[{"route": "false_assumption_or_overclaim_artifact", "summary": "May feed overclaim review."}],
        mlcf_normalization_hints=[{"hint": "conflict/disconfirmation markers", "value": "present"}],
        oer_or_noop_hints=[{"hint": "route_to_operator_review"}],
        candidate_preparation_eligibility="candidate_preparation_possible_after_review",
        review_requirements={
            "owner_authorization_required": False,
            "owner_authorization_present": False,
            "operator_review_required": True,
            "expert_review_required": False,
            "required_review_labels": ["operator_review"],
        },
        blocked_claims=["no overclaim escalation", "no certainty escalation"],
        denied_authority_flags={flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=["overclaim blocked", "certainty blocked"],
        blocked_labels=["review_bound"],
        safe_metadata_summary="report used for disconfirmation mapping only",
        next_safe_step="operator_review",
        final_judgment="interpretation_packet_pending_review",
    )

    known_science = build_source_interpretation_packet_v1(
        interpretation_packet_id="pulsar_known_science_replay_reference",
        ingestion_request_id="pulsar_known_science_replay_reference",
        authorization_packet_ref="authorization_packet_v1:pulsar_known_science_replay_reference",
        source_ref="https://example.org/pulsar",
        source_class="public_research_paper",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        retention_mode="derived_summary_only",
        source_metadata={
            "title": "Pulsar reference",
            "source_host_or_domain": "example.org",
            "citation_or_provenance_ref": "Pulsar reference 2024",
        },
        extracted_claims=[
            {
                "claim_id": "k1",
                "claim_text_or_safe_paraphrase": "This source supports a known-science replay reference.",
                "claim_type": "context",
                "source_location_ref": "section 1",
                "evidence_role_candidate": "known_science_replay_reference",
                "confidence_posture": "interpretation_high",
                "required_review": "operator_review",
                "blocked_claims": ["mechanistic overclaim"],
                "disconfirmation_need": "A better-known reference or a direct contradiction.",
            }
        ],
        evidence_role_candidates=[{"evidence_role_candidate": "known_science_replay_reference"}],
        counterevidence_or_disconfirmation=[{"hint": "A closer match with different mechanistic details would reduce analogy strength."}],
        source_conflicts=[{"conflict_status": "conflict_with_known_science_replay", "summary": "Potential analogy conflict."}],
        missing_evidence=[{"hint": "Need separate evidence before mechanistic claims."}],
        pattern_attribution_candidates=[
            {
                "source_pattern_id": "known_science_replay_pattern",
                "target_domain_or_experiment": "known science replay",
                "shared_structure": "similar bounded structure",
                "key_differences": "Mechanism not asserted identical.",
                "possible_mechanism_overlap_posture": "possible overlap only",
                "disconfirmation_tests": ["different mechanism evidence"],
                "analogy_strength": "interpretation_medium",
                "blocked_claims": ["mechanistic overclaim"],
                "next_safe_step": "operator review",
            }
        ],
        artifact_route_candidates=[{"route": "experiment_plan_artifact", "summary": "May support later experiment planning."}],
        mlcf_normalization_hints=[{"hint": "pattern-attribution", "value": "known-science replay"}],
        oer_or_noop_hints=[{"hint": "route_to_operator_review"}],
        candidate_preparation_eligibility="candidate_preparation_possible_after_review",
        review_requirements={
            "owner_authorization_required": False,
            "owner_authorization_present": False,
            "operator_review_required": True,
            "expert_review_required": True,
            "required_review_labels": ["operator_review", "expert_review"],
        },
        blocked_claims=["mechanistic overclaim"],
        denied_authority_flags={flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=["mechanistic overclaim blocked"],
        blocked_labels=["review_bound"],
        safe_metadata_summary="known-science replay reference remains review-bound and non-assertive",
        next_safe_step="expert_review",
        final_judgment="interpretation_packet_pending_review",
    )

    owner_uploaded = build_source_interpretation_packet_v1(
        interpretation_packet_id="owner_uploaded_pdf_no_raw_retention",
        ingestion_request_id="owner_uploaded_pdf_no_raw_retention",
        authorization_packet_ref="authorization_packet_v1:owner_uploaded_pdf_no_raw_retention",
        source_ref="file:///authorized/upload.pdf",
        source_class="owner_uploaded_file",
        source_access_level="owner_uploaded",
        license_access_posture="owner_authorized_private",
        privacy_posture="owner_authorized_private",
        retention_mode="full_text_transient_no_retention",
        source_metadata={
            "title": "Owner uploaded file",
            "source_host_or_domain": "local",
            "citation_or_provenance_ref": "owner provided upload",
            "locator_record_ref": "upload-1",
        },
        bounded_content_policy={
            "raw_content_allowed": False,
            "safe_paraphrase_allowed": True,
            "bounded_excerpt_allowed": False,
            "max_excerpt_chars": 0,
            "max_excerpt_count": 0,
            "citation_required": True,
            "source_location_ref_required": True,
            "raw_retention_allowed": False,
            "owner_authorization_required_for_raw_retention": False,
        },
        review_requirements={
            "owner_authorization_required": True,
            "owner_authorization_present": True,
            "operator_review_required": True,
            "expert_review_required": False,
            "required_review_labels": ["owner_authorization", "operator_review"],
        },
        extracted_claims=[
            {
                "claim_id": "o1",
                "claim_text_or_safe_paraphrase": "Safe paraphrase only; no raw retention.",
                "claim_type": "context",
                "source_location_ref": "page 1",
                "evidence_role_candidate": "primary_evidence_candidate",
                "confidence_posture": "interpretation_medium",
                "required_review": "operator_review",
                "blocked_claims": ["no raw retention"],
                "disconfirmation_need": "A later evidence lane if needed.",
            }
        ],
        evidence_role_candidates=[{"evidence_role_candidate": "primary_evidence_candidate"}],
        counterevidence_or_disconfirmation=[{"hint": "Owner can revoke authorization."}],
        source_conflicts=[{"conflict_status": "no_known_conflict", "summary": "No known conflict."}],
        missing_evidence=[{"hint": "Need only metadata/paraphrase review now."}],
        pattern_attribution_candidates=[
            {
                "source_pattern_id": "owner_upload_no_raw_retention_pattern",
                "target_domain_or_experiment": "owner-upload interpretation",
                "shared_structure": "authorized local upload",
                "key_differences": "No raw retention.",
                "possible_mechanism_overlap_posture": "not claimed",
                "disconfirmation_tests": ["authorization revocation"],
                "analogy_strength": "interpretation_high",
                "blocked_claims": ["mechanistic overclaim"],
                "next_safe_step": "operator review",
            }
        ],
        artifact_route_candidates=[{"route": "artifact_forward_work_plan", "summary": "May feed later work planning."}],
        mlcf_normalization_hints=[{"hint": "retention posture", "value": "transient no retention"}],
        oer_or_noop_hints=[{"hint": "no_ontology_action"}],
        candidate_preparation_eligibility="candidate_preparation_premature",
        blocked_claims=["no raw retention"],
        denied_authority_flags={flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=["no raw retention"],
        blocked_labels=["review_bound"],
        safe_metadata_summary="owner-uploaded source interpreted with transient no-retention posture only",
        next_safe_step="owner_review",
        final_judgment="interpretation_packet_pending_review",
    )

    unsafe_accepted_discovery = build_source_interpretation_packet_v1(
        interpretation_packet_id="unsafe_accepted_discovery_blocked",
        ingestion_request_id="unsafe_accepted_discovery_blocked",
        authorization_packet_ref="authorization_packet_v1:unsafe_accepted_discovery_blocked",
        source_ref="https://example.org/unsafe",
        source_class="public_news_or_report",
        source_access_level="public_open",
        license_access_posture="public_metadata_only",
        privacy_posture="public_non_private",
        retention_mode="metadata_only_no_content_retention",
        source_metadata={
            "title": "Unsafe report",
            "source_host_or_domain": "example.org",
            "citation_or_provenance_ref": "Unsafe report 2026",
        },
        extracted_claims=[
            {
                "claim_id": "u1",
                "claim_text_or_safe_paraphrase": "accepted discovery confirmed",
                "claim_type": "claim",
                "source_location_ref": "paragraph 1",
                "evidence_role_candidate": "primary_evidence_candidate",
                "confidence_posture": "interpretation_high",
                "required_review": "operator_review",
                "blocked_claims": ["overclaim escalation"],
                "disconfirmation_need": "N/A",
            }
        ],
        evidence_role_candidates=[{"evidence_role_candidate": "primary_evidence_candidate"}],
        blocked_claims=["overclaim escalation"],
        denied_authority_flags={flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=["overclaim blocked"],
        blocked_labels=["unsafe"],
        safe_metadata_summary="unsafe packet intentionally includes accepted-discovery wording",
        next_safe_step="blocked_state",
        final_judgment="interpretation_packet_pending_review",
    )

    unsafe_weslr = build_source_interpretation_packet_v1(
        interpretation_packet_id="unsafe_weslr_content_blocked",
        ingestion_request_id="unsafe_weslr_content_blocked",
        authorization_packet_ref="authorization_packet_v1:unsafe_weslr_content_blocked",
        source_ref=".weslr/private/source",
        source_class="blocked_source_class",
        source_access_level="blocked_access",
        license_access_posture="blocked_license_or_access",
        privacy_posture="blocked_private_or_secret",
        retention_mode="blocked_retention",
        source_metadata={
            "title": "Unsafe WESLR content",
            "source_host_or_domain": "local",
            "citation_or_provenance_ref": "unsafe",
        },
        blocked_claims=["no .weslr"],
        denied_authority_flags={flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=[".weslr"],
        blocked_labels=["unsafe"],
        safe_metadata_summary="unsafe packet intentionally includes .weslr content",
        next_safe_step="blocked_state",
        final_judgment="blocked_state",
    )

    weak_source = build_source_interpretation_packet_v1(
        interpretation_packet_id="weak_source_not_evidence",
        ingestion_request_id="weak_source_not_evidence",
        authorization_packet_ref="authorization_packet_v1:weak_source_not_evidence",
        source_ref="https://example.org/weak",
        source_class="forum_or_social_discussion",
        source_access_level="public_open",
        license_access_posture="public_metadata_only",
        privacy_posture="public_non_private",
        retention_mode="metadata_only_no_content_retention",
        source_metadata={
            "title": "Weak discussion",
            "source_host_or_domain": "example.org",
            "citation_or_provenance_ref": "Weak discussion 2026",
        },
        extracted_claims=[
            {
                "claim_id": "w1",
                "claim_text_or_safe_paraphrase": "Weak signal only; not evidence.",
                "claim_type": "signal",
                "source_location_ref": "thread reply",
                "evidence_role_candidate": "weak_signal_only",
                "confidence_posture": "interpretation_low",
                "required_review": "operator_review",
                "blocked_claims": ["not evidence"],
                "disconfirmation_need": "A stronger source or direct evidence.",
            }
        ],
        evidence_role_candidates=[{"evidence_role_candidate": "weak_signal_only"}, {"evidence_role_candidate": "not_evidence"}],
        counterevidence_or_disconfirmation=[{"hint": "Need direct evidence before promotion."}],
        source_conflicts=[{"conflict_status": "no_known_conflict", "summary": "No known conflict."}],
        missing_evidence=[{"hint": "Need direct evidence."}],
        pattern_attribution_candidates=[
            {
                "source_pattern_id": "weak_signal_pattern",
                "target_domain_or_experiment": "weak signal handling",
                "shared_structure": "discussion only",
                "key_differences": "Not evidence.",
                "possible_mechanism_overlap_posture": "not claimed",
                "disconfirmation_tests": ["stronger source"],
                "analogy_strength": "interpretation_low",
                "blocked_claims": ["mechanistic overclaim"],
                "next_safe_step": "operator review",
            }
        ],
        artifact_route_candidates=[{"route": "blocked_state", "summary": "Weak source remains blocked from promotion."}],
        mlcf_normalization_hints=[{"hint": "source role", "value": "weak signal only"}],
        oer_or_noop_hints=[{"hint": "route_to_oer_noop"}],
        candidate_preparation_eligibility="candidate_preparation_excluded",
        review_requirements={
            "owner_authorization_required": False,
            "owner_authorization_present": False,
            "operator_review_required": True,
            "expert_review_required": False,
            "required_review_labels": ["operator_review"],
        },
        blocked_claims=["not evidence"],
        denied_authority_flags={flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        abort_conditions=["not evidence"],
        blocked_labels=["review_bound"],
        safe_metadata_summary="weak source routed to weak-signal-only / not-evidence posture",
        next_safe_step="operator_review",
        final_judgment="interpretation_packet_pending_review",
    )

    return (
        public_research,
        official_standard,
        github_reference,
        false_assumption,
        known_science,
        owner_uploaded,
        unsafe_accepted_discovery,
        unsafe_weslr,
        weak_source,
    )


__all__ = [
    "build_source_interpretation_packet_v1",
    "validate_source_interpretation_packet_v1",
    "summarize_source_interpretation_packet_v1",
    "render_source_interpretation_packet_markdown_v1",
    "to_source_interpretation_packet_json_safe_v1",
    "build_initial_source_interpretation_examples_v1",
]
