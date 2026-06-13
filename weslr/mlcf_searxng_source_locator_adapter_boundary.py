"""WESLR MLCF SearXNG Source Locator Adapter Boundary V1.

Metadata-only adapter boundary for future SearXNG results.
It converts pre-supplied search-result metadata into validated locator records
without calling SearXNG, browsing, fetching, ingesting, retaining raw content,
or authorizing claims.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping
from urllib.parse import urlparse

from weslr.mlcf_metadata_only_source_locator_record import (
    allowed_mlcf_locator_access_license_statuses_v1,
    allowed_mlcf_locator_authority_levels_v1,
    allowed_mlcf_locator_evidence_roles_v1,
    allowed_mlcf_locator_freshness_statuses_v1,
    allowed_mlcf_locator_next_steps_v1,
    allowed_mlcf_locator_privacy_statuses_v1,
    allowed_mlcf_locator_source_classes_v1,
    build_mlcf_metadata_only_source_locator_record_v1,
    summarize_mlcf_metadata_only_source_locator_record_v1,
    to_mlcf_metadata_only_source_locator_record_json_safe_v1,
    validate_mlcf_metadata_only_source_locator_record_v1,
)

SCHEMA_VERSION_V1 = "mlcf_searxng_source_locator_adapter_boundary_v1"
HELPER_FAMILY_V1 = "mlcf_searxng_source_locator_adapter_boundary"

_ALLOWED_INPUT_FIELDS_V1 = (
    "title",
    "url",
    "domain",
    "snippet",
    "engine",
    "published_date",
    "score",
    "source_class_hint",
    "query_family",
)

_ALLOWED_RESULT_STATUSES_V1 = (
    "accepted",
    "rejected",
    "blocked",
    "invalid",
)

_AUTHORITY_FALSE_FLAGS_V1 = (
    "source_ingestion_authorized",
    "raw_retention_authorized",
    "web_call_authority",
    "github_call_authority",
    "searxng_call_authority",
    "source_fetching_authority",
    "source_summary_authority",
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

_HIDDEN_PRIVATE_PROTECTED_MARKERS_V1 = (
    "hidden",
    "private",
    "protected",
    "credential",
    "credentials",
    "cookie",
    "cookies",
    "api key",
    "apikey",
    "token",
    "bearer",
    "secret",
    "password",
    "session",
    "csrf",
)

_REQUIRED_FIELD_NAMES_V1 = (
    "schema_version",
    "adapter_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "query_used",
    "query_family",
    "searxng_results_input_count",
    "locator_records",
    "rejected_results",
    "blocked_results",
    "source_class_distribution",
    "authority_guess_distribution",
    "operator_review_need",
    "allowed_next_step",
    "blocked_conditions",
    "authority_status",
    "safe_metadata",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "adapter_packet_id",
    "science_direction_id",
    "science_direction_summary",
    "query_used",
    "query_family",
    "operator_review_need",
    "allowed_next_step",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "locator_records",
    "rejected_results",
    "blocked_results",
    "blocked_conditions",
)

_REQUIRED_DICT_FIELDS_V1 = (
    "source_class_distribution",
    "authority_guess_distribution",
    "authority_status",
    "safe_metadata",
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
    "no_searxng_calls",
    "no_source_fetching",
    "no_source_summary",
    "operator_review_required",
)

_ALLOWED_BLOCKED_SOURCE_HINTS_V1 = (
    "private",
    "hidden",
    "protected",
    "credential",
    "token",
    "cookie",
    "api key",
    "apikey",
    "secret",
    "password",
    "login",
    "gated",
    "paywalled",
    "restricted",
)

_ALLOWED_SOURCE_HINTS_V1 = allowed_mlcf_locator_source_classes_v1()


def allowed_mlcf_searxng_adapter_input_fields_v1() -> tuple[str, ...]:
    return _ALLOWED_INPUT_FIELDS_V1


def allowed_mlcf_searxng_adapter_result_statuses_v1() -> tuple[str, ...]:
    return _ALLOWED_RESULT_STATUSES_V1


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
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                return f"{path}.[non-string-key:{type(key).__name__}]"
            issue = _first_non_json_safe_path(item, f"{path}.{key}")
            if issue is not None:
                return issue
        return None
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(list(value) if not isinstance(value, list) else value):
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
            "status": "metadata_only_adapter_boundary",
            "boundary_notes": "metadata-only SearXNG source locator adapter boundary",
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
        "searxng_call_authority": False,
        "source_fetching_authority": False,
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


def _normalize_result_fields(result: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): result[key] for key in result.keys()}


def _unsupported_input_fields(result: Mapping[str, Any]) -> list[str]:
    return [key for key in result.keys() if key not in _ALLOWED_INPUT_FIELDS_V1]


def _infer_source_class(result: Mapping[str, Any], query_family: str) -> str:
    hint = _compact_text(result.get("source_class_hint"))
    title = _compact_text(result.get("title"))
    domain = _compact_text(result.get("domain"))
    url = _compact_text(result.get("url"))
    combined = f"{hint} {title} {domain} {url} {query_family}".lower()

    if _contains_any_marker(combined, _ALLOWED_BLOCKED_SOURCE_HINTS_V1):
        return "blocked_private_or_hidden_source"
    if "github.com" in combined or "githubusercontent.com" in combined:
        return "github_repository"
    if any(marker in combined for marker in (".gov", ".mil", "government", "agency")):
        return "official_government_or_agency_data"
    if any(marker in combined for marker in ("standard", "spec", "specification", "norm", "ietf", "ieee 802", "3gpp", "wifi alliance")):
        return "official_standard"
    if any(marker in combined for marker in ("vendor", "documentation", "docs", "developer", "manual", "support", "api")):
        return "official_vendor_documentation"
    if any(marker in combined for marker in ("dataset", "data", "benchmark", "leaderboard", "test suite", "test-suite", "evaluation")):
        if any(marker in combined for marker in ("benchmark", "leaderboard", "test suite", "test-suite", "evaluation")):
            return "public_benchmark_or_test_suite"
        return "public_dataset"
    if any(marker in combined for marker in ("paper", "preprint", "arxiv", "doi", "journal", "conference", "proceedings")):
        return "public_research_paper"
    if any(marker in combined for marker in ("lab", ".edu", "university", "research group", "thesis")):
        return "public_lab_or_university_artifact"
    return _compact_text(hint, "public_research_paper")


def _infer_authority_level(source_class: str) -> str:
    if source_class in {"official_standard", "official_government_or_agency_data", "official_vendor_documentation"}:
        return "official_primary"
    if source_class == "public_research_paper":
        return "public_primary"
    if source_class == "public_dataset":
        return "public_primary"
    if source_class == "github_repository":
        return "implementation_evidence"
    if source_class in {"public_lab_or_university_artifact", "public_benchmark_or_test_suite"}:
        return "public_secondary"
    if source_class == "blocked_private_or_hidden_source":
        return "blocked"
    return "unknown_authority"


def _infer_evidence_role(source_class: str) -> str:
    if source_class == "official_standard":
        return "definition_or_standard"
    if source_class == "official_government_or_agency_data":
        return "measurement_data"
    if source_class == "official_vendor_documentation":
        return "implementation_reference"
    if source_class == "public_research_paper":
        return "prior_art"
    if source_class == "public_dataset":
        return "measurement_data"
    if source_class == "github_repository":
        return "implementation_reference"
    if source_class == "public_lab_or_university_artifact":
        return "replication_target"
    if source_class == "public_benchmark_or_test_suite":
        return "counterexample_source"
    if source_class == "blocked_private_or_hidden_source":
        return "not_authoritative_context"
    return "candidate_signal"


def _infer_freshness_status(published_date: Any) -> str:
    text = _compact_text(published_date)
    if not text:
        return "unknown"
    lowered = text.lower()
    if lowered in {"today", "now", "current"}:
        return "current"
    cleaned = lowered.replace("z", "+00:00")
    try:
        if len(cleaned) == 4 and cleaned.isdigit():
            year = int(cleaned)
        else:
            parsed = datetime.fromisoformat(cleaned)
            year = parsed.year
    except ValueError:
        return "unknown"
    current_year = datetime.now(timezone.utc).year
    if year >= current_year:
        return "current"
    if current_year - year <= 2:
        return "recent"
    return "stale"


def _bounded_reason(title: str, snippet: str | None = None) -> str:
    title_text = _compact_text(title)
    snippet_text = _compact_text(snippet or "")
    if snippet_text:
        reason = f"{title_text}: {snippet_text}"
    else:
        reason = title_text or "Metadata-only locator record."
    return reason[:220]


def _privacy_status_for_source(source_class: str, is_blocked: bool) -> str:
    if is_blocked:
        return "high"
    if source_class in {"official_standard", "official_government_or_agency_data", "official_vendor_documentation", "public_research_paper", "public_dataset", "github_repository", "public_lab_or_university_artifact", "public_benchmark_or_test_suite"}:
        return "low"
    return "unknown"


def _access_license_status_for_source(is_blocked: bool) -> str:
    return "blocked" if is_blocked else "unknown"


def _blocked_conditions_for_result(source_class: str, blocked_reason: str | None = None) -> list[str]:
    conditions = ["metadata-only result", "operator review required"]
    if source_class == "github_repository":
        conditions.append("GitHub is implementation evidence only")
    if source_class == "blocked_private_or_hidden_source":
        conditions.append("safety block")
    if blocked_reason:
        conditions.append(blocked_reason)
    return list(dict.fromkeys(conditions))


def _result_has_unsafe_markers(result: Mapping[str, Any]) -> bool:
    return _contains_forbidden_markers(result, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1)


def build_mlcf_locator_record_from_searxng_result_v1(
    result: Any,
    *,
    science_direction_id: str,
    science_direction_summary: str,
    query_used: str,
    query_family: str,
) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        raise ValueError("invalid_result_type")

    unsupported = _unsupported_input_fields(result)
    if unsupported:
        raise ValueError("unsupported_input_fields:" + ",".join(sorted(unsupported)))

    title = _compact_text(result.get("title"))
    url = _compact_text(result.get("url"))
    domain = _compact_text(result.get("domain"))
    if not domain:
        parsed = urlparse(url)
        domain = _compact_text(parsed.netloc)
    if not title:
        raise ValueError("missing_title")
    if not url:
        raise ValueError("missing_url")
    if not domain:
        raise ValueError("missing_domain")

    source_class = _infer_source_class(result, query_family)
    blocked = source_class == "blocked_private_or_hidden_source" or _result_has_unsafe_markers(result)
    if blocked:
        source_class = "blocked_private_or_hidden_source"

    authority_level = _infer_authority_level(source_class)
    evidence_role = _infer_evidence_role(source_class)
    freshness_status = _infer_freshness_status(result.get("published_date"))
    if source_class == "blocked_private_or_hidden_source":
        freshness_status = freshness_status if freshness_status != "unknown" else "unknown"
    score = result.get("score")
    try:
        score_value = float(score) if score is not None else None
    except (TypeError, ValueError):
        score_value = None
    relevance_reason = _bounded_reason(title, result.get("snippet"))
    if source_class == "github_repository":
        relevance_reason = (relevance_reason + " GitHub is implementation evidence only, not official science evidence alone.")[:220]
    if source_class == "blocked_private_or_hidden_source":
        relevance_reason = "Blocked by safety."
        title = "Blocked source locator record"
        url = "blocked://source"
        domain = "blocked.local"

    record = build_mlcf_metadata_only_source_locator_record_v1(
        locator_id=f"searxng_locator_{sha256(f'{query_used}|{title}|{url}|{domain}'.encode('utf-8')).hexdigest()[:16]}",
        science_direction_id=science_direction_id,
        query_family=query_family,
        source_class=source_class,
        candidate_title=title,
        candidate_url_or_identifier=url,
        candidate_domain=domain,
        authority_level_guess=authority_level,
        evidence_role_guess=evidence_role,
        relevance_reason=relevance_reason,
        freshness_status=freshness_status,
        access_license_status=_access_license_status_for_source(blocked),
        privacy_status=_privacy_status_for_source(source_class, blocked),
        operator_review_need=(
            "Operator review required before any source access."
            if not blocked
            else "Operator review required; source is blocked by safety."
        ),
        allowed_next_step="blocked_by_safety" if blocked else "operator_review",
        blocked_conditions=_blocked_conditions_for_result(
            source_class,
            "sensitive metadata blocked by safety" if blocked else None,
        ),
        authority_status={
            **_default_authority_status(),
            "source_fetching_authorized": False,
            "source_summary_authorized": False,
            "status": "metadata_only_locator_record",
            "boundary_notes": "metadata-only SearXNG result converted into a locator record",
        },
        safe_metadata={
            **_default_safe_metadata(),
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
            "source_fetching_authority": False,
            "source_summary_authority": False,
            "public_claim_authorized": False,
            "final_answer_authority": False,
            "discovery_claim_authorized": False,
            "proof_claim_authorized": False,
            "agi_claim_authorized": False,
            "benchmark_claim_authorized": False,
            "public_science_claim_authorized": False,
        },
    )

    # Keep a couple of useful metadata hints on the record without broadening authority.
    record["candidate_domain"] = domain
    record["candidate_title"] = title
    record["candidate_url_or_identifier"] = url
    record["relevance_reason"] = relevance_reason
    record["freshness_status"] = freshness_status
    record["access_license_status"] = _access_license_status_for_source(blocked)
    record["privacy_status"] = _privacy_status_for_source(source_class, blocked)
    record["operator_review_need"] = (
        "Operator review required before any source access."
        if not blocked
        else "Operator review required; source is blocked by safety."
    )
    record["allowed_next_step"] = "blocked_by_safety" if blocked else "operator_review"
    return record


def _empty_distribution() -> dict[str, int]:
    return {}


def _count_distribution(values: list[str]) -> dict[str, int]:
    return dict(Counter(values))


def _classify_result(
    result: Any,
    *,
    science_direction_id: str,
    science_direction_summary: str,
    query_used: str,
    query_family: str,
) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    if not isinstance(result, Mapping):
        blocked_entry = {
            "result_status": "invalid",
            "blocked_conditions": ["invalid_result_type"],
            "reason": "Result must be a metadata mapping.",
        }
        return "invalid", None, blocked_entry

    unsupported = _unsupported_input_fields(result)
    if unsupported:
        blocked_entry = {
            "result_status": "rejected",
            "blocked_conditions": ["unsupported_input_fields:" + ",".join(sorted(unsupported))],
            "candidate_title": _compact_text(result.get("title")),
            "candidate_url_or_identifier": _compact_text(result.get("url")),
            "candidate_domain": _compact_text(result.get("domain")),
            "query_family": _compact_text(result.get("query_family"), query_family),
            "reason": "Unsupported raw-content or non-metadata fields present.",
        }
        return "rejected", None, blocked_entry

    try:
        record = build_mlcf_locator_record_from_searxng_result_v1(
            result,
            science_direction_id=science_direction_id,
            science_direction_summary=science_direction_summary,
            query_used=query_used,
            query_family=_compact_text(result.get("query_family"), query_family),
        )
    except ValueError as exc:
        blocked_entry = {
            "result_status": "rejected",
            "blocked_conditions": [str(exc)],
            "candidate_title": _compact_text(result.get("title")),
            "candidate_url_or_identifier": _compact_text(result.get("url")),
            "candidate_domain": _compact_text(result.get("domain")),
            "query_family": _compact_text(result.get("query_family"), query_family),
            "reason": "Could not convert result into a locator record.",
        }
        return "rejected", None, blocked_entry

    validation = validate_mlcf_metadata_only_source_locator_record_v1(record)
    if validation["blocked"]:
        blocked_entry = {
            "result_status": "blocked",
            "blocked_conditions": list(validation.get("blocked_labels", [])),
            "candidate_title": record.get("candidate_title", ""),
            "candidate_url_or_identifier": record.get("candidate_url_or_identifier", ""),
            "candidate_domain": record.get("candidate_domain", ""),
            "query_family": record.get("query_family", query_family),
            "reason": "Blocked locator record.",
        }
        return "blocked", record, blocked_entry

    return "accepted", record, None


def _default_packet() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "adapter_packet_id": "default_searxng_adapter_packet",
        "science_direction_id": "default_science_direction",
        "science_direction_summary": "Metadata-only SearXNG adapter packet.",
        "query_used": "",
        "query_family": "",
        "searxng_results_input_count": 0,
        "locator_records": [],
        "rejected_results": [],
        "blocked_results": [],
        "source_class_distribution": {},
        "authority_guess_distribution": {},
        "operator_review_need": "Operator review required before any source access.",
        "allowed_next_step": "operator_review",
        "blocked_conditions": ["metadata-only adapter boundary"],
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(),
    }


def build_mlcf_searxng_source_locator_adapter_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    packet = _default_packet()
    packet.update(_merge_payload(payload, **overrides))
    packet_results = packet.pop("searxng_results", packet.pop("results", None))
    if packet_results is None:
        packet_results = []
    packet["locator_records"] = []
    packet["rejected_results"] = []
    packet["blocked_results"] = []

    science_direction_id = _compact_text(packet.get("science_direction_id"))
    science_direction_summary = _compact_text(packet.get("science_direction_summary"))
    query_used = _compact_text(packet.get("query_used"))
    query_family = _compact_text(packet.get("query_family"))

    if isinstance(packet_results, list):
        results_iterable = packet_results
    elif isinstance(packet_results, tuple):
        results_iterable = list(packet_results)
    else:
        results_iterable = [packet_results]

    locator_classes: list[str] = []
    authority_guesses: list[str] = []
    blocked_conditions: list[str] = []
    had_blocked_or_rejected = False

    for result in results_iterable:
        status, record, blocked_entry = _classify_result(
            result,
            science_direction_id=science_direction_id,
            science_direction_summary=science_direction_summary,
            query_used=query_used,
            query_family=query_family,
        )
        if status == "accepted" and record is not None:
            packet["locator_records"].append(record)
            locator_classes.append(_compact_text(record.get("source_class")))
            authority_guesses.append(_compact_text(record.get("authority_level_guess")))
        elif status == "blocked" and record is not None:
            packet["locator_records"].append(record)
            locator_classes.append(_compact_text(record.get("source_class")))
            authority_guesses.append(_compact_text(record.get("authority_level_guess")))
            if blocked_entry is not None:
                packet["blocked_results"].append(blocked_entry)
                blocked_conditions.extend(_normalize_text_list(blocked_entry.get("blocked_conditions")))
            had_blocked_or_rejected = True
        else:
            if blocked_entry is not None:
                packet["rejected_results"].append(blocked_entry)
                blocked_conditions.extend(_normalize_text_list(blocked_entry.get("blocked_conditions")))
            had_blocked_or_rejected = True

    packet["searxng_results_input_count"] = len(results_iterable)
    packet["source_class_distribution"] = _count_distribution(locator_classes)
    packet["authority_guess_distribution"] = _count_distribution(authority_guesses)

    if had_blocked_or_rejected:
        blocked_conditions.append("one or more results were rejected or blocked")
    packet["blocked_conditions"] = list(dict.fromkeys(blocked_conditions or ["metadata-only adapter boundary"]))
    any_blocked_locator = any(
        isinstance(record, Mapping) and _compact_text(record.get("allowed_next_step")) == "blocked_by_safety"
        for record in packet["locator_records"]
    )
    packet["allowed_next_step"] = "blocked_by_safety" if had_blocked_or_rejected or any_blocked_locator else "operator_review"
    packet["operator_review_need"] = (
        "Operator review required before any source access."
        if packet["allowed_next_step"] == "operator_review"
        else "Operator review required; one or more results were blocked by safety."
    )
    return packet


def validate_mlcf_searxng_source_locator_adapter_packet_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_packet_type"],
            "validation_posture": "blocked",
            "summary_text": "Invalid metadata-only SearXNG adapter packet.",
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
            "summary_text": "Missing required adapter packet fields.",
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

    if _compact_text(packet.get("query_used")) == "":
        labels.append("missing_query_used")
    if _compact_text(packet.get("query_family")) == "":
        labels.append("missing_query_family")
    if _compact_text(packet.get("science_direction_id")) == "":
        labels.append("missing_science_direction_id")
    if _compact_text(packet.get("science_direction_summary")) == "":
        labels.append("missing_science_direction_summary")
    if _compact_text(packet.get("adapter_packet_id")) == "":
        labels.append("missing_adapter_packet_id")

    authority_status = packet.get("authority_status")
    if not isinstance(authority_status, Mapping):
        labels.append("invalid_authority_status")
    else:
        for flag in _AUTHORITY_FALSE_FLAGS_V1:
            if flag not in authority_status:
                labels.append(f"missing_authority_status_{flag}")
            elif authority_status[flag] is not False:
                labels.append(f"unsafe_authority_flag:{flag}")
        if authority_status.get("all_authority_flags_false") is not True:
            labels.append("unsafe_authority_flags")
        if _compact_text(authority_status.get("status")) != "metadata_only_adapter_boundary":
            labels.append("unsafe_authority_status")
        notes = _compact_text(authority_status.get("boundary_notes"))
        if not notes:
            labels.append("missing_authority_status_boundary_notes")
        elif _contains_any_marker(notes, _AUTHORITY_TEXT_MARKERS_V1):
            labels.append("unsafe_authority_text")

    safe_metadata = packet.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        labels.append("invalid_safe_metadata")
    else:
        for flag in _SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1:
            if safe_metadata.get(flag) is not True:
                labels.append(f"unsafe_safe_metadata_flag:{flag}")
        # Required false flags must remain false if present.
        false_flags = (
            "source_ingestion_authorized",
            "raw_retention_authorized",
            "web_call_authority",
            "github_call_authority",
            "searxng_call_authority",
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
        for flag in false_flags:
            if flag in safe_metadata and safe_metadata[flag] is not False:
                labels.append(f"unsafe_safe_metadata_flag:{flag}")
        if _contains_forbidden_markers(safe_metadata, _AUTHORITY_TEXT_MARKERS_V1):
            labels.append("unsafe_authority_text")
        if _contains_forbidden_markers(safe_metadata, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            labels.append("unsafe_hidden_private_protected_marker")

    packet_text_fields = {
        "science_direction_id": packet.get("science_direction_id"),
        "science_direction_summary": packet.get("science_direction_summary"),
        "query_used": packet.get("query_used"),
        "query_family": packet.get("query_family"),
        "operator_review_need": packet.get("operator_review_need"),
        "allowed_next_step": packet.get("allowed_next_step"),
        "blocked_conditions": packet.get("blocked_conditions"),
    }
    if _contains_forbidden_markers(packet_text_fields, ("raw page", "raw content", "full text", "downloaded content", "downloaded files")):
        labels.append("unsafe_raw_content_marker")
    if _contains_forbidden_markers(packet_text_fields, (".weslr",)):
        labels.append("unsafe_weslr_io_implication")
    if _contains_forbidden_markers(packet_text_fields, ("database write", "database writes", "database")):
        labels.append("unsafe_database_write_implication")
    if _contains_forbidden_markers(packet_text_fields, ("memory mutation", "project mutation")):
        labels.append("unsafe_memory_project_mutation_implication")
    if _contains_forbidden_markers(packet_text_fields, ("behavior pack", "behavior-pack", "promotion")):
        labels.append("unsafe_behavior_pack_promotion_implication")
    if _contains_forbidden_markers(packet_text_fields, _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_claim_language")
    if _contains_forbidden_markers(packet_text_fields, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("unsafe_hidden_private_protected_marker")

    records = packet.get("locator_records", [])
    if isinstance(records, list):
        for record in records:
            validation = validate_mlcf_metadata_only_source_locator_record_v1(record)
            if validation["blocked"]:
                labels.extend(validation.get("blocked_labels", []))
            # GitHub locator must remain implementation evidence only.
            if isinstance(record, Mapping) and _compact_text(record.get("source_class")) == "github_repository":
                if _compact_text(record.get("authority_level_guess")) != "implementation_evidence":
                    labels.append("github_locator_claims_official_science_authority")
            if isinstance(record, Mapping) and _compact_text(record.get("source_class")) == "blocked_private_or_hidden_source":
                if _compact_text(record.get("allowed_next_step")) != "blocked_by_safety":
                    labels.append("blocked_private_or_hidden_source_bad_next_step")

    blocked_results = packet.get("blocked_results", [])
    rejected_results = packet.get("rejected_results", [])
    for result_list, list_label in ((blocked_results, "blocked_results"), (rejected_results, "rejected_results")):
        if not isinstance(result_list, list):
            labels.append(f"invalid_{list_label}")
            continue
        for item in result_list:
            if not isinstance(item, Mapping):
                labels.append(f"invalid_{list_label}")
                continue
            if _first_non_json_safe_path(item) is not None:
                labels.append(f"non_json_safe_{list_label}")
            if _contains_forbidden_markers(item, _AUTHORITY_TEXT_MARKERS_V1):
                labels.append("unsafe_claim_language")
            if _contains_forbidden_markers(item, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
                labels.append("unsafe_hidden_private_protected_marker")

    dist = packet.get("source_class_distribution")
    if isinstance(dist, Mapping):
        for key, value in dist.items():
            if _compact_text(key) not in allowed_mlcf_locator_source_classes_v1():
                labels.append("invalid_source_class")
            if not isinstance(value, int) or value < 0:
                labels.append("invalid_source_class_distribution")
    auth_dist = packet.get("authority_guess_distribution")
    if isinstance(auth_dist, Mapping):
        for key, value in auth_dist.items():
            if _compact_text(key) not in allowed_mlcf_locator_authority_levels_v1():
                labels.append("invalid_authority_level")
            if not isinstance(value, int) or value < 0:
                labels.append("invalid_authority_guess_distribution")

    if _compact_text(packet.get("allowed_next_step")) not in allowed_mlcf_locator_next_steps_v1():
        labels.append("invalid_allowed_next_step")

    if _first_non_json_safe_path(packet) is not None:
        labels.append("non_json_safe_output")

    labels = list(dict.fromkeys(labels))
    if labels:
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": labels,
            "validation_posture": "blocked",
            "summary_text": "Blocked metadata-only SearXNG adapter packet.",
        }
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
        "validation_posture": "valid",
        "summary_text": "Valid metadata-only SearXNG adapter packet.",
    }


def summarize_mlcf_searxng_source_locator_adapter_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    data = packet if isinstance(packet, Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "adapter_packet_id": _compact_text(data.get("adapter_packet_id")),
        "science_direction_id": _compact_text(data.get("science_direction_id")),
        "query_used": _compact_text(data.get("query_used")),
        "query_family": _compact_text(data.get("query_family")),
        "searxng_results_input_count": int(data.get("searxng_results_input_count") or 0),
        "locator_record_count": len(data.get("locator_records", [])) if isinstance(data.get("locator_records"), list) else 0,
        "blocked_result_count": len(data.get("blocked_results", [])) if isinstance(data.get("blocked_results"), list) else 0,
        "rejected_result_count": len(data.get("rejected_results", [])) if isinstance(data.get("rejected_results"), list) else 0,
        "allowed_next_step": _compact_text(data.get("allowed_next_step")),
        "validation_posture": validation.get("validation_posture", "blocked"),
        "summary_text": _compact_text(data.get("science_direction_summary"), "Metadata-only SearXNG adapter packet.")[:220],
    }


def to_mlcf_searxng_source_locator_adapter_packet_json_safe_v1(packet: Any) -> Any:
    return _json_safe(deepcopy(packet))


def _count_by_field(records: list[Mapping[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        if isinstance(record, Mapping):
            value = _compact_text(record.get(field))
            if value:
                counter[value] += 1
    return dict(counter)


def _build_example_packet(packet_id: str, query: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    packet = build_mlcf_searxng_source_locator_adapter_packet_v1(
        adapter_packet_id=packet_id,
        science_direction_id="sparse_rf_spatial_change_map_floorplan_scattering_v1",
        science_direction_summary="Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.",
        query_used=query,
        query_family="rf_material_floorplan_locator_family",
        searxng_results=results,
    )
    # Ensure distributions reflect the records present in the packet.
    packet["source_class_distribution"] = _count_by_field(packet["locator_records"], "source_class")
    packet["authority_guess_distribution"] = _count_by_field(packet["locator_records"], "authority_level_guess")
    return packet


def build_initial_mlcf_searxng_source_locator_adapter_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []

    examples.append(
        _build_example_packet(
            "searxng_rf_wifi_standard_result_packet",
            "official WiFi RF standards indoor propagation floor-plan sensing",
            [
                {
                    "title": "IEEE 802.11 sensing standard overview",
                    "url": "https://example.invalid/standards/ieee-80211-sensing",
                    "domain": "example.invalid",
                    "snippet": "Official standard-style metadata for WiFi sensing.",
                    "engine": "searxng",
                    "published_date": "2024-01-01",
                    "score": 0.97,
                    "source_class_hint": "official_standard",
                    "query_family": "official WiFi / RF standards",
                }
            ],
        )
    )

    examples.append(
        _build_example_packet(
            "searxng_rf_public_paper_result_packet",
            "CSI-based motion detection RF multipath indoor mapping",
            [
                {
                    "title": "CSI-based motion detection for indoor RF sensing",
                    "url": "https://example.invalid/papers/csi-motion-detection",
                    "domain": "example.invalid",
                    "snippet": "Public-paper metadata for prior-art RF sensing work.",
                    "engine": "searxng",
                    "published_date": "2023-05-12",
                    "score": 0.92,
                    "source_class_hint": "public_research_paper",
                    "query_family": "CSI-based motion detection papers",
                }
            ],
        )
    )

    examples.append(
        _build_example_packet(
            "searxng_wifi_sensing_github_result_packet",
            "GitHub WiFi sensing CSI processing repo",
            [
                {
                    "title": "WiFi sensing GitHub repository",
                    "url": "https://github.com/example/wifi-sensing",
                    "domain": "github.com",
                    "snippet": "Implementation repository for CSI processing.",
                    "engine": "searxng",
                    "published_date": "2024-09-01",
                    "score": 0.91,
                    "source_class_hint": "github_repository",
                    "query_family": "public GitHub implementations of WiFi sensing or CSI processing",
                }
            ],
        )
    )

    examples.append(
        _build_example_packet(
            "searxng_private_hidden_result_blocked_packet",
            "sensitive locator query",
            [
                {
                    "title": "Private hidden result",
                    "url": "https://example.invalid/private/hidden",
                    "domain": "example.invalid",
                    "snippet": "credential gated private hidden result",
                    "engine": "searxng",
                    "published_date": "2025-01-01",
                    "score": 0.1,
                    "source_class_hint": "blocked_private_or_hidden_source",
                    "query_family": "blocked sensitive result family",
                }
            ],
        )
    )

    return examples
