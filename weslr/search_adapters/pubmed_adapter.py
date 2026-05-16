"""PubMed search adapter using NCBI E-utilities (free, no API key)."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


# Rate limit: 3 req/s → sleep 0.34s between requests
_RATE_LIMIT_DELAY = 0.34


def _rate_limit_sleep():
    time.sleep(_RATE_LIMIT_DELAY)


def _get_requests():
    """Return requests when optional search dependencies are installed."""
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PubMed search requires the optional 'search' dependencies. "
            "Install with: pip install -e .[search]"
        ) from exc
    return requests


def esearch(query: str, retmax: int = 20) -> List[str]:
    """Return list of PubMed IDs (PMIDs) for the query."""
    _rate_limit_sleep()
    requests = _get_requests()
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "sort": "relevance",
    }
    resp = requests.get(base, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("esearchresult", {}).get("idlist", [])


def efetch(pmids: List[str]) -> List[Dict[str, Any]]:
    """Fetch abstract data for a list of PMIDs.

    Returns list of dicts with keys:
    pmid, title, authors, journal, year, abstract, url
    """
    if not pmids:
        return []
    _rate_limit_sleep()
    requests = _get_requests()
    import xml.etree.ElementTree as ET
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    resp = requests.get(base, params=params, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    results: List[Dict[str, Any]] = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID", "")
        title = article.findtext(".//ArticleTitle", "")
        abstract_elem = article.find(".//AbstractText")
        abstract = abstract_elem.text if abstract_elem is not None else ""
        journal = article.findtext(".//Journal/Title", "")
        year = article.findtext(".//PubDate/Year", "")
        authors: List[str] = []
        for author in article.findall(".//Author"):
            last = author.findtext("LastName", "")
            fore = author.findtext("ForeName", "")
            if last or fore:
                authors.append(f"{fore} {last}".strip())
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        results.append({
            "pmid": pmid,
            "title": title or "",
            "abstract": abstract or "",
            "journal": journal or "",
            "year": year or "",
            "authors": authors,
            "url": url,
        })
    return results


def search_pubmed(query: str, max_results: int = 10) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Return (pmids, articles)."""
    pmids = esearch(query, retmax=max_results)
    articles = efetch(pmids) if pmids else []
    return pmids, articles