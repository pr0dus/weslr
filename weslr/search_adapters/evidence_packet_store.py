"""External evidence packet storage — append-only JSONL."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = ".weslr"
PACKET_FILE = "external_evidence_packets.jsonl"
PACKET_STORE_PATH = Path(DATA_DIR) / PACKET_FILE


def _packet_path(doc_store_path: Optional[Path | str] = None) -> Path:
    if doc_store_path is None:
        return PACKET_STORE_PATH
    return Path(doc_store_path)


def append_evidence_packet(
    packet: Dict[str, Any],
    doc_store_path: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """Append an evidence packet to external_evidence_packets.jsonl.
    
    Args:
        packet: dict with record_type, packet_id, source, query, retrieved_at,
                result_count, results, authority, automatic_change, hidden_learning, raw_prompt_stored
        doc_store_path: optional override path
    
    Returns:
        dict with status: "appended", path
    """
    import copy
    path = _packet_path(doc_store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    out = copy.deepcopy(packet)
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
    doc_store_path: Optional[Path | str] = None,
) -> List[Dict[str, Any]]:
    """Load evidence packets with optional source filter."""
    path = _packet_path(doc_store_path)
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
    doc_store_path: Optional[Path | str] = None,
) -> Optional[Dict[str, Any]]:
    """Find a packet by packet_id."""
    path = _packet_path(doc_store_path)
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