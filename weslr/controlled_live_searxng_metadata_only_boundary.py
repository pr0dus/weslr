from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from hashlib import sha256
from ipaddress import ip_address
from typing import Any, Callable, Mapping

SCHEMA_VERSION_V1 = "weslr_controlled_live_searxng_metadata_only_boundary_v1"
DEFAULT_URL_V1 = "http://127.0.0.1:8888"
DEFAULT_TIMEOUT_SECONDS_V1 = 5
DEFAULT_MAX_RESULTS_V1 = 5
DEFAULT_QUERY_FAMILY_V1 = "general"
DEFAULT_OPERATOR_ROLE_V1 = "owner"
ALLOWED_QUERY_FAMILIES_V1 = ("general", "standard", "rfc", "isbn", "paper-id", "domain-glossary")
ALLOWED_OPERATOR_ROLES_V1 = ("owner", "maintainer", "metadata-locator-runner")
ALLOWED_RESULT_FIELDS_V1 = (
    "query",
    "title",
    "url",
    "domain",
    "source_engine",
    "engines",
    "rank",
    "score",
    "published_date",
    "snippet",
    "source_class_hint",
    "authority_guess",
    "evidence_role_guess",
    "relevance_reason",
    "freshness_status_guess",
    "access_license_status_guess",
    "privacy_status_guess",
    "blocked_status",
    "locator_id",
)
BLOCKED_RESULT_FIELDS_V1 = ("url", "title", "block_reason")
TRACKING_DOMAINS_V1 = {
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "facebook.net",
    "scorecardresearch.com",
    "quantserve.com",
    "hotjar.com",
    "mixpanel.com",
    "segment.io",
    "amplitude.com",
}
PERSONAL_DATA_DOMAINS_V1 = {
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "quora.com",
}
OPEN_ACCESS_DOMAINS_V1 = {
    "arxiv.org",
    "github.com",
    "doi.org",
    "pubmed.ncbi.nlm.nih.gov",
    "europepmc.org",
}
PAYWALLED_DOMAINS_V1 = {
    "nature.com",
    "sciencedirect.com",
    "ieee.org",
    "acm.org",
}
OFFICIAL_STANDARD_MARKERS_V1 = ("standard", "spec", "specification", "ietf", "ieee", "rfc", "3gpp", "wifi alliance")
VENDOR_DOC_MARKERS_V1 = ("docs", "documentation", "developer", "manual", "support", "api")
LAB_MARKERS_V1 = (".edu", "university", "lab", "research group", "thesis")
PAPER_MARKERS_V1 = ("paper", "preprint", "arxiv", "doi", "journal", "conference", "proceedings")
DATASET_MARKERS_V1 = ("dataset", "data")
BLOCKED_URL_PATTERNS_V1 = (
    re.compile(r"(^|[/?#])(login|signin|sign-in|signup|sign-up|account|auth|sso|oauth|captcha)([/?#]|$)", re.I),
)
CREDENTIAL_URL_PATTERN_V1 = re.compile(r"(?:[?&](?:token|session|auth|key|api_key|password)=)", re.I)
EMAIL_PATTERN_V1 = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_PATTERN_V1 = re.compile(r"\+?\d[\d\s().-]{7,}\d")
IPV4_PATTERN_V1 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HTML_TAG_PATTERN_V1 = re.compile(r"<[^>]+>")
HTML_ENTITY_PATTERN_V1 = re.compile(r"&[A-Za-z#0-9]+;")
CONTROL_CHAR_PATTERN_V1 = re.compile(r"[\x00-\x1f\x7f]")
URL_QUERY_PATTERN_V1 = re.compile(r"^(?:https?|ftp|file|data|javascript):", re.I)
SNIPPET_BLOCK_MARKERS_V1 = ("login", "password", "sign in", "subscribe", "pay", "cookie", "gdpr")
AUTHORITY_FALSE_FLAGS_V1 = (
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
    "database_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "cross_user_leakage_authorized",
    "hidden_private_protected_authorized",
)

HttpGetterV1 = Callable[[str, int], Mapping[str, Any]]
_SELF_ABORTED_V1 = False


def boundary_self_abort() -> None:
    global _SELF_ABORTED_V1
    _SELF_ABORTED_V1 = True


def reset_boundary_self_abort_v1() -> None:
    global _SELF_ABORTED_V1
    _SELF_ABORTED_V1 = False


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


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


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _normalize_base_url(url: str) -> str:
    return _compact_text(url, DEFAULT_URL_V1).rstrip("/")


def _is_loopback_host(host: str) -> bool:
    lowered = _compact_text(host).lower()
    if lowered in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ip_address(lowered).is_loopback
    except ValueError:
        return False


def build_controlled_live_searxng_boundary_config_v1(**overrides: Any) -> dict[str, Any]:
    config = {
        "boundary_id": SCHEMA_VERSION_V1,
        "enabled": _bool_env("WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED", False),
        "base_url": _normalize_base_url(os.environ.get("WESLR_SEARXNG_URL", DEFAULT_URL_V1)),
        "timeout_seconds": min(max(_int_env("WESLR_SEARXNG_LIVE_BOUNDARY_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS_V1), 1), DEFAULT_TIMEOUT_SECONDS_V1),
        "max_results": min(max(_int_env("WESLR_SEARXNG_LIVE_BOUNDARY_MAX_RESULTS", DEFAULT_MAX_RESULTS_V1), 1), DEFAULT_MAX_RESULTS_V1),
        "snippet_policy": _compact_text(os.environ.get("WESLR_SEARXNG_LIVE_BOUNDARY_SNIPPET_POLICY", "disabled"), "disabled").lower(),
        "query_family": _compact_text(os.environ.get("WESLR_SEARXNG_LIVE_BOUNDARY_QUERY_FAMILY", DEFAULT_QUERY_FAMILY_V1), DEFAULT_QUERY_FAMILY_V1),
        "operator_role": _compact_text(os.environ.get("WESLR_SEARXNG_LIVE_BOUNDARY_OPERATOR_ROLE", DEFAULT_OPERATOR_ROLE_V1), DEFAULT_OPERATOR_ROLE_V1),
        "allow_live_http_without_injected_getter": False,
    }
    for key, value in overrides.items():
        if value is not None:
            config[key] = value
    config["base_url"] = _normalize_base_url(config.get("base_url", DEFAULT_URL_V1))
    config["timeout_seconds"] = min(max(int(config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS_V1)), 1), DEFAULT_TIMEOUT_SECONDS_V1)
    config["max_results"] = min(max(int(config.get("max_results", DEFAULT_MAX_RESULTS_V1)), 1), DEFAULT_MAX_RESULTS_V1)
    config["snippet_policy"] = _compact_text(config.get("snippet_policy"), "disabled").lower()
    config["query_family"] = _compact_text(config.get("query_family"), DEFAULT_QUERY_FAMILY_V1)
    config["operator_role"] = _compact_text(config.get("operator_role"), DEFAULT_OPERATOR_ROLE_V1)
    config["enabled"] = bool(config.get("enabled", False))
    config["allow_live_http_without_injected_getter"] = bool(config.get("allow_live_http_without_injected_getter", False))
    return config


def validate_controlled_live_searxng_boundary_config_v1(config: Mapping[str, Any] | None) -> dict[str, Any]:
    errors: list[str] = []
    candidate = build_controlled_live_searxng_boundary_config_v1(**dict(config or {}))
    parsed = urllib.parse.urlparse(candidate["base_url"])
    if parsed.scheme != "http":
        errors.append("non_http_scheme")
    if parsed.path not in {"", "/"}:
        errors.append("base_url_has_path")
    if not parsed.hostname:
        errors.append("missing_hostname")
    elif not _is_loopback_host(parsed.hostname):
        errors.append("non_loopback_host")
    if candidate["snippet_policy"] not in {"disabled", "enabled"}:
        errors.append("invalid_snippet_policy")
    if candidate["query_family"] not in ALLOWED_QUERY_FAMILIES_V1:
        errors.append("invalid_query_family")
    if candidate["operator_role"] not in ALLOWED_OPERATOR_ROLES_V1:
        errors.append("invalid_operator_role")
    return {
        "valid": not errors,
        "errors": errors,
        "config": candidate,
    }


def build_controlled_live_searxng_query_v1(query: Any, **overrides: Any) -> dict[str, Any]:
    packet = {
        "query": _compact_text(query),
        "query_family": DEFAULT_QUERY_FAMILY_V1,
        "operator_role": DEFAULT_OPERATOR_ROLE_V1,
    }
    for key, value in overrides.items():
        if value is not None:
            packet[key] = value
    packet["query"] = _compact_text(packet.get("query"))
    packet["query_family"] = _compact_text(packet.get("query_family"), DEFAULT_QUERY_FAMILY_V1)
    packet["operator_role"] = _compact_text(packet.get("operator_role"), DEFAULT_OPERATOR_ROLE_V1)
    return packet


def validate_controlled_live_searxng_query_v1(query_packet: Mapping[str, Any] | None) -> dict[str, Any]:
    packet = build_controlled_live_searxng_query_v1(**dict(query_packet or {})) if query_packet is not None and "query" in query_packet else build_controlled_live_searxng_query_v1((query_packet or {}).get("query") if isinstance(query_packet, Mapping) else query_packet)
    query = packet["query"]
    errors: list[str] = []
    if not query:
        errors.append("empty_query")
    encoded = urllib.parse.quote(query, safe="")
    if len(encoded.encode("utf-8")) > 200:
        errors.append("query_too_long")
    if CONTROL_CHAR_PATTERN_V1.search(query):
        errors.append("control_chars_in_query")
    if URL_QUERY_PATTERN_V1.match(query):
        errors.append("url_as_query")
    if packet["query_family"] not in ALLOWED_QUERY_FAMILIES_V1:
        errors.append("invalid_query_family")
    if packet["operator_role"] not in ALLOWED_OPERATOR_ROLES_V1:
        errors.append("invalid_operator_role")
    return {"valid": not errors, "errors": errors, "query": packet}


def build_controlled_live_searxng_request_url_v1(query_packet: Mapping[str, Any], config: Mapping[str, Any]) -> str:
    base_url = _normalize_base_url(config.get("base_url", DEFAULT_URL_V1))
    encoded_query = urllib.parse.quote(_compact_text(query_packet.get("query")), safe="")
    params = urllib.parse.urlencode({"q": encoded_query, "format": "json", "language": "en"})
    return f"{base_url}/search?{params}"


def _default_http_getter(url: str, timeout_seconds: int) -> Mapping[str, Any]:
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return {
            "status": int(getattr(response, "status", response.getcode())),
            "headers": dict(response.headers.items()),
            "body": response.read(),
            "url": getattr(response, "url", url),
        }


def _blocked_packet(url: str, title: str, reason: str) -> dict[str, str]:
    return {"url": _compact_text(url), "title": _compact_text(title), "block_reason": reason}


def _normalize_engines(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [_compact_text(item)[:100] for item in raw if _compact_text(item)][:10]
    text = _compact_text(raw)
    return [text[:100]] if text else []


def _parse_domain(url: str) -> str:
    try:
        return _compact_text(urllib.parse.urlparse(url).netloc).lower()
    except Exception:
        return ""


def _sanitize_snippet(snippet: Any, enabled: bool) -> tuple[str | None, bool]:
    if not enabled:
        return None, False
    text = _compact_text(snippet)
    text = HTML_TAG_PATTERN_V1.sub("", text)
    text = HTML_ENTITY_PATTERN_V1.sub("", text)
    text = text.replace("javascript:", "").replace("data:", "")
    lowered = text.lower()
    if (
        not text
        or EMAIL_PATTERN_V1.search(text)
        or PHONE_PATTERN_V1.search(text)
        or IPV4_PATTERN_V1.search(text)
        or any(marker in lowered for marker in SNIPPET_BLOCK_MARKERS_V1)
    ):
        return None, True
    return text[:280], True


def _derive_source_class(title: str, domain: str, url: str) -> str:
    combined = f"{title} {domain} {url}".lower()
    if domain.endswith(".gov") or any(marker in combined for marker in ("government", "agency", ".mil")):
        return "official_government_or_agency_data"
    if domain == "github.com" or domain.endswith(".github.com"):
        return "github_repository"
    if any(marker in combined for marker in OFFICIAL_STANDARD_MARKERS_V1):
        return "official_standard"
    if any(marker in combined for marker in VENDOR_DOC_MARKERS_V1):
        return "official_vendor_documentation"
    if any(marker in combined for marker in DATASET_MARKERS_V1):
        return "public_dataset"
    if any(marker in combined for marker in PAPER_MARKERS_V1):
        return "public_research_paper"
    if any(marker in combined for marker in LAB_MARKERS_V1):
        return "public_lab_or_university_artifact"
    return "unknown_authority"


def _derive_authority_guess(source_class_hint: str) -> str:
    mapping = {
        "official_standard": "official_primary",
        "official_government_or_agency_data": "official_primary",
        "official_vendor_documentation": "official_primary",
        "public_dataset": "public_primary",
        "public_research_paper": "public_primary",
        "github_repository": "community_signal",
        "public_lab_or_university_artifact": "public_secondary",
        "unknown_authority": "unknown_authority",
    }
    return mapping.get(source_class_hint, "unknown_authority")


def _derive_evidence_role_guess(query_family: str) -> str:
    if query_family in {"standard", "rfc", "isbn", "paper-id"}:
        return "prior_art"
    return "candidate_signal"


def _derive_freshness_status(published_date: Any) -> str:
    text = _compact_text(published_date)
    if not text:
        return "unknown"
    cleaned = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned) if not cleaned.isdigit() else datetime(int(cleaned), 1, 1, tzinfo=timezone.utc)
    except ValueError:
        return "unknown"
    now = datetime.now(timezone.utc)
    if parsed > now:
        return "unknown"
    age_days = (now - parsed).days
    if age_days <= 365:
        return "fresh"
    if age_days <= 365 * 3:
        return "recent"
    return "stale"


def _derive_access_license_status(domain: str, url: str) -> str:
    lowered_url = url.lower()
    if any(marker in lowered_url for marker in ("login", "signin", "account")):
        return "registration_required"
    if domain in OPEN_ACCESS_DOMAINS_V1 or domain.endswith(".gov"):
        return "open_access"
    if any(domain == item or domain.endswith(f".{item}") for item in PAYWALLED_DOMAINS_V1):
        return "paywalled"
    return "unknown"


def _derive_privacy_status(domain: str, snippet: str | None) -> str:
    lowered_domain = domain.lower()
    if any(lowered_domain == item or lowered_domain.endswith(f".{item}") for item in PERSONAL_DATA_DOMAINS_V1):
        return "mixed_personal_signals"
    if snippet and (EMAIL_PATTERN_V1.search(snippet) or "linkedin.com/in/" in snippet.lower()):
        return "personal_data_present"
    return "public_non_personal"


def _detect_block_reason(url: str, title: str, domain: str) -> str | None:
    lowered_url = url.lower()
    lowered_domain = domain.lower()
    if not domain:
        return "unparseable_domain"
    if CREDENTIAL_URL_PATTERN_V1.search(url):
        return "credential_in_url"
    if len(url.encode("utf-8")) > 2000:
        return "url_too_long"
    if not _is_loopback_host(domain) and (domain.startswith("127.") or domain.startswith("10.") or domain.startswith("192.168.") or domain.startswith("172.16.") or domain.endswith(".local") or domain.endswith(".onion") or domain == "0.0.0.0"):
        return "private_or_loopback_target"
    if any(domain == item or domain.endswith(f".{item}") for item in TRACKING_DOMAINS_V1):
        return "tracking_or_analytics_only"
    if any(domain == item or domain.endswith(f".{item}") for item in PERSONAL_DATA_DOMAINS_V1):
        return "personal_data_platform"
    if any(pattern.search(lowered_url) for pattern in BLOCKED_URL_PATTERNS_V1):
        return "login_or_account_url"
    if not _compact_text(title):
        return "empty_title"
    if len(_compact_text(title).encode("utf-8")) > 500:
        return "title_too_long"
    return None


def _result_from_raw(raw: Mapping[str, Any], query_packet: Mapping[str, Any], index: int, snippet_enabled: bool) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    title = _compact_text(raw.get("title"))[:500]
    url = _compact_text(raw.get("url"))[:2000]
    domain = _parse_domain(url)
    block_reason = _detect_block_reason(url, title, domain)
    snippet, _snippet_policy_applied = _sanitize_snippet(raw.get("content") or raw.get("description"), snippet_enabled)
    if block_reason is not None:
        return None, _blocked_packet(url, title, block_reason)
    source_class_hint = _derive_source_class(title, domain, url)
    authority_guess = _derive_authority_guess(source_class_hint)
    result = {
        "query": _compact_text(query_packet.get("query"))[:500],
        "title": title,
        "url": url,
        "domain": domain[:255],
        "source_engine": _compact_text(raw.get("engine") or (raw.get("engines") or [None])[0])[:100] or None,
        "engines": _normalize_engines(raw.get("engines")),
        "rank": index,
        "score": None,
        "published_date": _compact_text(raw.get("publishedDate") or raw.get("published_date"))[:50] or None,
        "snippet": snippet,
        "source_class_hint": source_class_hint,
        "authority_guess": authority_guess,
        "evidence_role_guess": _derive_evidence_role_guess(_compact_text(query_packet.get("query_family"), DEFAULT_QUERY_FAMILY_V1)),
        "relevance_reason": "engine_match",
        "freshness_status_guess": _derive_freshness_status(raw.get("publishedDate") or raw.get("published_date")),
        "access_license_status_guess": _derive_access_license_status(domain, url),
        "privacy_status_guess": _derive_privacy_status(domain, snippet),
        "blocked_status": "allowed",
        "locator_id": sha256(f"{_compact_text(query_packet.get('query'))}|{url}|{index}".encode("utf-8")).hexdigest(),
    }
    score = raw.get("score")
    try:
        result["score"] = float(score) if score is not None else None
    except (TypeError, ValueError):
        result["score"] = None
    return result, None


def _empty_packet(query: str, config: Mapping[str, Any], reason: str, *, status: int | None = None, latency_ms: int | None = None) -> dict[str, Any]:
    authority_status = {flag: False for flag in AUTHORITY_FALSE_FLAGS_V1}
    authority_status["all_authority_flags_false"] = True
    return {
        "boundary_version": SCHEMA_VERSION_V1,
        "boundary_id": SCHEMA_VERSION_V1,
        "ok": False,
        "query": query,
        "reason": reason,
        "searxng_call_status": status,
        "searxng_call_latency_ms": latency_ms,
        "results_count_kept": 0,
        "results_count_blocked": 0,
        "results": [],
        "blocked": [],
        "evidence_status": "metadata_only_locator_candidates",
        "automatic_truth_write": False,
        "raw_content_retained": False,
        "snippets_retained": config.get("snippet_policy") == "enabled",
        "authority_verdict": "external_evidence_unverified",
        "authority_status": authority_status,
        "safe_status": {
            "metadata_only": True,
            "json_safe": True,
            "no_raw_content": True,
            "no_ingestion": True,
            "no_claims": True,
            "no_persistence": True,
            "no_runtime_integration": True,
            "no_public_integration": True,
            "no_mlcf_routing": True,
        },
    }


def run_controlled_live_searxng_metadata_only_boundary_v1(
    query: Any,
    *,
    config: Mapping[str, Any] | None = None,
    http_getter: HttpGetterV1 | None = None,
) -> dict[str, Any]:
    built_config = build_controlled_live_searxng_boundary_config_v1(**dict(config or {}))
    query_packet = build_controlled_live_searxng_query_v1(query, query_family=built_config.get("query_family"), operator_role=built_config.get("operator_role"))
    if _SELF_ABORTED_V1:
        return _empty_packet(query_packet["query"], built_config, "boundary_self_aborted")
    config_validation = validate_controlled_live_searxng_boundary_config_v1(built_config)
    if not config_validation["valid"]:
        return _empty_packet(query_packet["query"], built_config, config_validation["errors"][0])
    query_validation = validate_controlled_live_searxng_query_v1(query_packet)
    if not query_validation["valid"]:
        return _empty_packet(query_packet["query"], built_config, query_validation["errors"][0])
    if not built_config["enabled"]:
        return _empty_packet(query_packet["query"], built_config, "disabled")
    if http_getter is None and not built_config.get("allow_live_http_without_injected_getter", False):
        return _empty_packet(query_packet["query"], built_config, "http_getter_required")
    getter = http_getter or _default_http_getter
    url = build_controlled_live_searxng_request_url_v1(query_packet, built_config)
    start = time.monotonic()
    try:
        response = getter(url, int(built_config["timeout_seconds"]))
        latency_ms = int((time.monotonic() - start) * 1000)
    except TimeoutError:
        return _empty_packet(query_packet["query"], built_config, "searxng_timeout")
    except urllib.error.HTTPError as error:
        code = int(getattr(error, "code", 500))
        if 500 <= code:
            return _empty_packet(query_packet["query"], built_config, f"searxng_5xx_{code}", status=code)
        if 300 <= code < 400:
            return _empty_packet(query_packet["query"], built_config, "searxng_redirect_rejected", status=code)
        return _empty_packet(query_packet["query"], built_config, f"searxng_4xx_{code}", status=code)
    except urllib.error.URLError:
        return _empty_packet(query_packet["query"], built_config, "searxng_network_error")
    except Exception:
        return _empty_packet(query_packet["query"], built_config, "boundary_internal_error")

    status = int(response.get("status", 0) or 0)
    headers = {str(key).lower(): str(value) for key, value in dict(response.get("headers", {})).items()}
    if 300 <= status < 400:
        return _empty_packet(query_packet["query"], built_config, "searxng_redirect_rejected", status=status, latency_ms=latency_ms)
    if 500 <= status:
        return _empty_packet(query_packet["query"], built_config, f"searxng_5xx_{status}", status=status, latency_ms=latency_ms)
    if 400 <= status:
        return _empty_packet(query_packet["query"], built_config, f"searxng_4xx_{status}", status=status, latency_ms=latency_ms)
    content_type = headers.get("content-type", "")
    if "application/json" not in content_type.lower():
        return _empty_packet(query_packet["query"], built_config, "searxng_wrong_content_type", status=status, latency_ms=latency_ms)
    body = response.get("body", b"")
    try:
        payload = json.loads(body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else str(body))
    except Exception:
        return _empty_packet(query_packet["query"], built_config, "searxng_malformed_json", status=status, latency_ms=latency_ms)
    raw_results = payload.get("results") if isinstance(payload, Mapping) else None
    if not isinstance(raw_results, list):
        return _empty_packet(query_packet["query"], built_config, "searxng_results_incomplete", status=status, latency_ms=latency_ms)

    kept: list[dict[str, Any]] = []
    blocked: list[dict[str, str]] = []
    for idx, item in enumerate(raw_results[: max(len(raw_results), built_config["max_results"])]):
        if not isinstance(item, Mapping):
            continue
        result, blocked_item = _result_from_raw(item, query_packet, idx + 1, built_config["snippet_policy"] == "enabled")
        if blocked_item is not None:
            blocked.append(blocked_item)
            continue
        if result is not None:
            kept.append({key: result.get(key) for key in ALLOWED_RESULT_FIELDS_V1})
        if len(kept) >= built_config["max_results"]:
            break
    if len(raw_results) > built_config["max_results"]:
        for overflow in raw_results[built_config["max_results"]:]:
            if isinstance(overflow, Mapping):
                blocked.append(_blocked_packet(_compact_text(overflow.get("url")), _compact_text(overflow.get("title")), "result_cap_exceeded"))
    packet = _empty_packet(query_packet["query"], built_config, "ok" if kept else "no_results", status=status, latency_ms=latency_ms)
    packet["ok"] = bool(kept)
    packet["results"] = kept
    packet["blocked"] = blocked
    packet["results_count_kept"] = len(kept)
    packet["results_count_blocked"] = len(blocked)
    packet["reason"] = "ok" if kept else "no_results"
    return packet


def validate_controlled_live_searxng_metadata_only_result_packet_v1(packet: Mapping[str, Any] | None) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return {"valid": False, "errors": ["invalid_packet_type"], "blocked": True}
    for key in ("boundary_version", "query", "reason", "results", "blocked", "authority_status", "safe_status"):
        if key not in packet:
            errors.append(f"missing_{key}")
    if packet.get("boundary_version") != SCHEMA_VERSION_V1:
        errors.append("invalid_boundary_version")
    if any(packet.get("authority_status", {}).get(flag) is True for flag in AUTHORITY_FALSE_FLAGS_V1):
        errors.append("unsafe_authority_flag_true")
    results = packet.get("results", [])
    if not isinstance(results, list):
        errors.append("invalid_results_type")
    else:
        for index, item in enumerate(results):
            if not isinstance(item, Mapping):
                errors.append(f"invalid_result_type:{index}")
                continue
            extra = [key for key in item.keys() if key not in ALLOWED_RESULT_FIELDS_V1]
            if extra:
                errors.append(f"unexpected_result_fields:{index}")
            if item.get("blocked_status") != "allowed":
                errors.append(f"invalid_blocked_status:{index}")
    blocked = packet.get("blocked", [])
    if not isinstance(blocked, list):
        errors.append("invalid_blocked_type")
    else:
        for index, item in enumerate(blocked):
            if not isinstance(item, Mapping):
                errors.append(f"invalid_blocked_item:{index}")
                continue
            extra = [key for key in item.keys() if key not in BLOCKED_RESULT_FIELDS_V1]
            if extra:
                errors.append(f"unexpected_blocked_fields:{index}")
    return {"valid": not errors, "errors": errors, "blocked": bool(errors)}


def summarize_controlled_live_searxng_metadata_only_result_packet_v1(packet: Mapping[str, Any] | None) -> dict[str, Any]:
    validation = validate_controlled_live_searxng_metadata_only_result_packet_v1(packet)
    packet = dict(packet or {})
    return {
        "boundary_version": packet.get("boundary_version", SCHEMA_VERSION_V1),
        "query": _compact_text(packet.get("query"))[:120],
        "reason": _compact_text(packet.get("reason"), "invalid")[:80],
        "results_count_kept": int(packet.get("results_count_kept", 0) or 0),
        "results_count_blocked": int(packet.get("results_count_blocked", 0) or 0),
        "snippets_retained": bool(packet.get("snippets_retained", False)),
        "validation_posture": "valid" if validation["valid"] else "invalid",
        "summary_text": (
            f"{_compact_text(packet.get('reason'), 'invalid')} | kept={int(packet.get('results_count_kept', 0) or 0)}"
            f" blocked={int(packet.get('results_count_blocked', 0) or 0)}"
        )[:220],
    }


def to_controlled_live_searxng_metadata_only_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)
