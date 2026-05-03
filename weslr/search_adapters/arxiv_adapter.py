"""
arXiv Search Adapter — searches arXiv preprints and extracts facts.

Uses the public arXiv API (http://export.arxiv.org/api/query) — no API key required.
Rate limit: 1 req every 3 seconds (https://arxiv.org/help/api_basics)

Facts are extracted from the abstract using the existing fact_extractor.
Evidence packets are stored to external_evidence_packets.jsonl.
"""
from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from weslr.fact_extractor import extract_facts_with_positions
from weslr.search_adapters.evidence_packet_store import append_evidence_packet

_ARXIV_BASE = "http://export.arxiv.org/api/query"
_RATE_LIMIT_DELAY = 3.0  # seconds between requests


def _rate_limit_sleep():
    time.sleep(_RATE_LIMIT_DELAY)


def search_arxiv(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
) -> List[Dict[str, Any]]:
    """Search arXiv and return list of result dicts.

    Args:
        query: arXiv search query (e.g. "all:crystal structure" or "ti:perovskite")
        max_results: maximum number of results to return (1-100)
        sort_by: "relevance" or "submittedDate"

    Returns:
        List of dicts with keys: id (URL), title, summary, authors, published (year),
        primary_category, pdf_url, comment.
    """
    _rate_limit_sleep()

    if max_results < 1:
        max_results = 1
    elif max_results > 100:
        max_results = 100

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending",
    }

    resp = requests.get(_ARXIV_BASE, params=params, timeout=60)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    results: List[Dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        title_elem = entry.find("atom:title", ns)
        title = _text_of(title_elem) if title_elem is not None else ""
        summary_elem = entry.find("atom:summary", ns)
        summary = _text_of(summary_elem) if summary_elem is not None else ""

        authors: List[str] = []
        for author in entry.findall("atom:author", ns):
            name_elem = author.find("atom:name", ns)
            name = _text_of(name_elem) if name_elem is not None else ""
            if name:
                authors.append(name)

        published_elem = entry.find("atom:published", ns)
        published = _text_of(published_elem) if published_elem is not None else ""
        # Extract year
        year_match = re.match(r"(\d{4})", published)
        year = year_match.group(1) if year_match else ""

        # Primary category
        cat_elem = entry.find("atom:category", ns)
        primary_category = cat_elem.get("term", "") if cat_elem is not None else ""

        # PDF link
        pdf_link = ""
        for link in entry.findall("atom:link", ns):
            if link.get("type") == "application/pdf":
                pdf_link = link.get("href", "")
                break

        # arXiv ID
        id_elem = entry.find("atom:id", ns)
        arxiv_id = _text_of(id_elem) if id_elem is not None else ""

        # Comments (if present)
        comment_elem = entry.find("arxiv:comment", {"arxiv": "http://arxiv.org/schemas/atom"})
        comment = _text_of(comment_elem) if comment_elem is not None else ""

        results.append({
            "arxiv_id": arxiv_id,
            "title": _clean_text(title),
            "summary": _clean_text(summary),
            "authors": authors,
            "published": published,
            "year": year,
            "primary_category": primary_category,
            "pdf_url": pdf_link,
            "comment": comment,
        })

    return results


def _text_of(elem: Optional[Any]) -> str:
    if elem is None:
        return ""
    return elem.text or ""


def _clean_text(text: str) -> str:
    """Normalize whitespace in text fields."""
    return re.sub(r"\s+", " ", text).strip()


def extract_arxiv_facts(
    articles: List[Dict[str, Any]],
    domain: Optional[str] = None,
    base_trust: float = 0.65,
) -> int:
    """Extract facts from arXiv abstracts using the fact extractor.

    Returns the total number of facts extracted.
    """
    fact_count = 0
    for article in articles:
        abstract = article.get("summary", "") or ""
        if not abstract:
            continue

        arxiv_id = article.get("arxiv_id", "")
        title = article.get("title", "") or ""
        year = article.get("year", "") or ""
        authors = article.get("authors", []) or []
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."

        raw_facts = extract_facts_with_positions(
            text=abstract,
            page=1,
            domain=domain or "materials_science",
        )

        fact_count += len(raw_facts)

    return fact_count


def search_and_store(
    query: str,
    max_results: int = 10,
    domain: Optional[str] = None,
    sort_by: str = "relevance",
) -> Dict[str, Any]:
    """Run arXiv search, store evidence packet, and extract facts.

    Returns a summary dict with result_count and fact_count.
    """
    articles = search_arxiv(query, max_results=max_results, sort_by=sort_by)

    if not articles:
        return {"result_count": 0, "fact_count": 0, "articles": []}

    # Build and store evidence packet
    packet_id = f"ax_{int(datetime.now(timezone.utc).timestamp())}_{id(query) % 100000:05d}"
    packet = {
        "record_type": "external_evidence_packet_v1",
        "packet_id": packet_id,
        "source": "arxiv",
        "query": query,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "result_count": len(articles),
        "results": articles,
        "authority": "external_evidence_unverified",
        "automatic_change": False,
        "hidden_learning": False,
        "raw_prompt_stored": False,
    }
    append_evidence_packet(packet)

    # Extract facts
    fact_count = extract_arxiv_facts(articles, domain=domain)

    return {
        "result_count": len(articles),
        "fact_count": fact_count,
        "packet_id": packet_id,
        "articles": articles,
    }


def format_search_results(articles: List[Dict[str, Any]]) -> str:
    """Format arXiv search results as a readable string."""
    if not articles:
        return "No results found."

    lines = []
    for i, article in enumerate(articles, 1):
        title = article.get("title", "Untitled")
        year = article.get("year", "?")
        authors = article.get("authors", [])
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."
        category = article.get("primary_category", "")
        arxiv_id = article.get("arxiv_id", "")
        arxiv_short = arxiv_id.split("/")[-1] if arxiv_id else ""

        lines.append(f"{i}. {title}")
        lines.append(f"   Authors: {author_str}")
        lines.append(f"   Year: {year}  |  Category: {category}")
        if arxiv_id:
            lines.append(f"   arXiv: {arxiv_id}")
        lines.append("")
    return "\n".join(lines)