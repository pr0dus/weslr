"""
External Evidence Answer Builder V1

Turns an external evidence packet into a cautious user-facing answer draft.
Read-only. No truth writes. No /chat integration. No Ollama.
"""

from typing import Optional

from weslr.evidence_packet_builder import (
    RECORD_TYPE as PACKET_RECORD_TYPE,
    build_evidence_packet,
)


RECORD_TYPE = "external_evidence_answer_v1"

# Depth options
DEPTH_BRIEF = "brief"
DEPTH_NORMAL = "normal"
DEPTH_DEEP = "deep"
VALID_DEPTHS = (DEPTH_BRIEF, DEPTH_NORMAL, DEPTH_DEEP)


def _is_valid_evidence_packet(evidence_packet: dict) -> bool:
    """Check if packet is a valid external_evidence_packet_v1 safe for answer building."""
    if not isinstance(evidence_packet, dict):
        return False
    if evidence_packet.get("record_type") != PACKET_RECORD_TYPE:
        return False
    if evidence_packet.get("safe_for_answer_builder") is not True:
        return False
    results = evidence_packet.get("results", [])
    if not isinstance(results, list) or len(results) == 0:
        return False
    return True


def _build_intro(query: str) -> str:
    return f"Based on external search results for \"{query}\" — not stored WESLR truth: "


def _build_brief_answer(query: str, packet: dict) -> str:
    """2-3 sentence answer."""
    results = packet.get("results", [])
    intro = _build_intro(query)

    if len(results) == 1:
        r = results[0]
        content = r.get("content", "").strip()
        if content:
            return (intro + content)[:500]
        title = r.get("title", "")
        return f"{intro}Found: {title}."

    # 2-3 results
    snippets = []
    for r in results[:2]:
        title = r.get("title", "")
        if title:
            snippets.append(title)
    if snippets:
        return intro + "Sources mention: " + ", ".join(snippets) + "."
    return intro + "Multiple sources found."


def _build_normal_answer(query: str, packet: dict) -> str:
    """Concise paragraph + source list."""
    results = packet.get("results", [])
    intro = _build_intro(query)

    paragraphs = []
    if results:
        first = results[0]
        content = first.get("content", "").strip()
        if content:
            paragraphs.append(content)
        else:
            title = first.get("title", "")
            if title:
                paragraphs.append(title)

    other_sources = []
    for r in results[1:3]:
        title = r.get("title", "")
        if title:
            other_sources.append(title)

    if other_sources:
        paragraphs.append("Other sources include: " + ", ".join(other_sources) + ".")

    body = " ".join(paragraphs)
    return intro + body


def _build_deep_answer(query: str, packet: dict) -> str:
    """Multi-part explanation using available result snippets only."""
    results = packet.get("results", [])
    intro = _build_intro(query)

    parts = []

    # Part 1: Primary finding
    if results:
        first = results[0]
        title = first.get("title", "")
        content = first.get("content", "").strip()
        if content:
            parts.append(f"1. Primary source: {title}\n   {content[:600]}")
        elif title:
            parts.append(f"1. Primary source: {title}")

    # Part 2: Supporting sources
    if len(results) > 1:
        supporting = []
        for r in results[1:3]:
            t = r.get("title", "")
            if t:
                supporting.append(t)
        if supporting:
            parts.append("2. Supporting sources: " + "; ".join(supporting))

    # Part 3: Source URLs
    urls = []
    for r in results[:3]:
        u = r.get("url", "")
        if u:
            urls.append(u)
    if urls:
        parts.append("3. Source URLs:\n   " + "\n   ".join(urls))

    body = "\n\n".join(parts)
    return intro + "\n\n" + body


def _build_answer_from_packet(query: str, evidence_packet: dict, depth: str) -> dict:
    """Build answer from a validated evidence packet."""
    results = evidence_packet.get("results", [])

    if depth == DEPTH_BRIEF:
        answer = _build_brief_answer(query, evidence_packet)
    elif depth == DEPTH_DEEP:
        answer = _build_deep_answer(query, evidence_packet)
    else:
        answer = _build_normal_answer(query, evidence_packet)

    sources = []
    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        if url:
            sources.append({"title": title, "url": url} if title else {"url": url})

    limitations = [
        "External search results are not verified WESLR truth",
        "Sources may be incomplete, outdated, or incorrect",
        "Do not rely on this answer for consequential decisions without verification",
    ]

    return {
        "record_type": RECORD_TYPE,
        "query": query,
        "answer": answer,
        "sources": sources,
        "source_count": len(sources),
        "authority": "external_evidence_unverified",
        "truth_status": "unverified",
        "automatic_truth_write": False,
        "limitations": limitations,
        "safe_for_user": True,
    }


def build_evidence_answer(query: str, evidence_packet: dict, depth: str = DEPTH_NORMAL) -> dict:
    """
    Build a cautious user-facing answer from an external evidence packet.

    Args:
        query: The original search query
        evidence_packet: An external_evidence_packet_v1 dict
        depth: "brief" | "normal" | "deep" (default "normal")

    Returns:
        An external_evidence_answer_v1 dict, or a safe failure answer if
        the packet is invalid or not safe for answer building.
    """
    if not _is_valid_evidence_packet(evidence_packet):
        limitations = [
            "Invalid or unsuitable evidence packet for answer building",
            "Requires external_evidence_packet_v1 with safe_for_answer_builder=true and at least one result",
        ]
        return {
            "record_type": RECORD_TYPE,
            "query": query,
            "answer": "I don't have enough external evidence to answer that yet.",
            "sources": [],
            "source_count": 0,
            "authority": "external_evidence_unverified",
            "truth_status": "unverified",
            "automatic_truth_write": False,
            "limitations": limitations,
            "safe_for_user": False,
        }

    if depth not in VALID_DEPTHS:
        depth = DEPTH_NORMAL

    return _build_answer_from_packet(query, evidence_packet, depth)


def build_no_evidence_answer(query: str, reason: str = "no_evidence") -> dict:
    """
    Build a safe answer when no evidence is available.

    Args:
        query: The original query
        reason: One of "no_evidence", "search_failed", "adapter_disabled"

    Returns:
        A safe external_evidence_answer_v1 dict.
    """
    reason_messages = {
        "no_evidence": "I don't have enough external evidence to answer that yet.",
        "search_failed": "External search failed. I can't answer based on external sources right now.",
        "adapter_disabled": "External search is not enabled. I don't have external evidence to draw from.",
    }
    msg = reason_messages.get(reason, "I don't have enough external evidence to answer that yet.")

    return {
        "record_type": RECORD_TYPE,
        "query": query,
        "answer": msg,
        "sources": [],
        "source_count": 0,
        "authority": "external_evidence_unverified",
        "truth_status": "unverified",
        "automatic_truth_write": False,
        "limitations": [
            "No external evidence available",
            "Cannot verify accuracy of answer without sources",
        ],
        "safe_for_user": True,
    }