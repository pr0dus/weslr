"""WESLR MLCF routing from live SearXNG metadata result helper V1.

Pure, deterministic, metadata-only helper functions for routing an already
validated live SearXNG metadata-only result packet into MLCF routing metadata.
This module does not fetch sources, ingest content, call models, touch runtime,
write state, or perform network/filesystem/subprocess actions.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any, Iterable, Mapping

SCHEMA_VERSION_V1 = "mlcf_routing_from_live_searxng_metadata_result_helper_v1"

_ALLOWED_ROUTE_ACTIONS_V1 = (
    "route_to_locator_metadata_candidate",
    "hold_for_operator_review",
    "block_from_routing",
)

_ALLOWED_ROUTE_STATUSES_V1 = (
    "ready_for_operator_review",
    "blocked",
)

_ALLOWED_NEXT_STEPS_V1 = (
    "operator_review",
    "blocked_by_safety",
    "no_next_step",
)

_ALLOWED_OPERATOR_ROLES_V1 = (
    "owner",
    "operator",
    "reviewer",
    "analyst",
)

_ALLOWED_BLOCKED_STATUS_V1 = (
    "kept",
    "result_cap_exceeded",
    "blocked_from_routing",
    "blocked_by_safety",
)

_ALLOWED_SOURCE_CLASS_HINTS_V1 = (
    "github_repository",
    "public_lab_or_university_artifact",
    "unknown_authority",
    "candidate_signal",
    "official_standard",
    "public_research_paper",
    "public_dataset",
    "public_benchmark_or_test_suite",
    "official_vendor_documentation",
    "official_government_or_agency_data",
    "blocked_private_or_hidden_source",
)

_ALLOWED_AUTHORITY_GUESSES_V1 = (
    "community_signal",
    "implementation_evidence",
    "public_secondary",
    "public_primary",
    "official_primary",
    "owner_context",
    "internal_context",
    "unknown_authority",
    "blocked",
)

_ALLOWED_EVIDENCE_ROLE_GUESSES_V1 = (
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

_AUTHORITY_FALSE_FLAGS_V1 = (
    "source_ingestion_authorized",
    "raw_retention_authorized",
    "final_answer_authority",
    "public_claim_authorized",
    "discovery_claim_authorized",
    "proof_claim_authorized",
    "benchmark_claim_authorized",
    "agi_claim_authorized",
    "consciousness_claim_authorized",
    "sentience_claim_authorized",
    "runtime_execution_authority",
    "memory_mutation_authority",
    "weslr_io_authority",
    "autonomous_routing_authority",
    "external_action_authority",
    "source_fetching_authority",
    "provider_authority",
    "model_authority",
    "http_authority",
    "web_call_authority",
    "github_call_authority",
    "source_summary_authorized",
    "source_access_authorized",
)

_FORBIDDEN_KEY_NAMES_V1 = {
    "raw_http_response_body",
    "raw_html",
    "full_snippets",
    "page_content",
    "source_excerpts",
    "source_summaries",
    "copied_article_text",
    "pdf_content",
    "repository_content",
    "downloaded_files",
    "embeddings",
    "content_hashes",
    "trusted_evidence_verdict",
    "accepted_evidence_verdict",
    "candidate_membership",
    "final_answer_content",
    "public_claims",
}

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw http response body",
    "raw html",
    "full snippets",
    "page content",
    "source excerpts",
    "source summaries",
    "copied article text",
    "pdf content",
    "repository content",
    "downloaded files",
    "trusted evidence verdict",
    "accepted evidence verdict",
    "candidate membership",
    "final answer",
    "public claim",
    "discovery claim",
    "proof claim",
    "benchmark claim",
    "agi",
    "consciousness",
    "sentience",
)

_PRIVATE_OR_SUSPICIOUS_DOMAIN_MARKERS_V1 = (
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    ".local",
    ".internal",
    "login",
    "auth",
    "credential",
    "credentials",
    "password",
    "private",
    "tracking",
    "analytics",
    "malware",
    "phishing",
    "facebook",
    "instagram",
    "tiktok",
    "linkedin",
    "twitter",
    "x.com",
)

_PRIVATE_OR_SUSPICIOUS_URL_MARKERS_V1 = (
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "file:",
    "ftp:",
    "data:",
    "javascript:",
    "login",
    "signin",
    "sign-in",
    "auth",
    "authenticate",
    "credential",
    "credentials",
    "password",
    "token",
    "private",
    "tracking",
    "analytics",
    "malware",
    "phishing",
)

_REQUIRED_POSTURE_FIELDS_V1 = (
    "evidence_status",
    "authority_verdict",
    "raw_content_retained",
    "snippets_retained",
    "automatic_truth_write",
    "results",
    "blocked",
)

_REQUIRED_ROUTE_FIELDS_V1 = (
    "schema_version",
    "route_id",
    "source_result_packet_reference",
    "query",
    "operator_role",
    "routing_posture",
    "route_status",
    "kept_locator_route_entries",
    "blocked_overflow_summary",
    "operator_review_requirements",
    "denied_authority_flags",
    "validation_status",
    "safe_metadata_summary",
    "next_safe_step",
)

_REQUIRED_ROUTE_ENTRY_FIELDS_V1 = (
    "original_rank",
    "locator_id",
    "title",
    "url",
    "domain",
    "source_engine",
    "source_class_posture",
    "authority_posture",
    "evidence_role_posture",
    "freshness_posture",
    "access/license_posture",
    "privacy_posture",
    "route_action",
    "operator_review_required",
    "allowed_next_MLCF_stage",
    "denied_authority_flags",
)


def allowed_mlcf_live_searxng_metadata_route_actions_v1() -> tuple[str, ...]:
    return _ALLOWED_ROUTE_ACTIONS_V1


def allowed_mlcf_live_searxng_metadata_route_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_ROUTE_STATUSES_V1


def allowed_mlcf_live_searxng_metadata_route_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEPS_V1


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _first_non_json_safe_path(value: Any, path: str = "$") -> str | None:
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and not math.isfinite(value):
            return path
        return None
    if isinstance(value, (bytes, bytearray, memoryview, tuple, set)):
        return path
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                return f"{path}.[non-string-key:{type(key).__name__}]"
            issue = _first_non_json_safe_path(nested, f"{path}.{key}")
            if issue is not None:
                return issue
        return None
    if isinstance(value, list):
        for index, nested in enumerate(value):
            issue = _first_non_json_safe_path(nested, f"{path}[{index}]")
            if issue is not None:
                return issue
        return None
    if callable(value):
        return path
    return path


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _compact_text_list(value: Any) -> list[str]:
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
    result: list[str] = []
    for item in items:
        text = _compact_text(item)
        if text:
            result.append(text)
    return result


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _contains_any_marker(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def _contains_forbidden_text(value: Any, markers: Iterable[str] = _FORBIDDEN_TEXT_MARKERS_V1) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_forbidden_text(item, markers) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    return _contains_any_marker(value, markers)


def _contains_forbidden_keys(value: Any, forbidden_keys: set[str] = _FORBIDDEN_KEY_NAMES_V1) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _compact_text(key).lower()
            if key_text in forbidden_keys:
                return True
            if _contains_forbidden_keys(nested, forbidden_keys):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_keys(item, forbidden_keys) for item in value)
    return False


def _contains_any_true_flag(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _compact_text(key).lower()
            if key_text.startswith("no_"):
                continue
            if key_text in _AUTHORITY_FALSE_FLAGS_V1 and nested is True:
                return True
            if key_text.endswith("_authorized") and nested is True:
                return True
            if key_text.endswith("_authority") and nested is True:
                return True
            if key_text.endswith("_claims") and nested is True:
                return True
            if _contains_any_true_flag(nested):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_any_true_flag(item) for item in value)
    return False


def _safe_domain_text(url: str | None, domain: str | None) -> tuple[str, str, list[str]]:
    url_text = _compact_text(url)
    domain_text = _compact_text(domain)
    issues: list[str] = []
    combined = f"{url_text} {domain_text}".lower()
    if not url_text:
        issues.append("missing_url")
    if not domain_text:
        issues.append("missing_domain")
    if combined and _contains_any_marker(combined, _PRIVATE_OR_SUSPICIOUS_DOMAIN_MARKERS_V1):
        issues.append("unsafe_domain_or_url")
    if url_text and _contains_any_marker(url_text.lower(), _PRIVATE_OR_SUSPICIOUS_URL_MARKERS_V1):
        issues.append("unsafe_url")
    if url_text and not (url_text.startswith("http://") or url_text.startswith("https://")):
        if not (url_text.startswith("urn:") or url_text.startswith("about:")):
            issues.append("unsafe_url_scheme")
    return url_text, domain_text, issues


def _default_denied_authority_flags() -> dict[str, bool]:
    flags = {flag: False for flag in _AUTHORITY_FALSE_FLAGS_V1}
    flags.update(
        {
            "all_authority_flags_false": True,
            "status": "metadata_only_route",
            "boundary_notes": "metadata-only routing helper boundary",
        }
    )
    return flags


def _default_operator_review_requirements() -> list[str]:
    return [
        "operator_must_confirm_metadata_only_posture",
        "operator_must_not_fetch_sources_or_ingest_content",
        "operator_must_not_promote_locators_to_evidence",
        "operator_must_keep_runtime_and_public_integration_blocked",
    ]


def _map_source_class_posture(source_class_hint: str, authority_guess: str, evidence_role_guess: str) -> tuple[str, str, str, str, bool]:
    source_class_hint = _compact_text(source_class_hint, "unknown_authority")
    authority_guess = _compact_text(authority_guess, "unknown_authority")
    evidence_role_guess = _compact_text(evidence_role_guess, "candidate_signal")

    if source_class_hint == "blocked_private_or_hidden_source":
        return "blocked", "blocked", "not_authoritative_context", "blocked_by_safety", False
    if source_class_hint == "github_repository":
        return "community_signal", "community_signal", "implementation_reference", "operator_review", True
    if source_class_hint == "public_lab_or_university_artifact":
        return "secondary_public_metadata", "public_secondary", evidence_role_guess or "candidate_signal", "operator_review", True
    if source_class_hint == "unknown_authority" or authority_guess == "unknown_authority":
        return "operator_review", "unknown_authority", evidence_role_guess or "candidate_signal", "operator_review", True
    if source_class_hint == "candidate_signal":
        return "candidate_signal", "candidate_signal", "candidate_signal", "operator_review", True
    return "operator_review", authority_guess, evidence_role_guess or "candidate_signal", "operator_review", True


def _validate_entry_fields(entry: Any, *, allow_blocked_overflow: bool = False) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(entry, Mapping):
        return None, ["invalid_entry_type"]
    issues: list[str] = []
    if _contains_forbidden_keys(entry):
        issues.append("forbidden_content_key_present")
    if _contains_forbidden_text(entry):
        issues.append("forbidden_content_text_present")
    if _contains_any_true_flag(entry):
        issues.append("unsafe_authority_or_claim_flag")

    blocked_status = _compact_text(entry.get("blocked_status"), "kept")
    if blocked_status not in _ALLOWED_BLOCKED_STATUS_V1:
        issues.append("invalid_blocked_status")
    if allow_blocked_overflow:
        if blocked_status != "result_cap_exceeded":
            issues.append("blocked_overflow_must_use_result_cap_exceeded")
    elif blocked_status == "result_cap_exceeded":
        issues.append("blocked_overflow_routed_as_kept")

    locator_id = _compact_text(entry.get("locator_id"))
    if not locator_id:
        issues.append("missing_locator_id")
    title = _compact_text(entry.get("title"))
    if not title:
        issues.append("missing_title")
    url, domain, url_issues = _safe_domain_text(entry.get("url"), entry.get("domain"))
    issues.extend(url_issues)
    source_engine = _compact_text(entry.get("source_engine"))
    if not source_engine:
        issues.append("missing_source_engine")
    source_class_hint = _compact_text(entry.get("source_class_hint"), "unknown_authority")
    authority_guess = _compact_text(entry.get("authority_guess"), "unknown_authority")
    evidence_role_guess = _compact_text(entry.get("evidence_role_guess"), "candidate_signal")
    relevance_reason = _compact_text(entry.get("relevance_reason"))
    if not relevance_reason:
        issues.append("missing_relevance_reason")
    freshness_status = _compact_text(entry.get("freshness_status_guess"), "unknown")
    access_status = _compact_text(entry.get("access_license_status_guess"), "unknown")
    privacy_status = _compact_text(entry.get("privacy_status_guess"), "unknown")
    rank = entry.get("rank")
    if rank is not None and not _is_finite_number(rank):
        issues.append("invalid_rank")
    score = entry.get("score")
    if score is not None and not _is_finite_number(score):
        issues.append("invalid_score")
    published_date = entry.get("published_date")
    if published_date is not None and not _compact_text(published_date):
        issues.append("invalid_published_date")

    if source_class_hint not in _ALLOWED_SOURCE_CLASS_HINTS_V1:
        issues.append("invalid_source_class_hint")
    if authority_guess not in _ALLOWED_AUTHORITY_GUESSES_V1:
        issues.append("invalid_authority_guess")
    if evidence_role_guess not in _ALLOWED_EVIDENCE_ROLE_GUESSES_V1:
        issues.append("invalid_evidence_role_guess")
    if blocked_status == "result_cap_exceeded" and not allow_blocked_overflow:
        issues.append("blocked_overflow_routed_as_kept")

    if any(_contains_any_marker(text, _FORBIDDEN_TEXT_MARKERS_V1) for text in (title, url, domain, source_engine, relevance_reason, freshness_status, access_status, privacy_status)):
        issues.append("forbidden_content_text_present")

    if issues:
        return None, list(dict.fromkeys(issues))

    source_class_posture, authority_posture, evidence_role_posture, allowed_next_stage, operator_review_required = _map_source_class_posture(
        source_class_hint,
        authority_guess,
        evidence_role_guess,
    )
    route_action = "block_from_routing"
    if blocked_status == "result_cap_exceeded":
        route_action = "block_from_routing"
        operator_review_required = False
        allowed_next_stage = "blocked_by_safety"
    elif source_class_hint == "github_repository":
        route_action = "route_to_locator_metadata_candidate"
    elif source_class_hint in {"public_lab_or_university_artifact", "unknown_authority", "candidate_signal"} or authority_guess == "unknown_authority":
        route_action = "hold_for_operator_review"
    elif source_class_posture == "blocked":
        route_action = "block_from_routing"
        operator_review_required = True
        allowed_next_stage = "blocked_by_safety"
    else:
        route_action = "route_to_locator_metadata_candidate"

    if route_action == "block_from_routing" and blocked_status not in {"result_cap_exceeded", "blocked_from_routing", "blocked_by_safety", "kept"}:
        issues.append("blocked_status_is_not_allowed")

    if issues:
        return None, list(dict.fromkeys(issues))

    return (
        {
            "original_rank": rank,
            "locator_id": locator_id,
            "title": title,
            "url": url,
            "domain": domain,
            "source_engine": source_engine,
            "source_class_posture": source_class_posture,
            "authority_posture": authority_posture,
            "evidence_role_posture": evidence_role_posture,
            "freshness_posture": freshness_status,
            "access/license_posture": access_status,
            "privacy_posture": privacy_status,
            "route_action": route_action,
            "operator_review_required": bool(operator_review_required),
            "allowed_next_MLCF_stage": allowed_next_stage,
            "denied_authority_flags": _default_denied_authority_flags(),
            "blocked_status": blocked_status,
            "source_class_hint": source_class_hint,
            "authority_guess": authority_guess,
            "evidence_role_guess": evidence_role_guess,
            "rank": rank,
            "score": score,
            "published_date": published_date,
            "blocked": False if blocked_status != "result_cap_exceeded" else True,
        },
        [],
    )


def _validate_blocked_overflow_entry(entry: Any) -> list[str]:
    if not isinstance(entry, Mapping):
        return ["invalid_blocked_entry_type"]
    issues: list[str] = []
    if _compact_text(entry.get("blocked_status")) != "result_cap_exceeded":
        issues.append("blocked_overflow_must_use_result_cap_exceeded")
    if _contains_forbidden_keys(entry):
        issues.append("forbidden_content_key_present")
    if _contains_forbidden_text(entry):
        issues.append("forbidden_content_text_present")
    if _contains_any_true_flag(entry):
        issues.append("unsafe_authority_or_claim_flag")
    url, domain, url_issues = _safe_domain_text(entry.get("url"), entry.get("domain"))
    issues.extend(url_issues)
    if url and _contains_any_marker(url.lower(), _PRIVATE_OR_SUSPICIOUS_URL_MARKERS_V1):
        issues.append("unsafe_url")
    if domain and _contains_any_marker(domain.lower(), _PRIVATE_OR_SUSPICIOUS_DOMAIN_MARKERS_V1):
        issues.append("unsafe_domain_or_url")
    if _compact_text(entry.get("locator_id")) == "":
        issues.append("missing_locator_id")
    return list(dict.fromkeys(issues))




def _validate_packet_core(packet: Any) -> list[str]:
    if not isinstance(packet, Mapping):
        return ["packet_must_be_a_dict"]
    issues: list[str] = []
    for field in _REQUIRED_POSTURE_FIELDS_V1:
        if field not in packet:
            issues.append(f"missing_{field}")
    if issues:
        return issues
    if _compact_text(packet.get("evidence_status")) != "metadata_only_locator_candidates":
        issues.append("invalid_evidence_status")
    if _compact_text(packet.get("authority_verdict")) != "external_evidence_unverified":
        issues.append("invalid_authority_verdict")
    if packet.get("raw_content_retained") is not False:
        issues.append("raw_content_retained_must_be_false")
    if packet.get("snippets_retained") is not False:
        issues.append("snippets_retained_must_be_false")
    if packet.get("automatic_truth_write") is not False:
        issues.append("automatic_truth_write_must_be_false")
    query = _compact_text(packet.get("query"))
    if not query:
        issues.append("missing_query")
    results = packet.get("results")
    blocked = packet.get("blocked")
    if not isinstance(results, list):
        issues.append("results_must_be_a_list")
    if not isinstance(blocked, list):
        issues.append("blocked_must_be_a_list")
    if isinstance(results, list):
        for item in results:
            _, entry_issues = _validate_entry_fields(item, allow_blocked_overflow=False)
            if entry_issues:
                issues.extend(entry_issues)
    if isinstance(blocked, list):
        for item in blocked:
            blocked_issues = _validate_blocked_overflow_entry(item)
            if blocked_issues:
                issues.extend(blocked_issues)
    if _contains_any_true_flag(packet):
        issues.append("unsafe_authority_or_claim_flag")
    if _contains_forbidden_keys(packet):
        issues.append("forbidden_content_key_present")
    if _contains_forbidden_text(packet):
        issues.append("forbidden_content_text_present")
    if _first_non_json_safe_path(packet) is not None:
        issues.append("non_json_safe_output")
    return list(dict.fromkeys(issues))


def validate_mlcf_route_from_live_searxng_metadata_result_request_v1(request: Any) -> dict[str, Any]:
    issues = _validate_packet_core(request)
    route_id = _compact_text(request.get("route_id")) if isinstance(request, Mapping) else ""
    operator_role = _compact_text(request.get("operator_role"), "owner") if isinstance(request, Mapping) else "owner"
    if operator_role and operator_role not in _ALLOWED_OPERATOR_ROLES_V1:
        issues.append("invalid_operator_role")
    if route_id and _contains_forbidden_text(route_id):
        issues.append("forbidden_content_text_present")
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": not issues,
        "blocked": bool(issues),
        "blocked_labels": issues,
        "validation_posture": "valid" if not issues else "blocked",
        "route_id": route_id,
        "operator_role": operator_role,
        "summary_text": (
            "Valid metadata-only live SearXNG route request."
            if not issues
            else "Blocked metadata-only live SearXNG route request."
        ),
    }


def _build_kept_entries(packet: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    kept_entries: list[dict[str, Any]] = []
    issues: list[str] = []
    for entry in packet.get("results", []):
        built, entry_issues = _validate_entry_fields(entry, allow_blocked_overflow=False)
        if entry_issues:
            issues.extend(entry_issues)
            continue
        if built is None:
            issues.append("invalid_kept_entry")
            continue
        if built["blocked_status"] == "result_cap_exceeded":
            issues.append("blocked_overflow_routed_as_kept")
            continue
        kept_entries.append(built)
    return kept_entries, list(dict.fromkeys(issues))


def _build_blocked_overflow_summary(packet: Mapping[str, Any]) -> dict[str, Any]:
    blocked_entries = []
    for entry in packet.get("blocked", []):
        if isinstance(entry, Mapping):
            blocked_entries.append(entry)
        else:
            blocked_entries.append({"blocked_status": "result_cap_exceeded"})
    count = len(blocked_entries)
    result_cap_exceeded_count = sum(1 for entry in blocked_entries if _compact_text(entry.get("blocked_status")) == "result_cap_exceeded")
    return {
        "count": count,
        "result_cap_exceeded_count": result_cap_exceeded_count,
        "count_only": True,
        "routed_into_kept": False,
        "may_be_reviewed_only_in_future_owner_approved_larger_cap_sample": True,
        "future_larger_cap_requires_owner_authorization": True,
    }


def _build_safe_metadata_summary(packet: Mapping[str, Any], kept_count: int, blocked_summary: Mapping[str, Any], route_status: str, next_safe_step: str) -> dict[str, Any]:
    return {
        "metadata_only": True,
        "json_safe": True,
        "no_source_fetching": True,
        "no_ingestion": True,
        "no_evidence_elevation": True,
        "no_truth_elevation": True,
        "no_claims": True,
        "no_runtime_or_public_integration": True,
        "query": _compact_text(packet.get("query")),
        "kept_locator_count": kept_count,
        "blocked_overflow_count": int(blocked_summary.get("count", 0)),
        "route_status": route_status,
        "next_safe_step": next_safe_step,
    }


def _build_route_packet(packet: Mapping[str, Any], *, route_id: str | None, operator_role: str, validation: Mapping[str, Any]) -> dict[str, Any]:
    kept_entries, kept_issues = _build_kept_entries(packet)
    blocked_summary = _build_blocked_overflow_summary(packet)
    overall_issues = list(validation.get("blocked_labels", [])) + kept_issues
    route_status = "ready_for_operator_review" if not overall_issues else "blocked"
    next_safe_step = "operator_review" if route_status == "ready_for_operator_review" else "blocked_by_safety"
    source_reference = _compact_text(
        packet.get("source_result_packet_reference")
        or packet.get("result_packet_id")
        or packet.get("artifact_reference")
        or packet.get("packet_id"),
        "controlled_live_searxng_metadata_only_result_packet",
    )
    payload_for_id = {
        "source_result_packet_reference": source_reference,
        "query": _compact_text(packet.get("query")),
        "operator_role": operator_role,
        "kept_count": len(kept_entries),
        "blocked_count": blocked_summary["count"],
    }
    computed_route_id = _compact_text(route_id) or _stable_id("mlcf_route_live_searxng_v1", payload_for_id)
    route_packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "route_id": computed_route_id,
        "source_result_packet_reference": source_reference,
        "query": _compact_text(packet.get("query")),
        "operator_role": operator_role,
        "routing_posture": "metadata_only_operator_review",
        "route_status": route_status,
        "kept_locator_route_entries": kept_entries,
        "blocked_overflow_summary": blocked_summary,
        "operator_review_requirements": _default_operator_review_requirements(),
        "denied_authority_flags": _default_denied_authority_flags(),
        "validation_status": {
            "valid": not overall_issues,
            "blocked": bool(overall_issues),
            "blocked_labels": overall_issues,
            "validation_posture": "valid" if not overall_issues else "blocked",
            "route_id": computed_route_id,
        },
        "safe_metadata_summary": _build_safe_metadata_summary(packet, len(kept_entries), blocked_summary, route_status, next_safe_step),
        "next_safe_step": next_safe_step,
    }
    return to_mlcf_route_from_live_searxng_metadata_result_json_safe_v1(route_packet)


def build_mlcf_route_from_live_searxng_metadata_result_v1(packet: Any, *, route_id: str | None = None, operator_role: str = "owner") -> dict[str, Any]:
    if isinstance(packet, Mapping):
        request_payload = dict(packet)
        request_payload["route_id"] = route_id
        request_payload["operator_role"] = operator_role
    else:
        request_payload = packet
    request_validation = validate_mlcf_route_from_live_searxng_metadata_result_request_v1(request_payload)
    if not isinstance(packet, Mapping):
        packet = {}
    route_packet = _build_route_packet(packet, route_id=route_id, operator_role=_compact_text(operator_role, "owner"), validation=request_validation)
    route_packet["validation_status"] = validate_mlcf_route_from_live_searxng_metadata_result_v1(route_packet)
    return route_packet


def validate_mlcf_route_from_live_searxng_metadata_result_v1(route_packet: Any) -> dict[str, Any]:
    issues = []
    if not isinstance(route_packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["route_packet_must_be_a_dict"],
            "validation_posture": "blocked",
            "summary_text": "Blocked metadata-only route packet.",
        }
    for field in _REQUIRED_ROUTE_FIELDS_V1:
        if field not in route_packet:
            issues.append(f"missing_{field}")
    if issues:
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": issues,
            "validation_posture": "blocked",
            "route_id": _compact_text(route_packet.get("route_id")),
            "summary_text": "Blocked metadata-only route packet.",
        }
    if _compact_text(route_packet.get("schema_version")) != SCHEMA_VERSION_V1:
        issues.append("invalid_schema_version")
    if not _compact_text(route_packet.get("route_id")):
        issues.append("missing_route_id")
    if not _compact_text(route_packet.get("query")):
        issues.append("missing_query")
    if _compact_text(route_packet.get("operator_role")) not in _ALLOWED_OPERATOR_ROLES_V1:
        issues.append("invalid_operator_role")
    if _compact_text(route_packet.get("routing_posture")) != "metadata_only_operator_review":
        issues.append("invalid_routing_posture")
    if _compact_text(route_packet.get("route_status")) not in _ALLOWED_ROUTE_STATUSES_V1:
        issues.append("invalid_route_status")
    kept_entries = route_packet.get("kept_locator_route_entries")
    if not isinstance(kept_entries, list):
        issues.append("kept_locator_route_entries_must_be_a_list")
        kept_entries = []
    for entry in kept_entries:
        if not isinstance(entry, Mapping):
            issues.append("invalid_kept_locator_route_entry")
            continue
        for field in _REQUIRED_ROUTE_ENTRY_FIELDS_V1:
            if field not in entry:
                issues.append(f"missing_kept_entry_{field}")
        if _compact_text(entry.get("route_action")) not in _ALLOWED_ROUTE_ACTIONS_V1:
            issues.append("invalid_route_action")
        if _compact_text(entry.get("allowed_next_MLCF_stage")) not in _ALLOWED_NEXT_STEPS_V1:
            issues.append("invalid_allowed_next_MLCF_stage")
        if entry.get("denied_authority_flags") != _default_denied_authority_flags():
            issues.append("invalid_denied_authority_flags")
        if entry.get("route_action") == "block_from_routing" and _compact_text(entry.get("blocked_status")) == "result_cap_exceeded":
            issues.append("blocked_overflow_routed_as_kept")
    blocked_summary = route_packet.get("blocked_overflow_summary")
    if not isinstance(blocked_summary, Mapping):
        issues.append("invalid_blocked_overflow_summary")
    else:
        if blocked_summary.get("count_only") is not True:
            issues.append("blocked_overflow_summary_must_be_count_only")
        if blocked_summary.get("routed_into_kept") is not False:
            issues.append("blocked_overflow_must_not_be_routed")
    operator_review = route_packet.get("operator_review_requirements")
    if not isinstance(operator_review, list) or not operator_review:
        issues.append("invalid_operator_review_requirements")
    if route_packet.get("denied_authority_flags") != _default_denied_authority_flags():
        issues.append("invalid_denied_authority_flags")
    safe_summary = route_packet.get("safe_metadata_summary")
    if not isinstance(safe_summary, Mapping):
        issues.append("invalid_safe_metadata_summary")
    if _contains_forbidden_keys(route_packet) or _contains_forbidden_text(route_packet) or _contains_any_true_flag(route_packet):
        issues.append("unsafe_route_packet_content")
    if _first_non_json_safe_path(route_packet) is not None:
        issues.append("non_json_safe_output")
    route_id = _compact_text(route_packet.get("route_id"))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": not issues,
        "blocked": bool(issues),
        "blocked_labels": list(dict.fromkeys(issues)),
        "validation_posture": "valid" if not issues else "blocked",
        "route_id": route_id,
        "summary_text": "Valid metadata-only route packet." if not issues else "Blocked metadata-only route packet.",
    }


def summarize_mlcf_route_from_live_searxng_metadata_result_v1(route_packet: Any) -> dict[str, Any]:
    validation = validate_mlcf_route_from_live_searxng_metadata_result_v1(route_packet)
    packet = route_packet if isinstance(route_packet, Mapping) else {}
    kept = packet.get("kept_locator_route_entries", []) if isinstance(packet.get("kept_locator_route_entries", []), list) else []
    blocked = packet.get("blocked_overflow_summary", {}) if isinstance(packet.get("blocked_overflow_summary", {}), Mapping) else {}
    kept_count = len(kept)
    blocked_count = int(blocked.get("count", 0)) if isinstance(blocked, Mapping) else 0
    summary_text = (
        f"Route { _compact_text(packet.get('route_id')) or 'unassigned' }: "
        f"{kept_count} kept locators, {blocked_count} blocked overflow rows, "
        f"status={_compact_text(packet.get('route_status'), 'blocked')}."
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "route_id": _compact_text(packet.get("route_id")),
        "source_result_packet_reference": _compact_text(packet.get("source_result_packet_reference")),
        "operator_role": _compact_text(packet.get("operator_role")),
        "kept_locator_count": kept_count,
        "blocked_overflow_count": blocked_count,
        "route_status": _compact_text(packet.get("route_status")),
        "validation_posture": validation.get("validation_posture", "blocked"),
        "summary_text": summary_text[:240],
        "next_safe_step": _compact_text(packet.get("next_safe_step"), "blocked_by_safety"),
    }


def to_mlcf_route_from_live_searxng_metadata_result_json_safe_v1(route_packet: Any) -> Any:
    return _json_safe(copy.deepcopy(route_packet))


def _example_source_packet() -> dict[str, Any]:
    kept = [
        {
            "query": "wifi sensing floorplan metadata only",
            "title": "GitHub WiFi sensing implementation reference",
            "url": "https://github.example.invalid/wifi-sensing/repo",
            "domain": "github.example.invalid",
            "source_engine": "searxng",
            "engines": ["searxng"],
            "rank": 1,
            "score": 98.1,
            "published_date": "2026-06-13",
            "source_class_hint": "github_repository",
            "authority_guess": "community_signal",
            "evidence_role_guess": "implementation_reference",
            "relevance_reason": "GitHub implementation reference only; metadata-only community signal.",
            "freshness_status_guess": "current",
            "access_license_status_guess": "open",
            "privacy_status_guess": "low",
            "blocked_status": "kept",
            "locator_id": "github_wifi_sensing_locator",
        },
        {
            "query": "wifi sensing floorplan metadata only",
            "title": "Public lab artifact",
            "url": "https://lab.example.invalid/wifi/artifact",
            "domain": "lab.example.invalid",
            "source_engine": "searxng",
            "engines": ["searxng"],
            "rank": 2,
            "score": 96.2,
            "published_date": "2026-05-01",
            "source_class_hint": "public_lab_or_university_artifact",
            "authority_guess": "public_secondary",
            "evidence_role_guess": "prior_art",
            "relevance_reason": "Public lab artifact metadata only; operator review required.",
            "freshness_status_guess": "recent",
            "access_license_status_guess": "open",
            "privacy_status_guess": "low",
            "blocked_status": "kept",
            "locator_id": "public_lab_artifact_locator",
        },
        {
            "query": "wifi sensing floorplan metadata only",
            "title": "Unknown authority locator",
            "url": "https://unknown.example.invalid/loc",
            "domain": "unknown.example.invalid",
            "source_engine": "searxng",
            "engines": ["searxng"],
            "rank": 3,
            "score": 90.0,
            "published_date": "2026-04-11",
            "source_class_hint": "unknown_authority",
            "authority_guess": "unknown_authority",
            "evidence_role_guess": "candidate_signal",
            "relevance_reason": "Unknown authority remains operator review only.",
            "freshness_status_guess": "unknown",
            "access_license_status_guess": "unknown",
            "privacy_status_guess": "unknown",
            "blocked_status": "kept",
            "locator_id": "unknown_authority_locator",
        },
        {
            "query": "wifi sensing floorplan metadata only",
            "title": "Candidate signal locator",
            "url": "https://candidate.example.invalid/loc",
            "domain": "candidate.example.invalid",
            "source_engine": "searxng",
            "engines": ["searxng"],
            "rank": 4,
            "score": 88.4,
            "published_date": "2026-03-22",
            "source_class_hint": "candidate_signal",
            "authority_guess": "owner_context",
            "evidence_role_guess": "candidate_signal",
            "relevance_reason": "Candidate signal remains posture only.",
            "freshness_status_guess": "stale",
            "access_license_status_guess": "open",
            "privacy_status_guess": "low",
            "blocked_status": "kept",
            "locator_id": "candidate_signal_locator",
        },
        {
            "query": "wifi sensing floorplan metadata only",
            "title": "Official standard locator",
            "url": "https://standard.example.invalid/spec",
            "domain": "standard.example.invalid",
            "source_engine": "searxng",
            "engines": ["searxng"],
            "rank": 5,
            "score": 87.1,
            "published_date": "2026-02-10",
            "source_class_hint": "official_standard",
            "authority_guess": "official_primary",
            "evidence_role_guess": "definition_or_standard",
            "relevance_reason": "Metadata-only standard locator ready for operator review.",
            "freshness_status_guess": "recent",
            "access_license_status_guess": "open",
            "privacy_status_guess": "low",
            "blocked_status": "kept",
            "locator_id": "official_standard_locator",
        },
    ]
    blocked = [
        {
            "locator_id": f"overflow_{index:02d}",
            "blocked_status": "result_cap_exceeded",
            "title": f"Overflow locator {index:02d}",
            "url": f"https://overflow.example.invalid/{index:02d}",
            "domain": "overflow.example.invalid",
        }
        for index in range(1, 36)
    ]
    return {
        "packet_id": "synthetic_controlled_live_searxng_metadata_only_result_packet_v1",
        "evidence_status": "metadata_only_locator_candidates",
        "authority_verdict": "external_evidence_unverified",
        "raw_content_retained": False,
        "snippets_retained": False,
        "automatic_truth_write": False,
        "query": "wifi sensing floorplan metadata only",
        "results": kept,
        "blocked": blocked,
        "source_result_packet_reference": "synthetic_in_memory_example_only",
        "authority_flags": {flag: False for flag in _AUTHORITY_FALSE_FLAGS_V1},
    }


def _example_private_packet() -> dict[str, Any]:
    packet = _example_source_packet()
    packet = copy.deepcopy(packet)
    packet["results"] = [
        {
            "query": "wifi sensing floorplan metadata only",
            "title": "Private loopback locator",
            "url": "http://127.0.0.1/private",
            "domain": "127.0.0.1",
            "source_engine": "searxng",
            "engines": ["searxng"],
            "rank": 1,
            "score": 1.0,
            "published_date": "2026-06-13",
            "source_class_hint": "blocked_private_or_hidden_source",
            "authority_guess": "blocked",
            "evidence_role_guess": "not_authoritative_context",
            "relevance_reason": "Private loopback locator should be blocked.",
            "freshness_status_guess": "unknown",
            "access_license_status_guess": "blocked",
            "privacy_status_guess": "high",
            "blocked_status": "blocked_from_routing",
            "locator_id": "private_loopback_locator",
        }
    ]
    packet["blocked"] = []
    return packet


def build_initial_mlcf_route_from_live_searxng_metadata_result_examples_v1() -> list[dict[str, Any]]:
    examples = []
    examples.append(build_mlcf_route_from_live_searxng_metadata_result_v1(_example_source_packet(), operator_role="owner"))
    examples.append(build_mlcf_route_from_live_searxng_metadata_result_v1(_example_private_packet(), operator_role="owner"))
    return examples


__all__ = [
    "SCHEMA_VERSION_V1",
    "allowed_mlcf_live_searxng_metadata_route_actions_v1",
    "allowed_mlcf_live_searxng_metadata_route_statuses_v1",
    "allowed_mlcf_live_searxng_metadata_route_next_steps_v1",
    "build_mlcf_route_from_live_searxng_metadata_result_v1",
    "validate_mlcf_route_from_live_searxng_metadata_result_request_v1",
    "validate_mlcf_route_from_live_searxng_metadata_result_v1",
    "summarize_mlcf_route_from_live_searxng_metadata_result_v1",
    "to_mlcf_route_from_live_searxng_metadata_result_json_safe_v1",
    "build_initial_mlcf_route_from_live_searxng_metadata_result_examples_v1",
]
