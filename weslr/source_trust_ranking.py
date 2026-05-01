"""
Source Trust Ranking V1

Deterministic ranking layer for external evidence results.
Does not verify truth — only orders sources by trustworthiness.
Never drops sources. Never writes memory or JSONL.
"""

from __future__ import annotations
import re
from urllib.parse import urlparse


# ─────────────────────────────────────────────────────────────────────────────
# Domain / source-type classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_source(url: str, title: str = "", content: str = "") -> dict:
    """
    Classify a URL into source type and trust tier.

    Returns:
        {
            "record_type": "source_classification_v1",
            "domain": "...",
            "source_type": "reference|academic|educational|official|news_magazine|video|forum|social|commercial|unknown",
            "trust_tier": "high|medium|low|unknown",
            "reason": "...",
            "authority": "ranking_only"
        }
    """
    record = {
        "record_type": "source_classification_v1",
        "domain": "",
        "source_type": "unknown",
        "trust_tier": "unknown",
        "reason": "",
        "authority": "ranking_only",
    }

    if not url or not isinstance(url, str):
        record["reason"] = "Missing or malformed URL"
        return record

    lower_url = url.lower()

    # ── High trust: reference / academic / official ──────────────────────────

    if "wikipedia.org" in lower_url:
        record["domain"] = "wikipedia.org"
        record["source_type"] = "reference"
        record["trust_tier"] = "high"
        record["reason"] = "Wikipedia — open encyclopedia, high coverage, community reviewed"
        return record

    if "britannica.com" in lower_url:
        record["domain"] = "britannica.com"
        record["source_type"] = "reference"
        record["trust_tier"] = "high"
        record["reason"] = "Britannica — established reference encyclopedia"
        return record

    if "merriam-webster.com" in lower_url:
        record["domain"] = "merriam-webster.com"
        record["source_type"] = "reference"
        record["trust_tier"] = "high"
        record["reason"] = "Merriam-Webster — authoritative dictionary"
        return record

    if "dictionary.com" in lower_url:
        record["domain"] = "dictionary.com"
        record["source_type"] = "reference"
        record["trust_tier"] = "high"
        record["reason"] = "Dictionary — authoritative lexical reference"
        return record

    if "oxfordlearnersdictionaries.com" in lower_url:
        record["domain"] = "oxfordlearnersdictionaries.com"
        record["source_type"] = "reference"
        record["trust_tier"] = "high"
        record["reason"] = "Oxford — authoritative dictionary"
        return record

    # Quanta Magazine — science journalism, high quality
    if "quantamagazine.org" in lower_url:
        record["domain"] = "quantamagazine.org"
        record["source_type"] = "news_magazine"
        record["trust_tier"] = "high"
        record["reason"] = "Quanta Magazine — science journalism, peer-reviewed context"
        return record

    # .edu domains — academic / educational institutions
    if ".edu" in lower_url:
        parsed = urlparse(url)
        record["domain"] = parsed.netloc.lower() if parsed.netloc else lower_url
        record["source_type"] = "academic"
        record["trust_tier"] = "high"
        record["reason"] = ".edu domain — academic institution"
        return record

    # Government / institutional domains
    if any(p in lower_url for p in [
        ".gov", ".gov.",  # US and international government
        "nih.gov", "nasa.gov", "noaa.gov",  # US science agencies
        "cdc.gov", "who.int", "pubmed.ncbi.nlm.nih.gov",  # Health/official
        "epa.gov", "usgs.gov", "能源局",  # Various official
    ]):
        parsed = urlparse(url)
        record["domain"] = parsed.netloc.lower() if parsed.netloc else lower_url
        record["source_type"] = "official"
        record["trust_tier"] = "high"
        record["reason"] = "Government or institutional domain"
        return record

    # ── Medium trust ─────────────────────────────────────────────────────────

    # Established science magazines and journalism
    if any(p in lower_url for p in [
        "nature.com", "sciencemag.org", "scientificamerican.com",
        "arxiv.org", "pubmed.ncbi.nlm.nih.gov",  # arxiv is pre-print but academic
        "medium.com",  # Variable but can be high quality
        "theguardian.com", "nytimes.com", "washingtonpost.com",
        "reuters.com", "apnews.com",
    ]):
        parsed = urlparse(url)
        record["domain"] = parsed.netloc.lower() if parsed.netloc else lower_url
        record["source_type"] = "news_magazine"
        record["trust_tier"] = "medium"
        record["reason"] = "Established science news or journalism outlet"
        return record

    # Organization / NGO sites
    if any(p in lower_url for p in [
        ".org",  # General NGO/organization — medium unless otherwise matched
    ]):
        # Skip if already matched as high-trust .org (wikipedia, etc.)
        parsed = urlparse(url)
        domain = parsed.netloc.lower() if parsed.netloc else lower_url
        record["domain"] = domain
        record["source_type"] = "educational"
        record["trust_tier"] = "medium"
        record["reason"] = "Organization / NGO domain"
        return record

    # ── Low trust ────────────────────────────────────────────────────────────

    if "reddit.com" in lower_url:
        record["domain"] = "reddit.com"
        record["source_type"] = "forum"
        record["trust_tier"] = "low"
        record["reason"] = "Reddit — user-generated forum content, variable quality"
        return record

    if any(p in lower_url for p in ["youtube.com", "youtu.be", "youtube-nocookie.com"]):
        record["domain"] = "youtube.com"
        record["source_type"] = "video"
        record["trust_tier"] = "low"
        record["reason"] = "YouTube — video platform, unverified user content"
        return record

    if any(p in lower_url for p in [
        "stackoverflow.com", "stackexchange.com", "Stack Overflow",
        "quora.com", "forum", "forums",
    ]):
        parsed = urlparse(url)
        record["domain"] = parsed.netloc.lower() if parsed.netloc else lower_url
        record["source_type"] = "forum"
        record["trust_tier"] = "low"
        record["reason"] = "Forum / Q&A site — variable quality, anonymous contribution"
        return record

    if any(p in lower_url for p in ["twitter.com", "x.com", "facebook.com", "instagram.com", "linkedin.com"]):
        parsed = urlparse(url)
        record["domain"] = parsed.netloc.lower() if parsed.netloc else lower_url
        record["source_type"] = "social"
        record["trust_tier"] = "low"
        record["reason"] = "Social media platform — informal, unverified"
        return record

    # SEO / commercial pages with generic patterns
    if any(p in lower_url for p in [
        "best-", "-guide", "-review", "top-10", "top-5",
        "-comparison", "-vs-", " Alternatives",
    ]) and not record["domain"]:
        parsed = urlparse(url)
        record["domain"] = parsed.netloc.lower() if parsed.netloc else lower_url
        record["source_type"] = "commercial"
        record["trust_tier"] = "low"
        record["reason"] = "SEO/commercial content — ranking-driven, low editorial standard"
        return record

    # ── Default unknown ───────────────────────────────────────────────────────
    parsed = urlparse(url)
    record["domain"] = parsed.netloc.lower() if parsed.netloc else "unknown"
    record["reason"] = "Unclassified domain — default low trust"
    return record


# ─────────────────────────────────────────────────────────────────────────────
# Trust score computation
# ─────────────────────────────────────────────────────────────────────────────

def score_source(result: dict) -> dict:
    """
    Compute a trust score for a normalized search result.

    Input:
        Normalized search_result_v1 dict with url, title, content, searxng_score

    Returns:
        {
            "record_type": "source_trust_score_v1",
            "score": 0.0-1.0,
            "classification": {...},  # from classify_source
            "ranking_reasons": [...],
            "authority": "ranking_only"
        }
    """
    url = result.get("url", "")
    title = result.get("title", "")
    content = result.get("content", "")
    searxng_score = result.get("searxng_score", 0.5)

    classification = classify_source(url, title, content)

    # Base score from trust tier
    tier_scores = {
        "high": 0.90,
        "medium": 0.60,
        "low": 0.30,
        "unknown": 0.20,
    }
    base = tier_scores.get(classification["trust_tier"], 0.20)

    # Secondary modifier: small blend with SearXNG score
    # Classification drives the score; SearXNG provides minor adjustment
    searxng_val = searxng_score / 10.0  # Normalize 0-10 → 0-1
    blended = base * 0.92 + searxng_val * 0.08
    final_score = round(min(blended, 1.0), 3)

    ranking_reasons = [classification["reason"]]

    # Boost for having content (better quality signal)
    if content and len(content) > 100:
        ranking_reasons.append("Content present — more verifiable")

    # Boost for title presence
    if title:
        ranking_reasons.append(f"Title: {title[:60]}")

    return {
        "record_type": "source_trust_score_v1",
        "score": final_score,
        "classification": classification,
        "ranking_reasons": ranking_reasons,
        "authority": "ranking_only",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rank search results
# ─────────────────────────────────────────────────────────────────────────────

def rank_search_results(
    results: list[dict],
    prefer_source_types: list[str] | None = None,
) -> list[dict]:
    """
    Rank search results by trust score, highest first.

    Does not drop results. Preserves all entries.
    Adds _source_trust to each result.

    Args:
        results: List of normalized search_result_v1 dicts
        prefer_source_types: Not used in V1 — reserved for future tuning

    Returns:
        Sorted list of result copies with _source_trust metadata added
    """
    if not results:
        return []

    scored = []
    for result in results:
        trust = score_source(result)
        scored_result = {**result, "_source_trust": trust}
        scored.append(scored_result)

    # Stable sort by trust score descending
    scored.sort(key=lambda x: x["_source_trust"]["score"], reverse=True)

    return scored