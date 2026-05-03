"""
arXiv PDF Fetcher — download arXiv papers as PDF for full-text ingestion.

Uses the public arXiv PDF URL pattern: https://arxiv.org/pdf/{arxiv_id}.pdf
Rate limit: 1 req every 3 seconds (respect arXiv API terms).

Requires: requests, pypdf (already in Weslr dependencies)
"""
from __future__ import annotations

import pathlib
import time
from typing import Optional

import requests

_TENANT_DOCS_DIR = "tenants"
_ARXIV_PDF_USER_AGENT = "Weslr/1.0 (mailto:operator@weslr.de; research tool)"
_RATE_LIMIT_DELAY = 3.0


def _rate_limit_sleep():
    time.sleep(_RATE_LIMIT_DELAY)


def arxiv_id_to_pdf_url(arxiv_id: str) -> str:
    """Convert arXiv ID to PDF download URL.
    
    Args:
        arxiv_id: arXiv ID (with or without 'vN' version, with or without 'arXiv:' prefix).
                  Examples: '2404.00291', '2404.00291v1', 'arXiv:2404.00291'
    
    Returns:
        PDF URL: https://arxiv.org/pdf/{id}.pdf
    """
    # Strip version suffix
    aid = arxiv_id.strip()
    for prefix in ["arXiv:", "arxiv:", "ARXIV:"]:
        aid = aid.replace(prefix, "")
    # Strip version
    aid = aid.split("v")[0].strip()
    return f"https://arxiv.org/pdf/{aid}.pdf"


def fetch_pdf(url: str, save_path: pathlib.Path, timeout: int = 60) -> bool:
    """Download a PDF from URL and save to save_path.
    
    Args:
        url: PDF URL to download.
        save_path: Local path to save the PDF.
        timeout: Request timeout in seconds.
    
    Returns:
        True if download succeeded, False otherwise.
    """
    _rate_limit_sleep()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": _ARXIV_PDF_USER_AGENT},
            timeout=timeout,
            stream=True,
        )
        resp.raise_for_status()
        
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception:
        return False


def ingest_arxiv_paper_by_id(
    arxiv_id: str,
    tenant_id: Optional[str] = None,
    domain: str = "materials_science",
) -> dict:
    """Download arXiv PDF and ingest as a Weslr document.
    
    Args:
        arxiv_id: arXiv paper ID (e.g., '2404.00291')
        tenant_id: Tenant for multi-tenant path resolution. If None, uses default.
        domain: Domain for fact extraction (default: materials_science)
    
    Returns:
        dict with keys: status, arxiv_id, pdf_path, document_id, fact_count
    """
    from weslr.search_adapters.arxiv_adapter import search_arxiv
    from weslr.document_ingestor import ingest_document
    
    # Clean arxiv_id
    aid = arxiv_id.strip()
    for prefix in ["arXiv:", "arxiv:", "ARXIV:"]:
        aid = aid.replace(prefix, "")
    aid_base = aid.split("v")[0].strip()
    
    # Determine save path
    if tenant_id:
        doc_dir = pathlib.Path(_TENANT_DOCS_DIR) / tenant_id / "documents" / "arxiv"
    else:
        doc_dir = pathlib.Path("tenants") / "default" / "documents" / "arxiv"
    doc_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = doc_dir / f"{aid_base.replace('.', '_')}.pdf"
    
    # Download
    pdf_url = arxiv_id_to_pdf_url(arxiv_id)
    success = fetch_pdf(pdf_url, pdf_path)
    
    if not success:
        return {"status": "download_failed", "arxiv_id": arxiv_id, "pdf_url": pdf_url}
    
    # Fetch metadata from API
    metadata = {}
    try:
        articles = search_arxiv(f"id:{aid_base}", max_results=1)
        if articles:
            art = articles[0]
            metadata = {
                "title": art.get("title", ""),
                "authors": art.get("authors", []),
                "year": art.get("year", ""),
                "primary_category": art.get("primary_category", ""),
            }
    except Exception:
        pass
    
    # Ingest document (will call extract_facts_with_positions internally)
    try:
        result = ingest_document(
            file_path=str(pdf_path),
            source_type="arxiv_fulltext",
            domain=domain,
        )
        return {
            "status": "success",
            "arxiv_id": aid_base,
            "pdf_path": str(pdf_path),
            "document_id": result.get("document_id", ""),
            "fact_count": result.get("facts_stored", 0),
            "metadata": metadata,
        }
    except Exception as e:
        return {
            "status": "ingest_failed",
            "arxiv_id": arxiv_id,
            "pdf_path": str(pdf_path),
            "error": str(e),
        }


def get_arxiv_abstract(arxiv_id: str) -> dict:
    """Fetch just the abstract/metadata from arXiv API (no PDF download).
    
    Returns dict with keys: title, summary, authors, year, primary_category, pdf_url
    """
    from weslr.search_adapters.arxiv_adapter import search_arxiv
    
    aid = arxiv_id.strip()
    for prefix in ["arXiv:", "arxiv:", "ARXIV:"]:
        aid = aid.replace(prefix, "")
    aid_base = aid.split("v")[0].strip()
    
    articles = search_arxiv(f"id:{aid_base}", max_results=1)
    if not articles:
        return {}
    return articles[0]
