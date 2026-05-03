"""Gene Ontology (GO) adapter — retrieve GO terms and annotations.
Uses http://api.geneontology.org/api/ (no key required).
"""
from __future__ import annotations
import time
import requests

_RATE_LIMIT = 0.2


def _rate_limit():
    time.sleep(_RATE_LIMIT)


def get_go_term(term: str) -> dict:
    """Fetch GO term details by name or ID (e.g., "GO:0006915" or "apoptosis")."""
    _rate_limit()
    # If it looks like a GO ID, fetch directly
    if term.startswith("GO:"):
        url = f"https://rest.geneontology.org/ontol/goterm/term/{term}"
    else:
        # Search by label
        url = "https://rest.geneontology.org/api/bioentity/function"
        params = {"q": term}
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 404:
            return {"error": f"GO term not found: {term}"}
        resp.raise_for_status()
        data = resp.json()
        return {"results": data.get("associations", [])[:5]}

    resp = requests.get(url, timeout=30)
    if resp.status_code == 404:
        return {"error": f"GO term not found: {term}"}
    resp.raise_for_status()
    return resp.json()


def format_go_result(result: dict) -> str:
    """Format GO term result for display."""
    if "error" in result:
        return result["error"]
    return str(result)[:500]