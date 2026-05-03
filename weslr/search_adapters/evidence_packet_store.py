"""
External evidence packet storage — append-only JSONL.
Multi-tenant aware via tenant_context.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from weslr.tenant_context import resolve_path

DEFAULT_PACKET_STORE_REL = ".weslr/external_evidence_packets.jsonl"


def _resolve_packet_path(
    doc_store_path: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Path:
    """Resolve the evidence packet store path for the current tenant."""
    if doc_store_path:
        return resolve_path(doc_store_path, tenant_id)
    return resolve_path(DEFAULT_PACKET_STORE_REL, tenant_id)


def append_evidence_packet(
    packet: Dict[str, Any],
    tenant_id: Optional[str] = None,
    doc_store_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Append an evidence packet to external_evidence_packets.jsonl.

    Multi-tenant aware: path resolved through tenant_context.

    Args:
        packet: dict with record_type, packet_id, source, query, retrieved_at,
                study_count, studies, authority
        tenant_id: Optional tenant ID
        doc_store_path: optional path override

    Returns:
        dict with status: "appended", path, packet_id
    """
    path = _resolve_packet_path(doc_store_path, tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    out = dict(packet)
    if "packet_id" not in out:
        ts = int(datetime.now(timezone.utc).timestamp())
        out["packet_id"] = f"ev_{ts}_{uuid.uuid4().hex[:8]}"

    line = json.dumps(out, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return {"status": "appended", "path": str(path), "packet_id": out["packet_id"]}


def load_packets(
    source: Optional[str] = None,
    limit: int = 50,
    tenant_id: Optional[str] = None,
    doc_store_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Load evidence packets with optional source filter.

    Multi-tenant aware.
    """
    path = _resolve_packet_path(doc_store_path, tenant_id)
    if not path.exists():
        return []

    results: List[Dict[str, Any]] = []
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


def get_packet(
    packet_id: str,
    tenant_id: Optional[str] = None,
    doc_store_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Find a packet by packet_id.

    Multi-tenant aware.
    """
    path = _resolve_packet_path(doc_store_path, tenant_id)
    if not path.exists():
        return None

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
                if record.get("packet_id") == packet_id:
                    return record
    except OSError:
        pass
    return None