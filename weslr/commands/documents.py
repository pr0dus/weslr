"""Document and fact query commands for Weslr.

Provides read-only queries over ingested documents and fact assertions.

Commands:
- list_documents(limit: int = 20) -> str
- get_document(doc_id: str) -> str
- list_facts_about(entity: str, trust_min: float = 0.0, limit: int = 20) -> str
- show_trust_breakdown(fact_id: str) -> str

Helper:
- build_source_citation(source_reference: dict, fallback_doc_id: str = "") -> str
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List

__all__ = [
    "list_documents",
    "get_document",
    "list_facts_about",
    "show_trust_breakdown",
    "build_source_citation",
]

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

_WESLR_DATA = Path(__file__).resolve().parent.parent / ".weslr"


def _documents_path() -> Path:
    return _WESLR_DATA / "documents.jsonl"


def _facts_path() -> Path:
    return _WESLR_DATA / "fact_assertions.jsonl"


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read a .jsonl file, return list of parsed dicts. Empty list if absent."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# ---------------------------------------------------------------------------
# Source citation helper
# ---------------------------------------------------------------------------

def build_source_citation(source_reference: Optional[dict] = None, fallback_doc_id: str = "") -> str:
    """Build a human-readable citation string from a source_reference dict.

    Formats:
      - "Zhang et al. (2023) Nature Medicine, p.5 ll.12-18"
      - "doc_abc123 p.5 ll.12-18"   (when type is unknown)

    Args:
        source_reference: dict with keys: type, citation, page, line_range
        fallback_doc_id: doc_id string to use when no reference is provided

    Returns:
        Formatted citation string, e.g. "Zhang et al. (2023) Nature Medicine, p.5 ll.12-18"
        Returns the fallback doc_id if source_reference is None/empty.
    """
    if not source_reference:
        return fallback_doc_id or "unknown"

    ref_type = source_reference.get("type", "")

    if ref_type == "paper":
        citation = source_reference.get("citation", "")
        page = source_reference.get("page")
        line_range = source_reference.get("line_range")

        parts = []
        if citation:
            parts.append(citation)
        if page is not None:
            parts.append(f"p.{page}")
        if line_range and isinstance(line_range, list) and len(line_range) == 2:
            parts.append(f"ll.{line_range[0]}-{line_range[1]}")

        return ", ".join(parts) if parts else fallback_doc_id or "unknown"

    elif ref_type == "web":
        source = source_reference.get("source", source_reference.get("url", ""))
        page = source_reference.get("page")
        return f"{source} p.{page}" if page else source or fallback_doc_id or "unknown"

    elif ref_type == "document" or ref_type == "doc":
        page = source_reference.get("page")
        line_range = source_reference.get("line_range")
        parts = []
        if page is not None:
            parts.append(f"p.{page}")
        if line_range and isinstance(line_range, list) and len(line_range) == 2:
            parts.append(f"ll.{line_range[0]}-{line_range[1]}")
        return ", ".join(parts) if parts else fallback_doc_id or "unknown"

    else:
        # Unknown type — try to fall back to doc_id
        return fallback_doc_id or "unknown"


# ---------------------------------------------------------------------------
# Command: list_documents
# ---------------------------------------------------------------------------

def list_documents(limit: int = 20) -> str:
    """List the most recent ingested documents.

    Reads .weslr/documents.jsonl and returns a formatted table of the `limit`
    most recent records. Each record is expected to have at minimum:
      doc_id, filename, upload_date, source_type, trust_baseline

    Args:
        limit: Maximum number of records to return (default 20)

    Returns:
        Formatted table string, or a message if no documents are found.
    """
    docs = _read_jsonl(_documents_path())

    if not docs:
        return "No documents ingested yet. Run the ingestion pipeline first."

    # Sort by upload_date descending (most recent first)
    def sort_key(d: dict) -> str:
        return d.get("upload_date", "")

    sorted_docs = sorted(docs, key=sort_key, reverse=True)
    limited = sorted_docs[:limit]

    if not limited:
        return "No documents found."

    # Build table
    header = f"{'doc_id':<20} {'filename':<35} {'upload_date':<12} {'source_type':<15} {'trust_baseline':<14}"
    sep = "-" * len(header)
    rows = []
    for d in limited:
        doc_id = str(d.get("doc_id", ""))
        filename = str(d.get("filename", ""))[:35]
        upload_date = str(d.get("upload_date", ""))[:12]
        source_type = str(d.get("source_type", ""))[:15]
        trust_baseline = str(d.get("trust_baseline", ""))
        rows.append(f"{doc_id:<20} {filename:<35} {upload_date:<12} {source_type:<15} {trust_baseline:<14}")

    total = len(docs)
    shown = len(limited)
    out = [f"Showing {shown} of {total} document(s):", header, sep] + rows
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Command: get_document
# ---------------------------------------------------------------------------

def get_document(doc_id: str) -> str:
    """Get full metadata for a specific document by doc_id.

    Reads .weslr/documents.jsonl and returns all available metadata fields
    for the matching document.

    Args:
        doc_id: The document identifier to look up

    Returns:
        Formatted metadata string, or a not-found message.
    """
    docs = _read_jsonl(_documents_path())

    for d in docs:
        if d.get("doc_id") == doc_id:
            doc_hash = d.get("hash", "") or d.get("file_hash", "")
            if doc_hash and not doc_hash.startswith("sha256:"):
                doc_hash = f"sha256:{doc_hash}"

            fields = [
                ("doc_id", d.get("doc_id", "N/A")),
                ("filename", d.get("filename", "N/A")),
                ("hash", doc_hash or "N/A"),
                ("upload_date", d.get("upload_date", "N/A")),
                ("source_type", d.get("source_type", "N/A")),
                ("domain", d.get("domain", "N/A")),
                ("trust_baseline", d.get("trust_baseline", "N/A")),
                ("page_count", d.get("page_count", "N/A")),
                ("abstract", d.get("abstract", "N/A")),
                ("ingest_method", d.get("ingest_method", "N/A")),
                ("store_text", str(d.get("store_text", "N/A"))),
            ]

            width = 20
            lines = ["Document metadata:"]
            for key, val in fields:
                lines.append(f"  {key:<{width}}: {val}")
            return "\n".join(lines)

    return f"Document '{doc_id}' not found."


# ---------------------------------------------------------------------------
# Command: list_facts_about
# ---------------------------------------------------------------------------

def list_facts_about(entity: str, trust_min: float = 0.0, limit: int = 20) -> str:
    """List facts (assertions) that mention a given entity.

    Reads .weslr/fact_assertions.jsonl and returns facts where the subject
    or object contains the given entity string (case-insensitive substring).
    Optionally filters by minimum trust_score.

    Handles both old schema (source_event_ref) and new extended schema
    (source_doc_id, source_reference, trust_score, extraction_pattern).

    Args:
        entity: Substring to search in subject or object fields
        trust_min: Minimum trust_score threshold (default 0.0 = no filter)
        limit: Maximum number of facts to return (default 20)

    Returns:
        Formatted list of facts with citation, or a not-found message.
    """
    facts = _read_jsonl(_facts_path())

    if not facts:
        return (
            "No fact assertions found. "
            "Run the fact extraction pipeline first."
        )

    entity_lower = entity.lower()
    matched = []

    for f in facts:
        subject = f.get("subject", "")
        obj = f.get("object", "")

        if entity_lower not in subject.lower() and entity_lower not in obj.lower():
            continue

        # trust_score lives at top level or under a different key — handle both
        trust_score = f.get("trust_score")
        if trust_score is None:
            # Try legacy location
            trust_score = f.get("score")

        if trust_score is not None and trust_score < trust_min:
            continue

        fact_id = f.get("fact_id") or f.get("id") or ""
        assertion = f"{subject} — {obj}" if subject and obj else subject or obj

        # Source doc id
        source_doc_id = f.get("source_doc_id") or f.get("source_event_ref") or ""

        # Extraction pattern (confidence indicator)
        extraction_pattern = f.get("extraction_pattern") or ""

        # Build citation
        source_ref = f.get("source_reference")
        citation = build_source_citation(source_ref, source_doc_id)

        matched.append({
            "fact_id": fact_id,
            "assertion": assertion,
            "trust_score": trust_score,
            "source_doc_id": source_doc_id,
            "extraction_pattern": extraction_pattern,
            "citation": citation,
        })

        if len(matched) >= limit:
            break

    if not matched:
        return (
            f"No facts found mentioning '{entity}' "
            f"with trust >= {trust_min}."
        )

    total = len(matched)
    header = f"{'fact_id':<10} {'assertion':<50} {'trust':<7} {'source_doc_id':<15} {'pattern':<25}"
    sep = "-" * len(header)
    lines = [f"Found {total} fact(s) about '{entity}' (trust >= {trust_min}):", header, sep]

    for fact in matched:
        score_str = f"{fact['trust_score']:.2f}" if fact["trust_score"] is not None else "N/A"
        assertion = fact["assertion"][:50]
        pattern = fact["extraction_pattern"][:25] if fact["extraction_pattern"] else "N/A"
        citation_note = f" [{fact['citation']}]" if fact["citation"] and fact["citation"] != "unknown" else ""

        lines.append(
            f"{fact['fact_id']:<10} {assertion:<50} {score_str:<7} "
            f"{fact['source_doc_id']:<15} {pattern:<25}{citation_note}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Command: show_trust_breakdown
# ---------------------------------------------------------------------------

def show_trust_breakdown(fact_id: str) -> str:
    """Show the trust score breakdown for a specific fact.

    Reads .weslr/fact_assertions.jsonl and returns a formatted trust analysis
    showing: source_type (base trust), extraction_pattern (confidence indicator),
    trust_score formula, and final score.

    Args:
        fact_id: The fact identifier to look up

    Returns:
        Formatted trust breakdown, or a not-found message.
    """
    facts = _read_jsonl(_facts_path())

    for f in facts:
        fid = f.get("fact_id") or f.get("id") or ""
        if fid != fact_id:
            continue

        # Extract fields
        source_type = f.get("source_type", "N/A")
        extraction_pattern = f.get("extraction_pattern", "N/A")
        trust_score = f.get("trust_score")
        subject = f.get("subject", "N/A")
        obj = f.get("object", "N/A")

        # Base trust mapping (deterministic heuristics)
        base_trust_map = {
            "paper":       0.90,
            "web":         0.70,
            "document":    0.80,
            "doc":         0.80,
            "manual":      1.00,
            "api":         0.85,
        }
        base_trust = base_trust_map.get(source_type.lower(), 0.75)

        # Confidence modifier from extraction pattern
        pattern_confidence_map = {
            "exact_match":    1.00,
            "structured":     0.95,
            "inferred":       0.75,
            "fuzzy":          0.60,
        }
        confidence_mod = pattern_confidence_map.get(extraction_pattern.lower(), 0.80) if extraction_pattern else 0.80

        # Compute formula string
        formula = f"base_trust({source_type})={base_trust} × confidence({extraction_pattern})={confidence_mod}"
        computed = round(base_trust * confidence_mod, 4)
        final_score = trust_score if trust_score is not None else computed

        lines = [
            f"Trust breakdown for fact '{fact_id}':",
            f"  assertion    : {subject} — {obj}",
            f"  source_type  : {source_type}  [base trust = {base_trust}]",
            f"  extraction  : {extraction_pattern}  [confidence modifier = {confidence_mod}]",
            f"  formula     : {formula}",
            f"  trust_score : {final_score:.4f}",
        ]
        return "\n".join(lines)

    return f"Fact '{fact_id}' not found."