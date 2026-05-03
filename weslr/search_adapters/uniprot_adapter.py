"""UniProt REST API adapter — fetch protein sequences, functions, cross-references.
No API key required. Rate-limited to 5 req/s.
"""
from __future__ import annotations
import time
import requests

_RATE_LIMIT = 0.2  # 5 req/s


def _rate_limit():
    time.sleep(_RATE_LIMIT)


def search_uniprot(query: str, limit: int = 5) -> dict:
    """Search UniProt by protein name/gene name.

    Returns dict with: entries (list of protein records), count, query
    Each entry: name, gene_name, organism, sequence (truncated), function, length
    """
    _rate_limit()
    url = "https://rest.uniprot.org/uniprotkb/search"
    params = {
        "query": query,
        "format": "json",
        "size": limit,
        "fields": "accession,gene_names,organism_name,length,sequence,cc_function,cc_subcellular_location",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results = {
        "query": query,
        "count": data.get("total", 0),
        "entries": [],
    }

    for hit in data.get("results", []):
        entry = {
            "accession": hit.get("primaryAccession", ""),
            "gene_name": hit.get("genes", [{}])[0].get("geneName", {}).get("value", ""),
            "organism": hit.get("organism", {}).get("scientificName", ""),
            "length": hit.get("sequence", {}).get("length", 0),
            "sequence": _truncate_seq(hit.get("sequence", {}).get("value", ""), 200),
            "function": "",
            "location": "",
        }

        # Extract function from comments
        for comment in hit.get("comments", []):
            if comment.get("commentType") == "FUNCTION":
                entry["function"] = comment.get("texts", [{}])[0].get("value", "")[:200]
                break

        results["entries"].append(entry)

    return results


def _truncate_seq(seq: str, max_len: int) -> str:
    if len(seq) <= max_len:
        return seq
    return seq[:max_len] + f" [...] ({len(seq)} aa total)"


def format_uniprot_result(result: dict) -> str:
    """Format UniProt search result for display."""
    if not result.get("entries"):
        return f"No UniProt entries found for '{result.get('query', '')}'"

    lines = [
        f"UniProt search: {result['query']} ({result['count']} hits)",
        "",
    ]

    for e in result["entries"]:
        lines.append(f"**{e['accession']}** — {e['gene_name'] or '?'} ({e['organism']})")
        lines.append(f"   Length: {e['length']} aa")
        if e.get("function"):
            lines.append(f"   Function: {e['function']}")
        if e.get("sequence"):
            lines.append(f"   Sequence: {e['sequence']}")
        lines.append("")

    return "\n".join(lines)


def handle_search_uniprot(protein_name: str) -> str:
    """Handler for /search uniprot <protein_name>."""
    try:
        result = search_uniprot(protein_name, limit=3)
        return format_uniprot_result(result)
    except Exception as ex:
        return f"UniProt search failed: {ex}"