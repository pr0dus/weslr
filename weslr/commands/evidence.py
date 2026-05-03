"""Evidence packet query commands — read-only."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = ".weslr"
PACKET_FILE = "external_evidence_packets.jsonl"
PACKET_STORE_PATH = Path(DATA_DIR) / PACKET_FILE


def _load_packets(source: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    path = PACKET_STORE_PATH
    if not path.exists():
        return []
    results = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if source and record.get("source") != source:
                    continue
                results.append(record)
                if len(results) >= limit:
                    break
    except OSError:
        pass
    return results


def list_packets(source: Optional[str] = None, limit: int = 20) -> str:
    """List recent evidence packets, optionally filtered by source."""
    packets = _load_packets(source=source, limit=limit)
    if not packets:
        return "No evidence packets found."

    lines = [f"Evidence packets ({len(packets)} recent):"]
    lines.append(f"{'packet_id':<25} {'source':<10} {'query':<40} {'results':>8} {'retrieved_at':>20}")
    lines.append("-" * 110)

    for p in packets:
        q = (p.get("query", "") or "")[:40]
        src = p.get("source", "")
        pid = p.get("packet_id", "")
        cnt = p.get("result_count", 0)
        ts = p.get("retrieved_at", "")[:19]
        lines.append(f"{pid:<25} {src:<10} {q:<40} {cnt:>8} {ts:>20}")

    return "\n".join(lines)


def get_packet(packet_id: str) -> str:
    """Show full details of one packet."""
    packets = _load_packets(limit=500)
    for p in packets:
        if p.get("packet_id") == packet_id:
            lines = [f"Packet: {packet_id}", f"Source: {p.get('source')}", f"Query: {p.get('query')}",
                     f"Retrieved: {p.get('retrieved_at')}", f"Result count: {p.get('result_count')}", ""]
            results = p.get("results", [])
            if results:
                lines.append(f"Top results ({len(results)} total):")
                for i, r in enumerate(results[:5], 1):
                    authors_str = ", ".join(r.get("authors", [])[:3])
                    if len(r.get("authors", [])) > 3:
                        authors_str += " et al."
                    lines.append(f"  {i}. {r.get('title', 'N/A')}")
                    lines.append(f"     Authors: {authors_str}")
                    lines.append(f"     Journal: {r.get('journal', 'N/A')} ({r.get('year', 'N/A')})")
                    lines.append(f"     PMID: {r.get('pmid', 'N/A')} — {r.get('url', 'N/A')}")
                    abstract = (r.get("abstract", "") or "")[:200]
                    if abstract:
                        lines.append(f"     Abstract: {abstract}...")
                    lines.append("")
            return "\n".join(lines)
    return f"Packet '{packet_id}' not found."


def list_pubmed_facts(limit: int = 30) -> str:
    """List facts extracted from PubMed abstracts.

    Reads fact_assertions.jsonl and filters to source_type = pubmed_abstract.
    Handles both old format (no source_type) and new format gracefully.
    """
    from commands.documents import build_source_citation

    path = Path(".weslr/fact_assertions.jsonl")
    if not path.exists():
        return "No fact assertions found."

    facts = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Only PubMed-derived facts
                src_type = record.get("source_type", "")
                if src_type not in ("pubmed_abstract", "pubmed"):
                    continue
                facts.append(record)
                if len(facts) >= limit:
                    break
    except OSError:
        return "Could not read fact_assertions.jsonl."

    if not facts:
        return "No PubMed-derived facts found."

    lines = [f"PubMed facts ({len(facts)}):"]
    lines.append(f"{'fact_id':<20} {'predicate':<30} {'subject / object':<35} {'trust':>6}")
    lines.append("-" * 100)

    for fact in facts:
        fid = fact.get("fact_id", "?")[:20]
        pred = fact.get("predicate", "?")[:30]
        subj = (fact.get("subject", "") or "")[:17]
        obj = (fact.get("object", "") or "")[:17]
        trust = fact.get("trust_score", 0.0)
        src_ref = fact.get("source_reference", {})
        citation = build_source_citation(src_ref, fact.get("source_doc_id", ""))
        lines.append(f"{fid:<20} {pred:<30} {subj:<17} {obj:<17} {trust:>6.2f}")
        if citation:
            lines.append(f"  Source: {citation}")

    return "\n".join(lines)