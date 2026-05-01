"""
External Evidence Packet Builder V1

Builds bounded external evidence packets from normalized SearXNG search results.
Read-only. No truth writes. No /chat integration.
"""

from typing import Any


# Fields that are considered safe to include in evidence packets
SAFE_FIELDS = frozenset([
    "title",
    "url",
    "content",
    "source",
    "authority",
])

# Fields that must never appear in evidence packets
UNSAFE_FIELDS = frozenset([
    "raw",
    "raw_content",
    "full_html",
    "html",
    "cookies",
    "headers",
    "auth",
    "api_key",
    "token",
    "session",
])

# Maximum content length per result (characters)
MAX_CONTENT_LENGTH = 2000

# Record type identifier
RECORD_TYPE = "external_evidence_packet_v1"
SUMMARY_RECORD_TYPE = "external_evidence_packet_summary_v1"


def _is_valid_searxng_response(search_response: dict) -> bool:
    """Check if search_response is a valid searxng_search_response_v1."""
    if not isinstance(search_response, dict):
        return False
    if search_response.get("record_type") != "searxng_search_response_v1":
        return False
    if search_response.get("ok") is not True:
        return False
    results = search_response.get("results")
    if not isinstance(results, list) or len(results) == 0:
        return False
    return True


def _strip_unsafe_fields(result: dict) -> dict:
    """Remove unsafe fields from a result dict."""
    return {k: v for k, v in result.items() if k not in UNSAFE_FIELDS}


def _truncate_content(content: str, max_length: int = MAX_CONTENT_LENGTH) -> str:
    """Safely truncate content to max_length characters."""
    if not isinstance(content, str):
        return ""
    if len(content) <= max_length:
        return content
    return content[:max_length] + "…"


def _safe_result(result: dict) -> dict:
    """Build a safe result dict: only safe fields, content truncated."""
    safe = {}
    title = result.get("title", "")
    url = result.get("url", "")
    content = result.get("content", "")
    source = result.get("source", "")
    authority = result.get("authority", "")

    if title:
        safe["title"] = title
    if url:
        safe["url"] = url
    if content:
        safe["content"] = _truncate_content(content, MAX_CONTENT_LENGTH)
    if source:
        safe["source"] = source
    if authority:
        safe["authority"] = authority

    return safe


def build_evidence_packet(query: str, search_response: dict, max_results: int = 5) -> dict:
    """
    Build an external evidence packet from a normalized SearXNG search response.

    Args:
        query: The search query string
        search_response: A normalized searxng_search_response_v1 dict
        max_results: Maximum number of results to include (default 5)

    Returns:
        A dict with record_type "external_evidence_packet_v1", or a safe
        failure packet if validation fails.
    """
    # Validate response type and structure
    if not _is_valid_searxng_response(search_response):
        return {
            "record_type": RECORD_TYPE,
            "query": query,
            "source_adapter": "searxng",
            "authority": "external_evidence_unverified",
            "truth_status": "unverified",
            "automatic_truth_write": False,
            "result_count": 0,
            "results": [],
            "limitations": [
                "Invalid or missing search response",
                "Requires searxng_search_response_v1 with ok=true and at least one result",
            ],
            "safe_for_answer_builder": False,
        }

    all_results = search_response.get("results", [])
    limited = all_results[:max_results]

    safe_results = []
    for r in limited:
        safe_r = _safe_result(r)
        if safe_r.get("title") or safe_r.get("url"):
            safe_results.append(safe_r)

    result_count = len(safe_results)

    # Build limitations list
    limitations = []
    if result_count == 0:
        limitations.append("No valid results after filtering")
    if result_count < len(all_results):
        limitations.append(f"Limited to {result_count} of {len(all_results)} available results")
    limitations.append("Sources may not be current or complete")
    limitations.append("Truth status is unverified — not asserted as fact")

    return {
        "record_type": RECORD_TYPE,
        "query": query,
        "source_adapter": "searxng",
        "authority": "external_evidence_unverified",
        "truth_status": "unverified",
        "automatic_truth_write": False,
        "result_count": result_count,
        "results": safe_results,
        "limitations": limitations,
        "safe_for_answer_builder": result_count > 0,
    }


def summarize_evidence_packet(packet: dict) -> dict:
    """
    Summarize an evidence packet into a compact summary dict.

    Args:
        packet: An external_evidence_packet_v1 dict

    Returns:
        A dict with record_type "external_evidence_packet_summary_v1"
    """
    if packet.get("record_type") != RECORD_TYPE:
        return {
            "record_type": SUMMARY_RECORD_TYPE,
            "query": "",
            "result_count": 0,
            "top_titles": [],
            "top_domains": [],
            "authority": "external_evidence_unverified",
            "truth_status": "unverified",
            "safe_for_answer_builder": False,
        }

    query = packet.get("query", "")
    results = packet.get("results", [])
    authority = packet.get("authority", "external_evidence_unverified")
    truth_status = packet.get("truth_status", "unverified")
    safe = packet.get("safe_for_answer_builder", False)

    titles = []
    domains = []

    for r in results:
        title = r.get("title", "")
        url = r.get("url", "")
        if title:
            titles.append(title)
        if url:
            # Extract domain from URL
            try:
                if url.startswith("http://") or url.startswith("https://"):
                    domain = url.split("/")[2]
                else:
                    domain = url.split("/")[0]
                domains.append(domain)
            except Exception:
                pass

    return {
        "record_type": SUMMARY_RECORD_TYPE,
        "query": query,
        "result_count": len(results),
        "top_titles": titles,
        "top_domains": domains,
        "authority": authority,
        "truth_status": truth_status,
        "safe_for_answer_builder": safe,
    }