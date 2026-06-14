"""WESLR source ingestion authorization boundary V1.

Helper-only, metadata-only, deterministic, in-memory authorization helpers for
source ingestion requests. These helpers do not fetch sources, read PDFs,
ingest datasets, browse the web, call providers/models, write .weslr data, or
create accepted evidence, accepted candidates, final answers, public claims,
proof/discovery claims, or runtime authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

SCHEMA_NAME_V1 = "source_ingestion_authorization_boundary"
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
_ALLOWED_PURPOSES_V1 = (
    "evidence_candidate_extraction",
    "source_metadata_extraction",
    "claim_boundary_mapping",
    "disconfirmation_mapping",
    "method_limit_extraction",
    "implementation_reference_mapping",
    "known_science_replay",
    "pattern_attribution_support",
    "artifact_context_support",
    "source_selection_validation",
    "contradiction_or_counterevidence_check",
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
_ALLOWED_RETENTION_MODES_V1 = (
    "metadata_only_no_content_retention",
    "derived_summary_only",
    "bounded_excerpt_with_citation",
    "full_text_transient_no_retention",
    "full_text_retention_owner_authorized",
    "blocked_retention",
)
_DENIED_AUTHORITY_FLAGS_V1 = (
    "unauthorized_source_ingestion_authority",
    "autonomous_crawling_authority",
    "accepted_evidence_authority",
    "accepted_candidate_authority",
    "final_answer_authority",
    "public_claim_authority",
    "proof_claim_authority",
    "discovery_truth_claim_authority",
    "product_readiness_claim_authority",
    "runtime_wiring_authority",
    "provider_model_call_authority",
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
    "secret",
    "token",
    "final answer",
    "accepted evidence",
    "accepted candidate",
    "confirmed discovery",
    "proof",
    "public science claim",
    "product ready",
    "autonomous crawl",
    "provider call authorized",
    "runtime enabled",
    "ontology applied automatically",
    "self-modification",
)
_REQUIRED_FIELDS_V1 = (
    "schema_name",
    "schema_version",
    "ingestion_request_id",
    "requested_by",
    "source_ref",
    "source_class",
    "source_access_level",
    "license_access_posture",
    "privacy_posture",
    "ingestion_purpose",
    "artifact_target",
    "evidence_role_target",
    "retention_mode",
    "raw_retention_allowed",
    "derived_metadata_allowed",
    "quoted_excerpt_allowed",
    "max_excerpt_policy",
    "owner_authorization_required",
    "owner_authorization_present",
    "operator_review_required",
    "expert_review_required",
    "blocked_claims",
    "denied_authority_flags",
    "abort_conditions",
    "blocked_labels",
    "next_safe_step",
    "safe_metadata_summary",
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


def _forbidden(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _FORBIDDEN_WORDING_V1)


def _source_ref_markers(source_ref: str) -> bool:
    lowered = source_ref.lower()
    return ".weslr" in lowered


def build_source_ingestion_authorization_packet_v1(**packet: Any) -> dict[str, Any]:
    source_class = _t(packet.get("source_class", "unknown_source_class"))
    source_access_level = _t(packet.get("source_access_level", "unknown_access"))
    license_access_posture = _t(packet.get("license_access_posture", "license_unknown"))
    privacy_posture = _t(packet.get("privacy_posture", "unknown_privacy"))
    retention_mode = _t(packet.get("retention_mode", "metadata_only_no_content_retention"))
    owner_auth_present = bool(packet.get("owner_authorization_present", False))
    owner_auth_required = bool(packet.get("owner_authorization_required", False))
    raw_retention_allowed = bool(packet.get("raw_retention_allowed", False))
    if retention_mode == "full_text_retention_owner_authorized":
        raw_retention_allowed = True
        owner_auth_required = True
    blocked = source_class == "blocked_source_class" or retention_mode == "blocked_retention"
    packet_out = {
        "schema_name": SCHEMA_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "ingestion_request_id": _t(packet.get("ingestion_request_id", "ingestion_request_v1")),
        "requested_by": _t(packet.get("requested_by", "unknown_requester")),
        "source_ref": _t(packet.get("source_ref", "")),
        "source_class": source_class,
        "source_access_level": source_access_level,
        "license_access_posture": license_access_posture,
        "privacy_posture": privacy_posture,
        "ingestion_purpose": _t(packet.get("ingestion_purpose", "source_metadata_extraction")),
        "artifact_target": _t(packet.get("artifact_target", "governed_interpretation_packet")),
        "evidence_role_target": _t(packet.get("evidence_role_target", "not_evidence")),
        "retention_mode": retention_mode,
        "raw_retention_allowed": raw_retention_allowed,
        "derived_metadata_allowed": bool(packet.get("derived_metadata_allowed", True)),
        "quoted_excerpt_allowed": bool(packet.get("quoted_excerpt_allowed", False)),
        "max_excerpt_policy": _t(packet.get("max_excerpt_policy", "bounded_and_cited")),
        "owner_authorization_required": owner_auth_required,
        "owner_authorization_present": owner_auth_present,
        "operator_review_required": bool(packet.get("operator_review_required", True)),
        "expert_review_required": bool(packet.get("expert_review_required", False)),
        "blocked_claims": _l(packet.get("blocked_claims", [
            "no_final_answer",
            "no_accepted_evidence",
            "no_proof_claim",
        ])),
        "denied_authority_flags": {flag: False for flag in _DENIED_AUTHORITY_FLAGS_V1},
        "abort_conditions": _l(packet.get("abort_conditions", [
            "unknown_source_without_approval",
            "raw_retention_without_authorization",
            "no_review_gate_break",
        ])),
        "blocked_labels": _l(packet.get("blocked_labels", ["metadata_only_authorization_packet"])),
        "next_safe_step": _t(packet.get("next_safe_step", "operator_review")),
        "safe_metadata_summary": _t(packet.get("safe_metadata_summary", "authorization packet only; no source access performed")),
        "final_judgment": _t(packet.get("final_judgment", "authorization_packet_pending_review")),
    }
    if packet.get("denied_authority_flags"):
        for key, value in dict(packet["denied_authority_flags"]).items():
            if key in packet_out["denied_authority_flags"]:
                packet_out["denied_authority_flags"][key] = bool(value)
    if blocked:
        packet_out["blocked_labels"].append("blocked_source_or_retention")
    if owner_auth_present:
        packet_out["owner_authorization_required"] = True
    return packet_out


def validate_source_ingestion_authorization_packet_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    blocked_labels: list[str] = []
    def block(label: str) -> None:
        if label not in blocked_labels:
            blocked_labels.append(label)
    if not isinstance(packet, Mapping):
        return {"valid": False, "blocked": True, "blocked_labels": ["invalid_packet_type"]}
    missing = [f for f in _REQUIRED_FIELDS_V1 if f not in packet]
    for f in missing:
        block(f"missing_field:{f}")
    if _t(packet.get("schema_name")) != SCHEMA_NAME_V1:
        block("invalid_schema_name")
    if _t(packet.get("schema_version")) != SCHEMA_VERSION_V1:
        block("invalid_schema_version")
    source_ref = _t(packet.get("source_ref"))
    if not source_ref:
        block("missing_source_ref")
    if _source_ref_markers(source_ref):
        block("weslr_reference_blocked")
    for key in ("source_class", "source_access_level", "license_access_posture", "privacy_posture", "ingestion_purpose", "evidence_role_target", "retention_mode", "next_safe_step", "safe_metadata_summary", "final_judgment"):
        val = _t(packet.get(key))
        if _forbidden(val):
            block(f"forbidden_wording_present:{key}")
    blocked_claims = _l(packet.get("blocked_claims"))
    if not blocked_claims:
        block("blocked_claims_empty")
    abort_conditions = _l(packet.get("abort_conditions"))
    if not abort_conditions:
        block("abort_conditions_empty")
    if not _t(packet.get("next_safe_step")):
        block("missing_next_safe_step")
    review_req = [packet.get("owner_authorization_required"), packet.get("operator_review_required"), packet.get("expert_review_required")]
    if not any(v is True for v in review_req):
        block("review_requirements_missing")
    denied = packet.get("denied_authority_flags") or {}
    if not isinstance(denied, Mapping):
        block("denied_authority_flags_invalid")
    else:
        for flag in _DENIED_AUTHORITY_FLAGS_V1:
            if denied.get(flag) is True:
                block(f"denied_authority_true:{flag}")
    source_class = _t(packet.get("source_class"))
    source_access = _t(packet.get("source_access_level"))
    license_posture = _t(packet.get("license_access_posture"))
    privacy = _t(packet.get("privacy_posture"))
    owner_auth_present = packet.get("owner_authorization_present") is True
    owner_auth_required = packet.get("owner_authorization_required") is True
    if source_class in {"unknown_source_class", "blocked_source_class"} and not owner_auth_present:
        block("source_class_requires_owner_authorization")
    if source_access in {"blocked_access", "restricted_or_paid", "unknown_access"} and not owner_auth_present:
        block("source_access_requires_owner_authorization")
    if license_posture in {"license_unknown", "restricted_or_paid", "blocked_license_or_access"} and not owner_auth_present:
        block("license_posture_requires_owner_authorization")
    if privacy in {"private_requires_authorization", "contains_sensitive_data", "blocked_private_or_secret", "unknown_privacy"} and not owner_auth_present:
        block("privacy_posture_requires_owner_authorization")
    if packet.get("retention_mode") == "blocked_retention":
        block("blocked_retention_not_allowed")
    if packet.get("raw_retention_allowed") is True and packet.get("retention_mode") != "full_text_retention_owner_authorized":
        block("raw_retention_without_owner_authorization")
    if packet.get("retention_mode") == "full_text_retention_owner_authorized" and not owner_auth_present:
        block("raw_retention_without_owner_authorization")
    if packet.get("retention_mode") == "full_text_retention_owner_authorized" and not owner_auth_required:
        block("owner_authorization_required_missing_for_raw_retention")
    if _t(packet.get("ingestion_purpose")) not in _ALLOWED_PURPOSES_V1:
        block("invalid_ingestion_purpose")
    if _t(packet.get("evidence_role_target")) not in _ALLOWED_EVIDENCE_ROLE_TARGETS_V1:
        block("invalid_evidence_role_target")
    if source_class == "blocked_source_class":
        block("blocked_source_class_rejected")
    text_blobs = [
        source_ref,
        _t(packet.get("requested_by")),
        _t(packet.get("safe_metadata_summary")),
        _t(packet.get("final_judgment")),
        " ".join(map(_t, blocked_claims)),
        " ".join(map(_t, abort_conditions)),
    ]
    for text in text_blobs:
        lower = text.lower()
        if any(marker in lower for marker in ("hidden prompt", "private memory", "credential", "secret", "token")):
            block("sensitive_content_wording_present")
        if any(marker in lower for marker in ("final answer", "accepted evidence authority", "accepted candidate authority", "confirmed discovery", "proof", "public science claim", "product ready", "autonomous crawl", "provider call authorized", "runtime enabled", "ontology applied automatically", "self-modification")):
            block("forbidden_claim_wording_present")
    return {"valid": not blocked_labels, "blocked": bool(blocked_labels), "blocked_labels": blocked_labels}


def summarize_source_ingestion_authorization_packet_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_source_ingestion_authorization_packet_v1(packet)
    return {
        "ingestion_request_id": _t(packet.get("ingestion_request_id")),
        "source_class": _t(packet.get("source_class")),
        "source_access_level": _t(packet.get("source_access_level")),
        "license_access_posture": _t(packet.get("license_access_posture")),
        "privacy_posture": _t(packet.get("privacy_posture")),
        "ingestion_purpose": _t(packet.get("ingestion_purpose")),
        "retention_mode": _t(packet.get("retention_mode")),
        "owner_authorization_required": bool(packet.get("owner_authorization_required")),
        "owner_authorization_present": bool(packet.get("owner_authorization_present")),
        "operator_review_required": bool(packet.get("operator_review_required")),
        "expert_review_required": bool(packet.get("expert_review_required")),
        "blocked": validation["blocked"],
        "next_safe_step": _t(packet.get("next_safe_step")),
        "final_judgment": _t(packet.get("final_judgment")),
    }


def render_source_ingestion_authorization_markdown_v1(packet: Mapping[str, Any]) -> str:
    summary = summarize_source_ingestion_authorization_packet_v1(packet)
    blocked_claims = "\n".join(f"- {item}" for item in _l(packet.get("blocked_claims"))) or "- none"
    abort_conditions = "\n".join(f"- {item}" for item in _l(packet.get("abort_conditions"))) or "- none"
    denied = packet.get("denied_authority_flags") or {}
    denied_lines = "\n".join(f"- {key}: {bool(denied.get(key))}" for key in _DENIED_AUTHORITY_FLAGS_V1)
    return (
        f"# Source ingestion authorization packet\n\n"
        f"- Request ID: {summary['ingestion_request_id']}\n"
        f"- Source class: {summary['source_class']}\n"
        f"- Access level: {_t(packet.get('source_access_level'))}\n"
        f"- License posture: {summary['license_access_posture']}\n"
        f"- Privacy posture: {summary['privacy_posture']}\n"
        f"- Ingestion purpose: {summary['ingestion_purpose']}\n"
        f"- Retention mode: {summary['retention_mode']}\n"
        f"- Owner authorization required: {summary['owner_authorization_required']}\n"
        f"- Owner authorization present: {summary['owner_authorization_present']}\n"
        f"- Operator review required: {summary['operator_review_required']}\n"
        f"- Expert review required: {summary['expert_review_required']}\n"
        f"- Next safe step: {summary['next_safe_step']}\n"
        f"- Final judgment: {summary['final_judgment']}\n\n"
        f"## Authorization posture\n"
        f"{_t(packet.get('safe_metadata_summary'))}\n\n"
        f"## Blocked claims\n{blocked_claims}\n\n"
        f"## Abort conditions\n{abort_conditions}\n\n"
        f"## Denied authority summary\n{denied_lines}\n"
    )


def to_source_ingestion_authorization_json_safe_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    return _json_safe(packet)


def build_initial_source_ingestion_authorization_examples_v1() -> tuple[dict[str, Any], ...]:
    public_research = build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="public_research_paper_metadata_only",
        requested_by="owner",
        source_ref="https://example.org/paper.pdf",
        source_class="public_research_paper",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        ingestion_purpose="source_metadata_extraction",
        artifact_target="interpretation_packet",
        evidence_role_target="source_selection_reference",
        retention_mode="metadata_only_no_content_retention",
        owner_authorization_required=False,
        owner_authorization_present=False,
        operator_review_required=True,
        expert_review_required=False,
        blocked_claims=("no_authority_escalation", "no_review_gate_break"),
        abort_conditions=("owner review required", "review gate required"),
        final_judgment="authorization_packet_pending_review",
    )
    official_standard = build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="official_standard_metadata_only",
        requested_by="owner",
        source_ref="https://example.org/standard",
        source_class="official_standard",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        ingestion_purpose="claim_boundary_mapping",
        artifact_target="interpretation_packet",
        evidence_role_target="method_limit_source",
        retention_mode="metadata_only_no_content_retention",
        operator_review_required=True,
        blocked_claims=("no_review_gate_break",),
        abort_conditions=("owner review required",),
        final_judgment="authorization_packet_pending_review",
    )
    github_repo = build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="github_repo_implementation_reference",
        requested_by="owner",
        source_ref="https://github.com/example/repo",
        source_class="github_repository",
        source_access_level="public_open",
        license_access_posture="open_access_confirmed",
        privacy_posture="public_non_private",
        ingestion_purpose="implementation_reference_mapping",
        artifact_target="interpretation_packet",
        evidence_role_target="implementation_reference",
        retention_mode="derived_summary_only",
        operator_review_required=True,
        blocked_claims=("no_candidate_promotion",),
        abort_conditions=("candidate promotion blocked",),
        final_judgment="authorization_packet_pending_review",
    )
    owner_uploaded = build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="owner_uploaded_file_no_raw_retention",
        requested_by="owner",
        source_ref="file:///authorized/upload.pdf",
        source_class="owner_uploaded_file",
        source_access_level="owner_uploaded",
        license_access_posture="owner_authorized_private",
        privacy_posture="owner_authorized_private",
        ingestion_purpose="evidence_candidate_extraction",
        artifact_target="interpretation_packet",
        evidence_role_target="primary_evidence_candidate",
        retention_mode="full_text_transient_no_retention",
        owner_authorization_required=True,
        owner_authorization_present=True,
        raw_retention_allowed=False,
        derived_metadata_allowed=True,
        quoted_excerpt_allowed=True,
        operator_review_required=True,
        blocked_claims=("no_review_gate_break",),
        abort_conditions=("owner review required",),
        final_judgment="authorization_packet_pending_review",
    )
    private_blocked = build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="private_weslr_ingestion_blocked",
        requested_by="owner",
        source_ref=".weslr/private/source",
        source_class="blocked_source_class",
        source_access_level="blocked_access",
        license_access_posture="blocked_license_or_access",
        privacy_posture="blocked_private_or_secret",
        ingestion_purpose="source_metadata_extraction",
        artifact_target="blocked",
        evidence_role_target="blocked_evidence",
        retention_mode="blocked_retention",
        owner_authorization_required=False,
        owner_authorization_present=False,
        operator_review_required=True,
        blocked_claims=("no_review_gate_break", "no_accepted_evidence_authority"),
        abort_conditions=("no .weslr", "owner review required"),
        final_judgment="blocked_source_or_retention",
    )
    unsafe_final_answer = build_source_ingestion_authorization_packet_v1(
        ingestion_request_id="unsafe_final_answer_request_blocked",
        requested_by="owner",
        source_ref="https://example.org/article",
        source_class="public_news_or_report",
        source_access_level="public_open",
        license_access_posture="public_metadata_only",
        privacy_posture="public_non_private",
        ingestion_purpose="source_metadata_extraction",
        artifact_target="final_answer",
        evidence_role_target="primary_evidence_candidate",
        retention_mode="metadata_only_no_content_retention",
        operator_review_required=True,
        blocked_claims=("no_review_gate_break", "no_discovery_promotion"),
        abort_conditions=("final answer requested", "discovery request blocked"),
        final_judgment="blocked_source_or_retention",
    )
    return (public_research, official_standard, github_repo, owner_uploaded, private_blocked, unsafe_final_answer)


__all__ = [
    "build_source_ingestion_authorization_packet_v1",
    "validate_source_ingestion_authorization_packet_v1",
    "summarize_source_ingestion_authorization_packet_v1",
    "render_source_ingestion_authorization_markdown_v1",
    "to_source_ingestion_authorization_json_safe_v1",
    "build_initial_source_ingestion_authorization_examples_v1",
]
