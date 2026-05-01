"""
WESLR SearXNG Search Adapter V1

Disabled-by-default adapter for SearXNG web search.
Does NOT perform live searches in tests — all HTTP calls are mocked.

Authority: external_evidence_unverified — search results are evidence, not truth.
Automatic truth writes: disabled.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_SEARXNG_BASE_URL = "http://localhost:8888"
_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def _get_config() -> Dict[str, Any]:
    """Get cached config from environment. Cached to avoid repeated os.environ access."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = {
            "enabled": os.environ.get("WESLR_SEARXNG_ENABLED", "false").lower() in ("true", "1", "yes"),
            "base_url": os.environ.get("WESLR_SEARXNG_URL", DEFAULT_SEARXNG_BASE_URL).rstrip("/"),
        }
    return _CONFIG_CACHE


def is_searxng_enabled(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if SearXNG search is enabled.

    Default: False (disabled)

    Enable only with: WESLR_SEARXNG_ENABLED=true
    Override URL with: WESLR_SEARXNG_URL=http://custom:8888

    Returns:
        bool: True if enabled, False otherwise
    """
    if config is not None:
        return config.get("enabled", False)
    return _get_config()["enabled"]


def get_searxng_base_url(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the SearXNG base URL.

    Default: http://localhost:8888
    Override: WESLR_SEARXNG_URL environment variable

    Returns:
        str: The base URL for SearXNG
    """
    if config is not None:
        return config.get("base_url", DEFAULT_SEARXNG_BASE_URL).rstrip("/")
    return _get_config()["base_url"]


def build_search_url(query: str, base_url: Optional[str] = None) -> str:
    """
    Build a SearXNG search URL with JSON output.

    Args:
        query: The search query string
        base_url: Optional override for the base URL

    Returns:
        str: Full URL to fetch search results in JSON format
    """
    if base_url is None:
        base_url = get_searxng_base_url()
    encoded = urllib.parse.quote(query, safe="")
    return f"{base_url}/search?q={encoded}&format=json"


# ---------------------------------------------------------------------------
# Result normalization
# ---------------------------------------------------------------------------

_UNSAFE_FIELDS = frozenset([
    "cookies", "useragent", "user_id", "username", "ip", "闭合"
])


def _is_safe_field(key: str) -> bool:
    """Check if a field from a SearXNG result is safe to pass through."""
    key_lower = key.lower()
    for unsafe in _UNSAFE_FIELDS:
        if unsafe.lower() in key_lower:
            return False
    return True


def normalize_searxng_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a raw SearXNG result to a safe evidence packet.

    Removes:
    - cookies, user identifiers, IP addresses
    - raw HTML content
    - Any field flagged as unsafe

    Returns:
        {
            "record_type": "search_result_v1",
            "title": "...",
            "url": "...",
            "content": "...",
            "engines": [...],
            "score": float|null,
            "source": "searxng",
            "authority": "external_evidence_unverified"
        }
    """
    # Extract only safe fields
    title = str(raw.get("title", ""))[:500]
    url = str(raw.get("url", ""))[:2000]
    content = str(raw.get("content", ""))[:2000]

    # Sanitize content — remove any HTML tags if present
    import re
    content = re.sub(r"<[^>]+>", "", content).strip()

    engines = raw.get("engines", [])
    if isinstance(engines, list):
        engines = [str(e)[:100] for e in engines]
    else:
        engines = []

    score = raw.get("score")
    if score is not None:
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = None

    return {
        "record_type": "search_result_v1",
        "title": title,
        "url": url,
        "content": content,
        "engines": engines,
        "score": score,
        "source": "searxng",
        "authority": "external_evidence_unverified",
    }


# ---------------------------------------------------------------------------
# Core search function
# ---------------------------------------------------------------------------

def search_searxng(
    query: str,
    limit: int = 5,
    timeout_seconds: int = 5,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Perform a SearXNG search.

    Returns a structured response with normalized results.

    Returns:
        {
            "record_type": "searxng_search_response_v1",
            "query": "...",
            "enabled": bool,
            "ok": bool,
            "results": [...],
            "result_count": int,
            "authority": "external_evidence_unverified",
            "automatic_truth_write": False,
            "reason": "disabled|ok|timeout|error|invalid_query|validation_failed"
        }
    """
    # Check if enabled
    if not is_searxng_enabled(config):
        return {
            "record_type": "searxng_search_response_v1",
            "query": query,
            "enabled": False,
            "ok": False,
            "results": [],
            "result_count": 0,
            "authority": "external_evidence_unverified",
            "automatic_truth_write": False,
            "reason": "disabled",
        }

    # Validate query
    if not query or not query.strip():
        return {
            "record_type": "searxng_search_response_v1",
            "query": query,
            "enabled": True,
            "ok": False,
            "results": [],
            "result_count": 0,
            "authority": "external_evidence_unverified",
            "automatic_truth_write": False,
            "reason": "invalid_query",
        }

    # Validate limit
    if not isinstance(limit, int) or limit < 1:
        return {
            "record_type": "searxng_search_response_v1",
            "query": query,
            "enabled": True,
            "ok": False,
            "results": [],
            "result_count": 0,
            "authority": "external_evidence_unverified",
            "automatic_truth_write": False,
            "reason": "validation_failed",
        }

    # Build URL and perform request
    base_url = get_searxng_base_url(config)
    search_url = build_search_url(query, base_url)

    try:
        req = urllib.request.Request(
            search_url,
            headers={"Accept": "application/json", "User-Agent": "WESLR/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            raw_body = response.read()
            try:
                raw_results = json.loads(raw_body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {
                    "record_type": "searxng_search_response_v1",
                    "query": query,
                    "enabled": True,
                    "ok": False,
                    "results": [],
                    "result_count": 0,
                    "authority": "external_evidence_unverified",
                    "automatic_truth_write": False,
                    "reason": "invalid_query",  # malformed JSON from SearXNG
                }

    except urllib.error.URLError as e:
        return {
            "record_type": "searxng_search_response_v1",
            "query": query,
            "enabled": True,
            "ok": False,
            "results": [],
            "result_count": 0,
            "authority": "external_evidence_unverified",
            "automatic_truth_write": False,
            "reason": "error",
            "_error": str(e),
        }

    except TimeoutError:
        return {
            "record_type": "searxng_search_response_v1",
            "query": query,
            "enabled": True,
            "ok": False,
            "results": [],
            "result_count": 0,
            "authority": "external_evidence_unverified",
            "automatic_truth_write": False,
            "reason": "timeout",
        }

    # Process results
    results = []
    if isinstance(raw_results, dict):
        result_list = raw_results.get("results", [])
    elif isinstance(raw_results, list):
        result_list = raw_results
    else:
        result_list = []

    for raw in result_list[:limit]:
        if isinstance(raw, dict):
            results.append(normalize_searxng_result(raw))

    return {
        "record_type": "searxng_search_response_v1",
        "query": query,
        "enabled": True,
        "ok": True,
        "results": results,
        "result_count": len(results),
        "authority": "external_evidence_unverified",
        "automatic_truth_write": False,
        "reason": "ok",
    }


# ---------------------------------------------------------------------------
# Config reset (for testing)
# ---------------------------------------------------------------------------

def reset_config_cache() -> None:
    """Reset the cached config. Used in tests."""
    global _CONFIG_CACHE
    _CONFIG_CACHE = None


if __name__ == "__main__":
    import sys

    if is_searxng_enabled():
        if len(sys.argv) > 1:
            query = " ".join(sys.argv[1:])
            print(f"Searching: {query}")
            result = search_searxng(query)
            print(f"OK: {result['ok']}, Reason: {result['reason']}")
            print(f"Results: {result['result_count']}")
            for r in result["results"]:
                print(f"  - {r['title']} ({r['url']})")
        else:
            print("Usage: python searxng_search_adapter.py '<query>'")
            print("Note: SearXNG is currently disabled. Set WESLR_SEARXNG_ENABLED=true to enable.")
    else:
        print("SearXNG search is disabled.")
        print("Enable with: WESLR_SEARXNG_ENABLED=true")
        print("Default URL: http://localhost:8888")
        print("Override URL with: WESLR_SEARXNG_URL=http://custom:8888")